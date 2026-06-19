from src.data import get_stock_data, save_to_csv, load_from_csv, generate_mock_data
from src.strategy import generate_signal
from src.backtest import BacktestEngine
from src.risk import RiskManager
from src.report import PerformanceReport


def main():
    symbol = "000001"
    start_date = "20250619"
    end_date = "20260619"

    cache_file = "%s_%s_%s.csv" % (symbol, start_date, end_date)
    df = load_from_csv(cache_file)

    if df is None:
        try:
            df = get_stock_data(symbol, start_date, end_date)
            save_to_csv(df, cache_file)
            print("Data fetched from API")
        except Exception as e:
            print("API fetch failed, using mock data")
            df = generate_mock_data(days=252)
            save_to_csv(df, cache_file)

    print("Data loaded, shape: %s" % str(df.shape))
    print("Date range: %s to %s" % (df.index[0].date(), df.index[-1].date()))


if __name__ == "__main__":
    main()