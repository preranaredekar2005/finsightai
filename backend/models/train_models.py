import pandas as pd
import numpy as np
import pickle
import json
from sqlalchemy import create_engine
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_score,
                             recall_score, f1_score,
                             classification_report)
from xgboost import XGBClassifier
import os
import warnings
warnings.filterwarnings("ignore")

DATABASE_URL = "postgresql://postgres:prerana123@localhost/finsight_ai"
engine = create_engine(DATABASE_URL)
os.makedirs("backend/models/saved", exist_ok=True)

print("="*65)
print("  Phase 7: RSI Crossover Signal Prediction")
print("  BUY = RSI crosses above 30 (oversold recovery)")
print("  SELL = RSI crosses below 70 (overbought correction)")
print("  HOLD = everything else")
print("  Prerana Amit Redekar | PRN: 25070243030")
print("="*65)

# ── Load ──────────────────────────────────────────────────────
prices = pd.read_sql("""
    SELECT ticker, date, open, high, low, close, volume
    FROM stock_prices ORDER BY ticker, date
""", engine)

indicators = pd.read_sql("""
    SELECT ticker, date, rsi, macd, macd_signal,
           macd_hist, bb_upper, bb_middle, bb_lower, bb_pct
    FROM technical_indicators ORDER BY ticker, date
""", engine)

sentiment = pd.read_sql("""
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
df = pd.merge(df, sentiment, on="ticker", how="left")
df = df.sort_values(["ticker","date"]).reset_index(drop=True)

# ── Feature engineering ───────────────────────────────────────
print("\nEngineering features...")
all_dfs = []

for ticker in df["ticker"].unique():
    t = df[df["ticker"] == ticker].copy().reset_index(drop=True)

    # Returns
    ret = t["close"].pct_change()
    for p in [1,2,3,5,10,20]:
        t[f"ret_{p}d"] = t["close"].pct_change(p)

    # Volume
    vol_ma         = t["volume"].rolling(20).mean()
    t["vol_ratio"] = t["volume"] / (vol_ma + 1)
    t["vol_change"]= t["volume"].pct_change()

    # MA crossovers
    for w in [5,10,20,50]:
        ma = t["close"].rolling(w).mean()
        t[f"ma{w}_cross"] = (t["close"] - ma) / (ma + 1e-9)

    # RSI features
    t["rsi_prev"]    = t["rsi"].shift(1)
    t["rsi_prev2"]   = t["rsi"].shift(2)
    t["rsi_prev3"]   = t["rsi"].shift(3)
    t["rsi_slope"]   = t["rsi"].diff(1)
    t["rsi_slope3"]  = t["rsi"].diff(3)
    t["rsi_dist_70"] = t["rsi"] - 70
    t["rsi_dist_30"] = t["rsi"] - 30
    t["rsi_dist_50"] = t["rsi"] - 50
    t["rsi_ma5"]     = t["rsi"].rolling(5).mean()
    t["rsi_ma10"]    = t["rsi"].rolling(10).mean()
    t["rsi_accel"]   = t["rsi"].diff(1).diff(1)

    # MACD
    t["macd_cross"]  = t["macd"] - t["macd_signal"]
    t["macd_slope"]  = t["macd"].diff(3)
    t["macd_prev"]   = t["macd"].shift(1)
    t["macd_x_prev"] = (t["macd"] - t["macd_signal"]).shift(1)

    # BB
    t["bb_width"]    = (t["bb_upper"] - t["bb_lower"]) / (t["bb_middle"] + 1e-9)
    t["bb_slope"]    = t["bb_pct"].diff(3)
    t["bb_prev"]     = t["bb_pct"].shift(1)

    # Candle
    t["day_range"]   = (t["high"] - t["low"]) / (t["close"] + 1e-9)
    t["is_bullish"]  = (t["close"] > t["open"]).astype(int)
    t["body_size"]   = abs(t["close"] - t["open"]) / (t["close"] + 1e-9)

    # Daily sentiment proxy
    candle    = (t["close"] - t["open"]) / (t["close"].abs() + 1e-9)
    raw_sent  = (ret * 0.5 + candle * 0.3 + (t["vol_ratio"] - 1) * 0.2)
    real_sent = float(t["avg_sentiment"].iloc[0])
    t["daily_sent"]  = (0.7 * raw_sent + 0.3 * real_sent).clip(-1, 1)
    t["sent_3d"]     = t["daily_sent"].rolling(3).mean()
    t["sent_5d"]     = t["daily_sent"].rolling(5).mean()
    t["sent_mom"]    = t["daily_sent"].diff(3)

    # Lag features
    for lag in [1,2,3,5]:
        t[f"ret_l{lag}"]  = t["ret_1d"].shift(lag)
        t[f"sent_l{lag}"] = t["daily_sent"].shift(lag)

    # Rolling stats
    t["ret_std5"]    = t["ret_1d"].rolling(5).std()
    t["ret_std20"]   = t["ret_1d"].rolling(20).std()
    t["ret_mean5"]   = t["ret_1d"].rolling(5).mean()
    t["ret_mean20"]  = t["ret_1d"].rolling(20).mean()

    # ── TARGET: RSI Crossover Signal ─────────────────────────
    # BUY  = RSI was below 30 yesterday and crosses above 30 today
    #        OR RSI crosses above its 10-day MA from below
    # SELL = RSI was above 70 yesterday and crosses below 70 today
    #        OR RSI crosses below its 10-day MA from above
    # HOLD = everything else

    rsi_cross_buy = (
        ((t["rsi"] > 30) & (t["rsi_prev"] <= 30)) |
        ((t["rsi"] > t["rsi_ma10"]) & (t["rsi_prev"] <= t["rsi_ma10"].shift(1)))
    )
    rsi_cross_sell = (
        ((t["rsi"] < 70) & (t["rsi_prev"] >= 70)) |
        ((t["rsi"] < t["rsi_ma10"]) & (t["rsi_prev"] >= t["rsi_ma10"].shift(1)))
    )

    t["signal"] = 1  # HOLD
    t.loc[rsi_cross_buy,  "signal"] = 2  # BUY
    t.loc[rsi_cross_sell, "signal"] = 0  # SELL

    all_dfs.append(t)

full_df = pd.concat(all_dfs).reset_index(drop=True)

FEATURES = [
    # Core RSI features — most important
    "rsi", "rsi_prev", "rsi_prev2", "rsi_prev3",
    "rsi_slope", "rsi_slope3", "rsi_accel",
    "rsi_dist_70", "rsi_dist_30", "rsi_dist_50",
    "rsi_ma5", "rsi_ma10",
    # MACD
    "macd", "macd_signal", "macd_hist",
    "macd_cross", "macd_slope", "macd_prev", "macd_x_prev",
    # BB
    "bb_pct", "bb_width", "bb_slope", "bb_prev",
    # Returns
    "ret_1d", "ret_2d", "ret_3d", "ret_5d", "ret_10d", "ret_20d",
    # MA crossovers
    "ma5_cross", "ma10_cross", "ma20_cross", "ma50_cross",
    # Volume
    "vol_ratio", "vol_change",
    # Candle
    "day_range", "is_bullish", "body_size",
    # Lag returns
    "ret_l1", "ret_l2", "ret_l3", "ret_l5",
    # Sentiment
    "daily_sent", "sent_3d", "sent_5d", "sent_mom",
    "sent_l1", "sent_l2", "sent_l3", "sent_l5",
    # Rolling stats
    "ret_std5", "ret_std20", "ret_mean5", "ret_mean20",
    # Static sentiment
    "avg_sentiment", "pct_positive", "pct_negative",
]

clean = full_df.dropna(subset=FEATURES + ["signal"])
clean["signal"] = clean["signal"].astype(int)

print(f"  Dataset : {len(clean):,} rows")
print(f"  SELL(0) : {(clean['signal']==0).sum():,}")
print(f"  HOLD(1) : {(clean['signal']==1).sum():,}")
print(f"  BUY (2) : {(clean['signal']==2).sum():,}")
print(f"  Features: {len(FEATURES)}")

X = clean[FEATURES].values
y = clean["signal"].values

# ── 80/20 time-ordered split ──────────────────────────────────
split    = int(len(X) * 0.80)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

sc      = StandardScaler()
X_train = sc.fit_transform(X_train)
X_test  = sc.transform(X_test)

print(f"\n  Train: {len(X_train):,} | Test: {len(X_test):,}")

# ── Models ────────────────────────────────────────────────────
MODELS = {
    "Logistic Regression": LogisticRegression(
        max_iter=2000, C=1.0, random_state=42),
    "Random Forest": RandomForestClassifier(
        n_estimators=500, max_depth=12,
        min_samples_leaf=2, random_state=42, n_jobs=-1),
    "SVM": SVC(
        kernel="rbf", C=5.0, gamma="scale",
        probability=True, random_state=42),
    "XGBoost": XGBClassifier(
        n_estimators=500, max_depth=6,
        learning_rate=0.02, subsample=0.8,
        colsample_bytree=0.8, min_child_weight=3,
        random_state=42, eval_metric="mlogloss",
        verbosity=0),
}

print("\nTraining all 4 models...")
summary_rows = []
all_results  = {}
best_acc     = 0
best_model   = None
best_name    = ""
best_sc      = None

for name, model in MODELS.items():
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    acc  = round(accuracy_score(y_test, preds)  * 100, 2)
    prec = round(precision_score(y_test, preds,
                 average="macro", zero_division=0) * 100, 2)
    rec  = round(recall_score(y_test, preds,
                 average="macro", zero_division=0) * 100, 2)
    f1   = round(f1_score(y_test, preds,
                 average="macro", zero_division=0) * 100, 2)

    result = {"Accuracy": acc, "Precision": prec,
              "Recall": rec, "F1_Score": f1}
    all_results[name] = result
    summary_rows.append({"Model": name, **result})

    if acc > best_acc:
        best_acc   = acc
        best_model = model
        best_name  = name
        best_sc    = sc

    print(f"  {name:22s} → "
          f"Acc:{acc:6.2f}%  "
          f"Prec:{prec:6.2f}%  "
          f"Rec:{rec:6.2f}%  "
          f"F1:{f1:6.2f}%")

# ── Classification report for best model ──────────────────────
print(f"\n  Detailed report for {best_name}:")
preds_best = best_model.predict(X_test)
print(classification_report(
    y_test, preds_best,
    target_names=["SELL","HOLD","BUY"],
    zero_division=0
))

# ── Save ──────────────────────────────────────────────────────
with open("backend/models/saved/best_model.pkl",     "wb") as f:
    pickle.dump(best_model, f)
with open("backend/models/saved/best_scaler.pkl",    "wb") as f:
    pickle.dump(best_sc, f)
with open("backend/models/saved/best_features.json", "w") as f:
    json.dump(FEATURES, f)
with open("backend/models/saved/all_results.json",   "w") as f:
    json.dump(all_results, f, indent=2)

pd.DataFrame(summary_rows).to_csv(
    "backend/models/saved/model_comparison.csv", index=False)

# ── Final report ──────────────────────────────────────────────
print("\n" + "="*65)
print("  FINAL RESULTS — RSI Crossover Signal Prediction")
print("="*65)
print(f"\n{'Model':<24} {'Accuracy':>9} {'Precision':>10}"
      f" {'Recall':>8} {'F1':>8}")
print("─"*62)
for row in summary_rows:
    print(f"  {row['Model']:<22} {row['Accuracy']:>8.2f}%"
          f" {row['Precision']:>9.2f}%"
          f" {row['Recall']:>7.2f}%"
          f" {row['F1_Score']:>7.2f}%")
print("─"*62)
print(f"\n  ★ Best Model    : {best_name}")
print(f"  ★ Best Accuracy : {best_acc:.2f}%")
print(f"\n  Benchmark (Khalil 2026) : 68.50%")

if best_acc > 68.5:
    print(f"  Status: ✅ BENCHMARK BEATEN! "
          f"({best_acc:.2f}% > 68.50%)")
else:
    print(f"  Status: ❌ ({best_acc:.2f}% vs 68.50%)")

print("\n✅ Best model saved!")
print("   Ready for Phase 8 — FastAPI Backend!")