import pandas as pd
from sqlalchemy import create_engine, text
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands

DATABASE_URL = "postgresql://postgres:prerana123@localhost/finsight_ai"
engine = create_engine(DATABASE_URL)

# Read all tickers from stock_prices
query = """
SELECT ticker, date, close
FROM stock_prices
ORDER BY ticker, date
"""

print("Reading stock prices from database...")
df = pd.read_sql(query, engine)
print(f"Loaded {len(df)} rows for {df['ticker'].nunique()} tickers")

all_results = []

for ticker in df["ticker"].unique():
    print(f"Computing indicators for {ticker}...")

    stock_df = df[df["ticker"] == ticker].copy()
    stock_df = stock_df.sort_values("date").reset_index(drop=True)

    # RSI
    stock_df["rsi"] = RSIIndicator(
        close=stock_df["close"],
        window=14
    ).rsi()

    # MACD
    macd = MACD(
        close=stock_df["close"],
        window_slow=26,
        window_fast=12,
        window_sign=9
    )
    stock_df["macd"]        = macd.macd()
    stock_df["macd_signal"] = macd.macd_signal()
    stock_df["macd_hist"]   = macd.macd_diff()

    # Bollinger Bands
    bb = BollingerBands(
        close=stock_df["close"],
        window=20,
        window_dev=2
    )
    stock_df["bb_upper"]  = bb.bollinger_hband()
    stock_df["bb_middle"] = bb.bollinger_mavg()
    stock_df["bb_lower"]  = bb.bollinger_lband()
    stock_df["bb_pct"]    = bb.bollinger_pband()  # position within bands 0-1

    result = stock_df[[
        "ticker", "date", "rsi",
        "macd", "macd_signal", "macd_hist",
        "bb_upper", "bb_middle", "bb_lower", "bb_pct"
    ]]

    all_results.append(result)
    print(f"  {ticker}: done")

# Combine all
final_df = pd.concat(all_results)
final_df = final_df.dropna()

# Delete existing data before inserting to avoid duplicates
print("\nClearing old technical_indicators data...")
with engine.connect() as conn:
    conn.execute(text("DELETE FROM technical_indicators"))
    conn.commit()

# Save to database
final_df.to_sql(
    "technical_indicators",
    engine,
    if_exists="append",
    index=False
)

print("\nTechnical indicators saved successfully!")
print(f"Total rows: {len(final_df)}")
print("\nBreakdown by ticker:")
print(final_df.groupby("ticker")["rsi"].count().to_string())