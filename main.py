from src.data import fetch_stock_daily, clean_data, get_limit_up_down
from src.strategy import generate_signal
from src.backtest import BacktestEngine
from src.risk import RiskManager
from src.report import PerformanceReport


def main():
    symbol = "000001"
    start_date = "20230101"
    end_date = "20241231"

    df = fetch_stock_daily(symbol, start_date, end_date)
    df = clean_data(df)
    df = get_limit_up_down(df)
    df = generate_signal(df)

    engine = BacktestEngine()
    result = engine.run(df)

    report = PerformanceReport.generate_report(
        engine.equity_curve, engine.trades
    )

    PerformanceReport.plot_equity_curve(engine.equity_curve)
    PerformanceReport.plot_drawdown(engine.equity_curve)


if __name__ == "__main__":
    main()
