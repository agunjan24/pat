import { useState } from "react";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import api from "../api/client";
import { OptionsAnalysis, LeapsAnalysis } from "../types/options";
import "./Options.css";

function formatPct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function rollBadgeClass(rec: string): string {
  if (rec === "roll_now") return "roll-badge roll-now";
  if (rec === "monitor") return "roll-badge roll-monitor";
  return "roll-badge roll-hold";
}

export default function Options() {
  const [symbol, setSymbol] = useState("");
  const [optData, setOptData] = useState<OptionsAnalysis | null>(null);
  const [leapsData, setLeapsData] = useState<LeapsAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"overview" | "leaps">("overview");

  const analyze = () => {
    if (!symbol.trim()) return;
    const sym = symbol.trim().toUpperCase();
    setLoading(true);
    setError(null);

    const overviewReq = api
      .get<OptionsAnalysis>("/options/overview", { params: { symbol: sym } })
      .then((res) => setOptData(res.data))
      .catch(() => setOptData(null));

    const leapsReq = api
      .get<LeapsAnalysis>("/options/leaps", { params: { symbol: sym } })
      .then((res) => setLeapsData(res.data))
      .catch(() => setLeapsData(null));

    Promise.allSettled([overviewReq, leapsReq])
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") analyze();
  };

  return (
    <div>
      <h1>Options & LEAPS</h1>

      <div className="opt-controls">
        <input
          type="text"
          placeholder="Symbol (e.g. AAPL)"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          onKeyDown={handleKeyDown}
          className="symbol-input"
        />
        <button onClick={analyze} className="opt-btn" disabled={loading}>
          {loading ? "Loading..." : "Analyze"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {(optData || leapsData) && (
        <>
          <div className="tab-bar">
            <button
              className={`tab ${tab === "overview" ? "active" : ""}`}
              onClick={() => setTab("overview")}
            >
              IV / Skew / Term Structure
            </button>
            <button
              className={`tab ${tab === "leaps" ? "active" : ""}`}
              onClick={() => setTab("leaps")}
            >
              LEAPS Analysis
            </button>
          </div>

          {tab === "overview" && optData && <OverviewTab data={optData} />}
          {tab === "leaps" && leapsData && <LeapsTab data={leapsData} />}
          {tab === "leaps" && !leapsData && (
            <p className="no-data">No LEAPS expirations (&gt;1 year) available.</p>
          )}
        </>
      )}
    </div>
  );
}

function OverviewTab({ data }: { data: OptionsAnalysis }) {
  const iv = data.iv_metrics;

  const skewChartData = data.skew.points
    .filter((p) => p.call_iv || p.put_iv)
    .map((p) => ({
      strike: p.strike,
      call_iv: p.call_iv ? +(p.call_iv * 100).toFixed(1) : null,
      put_iv: p.put_iv ? +(p.put_iv * 100).toFixed(1) : null,
    }));

  const tsChartData = data.term_structure.map((p) => ({
    expiration: p.expiration,
    dte: p.days_to_expiry,
    iv: +(p.atm_iv * 100).toFixed(1),
  }));

  return (
    <>
      {/* IV Metrics Cards */}
      <div className="iv-cards">
        <div className="iv-card">
          <span className="iv-label">Current IV</span>
          <span className="iv-value">{formatPct(iv.current_iv)}</span>
        </div>
        <div className="iv-card">
          <span className="iv-label">IV Rank</span>
          <span className="iv-value">{iv.iv_rank.toFixed(1)}</span>
        </div>
        <div className="iv-card">
          <span className="iv-label">IV Percentile</span>
          <span className="iv-value">{iv.iv_percentile.toFixed(1)}</span>
        </div>
        <div className="iv-card">
          <span className="iv-label">52w Range</span>
          <span className="iv-value">
            {formatPct(iv.iv_low)} – {formatPct(iv.iv_high)}
          </span>
        </div>
        <div className="iv-card">
          <span className="iv-label">Put/Call Skew</span>
          <span className="iv-value">{data.skew.skew_ratio.toFixed(3)}</span>
        </div>
      </div>

      {/* Volatility Skew Chart */}
      {skewChartData.length > 0 && (
        <div className="chart-box">
          <h2>Volatility Skew (Nearest Expiry)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={skewChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="strike"
                tick={{ fill: "#888", fontSize: 12 }}
                label={{ value: "Strike", position: "insideBottom", offset: -5, fill: "#888" }}
              />
              <YAxis
                tick={{ fill: "#888", fontSize: 12 }}
                label={{ value: "IV %", angle: -90, position: "insideLeft", fill: "#888" }}
              />
              <Tooltip
                contentStyle={{ background: "#1a1a2e", border: "1px solid #333" }}
                labelStyle={{ color: "#aaa" }}
                formatter={(v: number) => `${v}%`}
              />
              <Legend />
              <Line type="monotone" dataKey="call_iv" name="Call IV" stroke="#50c878" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="put_iv" name="Put IV" stroke="#e55353" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Term Structure Chart */}
      {tsChartData.length > 0 && (
        <div className="chart-box">
          <h2>IV Term Structure</h2>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={tsChartData}>
              <defs>
                <linearGradient id="tsGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#646cff" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#646cff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="expiration"
                tick={{ fill: "#888", fontSize: 11 }}
                tickFormatter={(v: string) => v.slice(5)}
              />
              <YAxis
                tick={{ fill: "#888", fontSize: 12 }}
                label={{ value: "ATM IV %", angle: -90, position: "insideLeft", fill: "#888" }}
              />
              <Tooltip
                contentStyle={{ background: "#1a1a2e", border: "1px solid #333" }}
                labelStyle={{ color: "#aaa" }}
                formatter={(v: number) => [`${v}%`, "ATM IV"]}
              />
              <Area type="monotone" dataKey="iv" stroke="#646cff" fill="url(#tsGradient)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </>
  );
}

function LeapsTab({ data }: { data: LeapsAnalysis }) {
  const calls = data.candidates.filter((c) => c.option_type === "call");
  const puts = data.candidates.filter((c) => c.option_type === "put");

  return (
    <>
      <p className="leaps-summary">
        {data.symbol} @ ${data.spot_price.toFixed(2)} —{" "}
        {data.leaps_expirations.length} LEAPS expiration(s):{" "}
        {data.leaps_expirations.join(", ")}
      </p>

      {calls.length > 0 && (
        <>
          <h2>LEAPS Calls (Stock Replacement)</h2>
          <LeapsTable candidates={calls} />
        </>
      )}

      {puts.length > 0 && (
        <>
          <h2>LEAPS Puts</h2>
          <LeapsTable candidates={puts} />
        </>
      )}
    </>
  );
}

function LeapsTable({ candidates }: { candidates: LeapsAnalysis["candidates"] }) {
  return (
    <div className="leaps-table-wrap">
      <table>
        <thead>
          <tr>
            <th>Strike</th>
            <th>Exp</th>
            <th>DTE</th>
            <th>Price</th>
            <th>Delta</th>
            <th>Theta/Day</th>
            <th>IV</th>
            <th>Intrinsic</th>
            <th>Extrinsic</th>
            <th>Ext %</th>
            <th>Cost vs Stock</th>
            <th>Theta Eff</th>
            <th>Roll</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((c, i) => (
            <tr key={i}>
              <td>${c.strike}</td>
              <td>{c.expiration.slice(5)}</td>
              <td>{c.days_to_expiry}</td>
              <td>${c.market_price.toFixed(2)}</td>
              <td>{c.delta.toFixed(3)}</td>
              <td>${Math.abs(c.theta).toFixed(3)}</td>
              <td>{formatPct(c.iv)}</td>
              <td>${c.intrinsic.toFixed(2)}</td>
              <td>${c.extrinsic.toFixed(2)}</td>
              <td>{formatPct(c.extrinsic_pct)}</td>
              <td>{formatPct(c.stock_replacement_cost)}</td>
              <td>{c.theta_efficiency.theta_per_delta.toFixed(4)}</td>
              <td>
                <span className={rollBadgeClass(c.roll_recommendation)}>
                  {c.roll_recommendation.replace(/_/g, " ")}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
