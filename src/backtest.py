# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dataclasses import dataclass
from typing import Optional, List, Dict
import pandas as pd
import numpy as np


@dataclass
class Trade:
    date: str
    type: str
    price: float
    volume: int
    commission: float
    stamp_tax: float
    slippage: float
    net_amount: float


class BacktestEngine:

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

        self.capital = initial_capital
        self.position = 0
        self.avg_cost = 0.0
        self.max_position = 1000

        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.dates: List[str] = []

    def _calculate_commission(self, price: float, volume: int) -> float:
        commission = price * volume * self.commission_rate
        return max(commission, 5.0)

    def _calculate_stamp_tax(self, price: float, volume: int) -> float:
        return price * volume * self.stamp_tax_rate

    def _check_limit_up(self, df: pd.DataFrame, index: int) -> bool:
        if index + 1 >= len(df):
            return True
        today_close = df["close"].iloc[index]
        next_open = df["open"].iloc[index + 1]
        return next_open >= today_close * 1.1

    def _check_limit_down(self, df: pd.DataFrame, index: int) -> bool:
        if index + 1 >= len(df):
            return True
        today_close = df["close"].iloc[index]
        next_open = df["open"].iloc[index + 1]
        return next_open <= today_close * 0.9

    def _check_suspension(self, df: pd.DataFrame, index: int) -> bool:
        if index + 1 >= len(df):
            return True
        next_volume = df["volume"].iloc[index + 1]
        return next_volume == 0

    def buy(self, df: pd.DataFrame, index: int) -> Optional[Trade]:
        if index + 1 >= len(df):
            return None

        if self.position >= self.max_position:
            return None

        if self._check_limit_up(df, index):
            return None

        if self._check_suspension(df, index):
            return None

        next_open = df["open"].iloc[index + 1]
        actual_price = next_open * (1 + self.slippage)

        available_capital = self.capital
        max_volume = int(available_capital // actual_price // 100 * 100)
        volume = min(max_volume, self.max_position - self.position)

        if volume <= 0:
            return None

        commission = self._calculate_commission(actual_price, volume)
        total_cost = actual_price * volume + commission
        slippage_cost = (actual_price - next_open) * volume

        if total_cost > self.capital:
            return None

        self.capital -= total_cost

        if self.position == 0:
            self.avg_cost = actual_price
        else:
            self.avg_cost = (self.avg_cost * self.position + actual_price * volume) / (self.position + volume)

        self.position += volume

        trade_date = str(df.index[index + 1].date()) if hasattr(df.index[index + 1], "date") else str(df.index[index + 1])

        trade = Trade(
            date=trade_date,
            type="buy",
            price=actual_price,
            volume=volume,
            commission=commission,
            stamp_tax=0.0,
            slippage=slippage_cost,
            net_amount=-total_cost
        )

        self.trades.append(trade)
        return trade

    def sell(self, df: pd.DataFrame, index: int) -> Optional[Trade]:
        if index + 1 >= len(df):
            return None

        if self.position <= 0:
            return None

        if self._check_limit_down(df, index):
            return None

        if self._check_suspension(df, index):
            return None

        next_open = df["open"].iloc[index + 1]
        actual_price = next_open * (1 - self.slippage)

        volume = self.position

        commission = self._calculate_commission(actual_price, volume)
        stamp_tax = self._calculate_stamp_tax(actual_price, volume)
        total_revenue = actual_price * volume - commission - stamp_tax
        slippage_cost = (next_open - actual_price) * volume

        self.capital += total_revenue
        self.position = 0

        trade_date = str(df.index[index + 1].date()) if hasattr(df.index[index + 1], "date") else str(df.index[index + 1])

        trade = Trade(
            date=trade_date,
            type="sell",
            price=actual_price,
            volume=volume,
            commission=commission,
            stamp_tax=stamp_tax,
            slippage=slippage_cost,
            net_amount=total_revenue
        )

        self.trades.append(trade)
        return trade

    def run(self, df: pd.DataFrame) -> Dict:
        self.capital = self.initial_capital
        self.position = 0
        self.avg_cost = 0.0
        self.trades = []
        self.equity_curve = []
        self.dates = []

        for i in range(len(df)):
            signal = df["signal"].iloc[i] if "signal" in df.columns else 0

            if signal == 1 and self.position == 0:
                self.buy(df, i)
            elif signal == -1 and self.position > 0:
                self.sell(df, i)

            current_price = df["close"].iloc[i]
            equity = self.capital + self.position * current_price
            self.equity_curve.append(equity)

            date_str = str(df.index[i].date()) if hasattr(df.index[i], "date") else str(df.index[i])
            self.dates.append(date_str)

        final_equity = self.equity_curve[-1] if self.equity_curve else self.initial_capital
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100

        max_drawdown = 0.0
        peak = self.initial_capital
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        daily_returns = np.diff(self.equity_curve) / self.equity_curve[:-1] if len(self.equity_curve) > 1 else []
        if len(daily_returns) > 0:
            mean_return = np.mean(daily_returns)
            std_return = np.std(daily_returns)
            if std_return > 0:
                sharpe_ratio = (mean_return - 0.02 / 252) / std_return * np.sqrt(252)
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0

        trade_count = len(self.trades)

        return {
            "total_return": round(total_return, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "trade_count": trade_count,
            "trades": self.trades,
            "equity_curve": self.equity_curve,
            "dates": self.dates,
            "final_equity": round(final_equity, 2),
            "initial_capital": self.initial_capital
        }


if __name__ == "__main__":
    from src.data import generate_mock_data, save_to_csv, load_from_csv
    from src.strategy import generate_signals

    cache_file = "backtest_test_data.csv"
    df = load_from_csv(cache_file)

    if df is None:
        df = generate_mock_data(days=252, start_price=10.0)
        save_to_csv(df, cache_file)
        print("Generated mock data")
    else:
        print("Loaded cached data")

    df = generate_signals(df)

    engine = BacktestEngine(
        initial_capital=100000.0,
        commission_rate=0.00025,
        stamp_tax_rate=0.0005,
        slippage=0.001
    )

    result = engine.run(df)

    print("\n=== 回测结果 ===")
    print("初始资金: %.2f 元" % result["initial_capital"])
    print("最终资产: %.2f 元" % result["final_equity"])
    print("总收益率: %.2f%%" % result["total_return"])
    print("最大回撤: %.2f%%" % result["max_drawdown"])
    print("夏普比率: %.2f" % result["sharpe_ratio"])
    print("交易次数: %d" % result["trade_count"])

    if result["trades"]:
        print("\n=== 交易记录 ===")
        for trade in result["trades"]:
            print("[%s] %s %d股 @ %.2f元 (佣金: %.2f, 印花税: %.2f, 滑点: %.2f)" % (
                trade.date, trade.type, trade.volume, trade.price,
                trade.commission, trade.stamp_tax, trade.slippage
            ))