import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:prerana123@localhost/finsight_ai"
engine = create_engine(DATABASE_URL)

tickers = [
    "AAPL", "MSFT", "TSLA", "GOOGL", "AMZN",
    "RELIANCE.NS", "TCS.NS", "INFY.NS",
    "HDFCBANK.NS", "WIPRO.NS"
]

for ticker in tickers:
    print(f"Downloading {ticker}...")

    df = yf.download(
        ticker,
        start="2020-01-01",
        end="2024-12-31",
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        print(f"  WARNING: No data for {ticker}, skipping.")
        continue

    # Flatten multi-level columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    # Lowercase all column names
    df.columns = [col.lower() for col in df.columns]

    # Reset index — date comes from index
    df.reset_index(inplace=True)

    # Rename 'Date' → 'date' (capital D after reset_index)
    df.rename(columns={"Date": "date"}, inplace=True)

    df["date"] = pd.to_datetime(df["date"])
    df["ticker"] = ticker

    df = df[["ticker", "date", "open", "high", "low", "close", "volume"]]

    # Delete existing rows for this ticker before inserting
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM stock_prices WHERE ticker = :ticker"),
            {"ticker": ticker}
        )
        conn.commit()

    df.to_sql(
        "stock_prices",
        engine,
        if_exists="append",
        index=False
    )

    print(f"  {ticker}: {len(df)} rows saved successfully!")

print("\nAll tickers done!")