import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
} from "recharts";
import api from "../api/client";
import { PerformanceResponse } from "../types/analyzer";
import "./Analytics.css";

const PERIODS = ["1mo", "3mo", "6mo", "1y", "2y", "5y"] as const;

function formatCurrency(value: number): string {
  return value.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  });
}

function formatPct(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

export default function Analytics() {
  const [symbol, setSymbol] = useState("");
  const [period, setPeriod] = useState<string>("1y");
  const [data, setData] = useState<PerformanceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPerformance = () => {
    if (!symbol.trim()) return;
    setLoading(true);
    setError(null);
    api
      .get<PerformanceResponse>("/analyze/performance", {
        params: { symbol: symbol.trim().toUpperCase(), period },
      })
      .then((res) => setData(res.data))
      .catch((err) => {
        setError(err.response?.data?.detail || err.message);
        setData(null);
      })
      .finally(() => setLoading(false));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") fetchPerformance();
  };

  return (
    <div>
      <h1>Analytics</h1>

      {/* Controls */}
      <div className="controls">
        <input
          type="text"
          placeholder="Symbol (e.g. AAPL)"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          onKeyDown={handleKeyDown}
          className="symbol-input"
        />
        <div className="period-buttons">
          {PERIODS.map((p) => (
            <button
              key={p}
              className={`period-btn ${period === p ? "active" : ""}`}
              onClick={() => setPeriod(p)}
            >
              {p}
            </button>
          ))}
        </div>
        <button onClick={fetchPerformance} className="go-btn" disabled={loading}>
          {loading ? "Loading..." : "Analyze"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {data && (
        <>
          {/* Risk Metrics Cards */}
          <div className="metrics-cards">
            <div className="metric-card">
              <span className="metric-label">Sharpe Ratio</span>
              <span className="metric-value">{data.metrics.sharpe_ratio.toFixed(3)}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">CAGR</span>
              <span className="metric-value">{formatPct(data.metrics.cagr)}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Max Drawdown</span>
              <span className="metric-value dd">{formatPct(data.metrics.max_drawdown)}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Volatility</span>
              <span className="metric-value">{formatPct(data.metrics.volatility)}</span>
            </div>
          </div>

          {/* Price Chart */}
          <div className="chart-container">
            <h2>{data.symbol} — Price ({data.period})</h2>
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={data.prices}>
                <defs>
                  <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#646cff" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#646cff" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#888", fontSize: 12 }}
                  tickFormatter={(d: string) => d.slice(5)}
                />
                <YAxis
                  tick={{ fill: "#888", fontSize: 12 }}
                  domain={["auto", "auto"]}
                  tickFormatter={(v: number) => `$${v}`}
                />
                <Tooltip
                  contentStyle={{ background: "#1a1a2e", border: "1px solid #333" }}
                  labelStyle={{ color: "#aaa" }}
                  formatter={(value: number) => [formatCurrency(value), "Close"]}
                />
                <Area
                  type="monotone"
                  dataKey="close"
                  stroke="#646cff"
                  fill="url(#priceGradient)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Volume Chart */}
          <div className="chart-container">
            <h2>Volume</h2>
            <ResponsiveContainer width="100%" height={150}>
              <BarChart data={data.prices}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#888", fontSize: 12 }}
                  tickFormatter={(d: string) => d.slice(5)}
                />
                <YAxis
                  tick={{ fill: "#888", fontSize: 12 }}
                  tickFormatter={(v: number) =>
                    v >= 1_000_000 ? `${(v / 1_000_000).toFixed(1)}M` : `${(v / 1_000).toFixed(0)}K`
                  }
                />
                <Tooltip
                  contentStyle={{ background: "#1a1a2e", border: "1px solid #333" }}
                  labelStyle={{ color: "#aaa" }}
                  formatter={(value: number) => [value.toLocaleString(), "Volume"]}
                />
                <Bar dataKey="volume" fill="#61dafb" opacity={0.6} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}
