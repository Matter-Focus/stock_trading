from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass
class Trade:
    date: str
    type: str
    price: float
    volume: int
    commission: float
    slippage: float


@dataclass
class Position:
    volume: int
    avg_cost: float


@dataclass
class BacktestConfig:
    initial_capital: float = 100000.0
    commission_rate: float = 0.0003
    slippage_rate: float = 0.0002
    tax_rate: float = 0.001


class BacktestEngine:

    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()
        self.capital = self.config.initial_capital
        self.position = Position(volume=0, avg_cost=0.0)
        self.trades: list[Trade] = []
        self.equity_curve: list[tuple[str, float]] = []

    def calculate_slippage(self, price: float) -> float:
        ...

    def calculate_commission(self, price: float, volume: int) -> float:
        ...

    def calculate_tax(self, price: float, volume: int) -> float:
        ...

    def can_buy(self, df: pd.DataFrame, index: int) -> bool:
        ...

    def can_sell(self, df: pd.DataFrame, index: int) -> bool:
        ...

    def buy(self, df: pd.DataFrame, index: int) -> Optional[Trade]:
        ...

    def sell(self, df: pd.DataFrame, index: int) -> Optional[Trade]:
        ...

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        ...
