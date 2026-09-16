"""
EmaRsiTrendStrategyHyperopt — versione ottimizzabile di EmaRsiTrendStrategy
=============================================================================

DIFFERENZA rispetto a ema_rsi_trend_strategy.py:
Le due soglie RSI (ingresso e uscita) non sono piu' numeri fissi ma
IntParameter — hyperopt puo' cercare i valori migliori dentro il range
che definisci, invece di usare quelli scelti a mano.

stoploss, minimal_roi e trailing_stop restano come attributi normali:
Freqtrade li ottimizza automaticamente se aggiungi "roi", "stoploss" e
"trailing" alla lista --spaces del comando hyperopt, senza bisogno di
altri IntParameter/DecimalParameter per quelli.

COME TROVARE IL TUO PUNTO TRA PROFITTO E CONSERVAZIONE
--------------------------------------------------------
1. Cerca sui dati "in-sample" (es. 2022-2023, un anno ribassista + uno
   rialzista, cosi' l'ottimizzatore vede entrambi i regimi):

   freqtrade hyperopt --strategy EmaRsiTrendStrategyHyperopt \
       --hyperopt-loss CalmarHyperOptLoss \
       --spaces buy sell roi stoploss trailing \
       --epochs 300 \
       --timerange 20220101-20240101 \
       -c user_data\\config.json

   Usa CalmarHyperOptLoss se vuoi dare priorita' alla conservazione
   (penalizza il drawdown), SortinoHyperOptLoss per un compromesso,
   o ProfitDrawDownHyperOptLoss per una via di mezzo esplicita.

2. VALIDA su un periodo che l'hyperopt NON ha mai visto (fondamentale:
   altrimenti stai solo misurando quanto bene ha overfittato):

   freqtrade backtesting --strategy EmaRsiTrendStrategyHyperopt \
       --timerange 20240101-20250101 \
       -c user_data\\config.json

   Se i risultati out-of-sample sono molto peggiori di quelli in-sample,
   i parametri trovati sono overfittati: riduci gli epochs, allarga i
   range dei parametri, o accetta che la versione base andava gia' bene.

3. Solo a questo punto confronta 2-3 set di parametri (conservativo vs
   aggressivo) sugli STESSI due periodi, e scegli in base a quanto
   drawdown puoi psicologicamente ed economicamente sopportare — non
   in base a quale numero di profitto e' piu' alto.
"""

from pandas import DataFrame
from freqtrade.strategy import IStrategy, IntParameter
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class EmaRsiTrendStrategyHyperopt(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    # --- Parametri ottimizzabili con hyperopt (--spaces buy sell) ---
    # Range volutamente ampio: 20-45 per l'ingresso copre da "pullback
    # profondo, pochi trade" a "quasi nessun filtro, molti trade".
    buy_rsi = IntParameter(20, 45, default=24, space="buy", optimize=True)
    sell_rsi = IntParameter(60, 85, default=75, space="sell", optimize=True)

    # --- Questi restano ottimizzabili via --spaces roi / stoploss / trailing ---
    # I valori qui sotto sono solo il punto di partenza prima dell'hyperopt.
    minimal_roi = {
        "0": 0.564,
        "438": 0.148,
        "1055": 0.072,
        "2004": 0,
    }
    stoploss = -0.041

    trailing_stop = True
    trailing_stop_positive = 0.158
    trailing_stop_positive_offset = 0.204
    trailing_only_offset_is_reached = False

    startup_candle_count = 210

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
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe), window=20, stds=2
        )
        dataframe["bb_lowerband"] = bollinger["lower"]
        dataframe["bb_middleband"] = bollinger["mid"]

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["ema50"] > dataframe["ema200"])
                & (dataframe["close"] > dataframe["ema200"])
                & (dataframe["rsi"] < self.buy_rsi.value)  # <- ora parametrico
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "trend_pullback")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi"] > self.sell_rsi.value)  # <- ora parametrico
                | (dataframe["ema50"] < dataframe["ema200"])
            )
            & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "trend_exhausted")

        return dataframe
