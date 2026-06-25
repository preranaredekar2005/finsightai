import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:prerana123@localhost/finsight_ai"
engine = create_engine(DATABASE_URL)

print("=" * 55)
print("  Phase 6 (Updated): ML Dataset with Daily Sentiment")
print("=" * 55)

prices = pd.read_sql("""
    SELECT ticker, date, open, high, low, close, volume
    FROM stock_prices ORDER BY ticker, date
""", engine)

indicators = pd.read_sql("""
    SELECT ticker, date, rsi, macd, macd_signal,
           macd_hist, bb_upper, bb_middle, bb_lower, bb_pct
    FROM technical_indicators ORDER BY ticker, date
""", engine)

# Static sentiment per ticker (from real NewsAPI data)
static_sent = pd.read_sql("""
    SELECT ticker,
           AVG(sentiment_score) as avg_sentiment,
           SUM(CASE WHEN sentiment_label='POSITIVE'
               THEN 1 ELSE 0 END)*100.0/COUNT(*) as pct_positive,
           SUM(CASE WHEN sentiment_label='NEGATIVE'
               THEN 1 ELSE 0 END)*100.0/COUNT(*) as pct_negative
    FROM news_articles GROUP BY ticker
""", engine)

prices["date"]     = pd.to_datetime(prices["date"])
indicators["date"] = pd.to_datetime(indicators["date"])

df = pd.merge(prices, indicators, on=["ticker","date"], how="inner")
df = pd.merge(df, static_sent, on="ticker", how="left")
df = df.sort_values(["ticker","date"]).reset_index(drop=True)

print(f"Base rows: {len(df)}")

all_dfs = []

for ticker in df["ticker"].unique():
    t = df[df["ticker"] == ticker].copy().reset_index(drop=True)

    # ── Daily price-implied sentiment ─────────────────────────
    # Method: combine return strength + volume surge + candle type
    # This is a standard proxy used when historical news unavailable
    ret       = t["close"].pct_change()
    vol_ratio = t["volume"] / (t["volume"].rolling(20).mean() + 1)
    candle    = (t["close"] - t["open"]) / (t["close"].abs() + 1e-9)

    # Raw daily sentiment proxy
    raw_sent  = (ret * 0.5) + (candle * 0.3) + (vol_ratio - 1) * 0.2

    # Blend with real NewsAPI sentiment (30% real, 70% daily proxy)
    real_sent = t["avg_sentiment"].iloc[0]
    t["daily_sentiment"] = (
        0.7 * raw_sent + 0.3 * real_sent
    ).clip(-1, 1)

    # 3-day and 5-day rolling sentiment
    t["sentiment_3d"]  = t["daily_sentiment"].rolling(3).mean()
    t["sentiment_5d"]  = t["daily_sentiment"].rolling(5).mean()

    # Sentiment momentum — is sentiment improving?
    t["sent_momentum"] = t["daily_sentiment"].diff(3)

    # Sentiment divergence — sentiment vs RSI direction
    t["sent_rsi_div"]  = t["daily_sentiment"] - (t["rsi"] - 50) / 50

    # ── Additional price features ─────────────────────────────
    t["returns"]     = ret
    t["vol_change"]  = t["volume"].pct_change()
    t["vol_ratio"]   = vol_ratio
    t["day_range"]   = (t["high"] - t["low"]) / (t["close"] + 1e-9)
    t["is_bullish"]  = (t["close"] > t["open"]).astype(int)

    # Multi-period returns
    for p in [2, 3, 5, 10]:
        t[f"ret_{p}d"] = t["close"].pct_change(p)

    # MA crossovers
    for w in [5, 10, 20, 50]:
        ma = t["close"].rolling(w).mean()
        t[f"ma{w}_cross"] = (t["close"] - ma) / (ma + 1e-9)

    # RSI features
    t["rsi_slope"]   = t["rsi"].diff(3)
    t["rsi_dist_70"] = t["rsi"] - 70
    t["rsi_dist_30"] = t["rsi"] - 30

    # MACD features
    t["macd_cross"]  = t["macd"] - t["macd_signal"]
    t["macd_slope"]  = t["macd"].diff(3)

    # BB features
    t["bb_width"]    = (
        (t["bb_upper"] - t["bb_lower"]) / (t["bb_middle"] + 1e-9)
    )

    # Lag features
    for lag in [1, 2, 3]:
        t[f"rsi_lag{lag}"]  = t["rsi"].shift(lag)
        t[f"ret_lag{lag}"]  = t["returns"].shift(lag)
        t[f"sent_lag{lag}"] = t["daily_sentiment"].shift(lag)

    # Rolling stats
    t["ret_std5"]    = t["returns"].rolling(5).std()
    t["ret_mean5"]   = t["returns"].rolling(5).mean()

    # ── Target label ──────────────────────────────────────────
    # BUY=2  if next day return > 0.5%
    # SELL=0 if next day return < -0.5%
    # HOLD=1 otherwise
    fwd = t["close"].pct_change().shift(-1)
    t["signal"] = 1
    t.loc[fwd >  0.005, "signal"] = 2
    t.loc[fwd < -0.005, "signal"] = 0

    all_dfs.append(t)

full_df = pd.concat(all_dfs).reset_index(drop=True)
full_df  = full_df.dropna()

# Save to database
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS ml_dataset"))
    conn.commit()

full_df.to_sql("ml_dataset", engine, if_exists="replace", index=False)

print(f"Saved {len(full_df)} rows to ml_dataset")
print(f"SELL: {(full_df['signal']==0).sum()}")
print(f"HOLD: {(full_df['signal']==1).sum()}")
print(f"BUY:  {(full_df['signal']==2).sum()}")
print("✅ ML Dataset updated with daily sentiment!")