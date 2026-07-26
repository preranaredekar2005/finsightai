import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from "recharts";

import "./Page.css";

const models = [
  { name: "Logistic", accuracy: 80.09 },
  { name: "SVM", accuracy: 84.89 },
  { name: "Random Forest", accuracy: 87.81 },
  { name: "XGBoost", accuracy: 90.39 },
];

const colors = [
  "#3b82f6",
  "#06b6d4",
  "#f59e0b",
  "#22c55e",
];

export default function Models() {
  return (
    <div className="page">

      <h1>Machine Learning Models</h1>

      <p>
        Performance comparison of all machine learning models trained for
        FinSightAI.
      </p>

      <div
        style={{
          background: "#1e293b",
          borderRadius: 16,
          padding: 25,
          marginTop: 30,
          height: 450,
        }}
      >

        <ResponsiveContainer width="100%" height="100%">

          <BarChart data={models}>

            <CartesianGrid stroke="#334155" />

            <XAxis dataKey="name" stroke="#cbd5e1" />

            <YAxis stroke="#cbd5e1" />

            <Tooltip />

            <Bar dataKey="accuracy">

              {models.map((item, index) => (

                <Cell
                  key={index}
                  fill={colors[index]}
                />

              ))}

            </Bar>

          </BarChart>

        </ResponsiveContainer>

      </div>

      <div className="info-grid">

        <div className="info-card">
          <h2>🏆 Best Model</h2>
          <h1 style={{ color: "#22c55e" }}>
            XGBoost
          </h1>
          <p>
            Accuracy: <strong>90.39%</strong>
          </p>
        </div>

        <div className="info-card">
          <h2>Feature Engineering</h2>

          <ul>
            <li>RSI</li>
            <li>MACD</li>
            <li>Bollinger Bands</li>
            <li>Moving Averages</li>
            <li>Volume Indicators</li>
          </ul>

        </div>

      </div>

    </div>
  );
}