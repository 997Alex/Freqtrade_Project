"""
EmaRsiTrendStrategyHyperoptV3 — Split ADX in ENTRY, exit differenziato
=============================================================================

ENTRY 1: trend_pullback — RSI<31 + ADX<=breakout_adx (exit rapido su RSI>sell_rsi)
ENTRY 2: trend_breakout — RSI<31 + ADX>breakout_adx (exit lungo su EMA50<EMA200)

Il mercato con RSI<31 e ADX alto indica un pullback in un trend molto forte.
In quel caso il trade resta aperto più a lungo per catturare il rally.
"""

from datetime import datetime
from pandas import DataFrame
from freqtrade.strategy import IStrategy, IntParameter
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class EmaRsiTrendStrategyHyperoptV3(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    # --- Parametri ---
    buy_rsi = IntParameter(20, 45, default=31, space="buy", optimize=True)
    sell_rsi = IntParameter(60, 85, default=68, space="sell", optimize=True)
    breakout_adx = IntParameter(10, 40, default=15, space="buy", optimize=True)

    # --- ROI / Stoploss / Trailing ---
    minimal_roi = {
        "0": 0.08,
        "60": 0.04,
        "180": 0.02,
        "720": 0.01,
    }
    stoploss = -0.034

    trailing_stop = True
    trailing_stop_positive = 0.017
    trailing_stop_positive_offset = 0.055
    trailing_only_offset_is_reached = True

    max_open_trades = 4
    startup_candle_count = 210

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, side: str, **kwargs) -> float:
        return 3.0

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
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe), window=20, stds=2
        )
        dataframe["bb_lowerband"] = bollinger["lower"]
        dataframe["bb_middleband"] = bollinger["mid"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # --- trend_pullback: ADX basso → exit rapido ---
        dataframe.loc[
            (
                (dataframe["ema50"] > dataframe["ema200"])
                & (dataframe["close"] > dataframe["ema200"])
                & (dataframe["rsi"] < self.buy_rsi.value)
                & (dataframe["adx"] <= self.breakout_adx.value)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "trend_pullback")

        # --- trend_breakout: ADX alto → exit lungo ---
        dataframe.loc[
            (
                (dataframe["ema50"] > dataframe["ema200"])
                & (dataframe["close"] > dataframe["ema200"])
                & (dataframe["rsi"] < self.buy_rsi.value)
                & (dataframe["adx"] > self.breakout_adx.value)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "trend_breakout")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # --- TREND_BREAKOUT: exit su inversione trend ---
        dataframe.loc[
            (
                (dataframe["ema50"] < dataframe["ema200"])
                & (dataframe["enter_tag"] == "trend_breakout")
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "trend_exhausted")

        # --- TREND_PULLBACK: exit su RSI ipercomprato ---
        dataframe.loc[
            (
                (dataframe["rsi"] > self.sell_rsi.value)
                & (dataframe["enter_tag"] == "trend_pullback")
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "trend_exhausted")

        return dataframe
