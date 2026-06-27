from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
import pandas as pd
import numpy as np
import pickle
import json
import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
import requests
import warnings
warnings.filterwarnings("ignore")

app = FastAPI(title="FinSightAI API", version="1.0.0")

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve React frontend ──────────────────────────────────────
if os.path.exists("frontend/dist"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

@app.get("/app")
def serve_frontend():
    return FileResponse("frontend/dist/index.html")

# ── Database (optional) ───────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:prerana123@localhost/finsight_ai"
)
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    DB_AVAILABLE = True
    print("Database connected successfully")
except Exception as e:
    DB_AVAILABLE = False
    engine = None
    print(f"Database not available: {e}")

analyzer     = SentimentIntensityAnalyzer()
NEWS_API_KEY = "72aba2b041d445cc8a3fe2bb64c0c79a"

# ── Load saved model ──────────────────────────────────────────
with open("backend/models/saved/best_model.pkl",     "rb") as f:
    model = pickle.load(f)
with open("backend/models/saved/best_scaler.pkl",    "rb") as f:
    scaler = pickle.load(f)
with open("backend/models/saved/best_features.json", "r") as f:
    FEATURES = json.load(f)

SIGNAL_MAP   = {0: "SELL", 1: "HOLD", 2: "BUY"}
SIGNAL_COLOR = {0: "red",  1: "yellow", 2: "green"}

US_TICKERS  = ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN"]
IN_TICKERS  = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "WIPRO.NS"]
ALL_TICKERS = US_TICKERS + IN_TICKERS

KEYWORD_MAP = {
    "AAPL":        "Apple stock",
    "MSFT":        "Microsoft stock",
    "TSLA":        "Tesla stock",
    "GOOGL":       "Google Alphabet stock",
    "AMZN":        "Amazon stock",
    "RELIANCE.NS": "Reliance Industries stock",
    "TCS.NS":      "TCS Tata Consultancy stock",
    "INFY.NS":     "Infosys stock",
    "HDFCBANK.NS": "HDFC Bank stock",
    "WIPRO.NS":    "Wipro stock",
}

# ── Helper: fetch live sentiment from NewsAPI ─────────────────
def fetch_live_sentiment(ticker: str):
    keyword = KEYWORD_MAP.get(ticker, ticker)
    url     = "https://newsapi.org/v2/everything"
    params  = {
        "q":        keyword,
        "sortBy":   "publishedAt",
        "language": "en",
        "pageSize": 10,
        "apiKey":   NEWS_API_KEY,
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data     = response.json()
        articles = data.get("articles", [])
        results  = []
        scores   = []
        for a in articles:
            headline = a.get("title", "")
            if not headline or headline == "[Removed]":
                continue
            score = analyzer.polarity_scores(headline)["compound"]
            label = ("POSITIVE" if score >= 0.05
                     else "NEGATIVE" if score <= -0.05
                     else "NEUTRAL")
            scores.append(score)
            results.append({
                "headline":        headline,
                "source":          a.get("source", {}).get("name", ""),
                "published_at":    a.get("publishedAt", "")[:10],
                "sentiment_score": round(score, 3),
                "sentiment_label": label,
            })
        avg = round(sum(scores) / len(scores), 3) if scores else 0.1
        return avg, results
    except Exception:
        return 0.1, []

# ── Helper: compute ML features ──────────────────────────────
def compute_features(df: pd.DataFrame, avg_sentiment: float = 0.1) -> dict:
    from ta.momentum   import RSIIndicator
    from ta.trend      import MACD
    from ta.volatility import BollingerBands

    close  = df["Close"]
    volume = df["Volume"]

    rsi_ind  = RSIIndicator(close=close, window=14)
    rsi      = rsi_ind.rsi()

    macd_ind = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
    macd     = macd_ind.macd()
    macd_sig = macd_ind.macd_signal()
    macd_hist= macd_ind.macd_diff()

    bb       = BollingerBands(close=close, window=20, window_dev=2)
    bb_upper = bb.bollinger_hband()
    bb_mid   = bb.bollinger_mavg()
    bb_lower = bb.bollinger_lband()
    bb_pct   = bb.bollinger_pband()

    ret      = close.pct_change()
    vol_ma20 = volume.rolling(20).mean()
    vol_ratio= volume / (vol_ma20 + 1)
    vol_chg  = volume.pct_change()
    candle   = (df["Close"] - df["Open"]) / (df["Close"].abs() + 1e-9)
    raw_sent = ret * 0.5 + candle * 0.3 + (vol_ratio - 1) * 0.2
    daily_s  = (0.7 * raw_sent + 0.3 * avg_sentiment).clip(-1, 1)

    return {
        "rsi":         rsi.iloc[-1],
        "rsi_prev":    rsi.iloc[-2],
        "rsi_prev2":   rsi.iloc[-3],
        "rsi_prev3":   rsi.iloc[-4],
        "rsi_slope":   rsi.diff(1).iloc[-1],
        "rsi_slope3":  rsi.diff(3).iloc[-1],
        "rsi_accel":   rsi.diff(1).diff(1).iloc[-1],
        "rsi_dist_70": rsi.iloc[-1] - 70,
        "rsi_dist_30": rsi.iloc[-1] - 30,
        "rsi_dist_50": rsi.iloc[-1] - 50,
        "rsi_ma5":     rsi.rolling(5).mean().iloc[-1],
        "rsi_ma10":    rsi.rolling(10).mean().iloc[-1],
        "macd":        macd.iloc[-1],
        "macd_signal": macd_sig.iloc[-1],
        "macd_hist":   macd_hist.iloc[-1],
        "macd_cross":  (macd - macd_sig).iloc[-1],
        "macd_slope":  macd.diff(3).iloc[-1],
        "macd_prev":   macd.iloc[-2],
        "macd_x_prev": (macd - macd_sig).iloc[-2],
        "bb_pct":      bb_pct.iloc[-1],
        "bb_width":    ((bb_upper - bb_lower) / (bb_mid + 1e-9)).iloc[-1],
        "bb_slope":    bb_pct.diff(3).iloc[-1],
        "bb_prev":     bb_pct.iloc[-2],
        "ret_1d":      ret.iloc[-1],
        "ret_2d":      close.pct_change(2).iloc[-1],
        "ret_3d":      close.pct_change(3).iloc[-1],
        "ret_5d":      close.pct_change(5).iloc[-1],
        "ret_10d":     close.pct_change(10).iloc[-1],
        "ret_20d":     close.pct_change(20).iloc[-1],
        "ma5_cross":   ((close - close.rolling(5).mean())  / (close.rolling(5).mean()  + 1e-9)).iloc[-1],
        "ma10_cross":  ((close - close.rolling(10).mean()) / (close.rolling(10).mean() + 1e-9)).iloc[-1],
        "ma20_cross":  ((close - close.rolling(20).mean()) / (close.rolling(20).mean() + 1e-9)).iloc[-1],
        "ma50_cross":  ((close - close.rolling(50).mean()) / (close.rolling(50).mean() + 1e-9)).iloc[-1],
        "vol_ratio":   vol_ratio.iloc[-1],
        "vol_change":  vol_chg.iloc[-1],
        "day_range":   ((df["High"] - df["Low"]) / (close + 1e-9)).iloc[-1],
        "is_bullish":  int(close.iloc[-1] > df["Open"].iloc[-1]),
        "body_size":   (abs(close - df["Open"]) / (close + 1e-9)).iloc[-1],
        "ret_l1":      ret.iloc[-2],
        "ret_l2":      ret.iloc[-3],
        "ret_l3":      ret.iloc[-4],
        "ret_l5":      ret.iloc[-6],
        "daily_sent":  daily_s.iloc[-1],
        "sent_3d":     daily_s.rolling(3).mean().iloc[-1],
        "sent_5d":     daily_s.rolling(5).mean().iloc[-1],
        "sent_mom":    daily_s.diff(3).iloc[-1],
        "sent_l1":     daily_s.iloc[-2],
        "sent_l2":     daily_s.iloc[-3],
        "sent_l3":     daily_s.iloc[-4],
        "sent_l5":     daily_s.iloc[-6],
        "ret_std5":    ret.rolling(5).std().iloc[-1],
        "ret_std20":   ret.rolling(20).std().iloc[-1],
        "ret_mean5":   ret.rolling(5).mean().iloc[-1],
        "ret_mean20":  ret.rolling(20).mean().iloc[-1],
        "avg_sentiment":  avg_sentiment,
        "pct_positive":   50.0,
        "pct_negative":   20.0,
    }

# ── Helper: download price data ───────────────────────────────
def download_price(ticker: str, period: str = "6mo") -> pd.DataFrame:
    """Try multiple methods to get price data."""
    try:
        data = yf.download(
            ticker, period=period,
            auto_adjust=True, progress=False,
            timeout=30
        )
        if not data.empty:
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = [c[0] for c in data.columns]
            return data
    except Exception as e:
        print(f"yfinance error: {e}")

    # Try with yf.Ticker as fallback
    try:
        t    = yf.Ticker(ticker)
        data = t.history(period=period, auto_adjust=True)
        if not data.empty:
            return data
    except Exception as e:
        print(f"yf.Ticker error: {e}")

    return pd.DataFrame()

# ─────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name":         "FinSightAI API",
        "version":      "1.0.0",
        "status":       "running",
        "db_available": DB_AVAILABLE,
        "endpoints": [
            "/api/tickers",
            "/api/price/{ticker}",
            "/api/signal/{ticker}",
            "/api/sentiment/{ticker}",
            "/api/dashboard/{ticker}",
            "/api/model-results",
        ]
    }

# 1. Tickers
@app.get("/api/tickers")
def get_tickers():
    return {"us_tickers": US_TICKERS, "indian_tickers": IN_TICKERS, "all": ALL_TICKERS}

# 2. Live price
@app.get("/api/price/{ticker}")
def get_price(ticker: str, period: str = "6mo"):
    try:
        ticker = ticker.upper()
        data   = download_price(ticker, period)

        if data.empty:
            raise HTTPException(404, f"No data for {ticker}")

        data = data.reset_index()
        data["Date"] = data["Date"].astype(str)

        return {
            "ticker":        ticker,
            "period":        period,
            "current_price": round(float(data["Close"].iloc[-1]), 2),
            "prev_close":    round(float(data["Close"].iloc[-2]), 2),
            "change":        round(float(data["Close"].iloc[-1] - data["Close"].iloc[-2]), 2),
            "change_pct":    round(float((data["Close"].iloc[-1] - data["Close"].iloc[-2]) / data["Close"].iloc[-2] * 100), 2),
            "high_52w":      round(float(data["Close"].max()), 2),
            "low_52w":       round(float(data["Close"].min()), 2),
            "volume":        int(data["Volume"].iloc[-1]),
            "history": [
                {
                    "date":   row["Date"],
                    "open":   round(float(row["Open"]),  2),
                    "high":   round(float(row["High"]),  2),
                    "low":    round(float(row["Low"]),   2),
                    "close":  round(float(row["Close"]), 2),
                    "volume": int(row["Volume"]),
                }
                for _, row in data.iterrows()
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

# 3. ML Signal
@app.get("/api/signal/{ticker}")
def get_signal(ticker: str):
    try:
        ticker = ticker.upper()
        data   = download_price(ticker, "6mo")

        if data.empty:
            raise HTTPException(404, f"No data for {ticker}")

        # Get sentiment
        avg_sent = 0.1
        if DB_AVAILABLE and engine:
            try:
                sent_q  = f"SELECT AVG(sentiment_score) as avg_sent FROM news_articles WHERE ticker='{ticker}'"
                sent_df = pd.read_sql(sent_q, engine)
                avg_sent = float(sent_df["avg_sent"].iloc[0] or 0.1)
            except Exception:
                pass

        if avg_sent == 0.1:
            live_avg, _ = fetch_live_sentiment(ticker)
            avg_sent    = live_avg

        feats = compute_features(data, avg_sent)
        X     = np.array([[feats.get(f, 0.0) for f in FEATURES]])
        X     = scaler.transform(X)

        pred        = model.predict(X)[0]
        proba       = model.predict_proba(X)[0]
        confidence  = round(float(max(proba)) * 100, 1)
        signal_name = SIGNAL_MAP[pred]

        if signal_name == "BUY"  and confidence < 60:
            signal_name = "HOLD"
        if signal_name == "SELL" and confidence < 60:
            signal_name = "HOLD"

        return {
            "ticker":      ticker,
            "signal":      signal_name,
            "confidence":  confidence,
            "color":       SIGNAL_COLOR.get(pred, "yellow"),
            "rsi":         round(feats["rsi"], 2),
            "macd":        round(feats["macd"], 4),
            "bb_pct":      round(feats["bb_pct"], 4),
            "probabilities": {
                "SELL": round(float(proba[0]) * 100, 1),
                "HOLD": round(float(proba[1]) * 100, 1),
                "BUY":  round(float(proba[2]) * 100, 1),
            },
            "generated_at": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

# 4. Sentiment
@app.get("/api/sentiment/{ticker}")
def get_sentiment(ticker: str):
    try:
        ticker = ticker.upper()

        # Try DB first
        if DB_AVAILABLE and engine:
            try:
                query = f"""
                    SELECT headline, source, published_at,
                           sentiment_score, sentiment_label
                    FROM news_articles
                    WHERE ticker = '{ticker}'
                    ORDER BY published_at DESC LIMIT 10
                """
                df = pd.read_sql(query, engine)
                if not df.empty:
                    df["published_at"] = df["published_at"].astype(str)
                    avg_sent = round(float(df["sentiment_score"].mean()), 3)
                    mood = ("Positive 📈" if avg_sent > 0.05
                            else "Negative 📉" if avg_sent < -0.05
                            else "Neutral ➡️")
                    return {
                        "ticker":         ticker,
                        "avg_sentiment":  avg_sent,
                        "mood":           mood,
                        "total_articles": len(df),
                        "positive":       int((df["sentiment_label"] == "POSITIVE").sum()),
                        "negative":       int((df["sentiment_label"] == "NEGATIVE").sum()),
                        "neutral":        int((df["sentiment_label"] == "NEUTRAL").sum()),
                        "articles":       df.to_dict(orient="records"),
                    }
            except Exception:
                pass

        # Fall back to live NewsAPI
        avg_sent, results = fetch_live_sentiment(ticker)
        mood = ("Positive 📈" if avg_sent > 0.05
                else "Negative 📉" if avg_sent < -0.05
                else "Neutral ➡️")

        return {
            "ticker":         ticker,
            "avg_sentiment":  avg_sent,
            "mood":           mood,
            "total_articles": len(results),
            "positive":       sum(1 for r in results if r["sentiment_label"] == "POSITIVE"),
            "negative":       sum(1 for r in results if r["sentiment_label"] == "NEGATIVE"),
            "neutral":        sum(1 for r in results if r["sentiment_label"] == "NEUTRAL"),
            "articles":       results,
        }
    except Exception as e:
        raise HTTPException(500, str(e))

# 5. Full dashboard
@app.get("/api/dashboard/{ticker}")
def get_dashboard(ticker: str):
    price     = get_price(ticker)
    signal    = get_signal(ticker)
    sentiment = get_sentiment(ticker)
    return {
        "ticker":       ticker.upper(),
        "price":        price,
        "signal":       signal,
        "sentiment":    sentiment,
        "generated_at": datetime.now().isoformat(),
    }

# 6. Model results
@app.get("/api/model-results")
def get_model_results():
    try:
        with open("backend/models/saved/all_results.json", "r") as f:
            results = json.load(f)
        df = pd.read_csv("backend/models/saved/model_comparison.csv")
        return {
            "results":       results,
            "summary":       df.to_dict(orient="records"),
            "best_model":    "XGBoost",
            "best_accuracy": 90.39,
            "benchmark":     68.50,
            "improvement":   21.89,
        }
    except Exception as e:
        raise HTTPException(500, str(e))