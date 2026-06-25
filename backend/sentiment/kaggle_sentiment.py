import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:prerana123@localhost/finsight_ai"
engine       = create_engine(DATABASE_URL)
analyzer     = SentimentIntensityAnalyzer()

KAGGLE_FILE  = r"C:\Users\Dell\Downloads\archive (2)\raw_partner_headlines.csv"
US_TICKERS   = ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN"]

print("=" * 60)
print("  Kaggle Historical Sentiment Processing")
print("=" * 60)

# ── Step 1: Load ──────────────────────────────────────────────
print("\nLoading Kaggle dataset (30 seconds)...")
df = pd.read_csv(KAGGLE_FILE)
print(f"  Total rows: {len(df):,}")

# ── Step 2: Filter our tickers only ──────────────────────────
print("\nFiltering for our tickers...")
df = df[df["stock"].isin(US_TICKERS)].copy()
print(f"  Rows after filter: {len(df):,}")
print(df.groupby("stock").size().to_string())

# ── Step 3: Clean dates ───────────────────────────────────────
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date", "headline"])
df["date"] = df["date"].dt.date
df = df[
    (df["date"] >= pd.to_datetime("2020-01-01").date()) &
    (df["date"] <= pd.to_datetime("2024-12-31").date())
]
print(f"\n  Rows after date filter (2020-2024): {len(df):,}")

# ── Step 4: VADER sentiment on each headline ──────────────────
print("\nRunning VADER sentiment on headlines...")
print("  (this takes 1-2 minutes for large datasets)")

def get_sentiment(text):
    if not isinstance(text, str) or len(text.strip()) == 0:
        return 0.0, "NEUTRAL"
    score = analyzer.polarity_scores(text)["compound"]
    if score >= 0.05:
        label = "POSITIVE"
    elif score <= -0.05:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"
    return score, label

scores = df["headline"].apply(
    lambda x: pd.Series(get_sentiment(x),
    index=["sentiment_score", "sentiment_label"])
)
df = pd.concat([df, scores], axis=1)

# ── Step 5: Aggregate to daily sentiment per ticker ───────────
print("\nAggregating to daily sentiment...")
daily = df.groupby(["stock", "date"]).agg(
    sentiment_score  = ("sentiment_score", "mean"),
    article_count    = ("headline", "count"),
    pct_positive     = ("sentiment_label",
                        lambda x: (x=="POSITIVE").sum()*100/len(x)),
    pct_negative     = ("sentiment_label",
                        lambda x: (x=="NEGATIVE").sum()*100/len(x)),
).reset_index()

daily.rename(columns={"stock": "ticker"}, inplace=True)
daily["date"] = pd.to_datetime(daily["date"])

print(f"  Daily sentiment rows: {len(daily):,}")
print("\n  Coverage per ticker:")
print(daily.groupby("ticker").agg(
    days        = ("date", "count"),
    avg_sent    = ("sentiment_score", "mean"),
    date_from   = ("date", "min"),
    date_to     = ("date", "max"),
).round(3).to_string())

# ── Step 6: Save to new table ─────────────────────────────────
print("\nSaving to database...")
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS daily_sentiment"))
    conn.commit()

daily.to_sql("daily_sentiment", engine,
             if_exists="replace", index=False)

print(f"\n✅ Saved {len(daily):,} daily sentiment rows!")
print("   Table: daily_sentiment")
print("\nSample:")
print(daily.head(10).to_string())

# ── Step 7: Quick stats ───────────────────────────────────────
print("\n" + "="*60)
print("  SENTIMENT SUMMARY")
print("="*60)
for ticker in US_TICKERS:
    t = daily[daily["ticker"]==ticker]
    if len(t) == 0:
        print(f"  {ticker:8s} → No data found")
        continue
    print(f"  {ticker:8s} → {len(t):4d} days | "
          f"avg sentiment: {t['sentiment_score'].mean():+.3f} | "
          f"articles: {t['article_count'].sum():,}")