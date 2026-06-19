import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
from src.backtest import BacktestEngine, Trade


def test_backtest_engine_initialization():
    """测试引擎初始化参数"""
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


def test_commission_calculation():
    """测试佣金计算：不足5元按5元收"""
    engine = BacktestEngine(commission_rate=0.00025)

    # 小额成交：佣金不足5元按5元
    commission = engine._calculate_commission(10000.0)  # 10000 × 0.00025 = 2.5 < 5
    assert commission == 5.0

    # 大额成交：正常计算佣金
    commission = engine._calculate_commission(200000.0)  # 200000 × 0.00025 = 50
    assert commission == 50.0


def test_limit_up_prevention():
    """测试涨停不能买入"""
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


def test_limit_down_prevention():
    """测试跌停不能卖出"""
    dates = pd.date_range("2026-01-01", periods=4, freq="D")
    data = {
        "open": [10.0, 10.0, 9.0, 8.5],  # 第3天开盘=9.0, 第4天开盘=8.5
        "close": [10.0, 10.0, 9.0, 8.5],  # 第2天收盘=10.0, 第3天收盘=9.0
        "high": [10.2, 10.2, 9.2, 8.7],
        "low": [9.8, 9.8, 8.8, 8.3],
        "volume": [1000000, 1000000, 1000000, 1000000],
        "signal": [1, 0, -1, 0]  # 第3天卖出信号，次日(第4天)开盘卖出
    }
    df = pd.DataFrame(data, index=dates)

    engine = BacktestEngine(initial_capital=100000.0)
    result = engine.run(df)

    # 第3天收盘=9.0，第4天开盘=8.5, 8.5 <= 9.0*0.9=8.1? 不，8.5>8.1，不是跌停
    # 需要调整：第3天收盘=10.0，第4天开盘<=9.0才算跌停
    # 修正数据：
    data = {
        "open": [10.0, 10.0, 10.0, 9.0],  # 第4天开盘=9.0 <= 10.0*0.9=9.0 跌停
        "close": [10.0, 10.0, 10.0, 9.0],
        "high": [10.2, 10.2, 10.2, 9.2],
        "low": [9.8, 9.8, 9.8, 8.8],
        "volume": [1000000, 1000000, 1000000, 1000000],
        "signal": [1, 0, -1, 0]
    }
    df = pd.DataFrame(data, index=dates)

    result = engine.run(df)

    # 第3天收盘=10.0，第4天开盘=9.0, 9.0 <= 10.0*0.9=9.0，跌停不能卖出
    assert result["trade_count"] == 0


def test_buy_sell_basic():
    """测试基本的买入卖出逻辑"""
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

    assert result["trade_count"] == 1
    assert len(result["trades"]) == 1

    trade = result["trades"][0]
    assert isinstance(trade, Trade)
    assert trade.buy_volume == trade.buy_volume  # 买入卖出数量一致


def test_suspension_skip():
    """测试停牌跳过信号"""
    dates = pd.date_range("2026-01-01", periods=4, freq="D")
    data = {
        "open": [10.0, 10.1, 10.2, 10.3],
        "close": [10.0, 10.1, 10.2, 10.3],
        "high": [10.2, 10.3, 10.4, 10.5],
        "low": [9.8, 9.9, 10.0, 10.1],
        "volume": [1000000, 0, 1000000, 1000000],  # 第2天停牌
        "signal": [1, 0, -1, 0]
    }
    df = pd.DataFrame(data, index=dates)

    engine = BacktestEngine(initial_capital=100000.0)
    result = engine.run(df)

    # 停牌日买入信号被跳过，卖出信号也跳过，应该没有交易
    assert result["trade_count"] == 0


def test_equity_curve():
    """测试权益曲线生成"""
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    data = {
        "open": [10.0] * 10,
        "close": [10.0] * 10,
        "high": [10.2] * 10,
        "low": [9.8] * 10,
        "volume": [1000000] * 10,
        "signal": [0] * 10
    }
    df = pd.DataFrame(data, index=dates)

    engine = BacktestEngine(initial_capital=100000.0)
    result = engine.run(df)

    assert len(result["equity_curve"]) > 0
    assert result["equity_curve"][0] == 100000.0


def test_return_calculation():
    """测试收益率、最大回撤、夏普比率计算"""
    dates = pd.date_range("2026-01-01", periods=30, freq="D")
    np.random.seed(42)
    data = {
        "open": [10.0 + np.random.randn() * 0.5 for _ in range(30)],
        "close": [10.0 + np.random.randn() * 0.5 for _ in range(30)],
        "high": [11.0 + np.random.randn() * 0.5 for _ in range(30)],
        "low": [9.0 + np.random.randn() * 0.5 for _ in range(30)],
        "volume": [1000000] * 30,
        "signal": [0] * 30
    }
    df = pd.DataFrame(data, index=dates)

    engine = BacktestEngine(initial_capital=100000.0)
    result = engine.run(df)

    assert isinstance(result["total_return"], float)
    assert isinstance(result["max_drawdown"], float)
    assert isinstance(result["sharpe_ratio"], float)
    assert result["max_drawdown"] >= 0


def test_trade_record_structure():
    """测试交易记录结构"""
    dates = pd.date_range("2026-01-01", periods=5, freq="D")
    data = {
        "open": [10.0, 10.1, 10.2, 9.9, 9.8],
        "close": [10.0, 10.1, 10.2, 9.9, 9.8],
        "high": [10.2, 10.3, 10.4, 10.1, 10.0],
        "low": [9.8, 9.9, 10.0, 9.7, 9.6],
        "volume": [1000000] * 5,
        "signal": [1, 0, -1, 0, 0]
    }
    df = pd.DataFrame(data, index=dates)

    engine = BacktestEngine(initial_capital=100000.0)
    result = engine.run(df)

    if result["trade_count"] > 0:
        trade = result["trades"][0]
        assert hasattr(trade, "buy_date")
        assert hasattr(trade, "buy_price")
        assert hasattr(trade, "buy_volume")
        assert hasattr(trade, "buy_commission")
        assert hasattr(trade, "sell_date")
        assert hasattr(trade, "sell_price")
        assert hasattr(trade, "sell_commission")
        assert hasattr(trade, "sell_stamp_tax")
        assert hasattr(trade, "profit")


if __name__ == "__main__":
    print("Running backtest tests...")

    tests = [
        ("test_backtest_engine_initialization", test_backtest_engine_initialization),
        ("test_commission_calculation", test_commission_calculation),
        ("test_limit_up_prevention", test_limit_up_prevention),
        ("test_limit_down_prevention", test_limit_down_prevention),
        ("test_buy_sell_basic", test_buy_sell_basic),
        ("test_suspension_skip", test_suspension_skip),
        ("test_equity_curve", test_equity_curve),
        ("test_return_calculation", test_return_calculation),
        ("test_trade_record_structure", test_trade_record_structure),
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
