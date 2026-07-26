import "./Card.css";

export default function PriceCard({ data }) {
  if (!data) return null;

  const positive = Number(data.change) >= 0;

  return (
    <div className="card">

      <h3>Live Market Price</h3>

      <h1>
        ${Number(data.current_price).toFixed(2)}
      </h1>

      <h2
        style={{
          color: positive ? "#22c55e" : "#ef4444",
          marginTop: 10,
        }}
      >
        {positive ? "+" : ""}
        {Number(data.change).toFixed(2)}
        {" "}
        (
        {positive ? "+" : ""}
        {Number(data.change_pct).toFixed(2)}
        %)
      </h2>

      <hr />

      <div className="stats">

        <div>
          <span>52W High</span>

          <strong>
            ${data.high_52w}
          </strong>
        </div>

        <div>
          <span>52W Low</span>

          <strong>
            ${data.low_52w}
          </strong>
        </div>

        <div>
          <span>Volume</span>

          <strong>
            {Number(data.volume).toLocaleString()}
          </strong>
        </div>

      </div>

    </div>
  );
}