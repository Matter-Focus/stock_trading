from src.data import get_stock_data, save_to_csv, load_from_csv


def main():
    symbol = "000001"
    start_date = "2025-06-19"
    end_date = "2026-06-19"

    cache_file = "%s_%s_%s.csv" % (symbol, start_date, end_date)
    df = load_from_csv(cache_file)

    if df is None:
        df = get_stock_data(symbol, start_date, end_date)
        save_to_csv(df, cache_file)
        print("Data fetched from API")
    else:
        print("Data loaded from cache")

    print("Data loaded, shape: %s" % str(df.shape))
    print("Date range: %s to %s" % (df.index[0].date(), df.index[-1].date()))


if __name__ == "__main__":
    main()