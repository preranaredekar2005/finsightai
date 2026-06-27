import { useState, useEffect } from "react"
import axios from "axios"
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, BarChart, Bar
} from "recharts"

const API = window.location.hostname === "localhost" 
  ? "http://localhost:8000"
  : "https://finsightai-0in2.onrender.com"
const TICKERS = {
  US: ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN"],
  India: ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "WIPRO.NS"]
}

const SIGNAL_COLOR = { BUY: "#22c55e", SELL: "#ef4444", HOLD: "#f59e0b" }

const card = {
  background: "#1e293b", borderRadius: 12,
  padding: 20, border: "1px solid #334155"
}

export default function App() {
  const [ticker, setTicker]       = useState("AAPL")
  const [price, setPrice]         = useState(null)
  const [signal, setSignal]       = useState(null)
  const [sentiment, setSentiment] = useState(null)
  const [modelRes, setModelRes]   = useState(null)
  const [loading, setLoading]     = useState(false)
  const [activeTab, setActiveTab] = useState("dashboard")

  const fetchData = async (t) => {
    setLoading(true)
    try {
      const [p, s, sent] = await Promise.all([
        axios.get(`${API}/api/price/${t}`),
        axios.get(`${API}/api/signal/${t}`),
        axios.get(`${API}/api/sentiment/${t}`),
      ])
      setPrice(p.data)
      setSignal(s.data)
      setSentiment(sent.data)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => { fetchData(ticker) }, [ticker])
  useEffect(() => {
    axios.get(`${API}/api/model-results`).then(r => setModelRes(r.data))
  }, [])

  const chartData = price?.history?.slice(-60).map(d => ({
    date: d.date.slice(5),
    close: d.close,
  })) || []

  return (
    <div style={{
      minHeight: "100vh", background: "#0f172a",
      color: "#e2e8f0", fontFamily: "Inter, sans-serif"
    }}>

      {/* NAVBAR */}
      <nav style={{
        background: "#1e293b", padding: "16px 32px",
        display: "flex", alignItems: "center",
        justifyContent: "space-between",
        borderBottom: "1px solid #334155"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            background: "linear-gradient(135deg,#6366f1,#8b5cf6)",
            borderRadius: 8, padding: "6px 14px",
            fontWeight: 700, fontSize: 18
          }}>FinSightAI</div>
          <span style={{ color: "#64748b", fontSize: 13 }}>
            AI-Powered Market Intelligence
          </span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {["dashboard", "models", "about"].map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} style={{
              background: activeTab === tab ? "#6366f1" : "transparent",
              border: "1px solid #334155", color: "#e2e8f0",
              padding: "6px 16px", borderRadius: 6,
              cursor: "pointer", textTransform: "capitalize", fontSize: 13
            }}>{tab}</button>
          ))}
        </div>
      </nav>

      <div style={{ padding: "24px 32px" }}>

        {/* ── DASHBOARD TAB ── */}
        {activeTab === "dashboard" && (
          <>
            {/* Ticker Buttons */}
            <div style={{ marginBottom: 24 }}>
              <p style={{ color: "#64748b", fontSize: 13, marginBottom: 8 }}>US Markets</p>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {TICKERS.US.map(t => (
                  <button key={t} onClick={() => setTicker(t)} style={{
                    background: ticker === t ? "#6366f1" : "#1e293b",
                    border: `1px solid ${ticker === t ? "#6366f1" : "#334155"}`,
                    color: "#e2e8f0", padding: "8px 18px",
                    borderRadius: 8, cursor: "pointer", fontWeight: 600
                  }}>{t}</button>
                ))}
              </div>
              <p style={{ color: "#64748b", fontSize: 13, margin: "12px 0 8px" }}>Indian Markets (NSE)</p>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {TICKERS.India.map(t => (
                  <button key={t} onClick={() => setTicker(t)} style={{
                    background: ticker === t ? "#f59e0b" : "#1e293b",
                    border: `1px solid ${ticker === t ? "#f59e0b" : "#334155"}`,
                    color: "#e2e8f0", padding: "8px 18px",
                    borderRadius: 8, cursor: "pointer", fontWeight: 600, fontSize: 13
                  }}>{t}</button>
                ))}
              </div>
            </div>

            {loading ? (
              <div style={{ textAlign: "center", padding: 80, color: "#64748b" }}>
                Loading data for {ticker}...
              </div>
            ) : (
              <>
                {/* Stats Row */}
                <div style={{
                  display: "grid", gridTemplateColumns: "repeat(4,1fr)",
                  gap: 16, marginBottom: 24
                }}>
                  <div style={card}>
                    <p style={{ color: "#64748b", fontSize: 12, marginBottom: 4 }}>CURRENT PRICE</p>
                    <p style={{ fontSize: 28, fontWeight: 700, margin: "4px 0" }}>
                      ${price?.current_price?.toFixed(2)}
                    </p>
                    <p style={{ color: price?.change >= 0 ? "#22c55e" : "#ef4444", fontSize: 14 }}>
                      {price?.change >= 0 ? "▲" : "▼"} {Math.abs(price?.change || 0).toFixed(2)} ({price?.change_pct?.toFixed(2)}%)
                    </p>
                  </div>

                  <div style={card}>
                    <p style={{ color: "#64748b", fontSize: 12, marginBottom: 4 }}>ML SIGNAL</p>
                    <p style={{
                      fontSize: 32, fontWeight: 800,
                      color: SIGNAL_COLOR[signal?.signal] || "#e2e8f0", margin: "4px 0"
                    }}>{signal?.signal || "—"}</p>
                    <p style={{ color: "#64748b", fontSize: 13 }}>
                      Confidence: {signal?.confidence}%
                    </p>
                  </div>

                  <div style={card}>
                    <p style={{ color: "#64748b", fontSize: 12, marginBottom: 4 }}>RSI (14)</p>
                    <p style={{ fontSize: 28, fontWeight: 700, margin: "4px 0" }}>
                      {signal?.rsi?.toFixed(2)}
                    </p>
                    <p style={{
                      fontSize: 13,
                      color: signal?.rsi > 70 ? "#ef4444" : signal?.rsi < 30 ? "#22c55e" : "#64748b"
                    }}>
                      {signal?.rsi > 70 ? "Overbought" : signal?.rsi < 30 ? "Oversold" : "Neutral"}
                    </p>
                  </div>

                  <div style={card}>
                    <p style={{ color: "#64748b", fontSize: 12, marginBottom: 4 }}>NEWS SENTIMENT</p>
                    <p style={{ fontSize: 20, fontWeight: 700, margin: "4px 0" }}>
                      {sentiment?.mood || "—"}
                    </p>
                    <p style={{ color: "#64748b", fontSize: 13 }}>
                      Score: {sentiment?.avg_sentiment?.toFixed(3)}
                    </p>
                  </div>
                </div>

                {/* Charts Row */}
                <div style={{
                  display: "grid", gridTemplateColumns: "2fr 1fr",
                  gap: 16, marginBottom: 24
                }}>
                  <div style={card}>
                    <p style={{ fontWeight: 600, marginBottom: 16, fontSize: 15 }}>
                      {ticker} — Price History (Last 60 Days)
                    </p>
                    <ResponsiveContainer width="100%" height={220}>
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="date" stroke="#64748b" fontSize={11} interval={9} />
                        <YAxis stroke="#64748b" fontSize={11} domain={["auto", "auto"]} />
                        <Tooltip contentStyle={{
                          background: "#0f172a", border: "1px solid #334155", borderRadius: 8
                        }} />
                        <Line type="monotone" dataKey="close" stroke="#6366f1" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  <div style={card}>
                    <p style={{ fontWeight: 600, marginBottom: 16, fontSize: 15 }}>Signal Probabilities</p>
                    {signal?.probabilities && Object.entries(signal.probabilities).map(([k, v]) => (
                      <div key={k} style={{ marginBottom: 16 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                          <span style={{ fontWeight: 600, color: SIGNAL_COLOR[k] || "#e2e8f0" }}>{k}</span>
                          <span style={{ color: "#94a3b8" }}>{v}%</span>
                        </div>
                        <div style={{ background: "#334155", borderRadius: 999, height: 8 }}>
                          <div style={{
                            background: SIGNAL_COLOR[k] || "#6366f1",
                            width: `${v}%`, height: "100%", borderRadius: 999,
                            transition: "width 0.5s ease"
                          }} />
                        </div>
                      </div>
                    ))}
                    <div style={{
                      marginTop: 20, padding: "10px 14px",
                      background: "#0f172a", borderRadius: 8, border: "1px solid #334155"
                    }}>
                      <p style={{ color: "#64748b", fontSize: 12 }}>Technical Indicators</p>
                      <p style={{ fontSize: 13, marginTop: 4 }}>
                        MACD: <span style={{ color: "#94a3b8" }}>{signal?.macd?.toFixed(4)}</span>
                      </p>
                      <p style={{ fontSize: 13 }}>
                        BB%: <span style={{ color: "#94a3b8" }}>{signal?.bb_pct?.toFixed(4)}</span>
                      </p>
                    </div>
                  </div>
                </div>

                {/* News */}
                <div style={{ ...card, marginBottom: 24 }}>
                  <p style={{ fontWeight: 600, marginBottom: 16, fontSize: 15 }}>
                    Latest News — {ticker}
                  </p>
                  {sentiment?.articles?.slice(0, 5).map((a, i) => (
                    <div key={i} style={{
                      padding: "12px 0",
                      borderBottom: i < 4 ? "1px solid #334155" : "none",
                      display: "flex", alignItems: "flex-start", gap: 12
                    }}>
                      <span style={{
                        background: a.sentiment_label === "POSITIVE" ? "#16a34a33"
                          : a.sentiment_label === "NEGATIVE" ? "#dc262633" : "#33415533",
                        color: a.sentiment_label === "POSITIVE" ? "#22c55e"
                          : a.sentiment_label === "NEGATIVE" ? "#ef4444" : "#64748b",
                        padding: "2px 8px", borderRadius: 4, fontSize: 11,
                        fontWeight: 600, whiteSpace: "nowrap", marginTop: 2
                      }}>{a.sentiment_label}</span>
                      <div>
                        <p style={{ fontSize: 13, lineHeight: 1.5 }}>{a.headline}</p>
                        <p style={{ color: "#64748b", fontSize: 11, marginTop: 4 }}>
                          {a.source} · {a.published_at?.slice(0, 10)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* 52W Range */}
                <div style={card}>
                  <p style={{ fontWeight: 600, marginBottom: 16, fontSize: 15 }}>52-Week Range</p>
                  <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                    <span style={{ color: "#64748b", fontSize: 13 }}>${price?.low_52w}</span>
                    <div style={{
                      flex: 1, background: "#334155",
                      borderRadius: 999, height: 8, position: "relative"
                    }}>
                      <div style={{
                        position: "absolute",
                        left: `${((price?.current_price - price?.low_52w) /
                          (price?.high_52w - price?.low_52w)) * 100}%`,
                        top: "50%", transform: "translate(-50%,-50%)",
                        background: "#6366f1", width: 16, height: 16,
                        borderRadius: "50%", border: "2px solid #e2e8f0"
                      }} />
                    </div>
                    <span style={{ color: "#64748b", fontSize: 13 }}>${price?.high_52w}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
                    <span style={{ color: "#64748b", fontSize: 12 }}>52W Low</span>
                    <span style={{ fontWeight: 600 }}>Current: ${price?.current_price}</span>
                    <span style={{ color: "#64748b", fontSize: 12 }}>52W High</span>
                  </div>
                </div>
              </>
            )}
          </>
        )}

        {/* ── MODELS TAB ── */}
        {activeTab === "models" && modelRes && (
          <div>
            <h2 style={{ marginBottom: 24, fontSize: 22 }}>ML Model Performance Comparison</h2>
            <div style={{
              display: "grid", gridTemplateColumns: "repeat(4,1fr)",
              gap: 16, marginBottom: 32
            }}>
              {modelRes.summary?.map(m => (
                <div key={m.Model} style={{
                  background: m.Model === "XGBoost" ? "#1e1b4b" : "#1e293b",
                  borderRadius: 12, padding: 20,
                  border: `1px solid ${m.Model === "XGBoost" ? "#6366f1" : "#334155"}`
                }}>
                  {m.Model === "XGBoost" && (
                    <span style={{
                      background: "#6366f1", fontSize: 11, padding: "2px 8px",
                      borderRadius: 4, fontWeight: 700, marginBottom: 8, display: "inline-block"
                    }}>★ BEST</span>
                  )}
                  <p style={{ fontWeight: 700, fontSize: 15, marginBottom: 12 }}>{m.Model}</p>
                  <p style={{ fontSize: 32, fontWeight: 800, color: "#6366f1" }}>{m.Accuracy}%</p>
                  <p style={{ color: "#64748b", fontSize: 12 }}>Accuracy</p>
                  <div style={{ marginTop: 12, fontSize: 13 }}>
                    <p>Precision: <strong>{m.Precision}%</strong></p>
                    <p>Recall: <strong>{m.Recall}%</strong></p>
                    <p>F1 Score: <strong>{m.F1_Score}%</strong></p>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ ...card, marginBottom: 20 }}>
              <p style={{ fontWeight: 600, marginBottom: 16, fontSize: 15 }}>Accuracy Comparison</p>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={modelRes.summary}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="Model" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" domain={[0, 100]} fontSize={12} />
                  <Tooltip contentStyle={{
                    background: "#0f172a", border: "1px solid #334155", borderRadius: 8
                  }} />
                  <Bar dataKey="Accuracy" fill="#6366f1" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div style={{
              padding: 20, background: "#052e16",
              borderRadius: 12, border: "1px solid #16a34a"
            }}>
              <p style={{ color: "#22c55e", fontWeight: 700, fontSize: 16 }}>✅ Benchmark Beaten!</p>
              <p style={{ color: "#86efac", marginTop: 8 }}>
                Our best model (XGBoost) achieved {modelRes.best_accuracy}% accuracy,
                exceeding the Khalil (2026) benchmark of {modelRes.benchmark}% by{" "}
                <strong>{modelRes.improvement} percentage points</strong>.
              </p>
            </div>
          </div>
        )}

        {/* ── ABOUT TAB ── */}
        {activeTab === "about" && (
          <div style={{ maxWidth: 700 }}>
            <h2 style={{ marginBottom: 20, fontSize: 22 }}>About FinSightAI</h2>
            <div style={{ ...card, marginBottom: 16 }}>
              <p style={{ fontWeight: 600, marginBottom: 8 }}>Project</p>
              <p style={{ color: "#94a3b8", lineHeight: 1.7 }}>
                AI-Powered Real-Time Financial Intelligence and Market Signal Analysis Platform —
                M.Sc. DSSA Two-Month Project, Symbiosis Institute of Geoinformatics, 2026.
              </p>
            </div>
            <div style={{ ...card, marginBottom: 16 }}>
              <p style={{ fontWeight: 600, marginBottom: 12 }}>Tech Stack</p>
              {[
                ["Backend", "Python, FastAPI, PostgreSQL"],
                ["ML Models", "XGBoost, Random Forest, SVM, Logistic Regression"],
                ["NLP", "VADER Sentiment Analysis"],
                ["Data", "Yahoo Finance, NSEpy (NSE India), NewsAPI"],
                ["Frontend", "React, Recharts, Vite"],
                ["Deployment", "Docker, Render"],
              ].map(([k, v]) => (
                <div key={k} style={{ display: "flex", gap: 12, marginBottom: 8 }}>
                  <span style={{ color: "#6366f1", fontWeight: 600, minWidth: 120, fontSize: 13 }}>{k}</span>
                  <span style={{ color: "#94a3b8", fontSize: 13 }}>{v}</span>
                </div>
              ))}
            </div>
            <div style={card}>
              <p style={{ fontWeight: 600, marginBottom: 8 }}>Student</p>
              <p style={{ color: "#94a3b8", fontSize: 13, lineHeight: 1.8 }}>
                Prerana Amit Redekar<br />
                PRN: 25070243030<br />
                Internal Guide: Mr. Sahil Shah<br />
                Symbiosis Institute of Geoinformatics, Pune
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
