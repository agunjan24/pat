import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  AreaChart,
  Area,
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
  ReferenceLine,
} from "recharts";
import api from "../api/client";
import type { BacktestResult, HorizonMetrics } from "../types/backtest";
import "./Backtest.css";

function signalColor(score: number, correct: boolean | null): string {
  if (correct === null) return "#555";
  return correct ? "#50c878" : "#e55353";
}

function metricColor(value: number): string {
  if (value > 0) return "stat-positive";
  if (value < 0) return "stat-negative";
  return "";
}

function HorizonCard({ label, metrics, maxDrawdown }: { label: string; metrics: HorizonMetrics; maxDrawdown: number }) {
  return (
    <div className="horizon-card">
      <h3>{label}</h3>
      <div className="horizon-stats">
        <div className="horizon-stat">
          <span className="stat-label">Hit Rate</span>
          <span className={`stat-value ${metrics.hit_rate >= 50 ? "stat-positive" : "stat-negative"}`}>
            {metrics.hit_rate.toFixed(1)}%
          </span>
        </div>
        <div className="horizon-stat">
          <span className="stat-label">Avg Signal Return</span>
          <span className={`stat-value ${metricColor(metrics.avg_signal_return)}`}>
            {metrics.avg_signal_return > 0 ? "+" : ""}{metrics.avg_signal_return.toFixed(4)}
          </span>
        </div>
        <div className="horizon-stat">
          <span className="stat-label">Profit Factor</span>
          <span className={`stat-value ${metrics.profit_factor && metrics.profit_factor >= 1 ? "stat-positive" : "stat-negative"}`}>
            {metrics.profit_factor != null ? metrics.profit_factor.toFixed(2) : "N/A"}
          </span>
        </div>
        <div className="horizon-stat">
          <span className="stat-label">Win / Loss</span>
          <span className="stat-value">{metrics.wins} / {metrics.losses}</span>
        </div>
        <div className="horizon-stat">
          <span className="stat-label">Total Signals</span>
          <span className="stat-value">{metrics.total_signals}</span>
        </div>
        <div className="horizon-stat">
          <span className="stat-label">Max Drawdown</span>
          <span className="stat-value stat-negative">{maxDrawdown.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
}

export default function Backtest() {
  const [searchParams] = useSearchParams();
  const [symbol, setSymbol] = useState(searchParams.get("symbol") || "");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runBacktest = () => {
    if (!symbol.trim() || !startDate || !endDate) return;
    setLoading(true);
    setError(null);
    api
      .get<BacktestResult>("/backtest/run", {
        params: {
          symbol: symbol.trim().toUpperCase(),
          start: startDate,
          end: endDate,
        },
      })
      .then((res) => setResult(res.data))
      .catch((err) => {
        setError(err.response?.data?.detail || err.message);
        setResult(null);
      })
      .finally(() => setLoading(false));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") runBacktest();
  };

  // Signal timeline data: bar chart colored by 5d correctness
  const timelineData =
    result?.daily_signals.map((ds) => {
      const correct5d =
        ds.forward_5d != null
          ? (ds.composite_score > 0 && ds.forward_5d > 0) ||
            (ds.composite_score < 0 && ds.forward_5d < 0)
          : null;
      return {
        date: ds.date,
        score: ds.composite_score,
        correct: correct5d,
      };
    }) ?? [];

  return (
    <div>
      <h1>Signal Backtest</h1>

      <div className="backtest-controls">
        <label>
          Symbol
          <input
            type="text"
            placeholder="e.g. AAPL"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            onKeyDown={handleKeyDown}
            className="symbol-input"
          />
        </label>
        <label>
          Start Date
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </label>
        <label>
          End Date
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </label>
        <button onClick={runBacktest} className="run-btn" disabled={loading}>
          {loading ? "Running..." : "Run Backtest"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {result && (
        <>
          {/* Meta info */}
          <div className="backtest-meta">
            <span>Symbol: <strong>{result.symbol}</strong></span>
            <span>Period: <strong>{result.start_date}</strong> to <strong>{result.end_date}</strong></span>
            <span>Trading Days: <strong>{result.total_trading_days}</strong></span>
          </div>

          {/* Summary Cards */}
          <div className="horizon-summary">
            <HorizonCard label="1-Day Horizon" metrics={result.horizon_1d} maxDrawdown={result.max_drawdown_1d} />
            <HorizonCard label="5-Day Horizon" metrics={result.horizon_5d} maxDrawdown={result.max_drawdown_5d} />
            <HorizonCard label="21-Day Horizon" metrics={result.horizon_21d} maxDrawdown={result.max_drawdown_21d} />
          </div>

          {/* Equity Curve */}
          <div className="backtest-chart-container">
            <h2>Cumulative Signal Returns</h2>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={result.equity_curve}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#888", fontSize: 11 }}
                  interval="preserveStartEnd"
                />
                <YAxis tick={{ fill: "#888", fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ background: "#1a1a2e", border: "1px solid #333" }}
                  labelStyle={{ color: "#aaa" }}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="cum_1d"
                  name="1-Day"
                  stroke="#646cff"
                  fill="#646cff"
                  fillOpacity={0.1}
                />
                <Area
                  type="monotone"
                  dataKey="cum_5d"
                  name="5-Day"
                  stroke="#50c878"
                  fill="#50c878"
                  fillOpacity={0.1}
                />
                <Area
                  type="monotone"
                  dataKey="cum_21d"
                  name="21-Day"
                  stroke="#f5a623"
                  fill="#f5a623"
                  fillOpacity={0.1}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Signal Timeline */}
          <div className="backtest-chart-container">
            <h2>Daily Signal Scores (colored by 5d outcome)</h2>
            <ResponsiveContainer width="100%" height={250}>
              <ComposedChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#888", fontSize: 11 }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  domain={[-1, 1]}
                  tick={{ fill: "#888", fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{ background: "#1a1a2e", border: "1px solid #333" }}
                  labelStyle={{ color: "#aaa" }}
                  formatter={(value: number) => [value.toFixed(4), "Score"]}
                />
                <ReferenceLine y={0} stroke="#555" />
                <Bar dataKey="score" name="Composite Score">
                  {timelineData.map((d, i) => (
                    <Cell key={i} fill={signalColor(d.score, d.correct)} />
                  ))}
                </Bar>
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Conviction Breakdown */}
          <div className="conviction-table-section">
            <h2>Conviction Breakdown</h2>
            <table>
              <thead>
                <tr>
                  <th>Conviction</th>
                  <th>Count</th>
                  <th>Hit Rate 1d</th>
                  <th>Hit Rate 5d</th>
                  <th>Hit Rate 21d</th>
                  <th>Avg Return 1d</th>
                  <th>Avg Return 5d</th>
                  <th>Avg Return 21d</th>
                </tr>
              </thead>
              <tbody>
                {result.conviction_breakdown.map((cb) => (
                  <tr key={cb.conviction}>
                    <td style={{ textTransform: "capitalize", fontWeight: 600 }}>
                      {cb.conviction}
                    </td>
                    <td>{cb.count}</td>
                    <td className={cb.hit_rate_1d >= 50 ? "stat-positive" : "stat-negative"}>
                      {cb.hit_rate_1d.toFixed(1)}%
                    </td>
                    <td className={cb.hit_rate_5d >= 50 ? "stat-positive" : "stat-negative"}>
                      {cb.hit_rate_5d.toFixed(1)}%
                    </td>
                    <td className={cb.hit_rate_21d >= 50 ? "stat-positive" : "stat-negative"}>
                      {cb.hit_rate_21d.toFixed(1)}%
                    </td>
                    <td className={metricColor(cb.avg_return_1d)}>
                      {cb.avg_return_1d > 0 ? "+" : ""}{cb.avg_return_1d.toFixed(4)}
                    </td>
                    <td className={metricColor(cb.avg_return_5d)}>
                      {cb.avg_return_5d > 0 ? "+" : ""}{cb.avg_return_5d.toFixed(4)}
                    </td>
                    <td className={metricColor(cb.avg_return_21d)}>
                      {cb.avg_return_21d > 0 ? "+" : ""}{cb.avg_return_21d.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Daily Detail Table */}
          <div className="daily-table-section">
            <h2>Daily Signals ({result.daily_signals.length} days)</h2>
            <div className="daily-table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Score</th>
                    <th>Direction</th>
                    <th>Conviction</th>
                    <th>Confidence</th>
                    <th>Fwd 1d%</th>
                    <th>Fwd 5d%</th>
                    <th>Fwd 21d%</th>
                    <th>Sig Ret 1d</th>
                    <th>Sig Ret 5d</th>
                    <th>Sig Ret 21d</th>
                  </tr>
                </thead>
                <tbody>
                  {result.daily_signals.map((ds) => (
                    <tr key={ds.date}>
                      <td>{ds.date}</td>
                      <td style={{ fontWeight: 600 }}>
                        {ds.composite_score > 0 ? "+" : ""}
                        {ds.composite_score.toFixed(4)}
                      </td>
                      <td className={`dir-${ds.direction}`}>{ds.direction}</td>
                      <td style={{ textTransform: "capitalize" }}>{ds.conviction}</td>
                      <td>{ds.confidence}</td>
                      <td className={metricColor(ds.forward_1d ?? 0)}>
                        {ds.forward_1d != null ? `${ds.forward_1d > 0 ? "+" : ""}${ds.forward_1d.toFixed(2)}` : "-"}
                      </td>
                      <td className={metricColor(ds.forward_5d ?? 0)}>
                        {ds.forward_5d != null ? `${ds.forward_5d > 0 ? "+" : ""}${ds.forward_5d.toFixed(2)}` : "-"}
                      </td>
                      <td className={metricColor(ds.forward_21d ?? 0)}>
                        {ds.forward_21d != null ? `${ds.forward_21d > 0 ? "+" : ""}${ds.forward_21d.toFixed(2)}` : "-"}
                      </td>
                      <td className={metricColor(ds.signal_return_1d ?? 0)}>
                        {ds.signal_return_1d != null ? ds.signal_return_1d.toFixed(4) : "-"}
                      </td>
                      <td className={metricColor(ds.signal_return_5d ?? 0)}>
                        {ds.signal_return_5d != null ? ds.signal_return_5d.toFixed(4) : "-"}
                      </td>
                      <td className={metricColor(ds.signal_return_21d ?? 0)}>
                        {ds.signal_return_21d != null ? ds.signal_return_21d.toFixed(4) : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
