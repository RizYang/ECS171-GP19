"""Fetch yield and macroeconomic data from FRED.

Target label:
- DGS10 (10-Year Treasury Constant Maturity Rate, daily)

Feature variables:
- DGS1MO, DGS3MO, DGS1, DGS2, DGS5 (daily yields)
- CPIAUCSL, UNRATE (monthly macro indicators)
- DFF (Effective Federal Funds Rate, daily)
"""
# Please run this script: python fetch_fred_data.py --frequency daily
# AI citation: ChatGPT (OpenAI, 2026)

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd
import requests
from pandas_datareader.data import DataReader


FRED_SERIES = {
    "DGS10": "target_dgs10_10y_treasury_rate",
    "DGS1MO": "feat_dgs1mo_1m_treasury_rate",
    "DGS3MO": "feat_dgs3mo_3m_treasury_rate",
    "DGS1": "feat_dgs1_1y_treasury_rate",
    "DGS2": "feat_dgs2_2y_treasury_rate",
    "DGS5": "feat_dgs5_5y_treasury_rate",
    "CPIAUCSL": "feat_cpi_inflation_proxy",
    "UNRATE": "feat_unemployment_rate",
    "DFF": "feat_effective_federal_funds_rate",
}


def fetch_fred_dataframe(
    start_date: str = "1980-01-01",
    end_date: str | None = None,
    frequency: str = "daily",
    drop_all_nan_rows: bool = True,
    request_timeout_seconds: int = 20,
    retry_count: int = 3,
) -> pd.DataFrame:
    """Fetch selected FRED series and return a single aligned dataframe."""
    if end_date is None:
        end_date = str(date.today())

    tickers = list(FRED_SERIES.keys())
    session = requests.Session()
    original_request = session.request

    def request_with_timeout(method: str, url: str, **kwargs):
        kwargs.setdefault("timeout", request_timeout_seconds)
        return original_request(method, url, **kwargs)

    session.request = request_with_timeout  # type: ignore[method-assign]
    raw_df = DataReader(
        tickers,
        "fred",
        start=start_date,
        end=end_date,
        retry_count=retry_count,
        pause=0.5,
        session=session,
    )

    # Ensure deterministic order and readable names.
    df = raw_df[tickers].rename(columns=FRED_SERIES)
    df.index.name = "date"

    # Reindex to a complete daily timeline and ffill lower-frequency features
    # (e.g. CPI, UNRATE) so every date has aligned macro context.
    full_daily_index = pd.date_range(start=start_date, end=end_date, freq="D")
    df = df.reindex(full_daily_index).ffill()
    df.index.name = "date"

    if frequency == "weekly":
        # Friday-close style weekly snapshots.
        df = df.resample("W-FRI").last()
    elif frequency == "monthly":
        # End-of-month snapshots.
        df = df.resample("M").last()
    elif frequency != "daily":
        raise ValueError("frequency must be one of: daily, weekly, monthly")

    if drop_all_nan_rows:
        df = df.dropna(how="all")

    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch daily FRED yields/macro data and optionally resample."
    )
    parser.add_argument(
        "--start-date",
        default="1980-01-01",
        help="Start date in YYYY-MM-DD format (default: 1980-01-01).",
    )
    parser.add_argument(
        "--end-date",
        default=str(date.today()),
        help="End date in YYYY-MM-DD format (default: today).",
    )
    parser.add_argument(
        "--output",
        default="fred_yields_macro_1980_present.csv",
        help="Output CSV path (default: fred_yields_macro_1980_present.csv).",
    )
    parser.add_argument(
        "--frequency",
        choices=["daily", "weekly", "monthly"],
        default="daily",
        help="Output frequency after alignment (default: daily).",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=20,
        help="HTTP timeout per request in seconds (default: 20).",
    )
    parser.add_argument(
        "--retry-count",
        type=int,
        default=3,
        help="Number of retries when requests fail (default: 3).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = fetch_fred_dataframe(
        start_date=args.start_date,
        end_date=args.end_date,
        frequency=args.frequency,
        request_timeout_seconds=args.timeout_seconds,
        retry_count=args.retry_count,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path)

    print(f"Saved data to: {output_path.resolve()}")
    print(f"Date range: {df.index.min().date()} -> {df.index.max().date()}")
    print(f"Frequency: {args.frequency}")
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    if args.frequency == "weekly" and df.shape[0] < 10000:
        print(
            "Note: Weekly data from 1980-present cannot reach 10,000 rows. "
            "Use --frequency daily and/or an earlier --start-date."
        )
    print("Columns:")
    for col in df.columns:
        print(f"- {col}")


if __name__ == "__main__":
    main()
