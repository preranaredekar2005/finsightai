import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:prerana123@localhost/finsight_ai"

engine = create_engine(DATABASE_URL)

tickers = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "WIPRO.NS"
]

for ticker in tickers:

    print(f"Downloading {ticker}")

    df = yf.download(
        ticker,
        start="2024-01-01",
        end="2026-06-01"
    )

    df.reset_index(inplace=True)

    df["ticker"] = ticker

    df.columns = [
        "date",
        "close",
        "high",
        "low",
        "open",
        "volume",
        "ticker"
    ]

    df = df[
        [
            "ticker",
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]
    ]

    df.to_sql(
        "stock_prices",
        engine,
        if_exists="append",
        index=False
    )

    print(f"{ticker} saved")