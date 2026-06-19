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
    dates = pd.date_range("2026-01-01", periods=6, freq="D")
    data = {
        "open": [10.0, 10.1, 10.2, 10.3, 10.4, 10.5],
        "close": [10.0, 10.1, 10.2, 10.3, 10.4, 10.5],
        "high": [10.2, 10.3, 10.4, 10.5, 10.6, 10.7],
        "low": [9.8, 9.9, 10.0, 10.1, 10.2, 10.3],
        "volume": [1000000, 1000000, 1000000, 1000000, 1000000, 1000000],
        "signal": [1, 0, -1, 0, 0, 0]  # 买入信号在idx=0，卖出信号在idx=2
    }
    df = pd.DataFrame(data, index=dates)

    engine = BacktestEngine(initial_capital=100000.0)
    result = engine.run(df)

    # 买入信号idx=0执行买入，卖出信号idx=2执行卖出
    assert result["trade_count"] == 1
    assert len(result["trades"]) == 1

    trade = result["trades"][0]
    assert isinstance(trade, Trade)


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
        assert hasattr(trade, "stop_loss_triggered")
        assert hasattr(trade, "take_profit_triggered")


def test_stop_loss_risk_control():
    """测试止损风控：持仓期间价格跌破5%时强制卖出"""
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    # 买入后价格持续下跌，每天跌1%，第6天累计跌约5.5%触发止损
    data = {
        "open": [10.0, 9.95, 9.90, 9.85, 9.80, 9.75, 9.70, 9.65, 9.60, 9.55],
        "close": [10.0, 9.95, 9.90, 9.85, 9.80, 9.75, 9.70, 9.65, 9.60, 9.55],
        "high": [10.1, 10.0, 9.95, 9.90, 9.85, 9.80, 9.75, 9.70, 9.65, 9.60],
        "low": [9.9, 9.85, 9.80, 9.75, 9.70, 9.65, 9.60, 9.55, 9.50, 9.45],
        "volume": [1000000] * 10,
        "signal": [1] + [0] * 9  # 买入信号，然后持有
    }
    df = pd.DataFrame(data, index=dates)

    # 止损5%，在idx=5时（收盘价9.75）跌幅=(10-9.75)/10=2.5%未触发
    # 在idx=6时（收盘价9.70）跌幅=(10-9.70)/10=3.0%未触发
    # 在idx=7时（收盘价9.65）跌幅=(10-9.65)/10=3.5%未触发
    # 等等...止损检查是用当日收盘价，所以需要更陡峭的跌幅
    # 重新设计：买入价10.0，需要跌到9.5以下才触发5%止损
    # 重新设计数据：每天跌1%，5天后跌到9.59，6天后跌到9.50，7天后跌到9.41触发止损
    data = {
        "open": [10.0, 9.50, 9.40, 9.30, 9.20, 9.10, 9.00, 8.90, 8.80, 8.70],
        "close": [10.0, 9.50, 9.40, 9.30, 9.20, 9.10, 9.00, 8.90, 8.80, 8.70],
        "high": [10.1, 9.60, 9.50, 9.40, 9.30, 9.20, 9.10, 9.00, 8.90, 8.80],
        "low": [9.9, 9.40, 9.30, 9.20, 9.10, 9.00, 8.90, 8.80, 8.70, 8.60],
        "volume": [1000000] * 10,
        "signal": [1] + [0] * 9  # 买入信号，然后持有
    }
    df = pd.DataFrame(data, index=dates)

    # 止损5%，idx=1时收盘价9.50，跌幅=(10-9.50)/10=5.0%触发止损
    engine = BacktestEngine(initial_capital=100000.0, stop_loss_pct=0.05)
    result = engine.run(df)

    # 应该触发止损卖出
    assert result["trade_count"] >= 1
    # 检查是否有止损触发的交易
    stop_loss_trades = [t for t in result["trades"] if t.stop_loss_triggered]
    assert len(stop_loss_trades) >= 1


def test_take_profit_risk_control():
    """测试止盈风控：持仓期间价格涨超15%时强制卖出"""
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    # 买入后价格持续上涨，快速触发15%止盈
    # idx=0收盘价10.0，次日( idx=1)开盘买入，然后价格跳涨
    data = {
        "open": [10.0, 10.0, 12.0, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7],
        "close": [10.0, 10.0, 12.0, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7],
        "high": [10.1, 10.1, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8],
        "low": [9.9, 9.9, 11.9, 12.0, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6],
        "volume": [1000000] * 10,
        "signal": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 买入信号在idx=0
    }
    df = pd.DataFrame(data, index=dates)

    # 止盈15%，idx=0买入价=10.0*1.001≈10.01
    # idx=1收盘价=10.0，未触发止盈
    # idx=2收盘价=12.0，涨幅=(12.0-10.01)/10.01=19.9% > 15%，触发止盈
    engine = BacktestEngine(initial_capital=100000.0, take_profit_pct=0.15)
    result = engine.run(df)

    # 应该触发止盈卖出
    assert result["trade_count"] >= 1
    take_profit_trades = [t for t in result["trades"] if t.take_profit_triggered]
    assert len(take_profit_trades) >= 1


def test_position_limit_risk_control():
    """测试仓位限制风控"""
    dates = pd.date_range("2026-01-01", periods=3, freq="D")
    data = {
        "open": [10.0, 10.0, 10.0],
        "close": [10.0, 10.0, 10.0],
        "high": [10.2, 10.2, 10.2],
        "low": [9.8, 9.8, 9.8],
        "volume": [1000000] * 3,
        "signal": [1, 1, 1]  # 连续买入信号
    }
    df = pd.DataFrame(data, index=dates)

    # 仓位限制50%
    engine = BacktestEngine(initial_capital=100000.0, max_position_pct=0.5)
    result = engine.run(df)

    # 第一次买入后仓位达到50%，第二次应该被拒绝
    # 只有一笔交易
    assert result["trade_count"] <= 1


def test_trade_limit_risk_control():
    """测试交易次数限制风控"""
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    data = {
        "open": [10.0] * 10,
        "close": [10.0] * 10,
        "high": [10.2] * 10,
        "low": [9.8] * 10,
        "volume": [1000000] * 10,
        "signal": [1, -1, 1, -1, 1, -1, 1, -1, 1, -1]  # 连续买卖
    }
    df = pd.DataFrame(data, index=dates)

    # 最多交易3次
    engine = BacktestEngine(initial_capital=100000.0, max_trade_count=3)
    result = engine.run(df)

    # 交易次数不应超过3
    assert result["trade_count"] <= 3


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
        ("test_stop_loss_risk_control", test_stop_loss_risk_control),
        ("test_take_profit_risk_control", test_take_profit_risk_control),
        ("test_position_limit_risk_control", test_position_limit_risk_control),
        ("test_trade_limit_risk_control", test_trade_limit_risk_control),
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
