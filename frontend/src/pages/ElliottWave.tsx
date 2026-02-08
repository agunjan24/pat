import { useState } from "react";
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
import type { ElliottWaveResult } from "../types/elliott_wave";
import "./ElliottWave.css";

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

function confidenceClass(confidence: number): string {
  if (confidence >= 0.6) return "confidence-badge confidence-high";
  if (confidence >= 0.3) return "confidence-badge confidence-medium";
  return "confidence-badge confidence-low";
}

function patternDisplay(pattern: string): string {
  return pattern.replace(/_/g, " ");
}

export default function ElliottWave() {
  const [symbol, setSymbol] = useState("");
  const [result, setResult] = useState<ElliottWaveResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = () => {
    if (!symbol.trim()) return;
    setLoading(true);
    setError(null);
    api
      .get<ElliottWaveResult>("/elliott-wave/analyze", {
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
    if (e.key === "Enter") analyze();
  };

  const chartData =
    result?.signals.map((s) => ({
      name: s.name.replace(/_/g, " "),
      score: s.score,
    })) ?? [];

  return (
    <div>
      <h1>Elliott Wave</h1>

      <div className="scan-controls">
        <input
          type="text"
          placeholder="Symbol (e.g. AAPL)"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          onKeyDown={handleKeyDown}
          className="symbol-input"
        />
        <button onClick={analyze} className="scan-btn" disabled={loading}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {result && (
        <>
          {/* Direction + Wave Analysis Header */}
          <div className="wave-header" style={{ borderColor: directionColor(result.direction) }}>
            <div className="wave-main">
              <span
                className="ew-direction"
                style={{ color: directionColor(result.direction) }}
              >
                {result.direction.toUpperCase()}
              </span>
              <span className="rec-symbol">{result.symbol}</span>
              <span className="rec-price">{formatCurrency(result.current_price)}</span>
              <span className={confidenceClass(result.wave_analysis.confidence)}>
                {result.conviction}
              </span>
            </div>
            <div className="ew-rec-meta">
              <span>
                Pattern: <strong>{patternDisplay(result.wave_analysis.pattern)}</strong>
              </span>
              <span>
                Current Wave: <strong>{result.wave_analysis.current_wave}</strong>
              </span>
              <span>
                Confidence: <strong>{(result.wave_analysis.confidence * 100).toFixed(0)}%</strong>
              </span>
            </div>
          </div>

          {/* Fibonacci Levels */}
          {result.wave_analysis.fib_levels.length > 0 && (
            <>
              <h2>Fibonacci Levels</h2>
              <div className="fib-grid">
                {result.wave_analysis.fib_levels.map((fl) => (
                  <div key={fl.ratio + fl.label} className="fib-card">
                    <span className="fib-ratio">{fl.ratio}</span>
                    <span className="fib-price">{formatCurrency(fl.level)}</span>
                    <span className="fib-label">{fl.label}</span>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Signal Scores Bar Chart */}
          <div className="ew-signal-chart">
            <h2>Signal Scores</h2>
            <ResponsiveContainer width="100%" height={160}>
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
                  width={110}
                />
                <Tooltip
                  contentStyle={{ background: "#1a1a2e", border: "1px solid #333" }}
                  labelStyle={{ color: "#aaa" }}
                  formatter={(value: number) => [value.toFixed(4), "Score"]}
                />
                <ReferenceLine x={0} stroke="#555" />
                <Bar dataKey="score" name="Score">
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
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Wave Pivots Table */}
          {result.wave_analysis.wave_pivots.length > 0 && (
            <div className="pivot-section">
              <h2>Wave Pivots</h2>
              <table>
                <thead>
                  <tr>
                    <th>Wave</th>
                    <th>Type</th>
                    <th>Date</th>
                    <th>Price</th>
                  </tr>
                </thead>
                <tbody>
                  {result.wave_analysis.wave_pivots.map((wp) => (
                    <tr key={wp.wave_label + wp.index}>
                      <td style={{ fontWeight: 600, color: "#646cff" }}>
                        {wp.wave_label}
                      </td>
                      <td>{wp.type}</td>
                      <td>{wp.date}</td>
                      <td>{formatCurrency(wp.price)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Risk Cards */}
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
        </>
      )}
    </div>
  );
}
