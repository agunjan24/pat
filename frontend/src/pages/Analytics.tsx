import { useState, useMemo } from "react";
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
  ComposedChart,
  ReferenceLine,
  Legend,
  Brush,
} from "recharts";
import api from "../api/client";
import type { PerformanceResponse, PricePoint } from "../types/analyzer";
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

/* ── Indicator computations ── */

function computeSMA(closes: number[], period: number): (number | null)[] {
  return closes.map((_, i) => {
    if (i < period - 1) return null;
    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) sum += closes[j];
    return +(sum / period).toFixed(2);
  });
}

function computeRSI(closes: number[], period = 14): (number | null)[] {
  const result: (number | null)[] = new Array(closes.length).fill(null);
  if (closes.length < period + 1) return result;

  let avgGain = 0;
  let avgLoss = 0;
  for (let i = 1; i <= period; i++) {
    const delta = closes[i] - closes[i - 1];
    if (delta > 0) avgGain += delta;
    else avgLoss -= delta;
  }
  avgGain /= period;
  avgLoss /= period;

  result[period] = avgLoss === 0 ? 100 : +(100 - 100 / (1 + avgGain / avgLoss)).toFixed(2);

  for (let i = period + 1; i < closes.length; i++) {
    const delta = closes[i] - closes[i - 1];
    avgGain = (avgGain * (period - 1) + (delta > 0 ? delta : 0)) / period;
    avgLoss = (avgLoss * (period - 1) + (delta < 0 ? -delta : 0)) / period;
    result[i] = avgLoss === 0 ? 100 : +(100 - 100 / (1 + avgGain / avgLoss)).toFixed(2);
  }
  return result;
}

function computeMACD(
  closes: number[],
  fast = 12,
  slow = 26,
  signal = 9
): { macd: (number | null)[]; signal: (number | null)[]; histogram: (number | null)[] } {
  const emaCalc = (data: number[], period: number): number[] => {
    const k = 2 / (period + 1);
    const ema: number[] = [data[0]];
    for (let i = 1; i < data.length; i++) {
      ema.push(data[i] * k + ema[i - 1] * (1 - k));
    }
    return ema;
  };

  const result = {
    macd: new Array(closes.length).fill(null) as (number | null)[],
    signal: new Array(closes.length).fill(null) as (number | null)[],
    histogram: new Array(closes.length).fill(null) as (number | null)[],
  };

  if (closes.length < slow) return result;

  const emaFast = emaCalc(closes, fast);
  const emaSlow = emaCalc(closes, slow);

  const macdLine: number[] = [];
  for (let i = 0; i < closes.length; i++) {
    macdLine.push(emaFast[i] - emaSlow[i]);
  }

  const signalStart = slow - 1;
  const macdForSignal = macdLine.slice(signalStart);
  const signalLine = emaCalc(macdForSignal, signal);

  for (let i = signalStart; i < closes.length; i++) {
    const mi = i - signalStart;
    result.macd[i] = +macdLine[i].toFixed(4);
    if (mi >= signal - 1) {
      result.signal[i] = +signalLine[mi].toFixed(4);
      result.histogram[i] = +(macdLine[i] - signalLine[mi]).toFixed(4);
    }
  }

  return result;
}

interface ChartPoint {
  date: string;
  close: number;
  volume: number;
  sma20?: number | null;
  sma50?: number | null;
  sma200?: number | null;
  rsi?: number | null;
  macd?: number | null;
  macdSignal?: number | null;
  macdHistPos?: number | null;
  macdHistNeg?: number | null;
}

function buildChartData(prices: PricePoint[]): ChartPoint[] {
  const closes = prices.map((p) => p.close);
  const sma20 = computeSMA(closes, 20);
  const sma50 = computeSMA(closes, 50);
  const sma200 = computeSMA(closes, 200);
  const rsi = computeRSI(closes);
  const macd = computeMACD(closes);

  return prices.map((p, i) => ({
    date: p.date,
    close: p.close,
    volume: p.volume,
    sma20: sma20[i],
    sma50: sma50[i],
    sma200: sma200[i],
    rsi: rsi[i],
    macd: macd.macd[i],
    macdSignal: macd.signal[i],
    macdHistPos: macd.histogram[i] != null && macd.histogram[i]! >= 0 ? macd.histogram[i] : null,
    macdHistNeg: macd.histogram[i] != null && macd.histogram[i]! < 0 ? macd.histogram[i] : null,
  }));
}

export default function Analytics() {
  const [symbol, setSymbol] = useState("");
  const [period, setPeriod] = useState<string>("1y");
  const [data, setData] = useState<PerformanceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSMA, setShowSMA] = useState(false);

  const chartData = useMemo(
    () => (data ? buildChartData(data.prices) : []),
    [data]
  );

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
            <div className="chart-header">
              <h2>{data.symbol} — Price ({data.period})</h2>
              <label className="sma-toggle">
                <input
                  type="checkbox"
                  checked={showSMA}
                  onChange={(e) => setShowSMA(e.target.checked)}
                />
                <span className="sma-toggle-slider" />
                <span className="sma-toggle-label">SMA 20 / 50 / 200</span>
              </label>
            </div>
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={chartData}>
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
                  formatter={(value: number, name: string) => {
                    const labels: Record<string, string> = {
                      close: "Close",
                      sma20: "SMA 20",
                      sma50: "SMA 50",
                      sma200: "SMA 200",
                    };
                    return [formatCurrency(value), labels[name] || name];
                  }}
                />
                {showSMA && <Legend />}
                <Area
                  type="monotone"
                  dataKey="close"
                  stroke="#646cff"
                  fill="url(#priceGradient)"
                  strokeWidth={2}
                  name="Close"
                />
                {showSMA && (
                  <Line
                    type="monotone"
                    dataKey="sma20"
                    stroke="#f5a623"
                    dot={false}
                    strokeWidth={1.5}
                    name="SMA 20"
                    connectNulls
                  />
                )}
                {showSMA && (
                  <Line
                    type="monotone"
                    dataKey="sma50"
                    stroke="#50c878"
                    dot={false}
                    strokeWidth={1.5}
                    name="SMA 50"
                    connectNulls
                  />
                )}
                {showSMA && (
                  <Line
                    type="monotone"
                    dataKey="sma200"
                    stroke="#e55353"
                    dot={false}
                    strokeWidth={1.5}
                    name="SMA 200"
                    connectNulls
                  />
                )}
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Volume Chart */}
          <div className="chart-container">
            <h2>Volume</h2>
            <ResponsiveContainer width="100%" height={150}>
              <BarChart data={chartData}>
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

          {/* RSI Chart */}
          <div className="chart-container">
            <h2>RSI (14)</h2>
            <ResponsiveContainer width="100%" height={220}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#888", fontSize: 12 }}
                  tickFormatter={(d: string) => d.slice(5)}
                />
                <YAxis
                  tick={{ fill: "#888", fontSize: 12 }}
                  domain={[0, 100]}
                  ticks={[0, 30, 50, 70, 100]}
                />
                <Tooltip
                  contentStyle={{ background: "#1a1a2e", border: "1px solid #333" }}
                  labelStyle={{ color: "#aaa" }}
                  formatter={(value: number) => [value.toFixed(2), "RSI"]}
                />
                <ReferenceLine y={70} stroke="#e55353" strokeDasharray="4 4" label={{ value: "70", fill: "#e55353", fontSize: 11, position: "right" }} />
                <ReferenceLine y={30} stroke="#50c878" strokeDasharray="4 4" label={{ value: "30", fill: "#50c878", fontSize: 11, position: "right" }} />
                <Line
                  type="monotone"
                  dataKey="rsi"
                  stroke="#c084fc"
                  dot={false}
                  strokeWidth={1.5}
                  connectNulls
                />
                <Brush
                  dataKey="date"
                  height={20}
                  stroke="#646cff"
                  fill="#1a1a2e"
                  tickFormatter={(d: string) => d.slice(5)}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* MACD Chart */}
          <div className="chart-container">
            <h2>MACD (12, 26, 9)</h2>
            <ResponsiveContainer width="100%" height={240}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#888", fontSize: 12 }}
                  tickFormatter={(d: string) => d.slice(5)}
                />
                <YAxis tick={{ fill: "#888", fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ background: "#1a1a2e", border: "1px solid #333" }}
                  labelStyle={{ color: "#aaa" }}
                  formatter={(value: number, name: string) => {
                    const labels: Record<string, string> = {
                      macd: "MACD",
                      macdSignal: "Signal",
                      macdHistPos: "Histogram",
                      macdHistNeg: "Histogram",
                    };
                    return [value.toFixed(4), labels[name] || name];
                  }}
                />
                <Legend payload={[
                  { value: "Histogram", type: "square", color: "#888" },
                  { value: "MACD", type: "line", color: "#646cff" },
                  { value: "Signal", type: "line", color: "#f5a623" },
                ]} />
                <ReferenceLine y={0} stroke="#555" />
                <Bar dataKey="macdHistPos" fill="#50c878" opacity={0.6} name="macdHistPos" legendType="none" stackId="hist" />
                <Bar dataKey="macdHistNeg" fill="#e55353" opacity={0.6} name="macdHistNeg" legendType="none" stackId="hist" />
                <Line
                  type="monotone"
                  dataKey="macd"
                  stroke="#646cff"
                  dot={false}
                  strokeWidth={1.5}
                  name="MACD"
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="macdSignal"
                  stroke="#f5a623"
                  dot={false}
                  strokeWidth={1.5}
                  name="Signal"
                  connectNulls
                />
                <Brush
                  dataKey="date"
                  height={20}
                  stroke="#646cff"
                  fill="#1a1a2e"
                  tickFormatter={(d: string) => d.slice(5)}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}
