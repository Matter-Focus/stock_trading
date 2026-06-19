import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import requests
import pandas as pd
import json


def get_stock_data_real(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Get A-share daily stock data directly from East Money API.
    """
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": "0.%s" % stock_code if stock_code.startswith("0") else "1.%s" % stock_code,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",
        "fqt": "1",
        "beg": start_date,
        "end": end_date,
        "lmt": "1000",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    klines = data.get("data", {}).get("klines", [])

    if not klines:
        raise ValueError("No data returned for stock %s" % stock_code)

    rows = []
    for line in klines:
        parts = line.split(",")
        rows.append({
            "date": parts[0],
            "open": float(parts[1]),
            "close": float(parts[2]),
            "high": float(parts[3]),
            "low": float(parts[4]),
            "volume": int(float(parts[5])),
        })

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    df = df.sort_index(ascending=True)

    return df


if __name__ == "__main__":
    print("Testing real data fetch...")
    try:
        df = get_stock_data_real("000001", "20250601", "20260619")
        print("Success! Fetched %d rows" % len(df))
        print("\nFirst 5 rows:")
        print(df.head())
        print("\nLast 5 rows:")
        print(df.tail())
        print("\nDate range: %s to %s" % (df.index[0].date(), df.index[-1].date()))
    except Exception as e:
        print("Error: %s" % e)
        import traceback
        traceback.print_exc()