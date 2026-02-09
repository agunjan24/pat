import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
import api from "../api/client";
import type { ScanResult } from "../types/signals";
import "./Signals.css";

function formatCurrency(value: number): string {
  return value.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  });
}

function directionColor(dir: string): string {
  if (dir === "buy") return "#50c878";
  if (dir === "sell") return "#e55353";
  return "#888";
}

function signalBarColor(score: number): string {
  if (score > 0.1) return "#50c878";
  if (score < -0.1) return "#e55353";
  return "#555";
}

function convictionBadge(conviction: string): string {
  return `conviction-badge conviction-${conviction}`;
}

export default function Signals() {
  const navigate = useNavigate();
  const [symbol, setSymbol] = useState("");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const scan = () => {
    if (!symbol.trim()) return;
    setLoading(true);
    setError(null);
    api
      .get<ScanResult>("/signals/scan", {
        params: { symbol: symbol.trim().toUpperCase() },
      })
      .then((res) => setResult(res.data))
      .catch((err) => {
        setError(err.response?.data?.detail || err.message);
        setResult(null);
      })
      .finally(() => setLoading(false));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") scan();
  };

  const chartData =
    result?.signals.map((s) => ({
      name: s.name.replace(/_/g, " "),
      score: s.score,
      weighted: +(s.score * s.weight).toFixed(4),
    })) ?? [];

  return (
    <div>
      <h1>Signal Scanner</h1>

      <div className="scan-controls">
        <input
          type="text"
          placeholder="Symbol (e.g. AAPL)"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          onKeyDown={handleKeyDown}
          className="symbol-input"
        />
        <button onClick={scan} className="scan-btn" disabled={loading}>
          {loading ? "Scanning..." : "Scan"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {result && (
        <>
          {/* Recommendation Header */}
          <div className="recommendation" style={{ borderColor: directionColor(result.direction) }}>
            <div className="rec-main">
              <span
                className="rec-direction"
                style={{ color: directionColor(result.direction) }}
              >
                {result.direction.toUpperCase()}
              </span>
              <span className="rec-symbol">{result.symbol}</span>
              <span className="rec-price">{formatCurrency(result.current_price)}</span>
              <span className={convictionBadge(result.conviction)}>
                {result.conviction}
              </span>
            </div>
            <div className="rec-meta">
              <span>
                Composite: <strong>{result.composite_score.toFixed(4)}</strong>
              </span>
              <span>
                Confidence: <strong>{result.confidence}</strong>/100
              </span>
              <button
                className="scan-btn"
                style={{ marginLeft: "auto", padding: "0.4rem 1rem", fontSize: "0.85rem" }}
                onClick={() => navigate(`/backtest?symbol=${result.symbol}`)}
              >
                Backtest
              </button>
            </div>
          </div>

          {/* Risk Context */}
          <div className="risk-cards">
            <div className="risk-card">
              <span className="risk-label">Stop Loss</span>
              <span className="risk-value">
                {result.risk.stop_loss != null
                  ? formatCurrency(result.risk.stop_loss)
                  : "N/A"}
              </span>
            </div>
            <div className="risk-card">
              <span className="risk-label">Target</span>
              <span className="risk-value">
                {result.risk.target_price != null
                  ? formatCurrency(result.risk.target_price)
                  : "N/A"}
              </span>
            </div>
            <div className="risk-card">
              <span className="risk-label">Risk/Reward</span>
              <span className="risk-value">
                {result.risk.risk_reward != null
                  ? `1:${result.risk.risk_reward}`
                  : "N/A"}
              </span>
            </div>
            <div className="risk-card">
              <span className="risk-label">Position Size</span>
              <span className="risk-value">
                {result.risk.position_size} shares ({result.risk.position_pct}%)
              </span>
            </div>
          </div>

          {/* Signal Breakdown Chart */}
          <div className="signal-chart-container">
            <h2>Signal Breakdown</h2>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis
                  type="number"
                  domain={[-1, 1]}
                  tick={{ fill: "#888", fontSize: 12 }}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fill: "#aaa", fontSize: 12 }}
                  width={120}
                />
                <Tooltip
                  contentStyle={{ background: "#1a1a2e", border: "1px solid #333" }}
                  labelStyle={{ color: "#aaa" }}
                  formatter={(value: number, name: string) => [
                    value.toFixed(4),
                    name === "score" ? "Raw Score" : "Weighted",
                  ]}
                />
                <ReferenceLine x={0} stroke="#555" />
                <Bar dataKey="score" name="Raw Score">
                  {chartData.map((d, i) => (
                    <Cell key={i} fill={signalBarColor(d.score)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Signal Detail Table */}
          <div className="signal-table-section">
            <h2>Signal Details</h2>
            <table>
              <thead>
                <tr>
                  <th>Signal</th>
                  <th>Description</th>
                  <th>Score</th>
                  <th>Weight</th>
                  <th>Contribution</th>
                </tr>
              </thead>
              <tbody>
                {result.signals.map((s) => (
                  <tr key={s.name}>
                    <td className="signal-name">{s.name.replace(/_/g, " ")}</td>
                    <td className="signal-desc">{s.description}</td>
                    <td
                      style={{
                        color: signalBarColor(s.score),
                        fontWeight: 600,
                      }}
                    >
                      {s.score > 0 ? "+" : ""}
                      {s.score.toFixed(4)}
                    </td>
                    <td>{(s.weight * 100).toFixed(0)}%</td>
                    <td
                      style={{
                        color: signalBarColor(s.score * s.weight),
                        fontWeight: 600,
                      }}
                    >
                      {s.score * s.weight > 0 ? "+" : ""}
                      {(s.score * s.weight).toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
