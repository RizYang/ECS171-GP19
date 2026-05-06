# FRED Data Extraction

This project fetches clean macro and treasury yield data from FRED for modeling.

## Variables (FRED tickers)

- Label: `DGS10` (10-Year Treasury Constant Maturity Rate, daily)
- Features:
  - `DGS1MO`, `DGS3MO`, `DGS1`, `DGS2`, `DGS5`
  - `CPIAUCSL`, `UNRATE`, `DFF`

## Date Range

- Default: `1980-01-01` to today

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python fetch_fred_data.py
```

## Optional Arguments

```bash
.venv/bin/python fetch_fred_data.py \
  --start-date 1980-01-01 \
  --end-date 2026-05-05 \
  --frequency daily \
  --output data/fred_yields_macro_1980_present.csv \
  --timeout-seconds 20 \
  --retry-count 3
```

## Frequency and Row Count

- `--frequency daily`: highest row count (recommended if you need more samples)
- `--frequency weekly`: much fewer rows (1980-present is roughly ~2.4k rows)
- `--frequency monthly`: around a few hundred rows

If you need at least 10,000 rows, weekly data from 1980-present is mathematically impossible. Use daily frequency and/or set an earlier `--start-date`.
