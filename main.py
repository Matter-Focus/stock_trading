# -*- coding: utf-8 -*-
"""
A股量化回测系统 - 入口文件

数据流向：
data.py -> strategy.py -> backtest.py -> report.py

使用方式：
python main.py --stock sh600519 --start 2025-01-01 --end 2026-06-01
"""
import argparse
import sys
from typing import Optional
import pandas as pd

from src.data import get_stock_data, save_to_csv, load_from_csv
from src.strategy import generate_signals
from src.backtest import BacktestEngine
from src.report import ReportGenerator


def main() -> None:
    """主函数：串联数据获取、策略生成、回测、报告生成"""

    # ========== 1. 解析命令行参数 ==========
    print("[1/5] 解析参数...")
    parser = argparse.ArgumentParser(description="A股量化回测系统")
    parser.add_argument(
        "--stock",
        type=str,
        default="sz000001",
        help="股票代码（如 sh600519、sz000001），默认 sz000001（平安银行）"
    )
    parser.add_argument(
        "--start",
        type=str,
        default="2025-01-01",
        help="开始日期，格式 YYYY-MM-DD，默认 2025-01-01"
    )
    parser.add_argument(
        "--end",
        type=str,
        default="2026-06-01",
        help="结束日期，格式 YYYY-MM-DD，默认 2026-06-01"
    )

    args = parser.parse_args()
    stock_code = args.stock
    start_date = args.start
    end_date = args.end

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

    # ========== 2. 获取数据 ==========
    print("\n[2/5] 获取数据...")
    cache_file = f"{stock_code}_{start_date}_{end_date}.csv"
    df = load_from_csv(cache_file)

    try:
        if df is None:
            print("  从API获取数据...")
            df = get_stock_data(stock_code, start_date, end_date)
            save_to_csv(df, cache_file)
            print(f"  数据已缓存到 {cache_file}")
        else:
            print("  从缓存加载数据")

        print(f"  数据范围: {df.index[0].date()} ~ {df.index[-1].date()}")
        print(f"  数据条数: {len(df)}")
    except Exception as e:
        print(f"\n错误：数据获取失败 - {str(e)}")
        sys.exit(1)

    # ========== 3. 生成信号 ==========
    print("\n[3/5] 生成交易信号...")
    df = generate_signals(df, short_window=5, long_window=20)
    buy_signals = (df["signal"] == 1).sum()
    sell_signals = (df["signal"] == -1).sum()
    print(f"  短均线: 5日")
    print(f"  长均线: 20日")
    print(f"  买入信号: {buy_signals} 个")
    print(f"  卖出信号: {sell_signals} 个")

    # ========== 4. 执行回测 ==========
    print("\n[4/5] 执行回测...")
    engine = BacktestEngine(
        initial_capital=initial_capital,
        commission_rate=commission_rate,
        stamp_tax_rate=stamp_tax_rate,
        slippage=slippage,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        max_position_pct=max_position_pct,
        max_trade_count=max_trade_count
    )
    result = engine.run(df)
    print(f"  完成 {result['trade_count']} 笔交易")

    if result["trade_count"] == 0:
        print("  警告：无交易记录")

    # ========== 5. 生成报告 ==========
    print("\n[5/5] 生成报告...")
    report_gen = ReportGenerator(output_dir="reports")
    report_gen.generate_report(result, stock_code=stock_code)

    print("\n" + "=" * 60)
    print("回测完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
