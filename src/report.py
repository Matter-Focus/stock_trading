import pandas as pd
import matplotlib.pyplot as plt


class PerformanceReport:

    @staticmethod
    def calculate_total_return(equity_curve: pd.Series) -> float:
        ...

    @staticmethod
    def calculate_max_drawdown(equity_curve: pd.Series) -> float:
        ...

    @staticmethod
    def calculate_sharpe_ratio(equity_curve: pd.Series, risk_free_rate: float = 0.03) -> float:
        ...

    @staticmethod
    def calculate_win_rate(trades: list) -> float:
        ...

    @staticmethod
    def generate_report(equity_curve: pd.Series, trades: list) -> dict:
        ...

    @staticmethod
    def plot_equity_curve(equity_curve: pd.Series, title: str = 'Equity Curve') -> None:
        ...

    @staticmethod
    def plot_drawdown(equity_curve: pd.Series, title: str = 'Drawdown') -> None:
        ...
