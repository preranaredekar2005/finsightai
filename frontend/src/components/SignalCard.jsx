import "./Card.css";

export default function SignalCard({ data }) {
  if (!data) return null;

  const signal = data.signal || "HOLD";

  const color =
    signal === "BUY"
      ? "#22c55e"
      : signal === "SELL"
      ? "#ef4444"
      : "#f59e0b";

  return (
    <div className="card">

      <h3>AI Trading Signal</h3>

      <h1
        style={{
          color: color,
        }}
      >
        {signal}
      </h1>

      <div className="stats">

        <div>
          <span>Confidence</span>
          <strong>{data.confidence}%</strong>
        </div>

        <div>
          <span>RSI</span>
          <strong>{data.rsi}</strong>
        </div>

        <div>
          <span>MACD</span>
          <strong>{data.macd}</strong>
        </div>

        <div>
          <span>BB %</span>
          <strong>{data.bb_pct}</strong>
        </div>

      </div>

    </div>
  );
}