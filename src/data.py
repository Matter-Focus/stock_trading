# -*- coding: utf-8 -*-
from typing import Optional
import pandas as pd
import os


def _get_exchange_prefix(stock_code: str) -> str:
    if stock_code.startswith("sh") or stock_code.startswith("SH"):
        return ""
    if stock_code.startswith("sz") or stock_code.startswith("SZ"):
        return ""
    if stock_code.startswith("6"):
        return "sh"
    else:
        return "sz"


def get_stock_data(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    import akshare as ak

    symbol = _get_exchange_prefix(stock_code) + stock_code

    df = ak.stock_zh_a_daily(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date
    )

    df = df[["date", "open", "close", "high", "low", "volume"]]
    df = df.dropna()
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    df = df.sort_index(ascending=True)

    return df


def save_to_csv(df: pd.DataFrame, filename: str) -> None:
    df.to_csv(filename, index_label="date")


def load_from_csv(filename: str) -> Optional[pd.DataFrame]:
    if os.path.exists(filename):
        df = pd.read_csv(filename, parse_dates=["date"], index_col="date")
        return df
    return None


if __name__ == "__main__":
    stock_code = "000001"
    start_date = "2025-06-19"
    end_date = "2026-06-19"

    cache_file = f"{stock_code}_{start_date}_{end_date}.csv"
    df = load_from_csv(cache_file)

    if df is None:
        df = get_stock_data(stock_code, start_date, end_date)
        save_to_csv(df, cache_file)
        print(f"Data fetched from API and saved to {cache_file}")
    else:
        print(f"Data loaded from cache: {cache_file}")

    print("\nFirst 5 rows:")
    print(df.head())
    print("\nLast 5 rows:")
    print(df.tail())
    print(f"\nTotal rows: {len(df)}")
    print(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")