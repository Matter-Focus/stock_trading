# -*- coding: utf-8 -*-
"""
报告模块
功能：输出回测结果，包括收益曲线图、交易明细、关键指标
"""
from typing import List, Dict
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class ReportGenerator:
    """
    回测报告生成器

    功能：
    - 生成收益曲线图
    - 输出关键绩效指标
    - 打印交易明细
    """

    def __init__(self, result: Dict, dates: List[str] = None):
        """
        初始化报告生成器

        Args:
            result: 回测结果字典，包含 equity_curve, total_return 等
            dates: 日期列表，与 equity_curve 对应
        """
        self.result = result
        self.dates = dates

    def plot_equity_curve(self, save_path: str = None) -> None:
        """
        绘制权益曲线图

        Args:
            save_path: 图片保存路径，默认为 None（不保存）
        """
        equity_curve = self.result.get("equity_curve", [])
        if not equity_curve:
            print("警告：权益曲线为空，无法绘图")
            return

        # 设置中文字体
        plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
        plt.rcParams["axes.unicode_minus"] = False

        fig, ax = plt.subplots(figsize=(12, 6))

        # 绘制权益曲线
        ax.plot(equity_curve, label="账户权益", color="#2E86AB", linewidth=1.5)

        # 标记买入点
        trades = self.result.get("trades", [])
        for trade in trades:
            if hasattr(trade, "buy_date") and self.dates:
                try:
                    buy_idx = self.dates.index(trade.buy_date)
                    ax.axvline(x=buy_idx, color="green", alpha=0.3, linestyle="--")
                except ValueError:
                    pass

        # 标记卖出点
        for trade in trades:
            if hasattr(trade, "sell_date") and self.dates:
                try:
                    sell_idx = self.dates.index(trade.sell_date)
                    ax.axvline(x=sell_idx, color="red", alpha=0.3, linestyle="--")
                except ValueError:
                    pass

        # 添加初始资金线
        initial = self.result.get("initial_capital", 100000)
        ax.axhline(y=initial, color="gray", alpha=0.5, linestyle="--", label="初始资金")

        # 设置标题和标签
        ax.set_title("回测权益曲线", fontsize=14, fontweight="bold")
        ax.set_xlabel("交易日", fontsize=11)
        ax.set_ylabel("账户权益 (元)", fontsize=11)
        ax.legend(loc="upper left")
        ax.grid(True, alpha=0.3)

        # 格式化Y轴为万元
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x/10000:.1f}万"))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"图表已保存到: {save_path}")

        plt.show()

    def print_summary(self) -> None:
        """
        打印回测摘要指标
        """
        print("\n" + "=" * 60)
        print("回测结果摘要")
        print("=" * 60)

        initial = self.result.get("initial_capital", 100000)
        final = self.result.get("final_equity", 0)
        total_return = self.result.get("total_return", 0)
        max_drawdown = self.result.get("max_drawdown", 0)
        sharpe = self.result.get("sharpe_ratio", 0)
        trade_count = self.result.get("trade_count", 0)

        print(f"{'指标':<20} {'数值':<15}")
        print("-" * 60)
        print(f"{'初始资金':<20} {initial:>12,.2f} 元")
        print(f"{'最终资产':<20} {final:>12,.2f} 元")
        print(f"{'总收益率':<20} {total_return:>12.2f} %")
        print(f"{'最大回撤':<20} {max_drawdown:>12.2f} %")
        print(f"{'夏普比率':<20} {sharpe:>12.2f}")
        print(f"{'交易次数':<20} {trade_count:>12d}")

        # 计算年化收益率（简化版：假设252个交易日）
        if trade_count > 0:
            equity_curve = self.result.get("equity_curve", [])
            if len(equity_curve) > 1:
                days = len(equity_curve)
                annual_return = total_return * 252 / days
                print(f"{'年化收益率':<20} {annual_return:>12.2f} %")

        # 计算胜率
        trades = self.result.get("trades", [])
        if trades:
            win_count = sum(1 for t in trades if hasattr(t, "profit") and t.profit > 0)
            win_rate = win_count / len(trades) * 100 if trades else 0
            print(f"{'胜率':<20} {win_rate:>12.2f} %")

            # 计算平均盈亏
            profits = [t.profit for t in trades if hasattr(t, "profit")]
            if profits:
                avg_profit = sum(profits) / len(profits)
                print(f"{'平均每笔盈亏':<20} {avg_profit:>12.2f} 元")

        print("=" * 60)

    def print_trades(self, max_show: int = 20) -> None:
        """
        打印交易明细

        Args:
            max_show: 最多显示的交易数量，默认20
        """
        trades = self.result.get("trades", [])
        if not trades:
            print("\n无交易记录")
            return

        print("\n" + "-" * 80)
        print("交易明细")
        print("-" * 80)
        print(f"{'序号':<6} {'买入日期':<12} {'买入价':<10} {'数量':<8} {'卖出日期':<12} {'卖出价':<10} {'盈亏':<12}")
        print("-" * 80)

        for i, trade in enumerate(trades[:max_show], 1):
            profit_str = f"{trade.profit:+.2f}"
            profit_color = "+" if trade.profit > 0 else ""

            print(f"{i:<6} {trade.buy_date:<12} {trade.buy_price:<10.2f} "
                  f"{trade.buy_volume:<8} {trade.sell_date:<12} "
                  f"{trade.sell_price:<10.2f} {profit_color}{trade.profit:<11.2f}")

        if len(trades) > max_show:
            print(f"\n... 还有 {len(trades) - max_show} 笔交易未显示")

        print("-" * 80)

        # 统计买卖佣金和印花税
        total_buy_commission = sum(t.buy_commission for t in trades)
        total_sell_commission = sum(t.sell_commission for t in trades)
        total_stamp_tax = sum(t.sell_stamp_tax for t in trades)

        print(f"\n手续费统计：")
        print(f"  买入佣金合计: {total_buy_commission:.2f} 元")
        print(f"  卖出佣金合计: {total_sell_commission:.2f} 元")
        print(f"  印花税合计:   {total_stamp_tax:.2f} 元")
        print(f"  总手续费:     {total_buy_commission + total_sell_commission + total_stamp_tax:.2f} 元")


def generate_report(result: Dict, dates: List[str] = None, save_chart: str = None) -> None:
    """
    生成完整回测报告

    Args:
        result: 回测结果字典
        dates: 日期列表
        save_chart: 图表保存路径
    """
    report = ReportGenerator(result, dates)

    # 打印摘要
    report.print_summary()

    # 打印交易明细
    report.print_trades()

    # 绘制权益曲线
    report.plot_equity_curve(save_path=save_chart)


if __name__ == "__main__":
    # 测试报告模块
    from src.backtest import BacktestEngine, Trade

    # 创建模拟回测结果
    trades = [
        Trade(
            buy_date="2025-01-02",
            buy_price=10.10,
            buy_volume=9000,
            buy_commission=22.73,
            sell_date="2025-01-15",
            sell_price=10.50,
            sell_commission=23.63,
            sell_stamp_tax=47.25,
            profit=356.19
        ),
        Trade(
            buy_date="2025-02-03",
            buy_price=10.80,
            buy_volume=8200,
            buy_commission=22.18,
            sell_date="2025-02-20",
            sell_price=10.20,
            sell_commission=20.71,
            sell_stamp_tax=41.41,
            profit=-491.12
        ),
    ]

    import numpy as np
    equity_curve = list(np.linspace(100000, 105000, 100))

    result = {
        "initial_capital": 100000,
        "final_equity": 105000,
        "total_return": 5.0,
        "max_drawdown": 2.5,
        "sharpe_ratio": 1.2,
        "trade_count": 2,
        "trades": trades,
        "equity_curve": equity_curve,
    }

    dates = [f"2025-01-{i:02d}" for i in range(1, 101)]

    print("生成测试报告...")
    generate_report(result, dates)
