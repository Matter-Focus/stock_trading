import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd
import os
from src.data import get_stock_data, save_to_csv, load_from_csv, generate_mock_data


def test_generate_mock_data():
    df = generate_mock_data(days=20, start_price=10.0)

    assert isinstance(df, pd.DataFrame)
    assert len(df) >= 14
    assert list(df.columns) == ["open", "close", "high", "low", "volume"]
    assert df.index.name == "date"
    assert pd.api.types.is_datetime64_any_dtype(df.index)


def test_mock_data_range():
    df = generate_mock_data(days=10, start_price=5.0)

    assert df["open"].min() > 0
    assert df["close"].min() > 0
    assert df["high"].min() > 0
    assert df["low"].min() > 0
    assert df["volume"].min() > 0

    for i in range(len(df) - 1):
        assert df.index[i + 1] > df.index[i]


def test_save_and_load_csv():
    df = generate_mock_data(days=10)
    temp_file = "test_temp.csv"

    try:
        save_to_csv(df, temp_file)
        assert os.path.exists(temp_file)

        loaded_df = load_from_csv(temp_file)
        assert loaded_df is not None
        assert len(loaded_df) == len(df)
        assert list(loaded_df.columns) == list(df.columns)
        assert pd.api.types.is_datetime64_any_dtype(loaded_df.index)
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_load_from_nonexistent_file():
    result = load_from_csv("nonexistent_file_xyz.csv")
    assert result is None


def test_mock_data_price_logic():
    df = generate_mock_data(days=5, start_price=10.0)

    for i in range(len(df)):
        row = df.iloc[i]
        assert row["high"] >= max(row["open"], row["close"])
        assert row["low"] <= min(row["open"], row["close"])


if __name__ == "__main__":
    import sys
    print("Running tests...")

    tests = [
        ("test_generate_mock_data", test_generate_mock_data),
        ("test_mock_data_range", test_mock_data_range),
        ("test_save_and_load_csv", test_save_and_load_csv),
        ("test_load_from_nonexistent_file", test_load_from_nonexistent_file),
        ("test_mock_data_price_logic", test_mock_data_price_logic),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            print("[OK] %s: PASSED" % name)
            passed += 1
        except AssertionError as e:
            print("[FAIL] %s: FAILED - %s" % (name, e))
            failed += 1
        except Exception as e:
            print("[ERROR] %s: ERROR - %s" % (name, e))
            failed += 1

    print("\n%d passed, %d failed" % (passed, failed))
    sys.exit(0 if failed == 0 else 1)