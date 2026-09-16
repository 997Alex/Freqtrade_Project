"""
EmaRsiTrendStrategy — Strategia trend-following con pullback RSI per Freqtrade
================================================================================

COSA FA
-------
1. Identifica un trend rialzista di fondo: EMA50 > EMA200 (medio periodo).
2. Entra in acquisto SOLO durante un pullback dentro quel trend: RSI < 30
   (non compra in un downtrend, non insegue massimi).
3. Esce con: take-profit a scaglioni decrescenti nel tempo (minimal_roi),
    trailing stop una volta in guadagno, stop loss fisso al -3%,
    oppure se RSI > 75 (ipercomprato estremo).

PERCHÉ QUESTA STRATEGIA E NON UNA "BLACK BOX"
----------------------------------------------
- È completamente leggibile: per ogni trade sai esattamente qual è stata
  la condizione che lo ha aperto e chiuso (vedi enter_tag / exit_tag).
- Pochi parametri = meno rischio di overfitting rispetto a strategie con
  centinaia di condizioni ottimizzate a posteriori sui dati storici.
- NON è garanzia di profitto. Nessuna strategia lo è. Questo è un punto
  di partenza onesto da backtestare, ottimizzare e testare in dry-run
  PRIMA di usare soldi veri.

COME USARLA
-----------
1. Installa Freqtrade (richiede Docker o Python 3.11+):
   https://www.freqtrade.io/en/stable/installation/

2. Copia questo file in user_data/strategies/ema_rsi_trend_strategy.py

3. Scarica dati storici reali (esempio con Kraken, timeframe 1h, dal 2023):
   freqtrade download-data --exchange kraken --pairs BTC/EUR ETH/EUR \
       -t 1h --timerange 20230101-

4. Fai un backtest vero (non fidarti di numeri trovati online):
   freqtrade backtesting --strategy EmaRsiTrendStrategy \
       --timerange 20230101- --breakdown month

   Guarda soprattutto: Max Drawdown, Sharpe/Sortino ratio, e il numero
   di trade — non solo il "profitto totale", che da solo dice poco.

5. Ottimizza i parametri con hyperopt (facoltativo, ma occhio all'overfitting:
   ottimizza su un periodo e verifica su un periodo DIVERSO, mai visto
   durante l'ottimizzazione — altrimenti i numeri belli non si ripeteranno
   nel trading live).

6. SOLO dopo settimane di dry-run pulito (--dry-run in config.json,
   nessun soldo reale coinvolto) valuta il live, e comunque con capitale
   che puoi permetterti di perdere interamente.

7. Confronta questa strategia con NostalgiaForInfinity (repo pubblica
   iterativv/NostalgiaForInfinity) sugli STESSI dati e sullo STESSO
   periodo, prima di scegliere quale usare con soldi veri.

Non è consulenza finanziaria. Il trading — specialmente crypto e con
capitale piccolo — comporta il rischio concreto di perdere tutto il
capitale investito.
"""

from pandas import DataFrame
from freqtrade.strategy import IStrategy
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class EmaRsiTrendStrategy(IStrategy):
    INTERFACE_VERSION = 3

    # Timeframe delle candele. 1h è un buon compromesso tra rumore e
    # reattività per chi inizia; su timeframe più bassi (5m, 15m) le
    # commissioni pesano molto di più su un capitale piccolo come 1000€.
    timeframe = "1h"

    # Solo posizioni long: più semplice, adatto a spot trading (no derivati).
    can_short = False

    # --- Take profit a scaglioni: più tempo passa, meno pretendi ---
    # "0"   -> appena entri, target 15%
    # "60"  -> dopo 60 minuti, accetti anche solo 8%
    # "180" -> dopo 3 ore, 4%
    # "720" -> dopo 12 ore, 2% (meglio uscire con poco che restare bloccati)
    minimal_roi = {
        "0": 0.15,
        "60": 0.08,
        "180": 0.04,
        "720": 0.02,
    }

    # Stop loss fisso: mai perdere più del 3% su una singola posizione.
    # Sostituisce l'approccio "quasi mai in stop loss" di alcune strategie
    # community, che sulla carta sembra ridurre le perdite ma in pratica
    # blocca capitale su posizioni pesantemente in rosso per mesi.
    stoploss = -0.03

    # Trailing stop: una volta che il trade è in guadagno, blocca parte
    # del profitto invece di lasciare che torni in perdita.
    # Offset > positive assicura che il trailing stop si attivi correttamente.
    trailing_stop = True
    trailing_stop_positive = 0.02
    trailing_stop_positive_offset = 0.04
    trailing_only_offset_is_reached = True

    # Candele minime necessarie prima che EMA200 sia affidabile.
    startup_candle_count = 210

    # Protezioni integrate di Freqtrade: mettono in pausa il trading su
    # una coppia dopo una serie di perdite consecutive, per limitare i
    # danni durante fasi di mercato ostili alla strategia.
    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 4},
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 48,
                "trade_limit": 20,
                "stop_duration_candles": 12,
                "max_allowed_drawdown": 0.15,
            },
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 24,
                "trade_limit": 3,
                "stop_duration_candles": 12,
                "only_per_pair": True,
            },
        ]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # --- Trend di fondo ---
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)

        # --- Timing d'ingresso ---
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        # --- Contesto di volatilità (usato solo come riferimento/plot) ---
        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe), window=20, stds=2
        )
        dataframe["bb_lowerband"] = bollinger["lower"]
        dataframe["bb_middleband"] = bollinger["mid"]

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["ema50"] > dataframe["ema200"])   # trend rialzista di fondo
                & (dataframe["close"] > dataframe["ema200"])  # prezzo sopra il trend
                & (dataframe["rsi"] < 30)                      # pullback, non FOMO su massimi
                & (dataframe["volume"] > 0)                    # candela con volume reale
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "trend_pullback")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi"] > 75)
            )
            & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "overbought")

        return dataframe
