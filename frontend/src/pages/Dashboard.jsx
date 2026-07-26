import { useEffect, useState } from "react";
import { getDashboard, getTickers } from "../services/api";

import PriceCard from "../components/PriceCard";
import SignalCard from "../components/SignalCard";
import SentimentCard from "../components/SentimentCard";
import PriceChart from "../components/PriceChart";
import ProbabilityBar from "../components/ProbabilityBar";

import "./Dashboard.css";

export default function Dashboard() {
  const [ticker, setTicker] = useState("AAPL");
  const [tickers, setTickers] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTickers();
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [ticker]);

  async function loadTickers() {
    try {
      const res = await getTickers();

      if (res.data.all) {
        setTickers(res.data.all);
      } else {
        setTickers([]);
      }
    } catch (err) {
      console.error(err);
    }
  }

  async function loadDashboard() {
    setLoading(true);

    try {
      const res = await getDashboard(ticker);
      setDashboard(res.data);
    } catch (err) {
      console.error(err);
    }

    setLoading(false);
  }

  if (loading)
    return (
      <div className="loading-screen">
        Loading Dashboard...
      </div>
    );

  if (!dashboard)
    return (
      <div className="loading-screen">
        Failed to load dashboard.
      </div>
    );

  const price = dashboard.price || {};
  const signal = dashboard.signal || {};
  const sentiment = dashboard.sentiment || {};

  const history = price.history || [];
  const probabilities = signal.probabilities || {};
  const articles = sentiment.articles || [];

  return (
    <div className="dashboard-page">

      <div className="hero-banner">

        <div>

          <h1>FinSightAI</h1>

          <p>
            AI Powered Real-Time Financial Intelligence Platform
          </p>

        </div>

        <select
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          className="ticker-select"
        >

          {tickers.map((item) => (

            <option
              key={item}
              value={item}
            >
              {item}
            </option>

          ))}

        </select>

      </div>

      <div className="dashboard-grid">

        <PriceCard data={price} />

        <SignalCard data={signal} />

        <SentimentCard data={sentiment} />

      </div>

      <div className="chart-grid">

        <div className="glass-card">

          <h2>Price History</h2>

          <PriceChart data={history} />

        </div>

        <div className="glass-card">

          <h2>Prediction Confidence</h2>

          <ProbabilityBar data={probabilities} />

        </div>

      </div>

      <div className="glass-card">

        <h2>Latest News</h2>

        <table className="news-table">

          <thead>

            <tr>

              <th>Headline</th>

              <th>Source</th>

              <th>Date</th>

              <th>Sentiment</th>

            </tr>

          </thead>

          <tbody>

            {articles.map((item, index) => (

              <tr key={index}>

                <td>{item.headline}</td>

                <td>{item.source}</td>

                <td>{item.published_at}</td>

                <td>

                  {item.sentiment_label}

                </td>

              </tr>

            ))}

          </tbody>

        </table>

      </div>

    </div>
  );
}