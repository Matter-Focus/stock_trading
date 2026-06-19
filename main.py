# -*- coding: utf-8 -*-
"""
A股量化回测系统 - 入口文件

数据流向：
data.py -> strategy.py -> backtest.py -> risk.py -> report.py
"""
from src.data import get_stock_data, save_to_csv, load_from_csv
from src.strategy import generate_signals
from src.backtest import BacktestEngine
from src.risk import RiskManager
from src.report import generate_report


def main():
    """主函数：串联数据获取、策略生成、回测、风控、报告生成"""

    # ========== 1. 参数配置 ==========
    stock_code = "000001"
    start_date = "2025-06-19"
    end_date = "2026-06-19"
    cache_file = f"{stock_code}_{start_date}_{end_date}.csv"

    # 回测参数
    initial_capital = 100000.0   # 初始资金10万
    commission_rate = 0.00025    # 佣金万2.5
    stamp_tax_rate = 0.0005      # 印花税千0.5
    slippage = 0.001             # 滑点0.1%

    # 风控参数
    stop_loss_pct = 0.05         # 止损5%
    take_profit_pct = 0.15       # 止盈15%
    max_position_pct = 0.8       # 最大仓位80%
    max_trade_count = 50         # 最大交易次数

    print("=" * 60)
    print("A股量化回测系统")
    print("=" * 60)
    print(f"股票代码: {stock_code}")
    print(f"回测区间: {start_date} ~ {end_date}")
    print("-" * 60)

    # ========== 2. 数据获取 ==========
    print("\n[1/5] 获取数据...")
    df = load_from_csv(cache_file)

    if df is None:
        print("  从API获取数据...")
        df = get_stock_data(stock_code, start_date, end_date)
        save_to_csv(df, cache_file)
        print(f"  数据已缓存到 {cache_file}")
    else:
        print("  从缓存加载数据")

    print(f"  数据范围: {df.index[0].date()} ~ {df.index[-1].date()}")
    print(f"  数据条数: {len(df)}")

    # ========== 3. 策略生成 ==========
    print("\n[2/5] 生成交易信号...")
    df = generate_signals(df)
    buy_signals = (df["signal"] == 1).sum()
    sell_signals = (df["signal"] == -1).sum()
    print(f"  买入信号: {buy_signals} 个")
    print(f"  卖出信号: {sell_signals} 个")

    # ========== 4. 回测撮合 ==========
    print("\n[3/5] 执行回测...")
    engine = BacktestEngine(
        initial_capital=initial_capital,
        commission_rate=commission_rate,
        stamp_tax_rate=stamp_tax_rate,
        slippage=slippage
    )
    result = engine.run(df)
    print(f"  完成 {result['trade_count']} 笔交易")

    # ========== 5. 风控评估（可选：实际风控在回测时应用）==========
    print("\n[4/5] 风控评估...")
    risk_mgr = RiskManager(
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        max_position_pct=max_position_pct,
        max_trade_count=max_trade_count
    )
    print(f"  止损线: {stop_loss_pct*100:.0f}%")
    print(f"  止盈线: {take_profit_pct*100:.0f}%")
    print(f"  最大仓位: {max_position_pct*100:.0f}%")
    print(f"  最大交易次数: {max_trade_count}")

    # ========== 6. 生成报告 ==========
    print("\n[5/5] 生成报告...")
    dates = [str(d.date()) for d in df.index]
    generate_report(result, dates, save_chart="equity_curve.png")

    print("\n" + "=" * 60)
    print("回测完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
