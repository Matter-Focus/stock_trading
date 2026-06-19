# -*- coding: utf-8 -*-
"""
风控模块
功能：在回测过程中对交易行为进行拦截和控制，防止过度亏损、过度交易、仓位失控
"""
from typing import Union


class RiskManager:
    """
    风控管理器

    风控规则：
    - 止损：跌幅超过止损线强制平仓
    - 止盈：涨幅超过止盈线锁定利润
    - 仓位限制：单只股票仓位不超过总资金一定比例
    - 交易次数限制：防止过度交易
    """

    def __init__(
        self,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.15,
        max_position_pct: float = 0.8,
        max_trade_count: int = 50
    ):
        """
        初始化风控参数

        Args:
            stop_loss_pct: 止损比例，默认5%
            take_profit_pct: 止盈比例，默认15%
            max_position_pct: 最大仓位比例，默认80%
            max_trade_count: 最大交易次数，默认50次
        """
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_position_pct = max_position_pct
        self.max_trade_count = max_trade_count

    def check_stop_loss(self, entry_price: float, current_price: float) -> bool:
        """
        止损检查：当前价格相对买入价下跌超过止损比例

        Args:
            entry_price: 买入价格
            current_price: 当前价格

        Returns:
            True表示触发止损，需要强制卖出
        """
        if entry_price <= 0:
            return False

        # 计算跌幅：(买入价 - 当前价) / 买入价
        loss_pct = (entry_price - current_price) / entry_price

        # 跌幅超过止损线，返回True触发止损
        return loss_pct >= self.stop_loss_pct

    def check_take_profit(self, entry_price: float, current_price: float) -> bool:
        """
        止盈检查：当前价格相对买入价上涨超过止盈比例

        Args:
            entry_price: 买入价格
            current_price: 当前价格

        Returns:
            True表示触发止盈，需要卖出锁定利润
        """
        if entry_price <= 0:
            return False

        # 计算涨幅：(当前价 - 买入价) / 买入价
        profit_pct = (current_price - entry_price) / entry_price

        # 涨幅超过止盈线，返回True触发止盈
        return profit_pct >= self.take_profit_pct

    def check_position_limit(
        self,
        available_capital: float,
        trade_value: float
    ) -> bool:
        """
        仓位限制检查：本次交易金额是否超过最大仓位比例

        Args:
            available_capital: 可用资金
            trade_value: 本次交易金额

        Returns:
            True表示允许交易，False表示仓位超限拒绝交易
        """
        if available_capital <= 0:
            return False

        # 计算交易后占总资金的比例
        position_pct = trade_value / available_capital

        # 仓位比例超过上限，拒绝交易
        return position_pct <= self.max_position_pct

    def check_trade_limit(self, current_trade_count: int) -> bool:
        """
        交易次数限制检查：是否超过最大交易次数

        Args:
            current_trade_count: 当前已完成交易次数

        Returns:
            True表示允许继续交易，False表示达到上限
        """
        # 交易次数未达上限，允许继续交易
        return current_trade_count < self.max_trade_count

    def get_signal_override(
        self,
        entry_price: float,
        current_price: float,
        original_signal: int,
        trade_count: int
    ) -> int:
        """
        综合风控判断，返回实际执行信号

        信号优先级：
        1. 止损/止盈 > 其他信号（强制平仓）
        2. 交易次数限制 > 买入信号（拒绝开仓）

        Args:
            entry_price: 持仓买入价格（无持仓时为0）
            current_price: 当前价格
            original_signal: 原始策略信号（1=买, -1=卖, 0=持有）
            trade_count: 当前已完成交易次数

        Returns:
            1=买入, -1=卖出, 0=不操作
        """
        # ========== 第一优先级：止损/止盈强制平仓 ==========
        # 触发止损，强制卖出
        if entry_price > 0 and self.check_stop_loss(entry_price, current_price):
            return -1

        # 触发止盈，强制卖出
        if entry_price > 0 and self.check_take_profit(entry_price, current_price):
            return -1

        # ========== 第二优先级：交易次数限制 ==========
        # 达到交易次数上限，拒绝新开仓
        if original_signal == 1 and not self.check_trade_limit(trade_count):
            return 0

        # ========== 第三优先级：返回原始信号 ==========
        return original_signal


if __name__ == "__main__":
    # 测试风控模块
    rm = RiskManager(
        stop_loss_pct=0.05,
        take_profit_pct=0.15,
        max_position_pct=0.8,
        max_trade_count=50
    )

    print("=" * 50)
    print("风控模块测试")
    print("=" * 50)

    # 测试止损
    print("\n--- 止损测试 ---")
    print(f"买入价100，当前价96（跌4%），止损线5%：")
    print(f"  触发止损: {rm.check_stop_loss(100, 96)}")  # False
    print(f"买入价100，当前价94（跌6%），止损线5%：")
    print(f"  触发止损: {rm.check_stop_loss(100, 94)}")  # True

    # 测试止盈
    print("\n--- 止盈测试 ---")
    print(f"买入价100，当前价112（涨12%），止盈线15%：")
    print(f"  触发止盈: {rm.check_take_profit(100, 112)}")  # False
    print(f"买入价100，当前价116（涨16%），止盈线15%：")
    print(f"  触发止盈: {rm.check_take_profit(100, 116)}")  # True

    # 测试仓位限制
    print("\n--- 仓位限制测试 ---")
    print(f"可用资金100000，交易金额70000，仓位上限80%：")
    print(f"  允许交易: {rm.check_position_limit(100000, 70000)}")  # True
    print(f"可用资金100000，交易金额90000，仓位上限80%：")
    print(f"  允许交易: {rm.check_position_limit(100000, 90000)}")  # False

    # 测试交易次数限制
    print("\n--- 交易次数限制测试 ---")
    print(f"当前交易次数45，最大限制50：")
    print(f"  允许交易: {rm.check_trade_limit(45)}")  # True
    print(f"当前交易次数50，最大限制50：")
    print(f"  允许交易: {rm.check_trade_limit(50)}")  # False

    # 测试综合信号
    print("\n--- 综合信号测试 ---")
    print(f"持仓成本100，当前价94（触发止损），原始信号买入：")
    print(f"  最终信号: {rm.get_signal_override(100, 94, 1, 10)}")  # -1 卖出
    print(f"持仓成本100，当前价116（触发止盈），原始信号持有：")
    print(f"  最终信号: {rm.get_signal_override(100, 116, 0, 10)}")  # -1 卖出
    print(f"交易次数已达上限，原始信号买入：")
    print(f"  最终信号: {rm.get_signal_override(0, 100, 1, 50)}")  # 0 不操作
