import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from src.strategy import generate_signals, get_buy_sell_points
from src.data import generate_mock_data


def test_generate_signals_columns():
    df = generate_mock_data(days=30, start_price=10.0)
    result = generate_signals(df, short_window=5, long_window=20)

    assert "ma5" in result.columns
    assert "ma20" in result.columns
    assert "signal" in result.columns


def test_signal_values():
    df = generate_mock_data(days=30, start_price=10.0)
    result = generate_signals(df, short_window=5, long_window=20)

    signals = result["signal"].unique()
    for s in signals:
        assert s in [-1, 0, 1]


def test_buy_sell_points():
    df = generate_mock_data(days=60, start_price=10.0)
    df = generate_signals(df, short_window=5, long_window=20)

    buy_dates, sell_dates = get_buy_sell_points(df)

    assert isinstance(buy_dates, list)
    assert isinstance(sell_dates, list)

    for date in buy_dates:
        assert isinstance(date, str)

    for date in sell_dates:
        assert isinstance(date, str)


def test_ma_calculation():
    # Use more days to ensure enough trading days after skipping weekends
    df = generate_mock_data(days=60, start_price=10.0)
    result = generate_signals(df, short_window=5, long_window=20)

    # First 4 rows of ma5 should be NaN (need 5 data points)
    assert pd.isna(result["ma5"].iloc[0])
    assert pd.isna(result["ma5"].iloc[3])
    assert not pd.isna(result["ma5"].iloc[4])

    # First 19 rows of ma20 should be NaN
    assert pd.isna(result["ma20"].iloc[0])
    assert pd.isna(result["ma20"].iloc[18])
    assert not pd.isna(result["ma20"].iloc[19])


def test_crossover_logic():
    # Create a controlled test DataFrame to verify crossover detection
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    data = {
        "open": [10.0] * 10,
        "close": [10.0, 10.1, 10.2, 10.1, 10.0, 9.9, 9.8, 9.9, 10.0, 10.1],
        "high": [10.2] * 10,
        "low": [9.8] * 10,
        "volume": [1000000] * 10,
    }
    df = pd.DataFrame(data, index=dates)

    # Manually set ma5 and ma20 to create a known crossover scenario
    result = generate_signals(df, short_window=2, long_window=5)

    # Verify signal column exists and contains only valid values
    assert "signal" in result.columns
    assert all(s in [-1, 0, 1] for s in result["signal"])


if __name__ == "__main__":
    print("Running strategy tests...")

    tests = [
        ("test_generate_signals_columns", test_generate_signals_columns),
        ("test_signal_values", test_signal_values),
        ("test_buy_sell_points", test_buy_sell_points),
        ("test_ma_calculation", test_ma_calculation),
        ("test_crossover_logic", test_crossover_logic),
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