import { useEffect, useState } from "react";
import {
  getPrice,
  getSignal,
  getSentiment,
} from "../services/api";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
  LineChart,
  Line,
} from "recharts";

import "./Comparison.css";

const STOCKS = [
  "AAPL",
  "MSFT",
  "TSLA",
  "GOOGL",
  "AMZN",
  "RELIANCE.NS",
  "TCS.NS",
  "INFY.NS",
  "HDFCBANK.NS",
  "WIPRO.NS",
];

export default function Comparison2025() {

  const [ticker, setTicker] = useState("AAPL");

  const [price, setPrice] = useState(null);

  const [signal, setSignal] = useState(null);

  const [sentiment, setSentiment] = useState(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState(false);

  const historicalData = {

    avgPrice: 186.42,

    avgVolume: 42100000,

    avgRSI: 54.1,

    avgVolatility: 1.82,

    bullish: 61,

    bearish: 39,

  };

  useEffect(() => {

    loadData(ticker);

  }, [ticker]);

  async function loadData(stock) {

    setLoading(true);

    setError(false);

    try {

      const [priceRes, signalRes, sentimentRes] = await Promise.all([

        getPrice(stock),

        getSignal(stock),

        getSentiment(stock),

      ]);

      setPrice(priceRes.data);

      setSignal(signalRes.data);

      setSentiment(sentimentRes.data);

    }

    catch (err) {

      console.error(err);

      setError(true);

    }

    finally {

      setLoading(false);

    }

  }

  if (loading) {

    return (

      <div className="comparison-page">

        <h2>Loading Market Comparison...</h2>

      </div>

    );

  }

  if (error || !price || !signal || !sentiment) {

    return (

      <div className="comparison-page">

        <h2>Unable to load comparison data.</h2>

      </div>

    );

  }

  const comparisonChart = [
  {

    metric: "Price",

    Historical: historicalData.avgPrice,

    Current: price.current_price,

  },

  {

    metric: "Volume (M)",

    Historical: historicalData.avgVolume / 1000000,

    Current: price.volume / 1000000,

  },

  {

    metric: "RSI",

    Historical: historicalData.avgRSI,

    Current: signal.rsi,

  },

];

const trendData = [

  {

    name: "Historical",

    value: historicalData.avgPrice,

  },

  {

    name: "Current",

    value: price.current_price,

  },

];
return (

<div className="comparison-page">

<h1>

Historical vs Current Market Analysis

</h1>

<p className="subtitle">

Compare long-term market behaviour (2014–2024)
with today's live market data.

</p>

<div className="ticker-selector">

<label>

Select Stock

</label>

<select

value={ticker}

onChange={(e)=>setTicker(e.target.value)}

>

{

STOCKS.map(stock=>(

<option

key={stock}

value={stock}

>

{stock}

</option>

))

}

</select>

</div>

<div className="comparison-cards">

<div className="compare-card">

<h3>Historical Average Price</h3>

<h2>

${historicalData.avgPrice.toFixed(2)}

</h2>

<p>

2014–2024 Dataset

</p>

</div>

<div className="compare-card">

<h3>Current Price</h3>

<h2>

${price.current_price.toFixed(2)}

</h2>

<p>

Live Market

</p>

</div>

<div className="compare-card">

<h3>Historical RSI</h3>

<h2>

{historicalData.avgRSI}

</h2>

</div>

<div className="compare-card">

<h3>Current RSI</h3>

<h2>

{signal.rsi.toFixed(2)}

</h2>

</div>

<div className="compare-card">

<h3>Historical Volume</h3>

<h2>

{(historicalData.avgVolume/1000000).toFixed(1)} M

</h2>

</div>

<div className="compare-card">

<h3>Current Volume</h3>

<h2>

{(price.volume/1000000).toFixed(1)} M

</h2>

</div>

<div className="compare-card">

<h3>Historical Trend</h3>

<h2>

Bullish

</h2>

<p>

61% Bull Days

</p>

</div>

<div className="compare-card">

<h3>Current AI Signal</h3>

<h2>

{signal.signal}

</h2>

<p>

Live Prediction

</p>

</div>

</div>

<div className="chart-box">

<h2>

Historical vs Current Comparison

</h2>

<ResponsiveContainer

width="100%"

height={420}

>

<BarChart

data={comparisonChart}

>

<CartesianGrid strokeDasharray="3 3"/>

<XAxis dataKey="metric"/>

<YAxis/>

<Tooltip/>

<Legend/>

<Bar

dataKey="Historical"

fill="#3b82f6"

/>

<Bar

dataKey="Current"

fill="#22c55e"

/>

</BarChart>

</ResponsiveContainer>

</div>

<div className="chart-box">

<h2>

Price Difference

</h2>

<ResponsiveContainer

width="100%"

height={350}

>

<LineChart

data={trendData}

>

<CartesianGrid strokeDasharray="3 3"/>

<XAxis dataKey="name"/>

<YAxis/>

<Tooltip/>

<Legend/>

<Line

type="monotone"

dataKey="value"

stroke="#38bdf8"

strokeWidth={4}

/>

</LineChart>

</ResponsiveContainer>

</div>
<div className="feature-box">

<h2>

Market Snapshot

</h2>

<table>

<thead>

<tr>

<th>Metric</th>

<th>Historical</th>

<th>Current</th>

</tr>

</thead>

<tbody>

<tr>

<td>Average Price</td>

<td>${historicalData.avgPrice.toFixed(2)}</td>

<td>${price.current_price.toFixed(2)}</td>

</tr>

<tr>

<td>Average Volume</td>

<td>{(historicalData.avgVolume / 1000000).toFixed(1)} M</td>

<td>{(price.volume / 1000000).toFixed(1)} M</td>

</tr>

<tr>

<td>RSI</td>

<td>{historicalData.avgRSI}</td>

<td>{signal.rsi.toFixed(2)}</td>

</tr>

<tr>

<td>Sentiment</td>

<td>Neutral</td>

<td>{sentiment.mood}</td>

</tr>

<tr>

<td>Recommendation</td>

<td>HOLD</td>

<td>{signal.signal}</td>

</tr>

</tbody>

</table>

</div>

<div className="summary-box">

<h2>

AI Market Insight

</h2>

<p>

The current market performance of <b>{ticker}</b> is compared against
historical market behaviour collected from the 2014–2024 dataset.

The current stock price is

<b>

{" "}
{price.current_price > historicalData.avgPrice ? "above" : "below"}

{" "}

</b>

its historical average price.

The RSI has changed from

<b>

{" "}
{historicalData.avgRSI}

</b>

to

<b>

{" "}
{signal.rsi.toFixed(2)}

</b>

indicating

<b>

{" "}

{signal.rsi > 70
  ? "an overbought condition."
  : signal.rsi < 30
  ? "an oversold condition."
  : "normal market momentum."}

</b>

The latest news sentiment is

<b>

{" "}
{sentiment.mood}

</b>

and the AI prediction engine recommends

<b>

{" "}
{signal.signal}

</b>

based on technical indicators, market momentum and financial news.

This comparison enables investors to understand whether the current
market behaviour differs significantly from long-term historical trends
and assists in making more informed investment decisions.

</p>

</div>

</div>

);

}