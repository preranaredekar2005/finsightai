import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:prerana123@localhost/finsight_ai"
engine = create_engine(DATABASE_URL)

tickers = [
    # US Equities
    "AAPL", "MSFT", "TSLA", "GOOGL", "AMZN",

    # NSE Stocks
    "RELIANCE.NS", "TCS.NS", "INFY.NS",
    "HDFCBANK.NS", "WIPRO.NS",

    # Additional NSE Stocks
    "ICICIBANK.NS", "SBIN.NS", "BAJFINANCE.NS",
    "KOTAKBANK.NS", "HINDUNILVR.NS",

    # BSE Stocks (same companies, BSE listing)
    "RELIANCE.BO", "TCS.BO", "INFY.BO",
    "HDFCBANK.BO", "WIPRO.BO",

    # Indian Indices
    "^NSEI",   # Nifty 50
    "^BSESN",  # BSE Sensex
    "^NSEBANK", # Nifty Bank
]

for ticker in tickers:
    print(f"Downloading {ticker}...")

    df = yf.download(
        ticker,
        start="2014-01-01",
        end="2025-06-30",
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

    # Rename 'Date' → 'date'
    df.rename(columns={"Date": "date"}, inplace=True)

    df["date"]   = pd.to_datetime(df["date"])
    df["ticker"] = ticker

    # Handle indices — they may not have volume
    if "volume" not in df.columns:
        df["volume"] = 0

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
print("\nSummary:")
summary = pd.read_sql("""
    SELECT ticker, COUNT(*) as rows,
           MIN(date) as from_date,
           MAX(date) as to_date
    FROM stock_prices
    GROUP BY ticker
    ORDER BY ticker
""", engine)
print(summary.to_string(index=False))