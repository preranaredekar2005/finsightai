import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";

export default function ProbabilityBar({ data }) {
  if (!data) return null;

  const chartData = [
    {
      name: "SELL",
      value: data.SELL,
    },
    {
      name: "HOLD",
      value: data.HOLD,
    },
    {
      name: "BUY",
      value: data.BUY,
    },
  ];

  const colors = [
    "#ef4444",
    "#f59e0b",
    "#22c55e",
  ];

  return (
    <ResponsiveContainer
      width="100%"
      height={320}
    >
      <BarChart data={chartData}>

        <XAxis dataKey="name" />

        <YAxis />

        <Tooltip />

        <Bar dataKey="value">

          {chartData.map((entry, index) => (

            <Cell
              key={index}
              fill={colors[index]}
            />

          ))}

        </Bar>

      </BarChart>
    </ResponsiveContainer>
  );
}