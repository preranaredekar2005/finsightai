import "./Page.css";

export default function About() {
  return (
    <div className="page">

      <h1>About FinSightAI</h1>

      <p>
        FinSightAI is an AI-powered financial intelligence platform designed
        for real-time stock market analysis.
      </p>

      <div className="info-grid">

        <div className="info-card">
          <h2>Real-Time Market Data</h2>
          <p>
            Live stock prices using Yahoo Finance API with technical indicators.
          </p>
        </div>

        <div className="info-card">
          <h2>Machine Learning</h2>
          <p>
            AI models generate BUY, HOLD and SELL recommendations with
            confidence scores.
          </p>
        </div>

        <div className="info-card">
          <h2>News Sentiment</h2>
          <p>
            Financial news is analysed using NLP sentiment analysis to measure
            market mood.
          </p>
        </div>

        <div className="info-card">
          <h2>Technology Stack</h2>

          <ul>
            <li>FastAPI</li>
            <li>React + Vite</li>
            <li>PostgreSQL</li>
            <li>Scikit-Learn</li>
            <li>Recharts</li>
          </ul>

        </div>

      </div>

    </div>
  );
}