# -*- coding: utf-8 -*-
"""
A股回测撮合引擎
功能：基于交易信号执行买入/卖出，计算收益率、最大回撤、夏普比率等指标
"""
from dataclasses import dataclass
from typing import Dict, List
import pandas as pd
import numpy as np


@dataclass
class Trade:
    """交易记录数据类，记录一对完整的买卖交易"""
    buy_date: str           # 买入日期
    buy_price: float        # 买入价格（含滑点）
    buy_volume: int         # 买入数量（100股整数倍）
    buy_commission: float   # 买入佣金
    sell_date: str          # 卖出日期
    sell_price: float       # 卖出价格（含滑点）
    sell_commission: float  # 卖出佣金
    sell_stamp_tax: float   # 卖出印花税
    profit: float          # 盈亏金额


class BacktestEngine:
    """
    A股回测撮合引擎

    撮合规则：
    - 买入：次日开盘价 × (1 + 滑点)，佣金万2.5（不足5元按5元）
    - 卖出：次日开盘价 × (1 - 滑点)，佣金万2.5 + 印花税千0.5
    - 涨跌停：涨停不能买，跌停不能卖
    - 停牌：次日成交量为0则跳过
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.00025,
        stamp_tax_rate: float = 0.0005,
        slippage: float = 0.001
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.stamp_tax_rate = stamp_tax_rate
        self.slippage = slippage

    def _calculate_commission(self, amount: float) -> float:
        """佣金计算：成交金额 × 佣金率，不足5元按5元收"""
        commission = amount * self.commission_rate
        return max(commission, 5.0)

    def _check_limit_up(self, df: pd.DataFrame, idx: int) -> bool:
        """涨停判断：次日开盘价 >= 今日收盘价 × 1.1 则不能买入"""
        if idx + 1 >= len(df):
            return True
        today_close = df["close"].iloc[idx]
        next_open = df["open"].iloc[idx + 1]
        return next_open >= today_close * 1.1

    def _check_limit_down(self, df: pd.DataFrame, idx: int) -> bool:
        """跌停判断：次日开盘价 <= 今日收盘价 × 0.9 则不能卖出"""
        if idx + 1 >= len(df):
            return True
        today_close = df["close"].iloc[idx]
        next_open = df["open"].iloc[idx + 1]
        return next_open <= today_close * 0.9

    def _check_suspension(self, df: pd.DataFrame, idx: int) -> bool:
        """停牌判断：次日成交量为0则跳过该信号"""
        if idx + 1 >= len(df):
            return True
        next_volume = df["volume"].iloc[idx + 1]
        return next_volume == 0

    def run(self, df: pd.DataFrame) -> Dict:
        """
        执行回测

        Args:
            df: 带signal列的DataFrame（signal: 1=买入, -1=卖出, 0=持有）

        Returns:
            包含以下键的字典：
            - total_return: 总收益率（百分比）
            - max_drawdown: 最大回撤（百分比）
            - sharpe_ratio: 夏普比率（无风险利率2%年化）
            - trade_count: 交易次数
            - trades: 交易明细列表
        """
        capital = self.initial_capital
        position = 0
        avg_cost = 0.0
        trades: List[Trade] = []
        equity_curve: List[float] = []

        pending_buy = None  # 待入账的买入信息

        for idx in range(len(df) - 1):
            signal = df["signal"].iloc[idx] if "signal" in df.columns else 0

            # ========== 买入逻辑 ==========
            if signal == 1 and position == 0:
                # 涨停不能买入
                if self._check_limit_up(df, idx):
                    continue
                # 停牌不能买入
                if self._check_suspension(df, idx):
                    continue

                # 成交价 = 次日开盘价 × (1 + 滑点)
                next_open = df["open"].iloc[idx + 1]
                buy_price = next_open * (1 + self.slippage)

                # 买入数量 = 100股整数倍
                max_volume = int(capital // buy_price // 100 * 100)
                if max_volume <= 0:
                    continue

                # 佣金不足5元按5元收取
                buy_amount = buy_price * max_volume
                buy_commission = self._calculate_commission(buy_amount)

                # 更新资金和持仓
                total_cost = buy_amount + buy_commission
                capital -= total_cost
                avg_cost = buy_price
                position = max_volume

                # 记录买入信息，等卖出时配对
                buy_date = str(df.index[idx + 1].date())
                pending_buy = {
                    "date": buy_date,
                    "price": buy_price,
                    "volume": max_volume,
                    "commission": buy_commission
                }

            # ========== 卖出逻辑 ==========
            elif signal == -1 and position > 0:
                # 跌停不能卖出
                if self._check_limit_down(df, idx):
                    continue
                # 停牌不能卖出
                if self._check_suspension(df, idx):
                    continue

                # 成交价 = 次日开盘价 × (1 - 滑点)
                next_open = df["open"].iloc[idx + 1]
                sell_price = next_open * (1 - self.slippage)

                # 卖出全部持仓
                sell_volume = position
                sell_amount = sell_price * sell_volume

                # 佣金不足5元按5元收取
                sell_commission = self._calculate_commission(sell_amount)
                # 印花税 = 成交金额 × 印花税率
                sell_stamp_tax = sell_amount * self.stamp_tax_rate

                # 更新资金和持仓
                net_revenue = sell_amount - sell_commission - sell_stamp_tax
                capital += net_revenue
                position = 0

                sell_date = str(df.index[idx + 1].date())

                # 计算盈亏（含手续费）
                cost = avg_cost * sell_volume + pending_buy["commission"] + sell_commission + sell_stamp_tax
                profit = net_revenue - (avg_cost * sell_volume)

                # 配对记录买入和卖出
                if pending_buy:
                    trade = Trade(
                        buy_date=pending_buy["date"],
                        buy_price=pending_buy["price"],
                        buy_volume=pending_buy["volume"],
                        buy_commission=pending_buy["commission"],
                        sell_date=sell_date,
                        sell_price=sell_price,
                        sell_commission=sell_commission,
                        sell_stamp_tax=sell_stamp_tax,
                        profit=round(profit, 2)
                    )
                    trades.append(trade)
                    pending_buy = None

            # ========== 更新权益曲线 ==========
            current_price = df["close"].iloc[idx]
            equity = capital + position * current_price
            equity_curve.append(equity)

        # 如果还有未卖出的持仓，按最后收盘价计算
        if position > 0:
            final_price = df["close"].iloc[-1]
            unrealized_profit = position * (final_price - avg_cost)
            equity_curve.append(capital + position * final_price)

        # ========== 计算绩效指标 ==========
        final_equity = equity_curve[-1] if equity_curve else self.initial_capital

        # 总收益率
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100

        # 最大回撤
        max_drawdown = 0.0
        peak = self.initial_capital
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # 夏普比率（无风险利率2%年化）
        daily_returns = np.diff(equity_curve) / np.array(equity_curve[:-1]) if len(equity_curve) > 1 else []
        if len(daily_returns) > 0 and np.std(daily_returns) > 0:
            mean_return = np.mean(daily_returns)
            std_return = np.std(daily_returns)
            # 年化：日 Sharpe × sqrt(252)
            sharpe_ratio = (mean_return - 0.02 / 252) / std_return * np.sqrt(252)
        else:
            sharpe_ratio = 0.0

        trade_count = len(trades)

        return {
            "total_return": round(total_return, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "trade_count": trade_count,
            "trades": trades,
            "equity_curve": equity_curve,
            "final_equity": round(final_equity, 2),
            "initial_capital": self.initial_capital
        }


if __name__ == "__main__":
    from src.data import load_from_csv

    # 尝试加载缓存数据
    cache_file = "000001_2025-06-19_2026-06-19.csv"
    df = load_from_csv(cache_file)

    if df is None:
        print("请先运行 python src/data.py 获取数据")
        exit(1)

    # 生成交易信号
    from src.strategy import generate_signals
    df = generate_signals(df)

    # 创建回测引擎
    engine = BacktestEngine(
        initial_capital=100000.0,
        commission_rate=0.00025,
        stamp_tax_rate=0.0005,
        slippage=0.001
    )

    # 执行回测
    result = engine.run(df)

    # 打印结果
    print("\n" + "=" * 50)
    print("回测结果")
    print("=" * 50)
    print(f"初始资金: {result['initial_capital']:.2f} 元")
    print(f"最终资产: {result['final_equity']:.2f} 元")
    print(f"总收益率: {result['total_return']:.2f}%")
    print(f"最大回撤: {result['max_drawdown']:.2f}%")
    print(f"夏普比率: {result['sharpe_ratio']:.2f}")
    print(f"交易次数: {result['trade_count']}")

    if result["trades"]:
        print("\n" + "-" * 50)
        print("交易记录")
        print("-" * 50)
        for i, trade in enumerate(result["trades"], 1):
            print(f"\n第{i}笔交易:")
            print(f"  买入: {trade.buy_date} @ {trade.buy_price:.2f}元 × {trade.buy_volume}股")
            print(f"       佣金: {trade.buy_commission:.2f}元")
            print(f"  卖出: {trade.sell_date} @ {trade.sell_price:.2f}元 × {trade.buy_volume}股")
            print(f"       佣金: {trade.sell_commission:.2f}元, 印花税: {trade.sell_stamp_tax:.2f}元")
            print(f"  盈亏: {trade.profit:.2f}元")
