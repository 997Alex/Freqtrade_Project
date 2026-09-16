"""
EmaRsiTrendStrategyHyperoptV2 — con spazio di ricerca ristretto
==================================================================

DIFFERENZA rispetto a ema_rsi_trend_strategy_hyperopt.py:
Aggiunge una nested class "HyperOpt" che restringe i range di ricerca
per stoploss e trailing stop. Senza questa, Freqtrade usa i suoi range
di default, che arrivano fino al -35% di stoploss e al 35% di
trailing_stop_positive — abbastanza larghi da produrre le configurazioni
a drawdown 78% viste nel run con SortinoHyperOptLoss.

I valori qui sotto (-10% max stoploss, 0.5%-3% trailing) sono un punto
di partenza ragionevole per un capitale di 1000€, non "il" valore
corretto — puoi restringerli o allargarli in base a quanto drawdown sei
disposto a tollerare.

USO:
    freqtrade hyperopt --strategy EmaRsiTrendStrategyHyperoptV2 \
        --hyperopt-loss ConservativeCalmarLoss \
        --spaces buy sell roi stoploss trailing \
        --epochs 300 \
        --timerange 20220101-20240101 \
        -c user_data\\config.json

    (richiede conservative_calmar_loss.py in user_data/hyperopts/)

Poi valida SEMPRE su un periodo mai visto durante la ricerca:
    freqtrade backtesting --strategy EmaRsiTrendStrategyHyperoptV2 \
        --timerange 20240101-20250101 \
        -c user_data\\config.json
"""

from pandas import DataFrame
from freqtrade.strategy import IStrategy, IntParameter
from freqtrade.optimize.space import SKDecimal, Categorical
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class EmaRsiTrendStrategyHyperoptV2(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    buy_rsi = IntParameter(20, 45, default=35, space="buy", optimize=True)
    sell_rsi = IntParameter(60, 85, default=70, space="sell", optimize=True)

    minimal_roi = {
        "0": 0.08,
        "60": 0.04,
        "180": 0.02,
        "720": 0.01,
    }
    stoploss = -0.05

    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = True

    startup_candle_count = 210

    # --- Restringe lo spazio di ricerca hyperopt per stoploss e trailing ---
    # Senza questo, Freqtrade cerca stoploss fino a -35% e trailing_stop_positive
    # fino a 35%: valori che su 1000€ significano perdite enormi su un
    # singolo trade prima che qualunque protezione intervenga.
    class HyperOpt:
        @staticmethod
        def stoploss_space():
            # Mai oltre il 10% di perdita su un singolo trade
            return [SKDecimal(-0.10, -0.02, decimals=3, name="stoploss")]

        @staticmethod
        def trailing_space():
            return [
                Categorical([True], name="trailing_stop"),
                # Di quanto puo' ritracciare dal massimo prima che il
                # trailing stop scatti: 0.5%-3%, non fino al 35%
                SKDecimal(0.005, 0.03, decimals=3, name="trailing_stop_positive"),
                SKDecimal(
                    0.01, 0.05, decimals=3, name="trailing_stop_positive_offset_p1"
                ),
                Categorical([True], name="trailing_only_offset_is_reached"),
            ]

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
                & (dataframe["rsi"] < self.buy_rsi.value)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "trend_pullback")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["rsi"] > self.sell_rsi.value)
                | (dataframe["ema50"] < dataframe["ema200"])
            )
            & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "trend_exhausted")

        return dataframe
