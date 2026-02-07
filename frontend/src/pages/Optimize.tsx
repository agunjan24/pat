import { useState } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import api from "../api/client";
import "./Optimize.css";

interface FrontierPoint {
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
  weights: Record<string, number>;
}

interface OptResult {
  symbols: string[];
  min_variance: FrontierPoint;
  max_sharpe: FrontierPoint;
  risk_parity: FrontierPoint;
  frontier: FrontierPoint[];
}

function formatPct(v: number): string {
  return `${(v * 100).toFixed(2)}%`;
}

function WeightsBar({ weights }: { weights: Record<string, number> }) {
  const COLORS = ["#646cff", "#61dafb", "#f5a623", "#e55353", "#50c878", "#9b59b6", "#1abc9c", "#e67e22"];
  const entries = Object.entries(weights).filter(([, w]) => w > 0.001);
  return (
    <div className="weights-bar">
      {entries.map(([sym, w], i) => (
        <div
          key={sym}
          className="weight-segment"
          style={{ width: `${w * 100}%`, background: COLORS[i % COLORS.length] }}
          title={`${sym}: ${(w * 100).toFixed(1)}%`}
        >
          {w > 0.08 && <span>{sym}</span>}
        </div>
      ))}
    </div>
  );
}

export default function Optimize() {
  const [symbols, setSymbols] = useState("");
  const [result, setResult] = useState<OptResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = () => {
    if (!symbols.trim()) return;
    setLoading(true);
    setError(null);
    api
      .get<OptResult>("/analyze/optimize", { params: { symbols: symbols.trim().toUpperCase() } })
      .then((res) => setResult(res.data))
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") run();
  };

  const chartData = result?.frontier.map((p) => ({
    x: +(p.volatility * 100).toFixed(2),
    y: +(p.expected_return * 100).toFixed(2),
  })) ?? [];

  const specialPoints = result
    ? [
        { x: +(result.max_sharpe.volatility * 100).toFixed(2), y: +(result.max_sharpe.expected_return * 100).toFixed(2), label: "Max Sharpe" },
        { x: +(result.min_variance.volatility * 100).toFixed(2), y: +(result.min_variance.expected_return * 100).toFixed(2), label: "Min Var" },
        { x: +(result.risk_parity.volatility * 100).toFixed(2), y: +(result.risk_parity.expected_return * 100).toFixed(2), label: "Risk Parity" },
      ]
    : [];

  return (
    <div>
      <h1>Portfolio Optimizer</h1>
      <div className="opt-controls">
        <input
          type="text"
          placeholder="Symbols (e.g. AAPL,MSFT,GOOGL,AMZN)"
          value={symbols}
          onChange={(e) => setSymbols(e.target.value)}
          onKeyDown={handleKeyDown}
          className="symbols-input"
        />
        <button onClick={run} disabled={loading} className="opt-btn">
          {loading ? "Computing..." : "Optimize"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {result && (
        <>
          {/* Frontier Chart */}
          <div className="chart-box">
            <h2>Efficient Frontier</h2>
            <ResponsiveContainer width="100%" height={350}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis
                  type="number"
                  dataKey="x"
                  name="Volatility"
                  unit="%"
                  tick={{ fill: "#888", fontSize: 12 }}
                  label={{ value: "Volatility %", position: "insideBottom", offset: -5, fill: "#888" }}
                />
                <YAxis
                  type="number"
                  dataKey="y"
                  name="Return"
                  unit="%"
                  tick={{ fill: "#888", fontSize: 12 }}
                  label={{ value: "Return %", angle: -90, position: "insideLeft", fill: "#888" }}
                />
                <Tooltip
                  contentStyle={{ background: "#1a1a2e", border: "1px solid #333" }}
                  formatter={(v: number, name: string) => [`${v}%`, name]}
                />
                <Scatter name="Frontier" data={chartData} fill="#646cff" opacity={0.5} />
                <Scatter name="Key Portfolios" data={specialPoints} fill="#f5a623" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          {/* Allocation Cards */}
          <div className="alloc-cards">
            {([
              { label: "Max Sharpe", point: result.max_sharpe, color: "#50c878" },
              { label: "Min Variance", point: result.min_variance, color: "#61dafb" },
              { label: "Risk Parity", point: result.risk_parity, color: "#f5a623" },
            ] as const).map(({ label, point, color }) => (
              <div key={label} className="alloc-card" style={{ borderColor: color }}>
                <h3 style={{ color }}>{label}</h3>
                <div className="alloc-stats">
                  <span>Return: {formatPct(point.expected_return)}</span>
                  <span>Vol: {formatPct(point.volatility)}</span>
                  <span>Sharpe: {point.sharpe_ratio.toFixed(3)}</span>
                </div>
                <WeightsBar weights={point.weights} />
                <div className="weights-detail">
                  {Object.entries(point.weights)
                    .filter(([, w]) => w > 0.001)
                    .sort(([, a], [, b]) => b - a)
                    .map(([sym, w]) => (
                      <span key={sym}>
                        {sym}: {(w * 100).toFixed(1)}%
                      </span>
                    ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
