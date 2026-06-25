import requests
import pandas as pd
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:prerana123@localhost/finsight_ai"
engine = create_engine(DATABASE_URL)

API_KEY = "72aba2b041d445cc8a3fe2bb64c0c79a"

# Search keywords for each ticker
TICKER_KEYWORDS = {
    # US Stocks
    "AAPL":         "Apple stock",
    "MSFT":         "Microsoft stock",
    "TSLA":         "Tesla stock",
    "GOOGL":        "Google Alphabet stock",
    "AMZN":         "Amazon stock",
    # Indian Stocks
    "RELIANCE.NS":  "Reliance Industries stock",
    "TCS.NS":       "TCS Tata Consultancy stock",
    "INFY.NS":      "Infosys stock",
    "HDFCBANK.NS":  "HDFC Bank stock",
    "WIPRO.NS":     "Wipro stock",
}

analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text):
    score = analyzer.polarity_scores(text)["compound"]
    if score >= 0.05:
        label = "POSITIVE"
    elif score <= -0.05:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"
    return score, label

def fetch_news(ticker, keyword):
    print(f"  Fetching news for {ticker}...")
    
    # Free tier only allows last 30 days
    from_date = (datetime.now() - timedelta(days=29)).strftime("%Y-%m-%d")
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q":        keyword,
        "from":     from_date,
        "sortBy":   "publishedAt",
        "language": "en",
        "pageSize": 100,
        "apiKey":   API_KEY,
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get("status") != "ok":
        print(f"  ERROR for {ticker}: {data.get('message', 'Unknown error')}")
        return []
    
    articles = data.get("articles", [])
    print(f"  Found {len(articles)} articles for {ticker}")
    
    results = []
    for article in articles:
        headline = article.get("title", "")
        if not headline or headline == "[Removed]":
            continue
        
        score, label = get_sentiment(headline)
        
        results.append({
            "ticker":          ticker,
            "headline":        headline,
            "source":          article.get("source", {}).get("name", ""),
            "published_at":    article.get("publishedAt", ""),
            "url":             article.get("url", ""),
            "sentiment_score": score,
            "sentiment_label": label,
        })
    
    return results

def run():
    all_articles = []
    
    print("=" * 55)
    print("  Phase 4+5: News Ingestion + Sentiment Analysis")
    print("=" * 55)
    
    for ticker, keyword in TICKER_KEYWORDS.items():
        articles = fetch_news(ticker, keyword)
        all_articles.extend(articles)
    
    if not all_articles:
        print("No articles fetched. Check API key.")
        return
    
    df = pd.DataFrame(all_articles)
    df["published_at"] = pd.to_datetime(df["published_at"], utc=True)
    df["published_at"] = df["published_at"].dt.tz_localize(None)
    
    # Clear old data and insert fresh
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM news_articles"))
        conn.commit()
    
    df.to_sql(
        "news_articles",
        engine,
        if_exists="append",
        index=False
    )
    
    print("\n" + "=" * 55)
    print("SENTIMENT ANALYSIS RESULTS")
    print("=" * 55)
    
    summary = df.groupby("ticker").agg(
        total_articles  = ("headline", "count"),
        avg_sentiment   = ("sentiment_score", "mean"),
        positive        = ("sentiment_label", lambda x: (x == "POSITIVE").sum()),
        negative        = ("sentiment_label", lambda x: (x == "NEGATIVE").sum()),
        neutral         = ("sentiment_label", lambda x: (x == "NEUTRAL").sum()),
    ).round(3)
    
    print(summary.to_string())
    print(f"\nTotal articles saved: {len(df)}")
    print("\nDone! News + Sentiment saved to news_articles table ✅")

if __name__ == "__main__":
    run()