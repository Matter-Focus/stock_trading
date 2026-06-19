# -*- coding: utf-8 -*-
from typing import Optional
import pandas as pd
import os
from datetime import datetime, timedelta


def generate_mock_data(days: int = 252, start_price: float = 10.0) -> pd.DataFrame:
    """
    Generate mock stock daily data for testing.

    Args:
        days: Number of trading days
        start_price: Starting price

    Returns:
        DataFrame with columns: date, open, close, high, low, volume
    """
    dates = []
    opens = []
    closes = []
    highs = []
    lows = []
    volumes = []

    current_date = datetime.now() - timedelta(days=days * 2)
    current_price = start_price

    for _ in range(days):
        if current_date.weekday() < 5:
            change = (current_price * (0.02 * (os.urandom(1)[0] / 255 - 0.5)))
            open_price = current_price
            close_price = current_price + change
            high_price = max(open_price, close_price) * (1 + 0.005)
            low_price = min(open_price, close_price) * (1 - 0.005)
            volume = int(1000000 + os.urandom(4)[0] * 10000)

            dates.append(current_date.strftime("%Y-%m-%d"))
            opens.append(round(open_price, 2))
            closes.append(round(close_price, 2))
            highs.append(round(high_price, 2))
            lows.append(round(low_price, 2))
            volumes.append(volume)

            current_price = close_price

        current_date += timedelta(days=1)

    df = pd.DataFrame({
        "date": dates,
        "open": opens,
        "close": closes,
        "high": highs,
        "low": lows,
        "volume": volumes
    })

    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    df = df.sort_index(ascending=True)

    return df


def get_stock_data(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Get A-share daily stock data.

    Args:
        stock_code: Stock code like "000001"
        start_date: Start date in "YYYYMMDD" format
        end_date: End date in "YYYYMMDD" format

    Returns:
        DataFrame with columns: date, open, close, high, low, volume
    """
    import akshare as ak
    df = ak.stock_zh_a_hist(
        symbol=stock_code,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq"
    )

    column_mapping = {
        "日期": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume"
    }

    df = df.rename(columns=column_mapping)
    df = df[["date", "open", "close", "high", "low", "volume"]]
    df = df.dropna()
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    df = df.sort_index(ascending=True)

    return df


def save_to_csv(df: pd.DataFrame, filename: str) -> None:
    """
    Save DataFrame to CSV file.

    Args:
        df: DataFrame to save
        filename: Output filename
    """
    df.to_csv(filename)


def load_from_csv(filename: str) -> Optional[pd.DataFrame]:
    """
    Load DataFrame from CSV file.

    Args:
        filename: Input filename

    Returns:
        DataFrame or None if file doesn't exist
    """
    if os.path.exists(filename):
        df = pd.read_csv(filename, parse_dates=["date"], index_col="date")
        return df
    return None


if __name__ == "__main__":
    stock_code = "000001"
    start_date = "20250619"
    end_date = "20260619"

    cache_file = f"{stock_code}_{start_date}_{end_date}.csv"
    df = load_from_csv(cache_file)

    if df is None:
        try:
            df = get_stock_data(stock_code, start_date, end_date)
            save_to_csv(df, cache_file)
            print(f"Data fetched from API and saved to {cache_file}")
        except Exception as e:
            print(f"API fetch failed: {e}")
            print("Using mock data for testing...")
            df = generate_mock_data(days=252)
            save_to_csv(df, cache_file)
            print(f"Mock data generated and saved to {cache_file}")
    else:
        print(f"Data loaded from cache: {cache_file}")

    print("\nFirst 5 rows:")
    print(df.head())
    print(f"\nTotal rows: {len(df)}")
    print(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")