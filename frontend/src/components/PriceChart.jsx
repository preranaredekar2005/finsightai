import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function PriceChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div
        style={{
          color: "white",
          padding: 30,
          textAlign: "center",
        }}
      >
        No Price History
      </div>
    );
  }

  const chartData = data.map((item) => ({
    date: item.date.substring(5),
    close: Number(item.close),
  }));

  return (
    <ResponsiveContainer
      width="100%"
      height={350}
    >
      <LineChart data={chartData}>

        <CartesianGrid stroke="#334155" />

        <XAxis
          dataKey="date"
          stroke="#94a3b8"
        />

        <YAxis
          stroke="#94a3b8"
        />

        <Tooltip
          contentStyle={{
            background: "#1e293b",
            border: "none",
            color: "white",
          }}
        />

        <Line
          type="monotone"
          dataKey="close"
          stroke="#22c55e"
          strokeWidth={3}
          dot={false}
        />

      </LineChart>
    </ResponsiveContainer>
  );
}