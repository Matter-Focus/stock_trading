# -*- coding: utf-8 -*-
"""
回测报告生成模块
功能：将回测结果可视化输出，生成文字摘要、交易明细、资金曲线图
"""
from typing import Dict
import os

try:
    import matplotlib.pyplot as plt
    _matplotlib_available = True
except ImportError:
    plt = None
    _matplotlib_available = False


class ReportGenerator:
    """
    回测报告生成器

    功能：
    - 生成文字摘要（收益率、回撤、夏普比率、胜率、盈亏比）
    - 绘制资金曲线图
    - 打印交易明细
    """

    def __init__(self, output_dir: str = "reports"):
        """
        初始化报告生成器

        Args:
            output_dir: 报告输出目录，默认为 "reports"
        """
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def generate_summary(self, result: dict) -> str:
        """
        生成文字摘要

        Args:
            result: 回测结果字典，包含 total_return, max_drawdown, sharpe_ratio, trade_count, trades

        Returns:
            摘要字符串

        指标计算逻辑：
        - 胜率 = 盈利交易次数 / 总交易次数
        - 盈亏比 = 平均盈利金额 / 平均亏损金额
        """
        total_return = result.get("total_return", 0)
        max_drawdown = result.get("max_drawdown", 0)
        sharpe_ratio = result.get("sharpe_ratio", 0)
        trade_count = result.get("trade_count", 0)
        trades = result.get("trades", [])

        if trades:
            win_count = sum(1 for t in trades if t.profit > 0)
            win_rate = win_count / len(trades) * 100
            profits = [t.profit for t in trades if t.profit > 0]
            losses = [abs(t.profit) for t in trades if t.profit < 0]
            avg_profit = sum(profits) / len(profits) if profits else 0
            avg_loss = sum(losses) / len(losses) if losses else 1
            profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else 0
        else:
            win_rate = 0.0
            profit_loss_ratio = 0.0

        summary = f"""===== 回测报告 =====
总收益率：{total_return:.2f}%
最大回撤：{max_drawdown:.2f}%
夏普比率：{sharpe_ratio:.2f}
交易次数：{trade_count}
胜率：{win_rate:.2f}%
盈亏比：{profit_loss_ratio:.2f}
==================="""

        return summary

    def plot_equity_curve(self, result: dict, stock_code: str) -> None:
        """
        绘制资金曲线图

        Args:
            result: 回测结果字典，包含 equity_curve
            stock_code: 股票代码

        图表设置：
        - 横轴：交易日期
        - 纵轴：账户总资产
        - 标题："{stock_code} 回测资金曲线"
        - 保存路径：output_dir/equity_curve_{stock_code}.png
        """
        if not _matplotlib_available:
            print("警告：matplotlib未安装，无法绘制资金曲线图")
            return

        equity_curve = result.get("equity_curve", [])
        if not equity_curve:
            print("警告：权益曲线为空，无法绘图")
            return

        plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
        plt.rcParams["axes.unicode_minus"] = False

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(equity_curve, label="账户总资产", color="#2E86AB", linewidth=1.5)

        initial_capital = result.get("initial_capital", 100000)
        ax.axhline(y=initial_capital, color="gray", alpha=0.5, linestyle="--", label="初始资金")

        ax.set_title(f"{stock_code} 回测资金曲线", fontsize=14, fontweight="bold")
        ax.set_xlabel("交易日期", fontsize=11)
        ax.set_ylabel("账户总资产 (元)", fontsize=11)
        ax.legend(loc="upper left")
        ax.grid(True, alpha=0.3)

        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x/10000:.1f}万"))

        plt.tight_layout()

        save_path = os.path.join(self.output_dir, f"equity_curve_{stock_code}.png")
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"资金曲线图已保存到: {save_path}")

        plt.close()

    def print_trade_details(self, result: dict, limit: int = 20) -> None:
        """
        打印交易明细

        Args:
            result: 回测结果字典，包含 trades
            limit: 最多显示的交易数量，默认20

        输出表格列：
        - 买入日期、买入价、卖出日期、卖出价、数量、盈亏、收益率%
        """
        trades = result.get("trades", [])
        if not trades:
            print("\n无交易记录")
            return

        print("\n" + "-" * 90)
        print("交易明细")
        print("-" * 90)
        print(f"{'买入日期':<12} {'买入价':<10} {'卖出日期':<12} {'卖出价':<10} {'数量':<8} {'盈亏':<12} {'收益率%':<10}")
        print("-" * 90)

        sorted_trades = sorted(trades, key=lambda t: t.sell_date, reverse=True)

        for trade in sorted_trades[:limit]:
            if trade.buy_price > 0:
                return_rate = (trade.sell_price - trade.buy_price) / trade.buy_price * 100
            else:
                return_rate = 0.0

            profit_str = f"{trade.profit:+.2f}"
            return_rate_str = f"{return_rate:+.2f}"

            print(f"{trade.buy_date:<12} {trade.buy_price:<10.2f} "
                  f"{trade.sell_date:<12} {trade.sell_price:<10.2f} "
                  f"{trade.buy_volume:<8} {profit_str:<12} {return_rate_str:<10}")

        if len(trades) > limit:
            print(f"\n... 还有 {len(trades) - limit} 笔交易未显示")

        print("-" * 90)

    def generate_report(self, result: dict, stock_code: str) -> None:
        """
        生成完整回测报告

        整合流程：
        1. 打印文字摘要
        2. 打印交易明细
        3. 生成资金曲线图

        Args:
            result: 回测结果字典
            stock_code: 股票代码
        """
        summary = self.generate_summary(result)
        print(summary)
        self.print_trade_details(result)
        self.plot_equity_curve(result, stock_code)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from src.backtest import Trade
    import numpy as np

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
        Trade(
            buy_date="2025-03-01",
            buy_price=9.50,
            buy_volume=10000,
            buy_commission=23.75,
            sell_date="2025-03-25",
            sell_price=10.00,
            sell_commission=25.00,
            sell_stamp_tax=50.00,
            profit=401.25
        ),
    ]

    equity_curve = list(np.linspace(100000, 105000, 100))

    result = {
        "total_return": 5.0,
        "max_drawdown": 2.5,
        "sharpe_ratio": 1.2,
        "trade_count": 3,
        "trades": trades,
        "equity_curve": equity_curve,
        "initial_capital": 100000,
        "final_equity": 105000,
    }

    report_gen = ReportGenerator(output_dir="reports")
    report_gen.generate_report(result, stock_code="000001")
