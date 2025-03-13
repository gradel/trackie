import datetime as dt

from src.trackie.work.stats import get_stats


if __name__ == "__main__":
    # start_date = dt.date(2025, 3, 4)
    # end_date = dt.date(2025, 3, 4)
    start_date = None
    end_date = None
    stats = get_stats(start_date=start_date, end_date=end_date)
    print(stats)
