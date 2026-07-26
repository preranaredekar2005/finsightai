import pandas as pd
from sqlalchemy import create_engine
import os

# ==========================================================
# Database Connection
# ==========================================================
DATABASE_URL = "postgresql://postgres:prerana123@localhost/finsight_ai"
engine = create_engine(DATABASE_URL)

# ==========================================================
# Create Output Folder
# ==========================================================
SAVE_PATH = "backend/models/saved"
os.makedirs(SAVE_PATH, exist_ok=True)

print("=" * 60)
print("      FinSightAI Dataset Export Utility")
print("=" * 60)

# ==========================================================
# Export Stock Prices
# ==========================================================
print("\nExporting stock_prices...")

prices = pd.read_sql("""
SELECT *
FROM stock_prices
ORDER BY ticker, date
""", engine)

prices.to_csv(
    f"{SAVE_PATH}/stock_prices_2014_2025.csv",
    index=False
)

print(f"✓ Stock Prices Exported : {len(prices):,} rows")

# ==========================================================
# Export Technical Indicators
# ==========================================================
print("\nExporting technical_indicators...")

technical = pd.read_sql("""
SELECT *
FROM technical_indicators
ORDER BY ticker, date
""", engine)

technical.to_csv(
    f"{SAVE_PATH}/technical_indicators_2014_2025.csv",
    index=False
)

print(f"✓ Technical Indicators Exported : {len(technical):,} rows")

# ==========================================================
# Export News Articles
# ==========================================================
print("\nExporting news_articles...")

news = pd.read_sql("""
SELECT *
FROM news_articles
ORDER BY published_at DESC
""", engine)

news.to_csv(
    f"{SAVE_PATH}/news_articles_2014_2025.csv",
    index=False
)

print(f"✓ News Articles Exported : {len(news):,} rows")

# ==========================================================
# Create Combined Dataset
# ==========================================================
print("\nCreating merged dataset...")

prices["date"] = pd.to_datetime(prices["date"])
technical["date"] = pd.to_datetime(technical["date"])

merged = prices.merge(
    technical,
    on=["ticker", "date"],
    how="inner"
)

merged.to_csv(
    f"{SAVE_PATH}/merged_market_dataset_2014_2025.csv",
    index=False
)

print(f"✓ Merged Dataset Exported : {len(merged):,} rows")

print("\n" + "=" * 60)
print("EXPORT COMPLETED SUCCESSFULLY")
print("=" * 60)

print("\nFiles Created:")
print("1. stock_prices_2014_2025.csv")
print("2. technical_indicators_2014_2025.csv")
print("3. news_articles_2014_2025.csv")
print("4. merged_market_dataset_2014_2025.csv")

print("\nLocation:")
print(SAVE_PATH)