import "./Card.css";

export default function SentimentCard({ data }) {
  if (!data) return null;

  return (
    <div className="card">

      <h3>News Sentiment</h3>

      <h1
        style={{
          color: "#38bdf8",
        }}
      >
        {data.mood}
      </h1>

      <div className="stats">

        <div>
          <span>Average Score</span>

          <strong>
            {data.avg_sentiment}
          </strong>
        </div>

        <div>
          <span>Articles</span>

          <strong>
            {data.total_articles}
          </strong>
        </div>

        <div>
          <span>Positive</span>

          <strong
            style={{
              color: "#22c55e",
            }}
          >
            {data.positive}
          </strong>
        </div>

        <div>
          <span>Negative</span>

          <strong
            style={{
              color: "#ef4444",
            }}
          >
            {data.negative}
          </strong>
        </div>

        <div>
          <span>Neutral</span>

          <strong
            style={{
              color: "#f59e0b",
            }}
          >
            {data.neutral}
          </strong>
        </div>

      </div>

    </div>
  );
}