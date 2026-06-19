import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
from src.backtest import BacktestEngine, Trade
from src.data import generate_mock_data
from src.strategy import generate_signals


def test_backtest_engine_initialization():
    engine = BacktestEngine(
        initial_capital=100000.0,
        commission_rate=0.00025,
        stamp_tax_rate=0.0005,
        slippage=0.001
    )

    assert engine.initial_capital == 100000.0
    assert engine.commission_rate == 0.00025
    assert engine.stamp_tax_rate == 0.0005
    assert engine.slippage == 0.001
    assert engine.capital == 100000.0
    assert engine.position == 0
    assert engine.max_position == 1000


def test_commission_calculation():
    engine = BacktestEngine(commission_rate=0.00025)

    commission = engine._calculate_commission(10.0, 100)
    assert commission == 5.0

    commission = engine._calculate_commission(10.0, 20000)
    assert commission == 50.0


def test_stamp_tax_calculation():
    engine = BacktestEngine(stamp_tax_rate=0.0005)

    tax = engine._calculate_stamp_tax(10.0, 1000)
    assert tax == 5.0


def test_buy_sell_basic():
    dates = pd.date_range("2026-01-01", periods=5, freq="D")
    data = {
        "open": [10.0, 10.1, 10.2, 10.3, 10.4],
        "close": [10.0, 10.1, 10.2, 10.3, 10.4],
        "high": [10.2, 10.3, 10.4, 10.5, 10.6],
        "low": [9.8, 9.9, 10.0, 10.1, 10.2],
        "volume": [1000000, 1000000, 1000000, 1000000, 1000000],
        "signal": [1, 0, -1, 0, 0]
    }
    df = pd.DataFrame(data, index=dates)

    engine = BacktestEngine(initial_capital=100000.0)
    result = engine.run(df)

    assert result["trade_count"] >= 1


def test_limit_up_prevention():
    dates = pd.date_range("2026-01-01", periods=3, freq="D")
    data = {
        "open": [10.0, 11.0, 11.0],
        "close": [10.0, 10.0, 11.0],
        "high": [10.2, 11.2, 11.2],
        "low": [9.8, 9.8, 10.8],
        "volume": [1000000, 1000000, 1000000],
        "signal": [1, 0, 0]
    }
    df = pd.DataFrame(data, index=dates)

    engine = BacktestEngine(initial_capital=100000.0)
    result = engine.run(df)

    assert result["trade_count"] == 0


def test_equity_curve():
    df = generate_mock_data(days=30)
    df = generate_signals(df)

    engine = BacktestEngine(initial_capital=100000.0)
    result = engine.run(df)

    assert len(result["equity_curve"]) == len(df)
    assert len(result["dates"]) == len(df)
    assert result["equity_curve"][0] == 100000.0


def test_return_calculation():
    df = generate_mock_data(days=50)
    df = generate_signals(df)

    engine = BacktestEngine(initial_capital=100000.0)
    result = engine.run(df)

    assert isinstance(result["total_return"], float)
    assert isinstance(result["max_drawdown"], float)
    assert isinstance(result["sharpe_ratio"], float)
    assert result["max_drawdown"] >= 0


def test_max_position_limit():
    df = generate_mock_data(days=10)
    df["signal"] = 1

    engine = BacktestEngine(initial_capital=1000000.0, max_position=500)
    result = engine.run(df)

    assert engine.position <= 500


if __name__ == "__main__":
    print("Running backtest tests...")

    tests = [
        ("test_backtest_engine_initialization", test_backtest_engine_initialization),
        ("test_commission_calculation", test_commission_calculation),
        ("test_stamp_tax_calculation", test_stamp_tax_calculation),
        ("test_buy_sell_basic", test_buy_sell_basic),
        ("test_limit_up_prevention", test_limit_up_prevention),
        ("test_equity_curve", test_equity_curve),
        ("test_return_calculation", test_return_calculation),
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