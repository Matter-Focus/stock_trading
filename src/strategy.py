# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from typing import List, Tuple


def generate_signals(df: pd.DataFrame, short_window: int = 5, long_window: int = 20) -> pd.DataFrame:
    """
    Generate dual moving average crossover signals.

    Args:
        df: DataFrame with columns [open, close, high, low, volume]
        short_window: Short moving average window (default 5)
        long_window: Long moving average window (default 20)

    Returns:
        DataFrame with new columns: ma5, ma20, signal
        signal=1 (buy), signal=-1 (sell), signal=0 (hold)
    """
    result = df.copy()

    # Calculate moving averages using close price
    result["ma5"] = result["close"].rolling(window=short_window).mean()
    result["ma20"] = result["close"].rolling(window=long_window).mean()

    # Initialize signal column
    result["signal"] = 0

    # Calculate crossovers: when MA5 crosses MA20
    for i in range(1, len(result)):
        prev_ma5 = result["ma5"].iloc[i - 1]
        prev_ma20 = result["ma20"].iloc[i - 1]
        curr_ma5 = result["ma5"].iloc[i]
        curr_ma20 = result["ma20"].iloc[i]

        # Skip if either MA is NaN
        if pd.isna(prev_ma5) or pd.isna(prev_ma20) or pd.isna(curr_ma5) or pd.isna(curr_ma20):
            continue

        # MA5 crosses above MA20: buy signal
        if prev_ma5 <= prev_ma20 and curr_ma5 > curr_ma20:
            result.iloc[i, result.columns.get_loc("signal")] = 1
        # MA5 crosses below MA20: sell signal
        elif prev_ma5 >= prev_ma20 and curr_ma5 < curr_ma20:
            result.iloc[i, result.columns.get_loc("signal")] = -1

    return result


def get_buy_sell_points(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """
    Get buy and sell signal dates from the DataFrame.

    Args:
        df: DataFrame with 'signal' column

    Returns:
        Tuple of (buy_dates, sell_dates)
    """
    buy_dates = []
    sell_dates = []

    for idx, row in df.iterrows():
        if row["signal"] == 1:
            buy_dates.append(str(idx.date()) if hasattr(idx, "date") else str(idx))
        elif row["signal"] == -1:
            sell_dates.append(str(idx.date()) if hasattr(idx, "date") else str(idx))

    return buy_dates, sell_dates


if __name__ == "__main__":
    from src.data import generate_mock_data, save_to_csv, load_from_csv

    cache_file = "strategy_test_data.csv"
    df = load_from_csv(cache_file)

    if df is None:
        df = generate_mock_data(days=100, start_price=10.0)
        save_to_csv(df, cache_file)
        print("Generated mock data for strategy testing")
    else:
        print("Loaded cached data for strategy testing")

    # Generate signals
    df = generate_signals(df, short_window=5, long_window=20)

    # Print signal summary
    print("\nSignal summary:")
    print("  Total buy signals: %d" % (df["signal"] == 1).sum())
    print("  Total sell signals: %d" % (df["signal"] == -1).sum())
    print("  Total hold signals: %d" % (df["signal"] == 0).sum())

    # Get buy/sell points
    buy_dates, sell_dates = get_buy_sell_points(df)
    print("\nBuy dates: %s" % buy_dates)
    print("Sell dates: %s" % sell_dates)

    # Print last 10 rows with non-zero signals
    print("\nLast 10 rows with signals:")
    signal_rows = df[df["signal"] != 0].tail(10)
    if len(signal_rows) > 0:
        print(signal_rows[["close", "ma5", "ma20", "signal"]])
    else:
        print("No signals generated in last 10 rows")
        print("\nLast 10 rows for reference:")
        print(df.tail(10)[["close", "ma5", "ma20", "signal"]])