from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass
class RiskConfig:
    stop_loss_ratio: float = 0.05
    take_profit_ratio: float = 0.10
    max_position_ratio: float = 1.0


class RiskManager:

    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()

    def check_stop_loss(self, current_price: float, avg_cost: float) -> bool:
        ...

    def check_take_profit(self, current_price: float, avg_cost: float) -> bool:
        ...

    def check_max_position(self, position_value: float, total_capital: float) -> bool:
        ...

    def apply_risk_rules(self, df: pd.DataFrame, signal: str, index: int) -> str:
        ...
