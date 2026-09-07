# Bundled Sample Assets

This directory contains bundled data for offline/reproducible execution.

## `sample_assets.csv`

A bundled dataset of Indian large-cap equity tickers with sector classifications.
This dataset enables fully offline Judge Mode execution and reproducible results.

## Data Licensing Note

Yahoo Finance data retrieved via `yfinance` is used here for
research/demonstration purposes only, via `yfinance`'s unofficial access to
publicly available data. It is not redistributed and is not used for any
commercial trading purpose.

## `cache/` (gitignored)

Downloaded market data is cached here during live sessions.
This directory is excluded from version control.
