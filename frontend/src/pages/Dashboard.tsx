import { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import api from "../api/client";
import { PortfolioSummary } from "../types/analyzer";
import "./Dashboard.css";

const COLORS = [
  "#646cff",
  "#61dafb",
  "#f5a623",
  "#e55353",
  "#50c878",
  "#9b59b6",
  "#1abc9c",
  "#e67e22",
];

function formatCurrency(value: number): string {
  return value.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  });
}

function pnlClass(value: number): string {
  if (value > 0) return "pnl-positive";
  if (value < 0) return "pnl-negative";
  return "";
}

export default function Dashboard() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<PortfolioSummary>("/analyze/summary")
      .then((res) => setSummary(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="loading">Loading portfolio...</p>;
  if (error) return <p className="error">Error: {error}</p>;
  if (!summary || summary.position_count === 0) {
    return (
      <div>
        <h1>Portfolio Dashboard</h1>
        <p>No open positions. Add assets and open positions to get started.</p>
      </div>
    );
  }

  const allocationData = summary.allocation.map((a) => ({
    name: a.symbol,
    value: a.market_value,
  }));

  return (
    <div>
      <h1>Portfolio Dashboard</h1>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="card">
          <span className="card-label">Market Value</span>
          <span className="card-value">
            {formatCurrency(summary.total_market_value)}
          </span>
        </div>
        <div className="card">
          <span className="card-label">Cost Basis</span>
          <span className="card-value">
            {formatCurrency(summary.total_cost_basis)}
          </span>
        </div>
        <div className="card">
          <span className="card-label">Unrealized P&L</span>
          <span
            className={`card-value ${pnlClass(summary.total_unrealized_pnl)}`}
          >
            {formatCurrency(summary.total_unrealized_pnl)} (
            {summary.total_unrealized_pnl_pct.toFixed(2)}%)
          </span>
        </div>
        <div className="card">
          <span className="card-label">Positions</span>
          <span className="card-value">{summary.position_count}</span>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Positions Table */}
        <div className="table-section">
          <h2>Positions</h2>
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Type</th>
                <th>Qty</th>
                <th>Avg Cost</th>
                <th>Price</th>
                <th>Mkt Value</th>
                <th>P&L</th>
                <th>P&L %</th>
              </tr>
            </thead>
            <tbody>
              {summary.positions.map((p) => (
                <tr key={p.position_id}>
                  <td className="symbol">{p.symbol}</td>
                  <td>{p.asset_type}</td>
                  <td>{p.quantity}</td>
                  <td>{formatCurrency(p.avg_cost)}</td>
                  <td>{formatCurrency(p.current_price)}</td>
                  <td>{formatCurrency(p.market_value)}</td>
                  <td className={pnlClass(p.unrealized_pnl)}>
                    {formatCurrency(p.unrealized_pnl)}
                  </td>
                  <td className={pnlClass(p.unrealized_pnl_pct)}>
                    {p.unrealized_pnl_pct.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Allocation Chart */}
        <div className="chart-section">
          <h2>Allocation</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={allocationData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                dataKey="value"
                nameKey="name"
                label={({ name, percent }) =>
                  `${name} ${(percent * 100).toFixed(1)}%`
                }
                labelLine={false}
              >
                {allocationData.map((_, i) => (
                  <Cell
                    key={`cell-${i}`}
                    fill={COLORS[i % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number) => formatCurrency(value)}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
