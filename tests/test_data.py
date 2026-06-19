import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from src.data import save_to_csv, load_from_csv


def test_save_and_load_csv():
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    df = pd.DataFrame({
        "open": [10.0] * 10,
        "close": [10.1] * 10,
        "high": [10.2] * 10,
        "low": [9.9] * 10,
        "volume": [1000000] * 10
    }, index=dates)

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


if __name__ == "__main__":
    print("Running tests...")

    tests = [
        ("test_save_and_load_csv", test_save_and_load_csv),
        ("test_load_from_nonexistent_file", test_load_from_nonexistent_file),
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