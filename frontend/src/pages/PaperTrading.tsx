import { useEffect, useState } from "react";
import api from "../api/client";
import "./PaperTrading.css";

interface PaperTrade {
  id: number;
  symbol: string;
  direction: string;
  quantity: number;
  entry_price: number;
  exit_price: number | null;
  stop_loss: number | null;
  target_price: number | null;
  status: string;
  signal_score: number | null;
  pnl: number | null;
  pnl_pct: number | null;
  opened_at: string;
  closed_at: string | null;
}

interface PaperAccount {
  id: number;
  name: string;
  initial_cash: number;
  current_cash: number;
}

interface PaperSummary {
  account: PaperAccount;
  open_trades: PaperTrade[];
  closed_trades: PaperTrade[];
  total_pnl: number;
  win_rate: number;
  total_trades: number;
}

export default function PaperTrading() {
  const [summary, setSummary] = useState<PaperSummary | null>(null);
  const [symbol, setSymbol] = useState("");
  const [direction, setDirection] = useState("buy");
  const [quantity, setQuantity] = useState("");
  const [entryPrice, setEntryPrice] = useState("");
  const [stopLoss, setStopLoss] = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [closePrice, setClosePrice] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = () => {
    api
      .get<PaperSummary>("/paper/summary")
      .then((res) => setSummary(res.data))
      .catch(() => {});
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const openTrade = () => {
    if (!symbol.trim() || !quantity || !entryPrice) return;
    setLoading(true);
    setError(null);
    api
      .post("/paper/trades", {
        symbol: symbol.trim().toUpperCase(),
        direction,
        quantity: parseFloat(quantity),
        entry_price: parseFloat(entryPrice),
        stop_loss: stopLoss ? parseFloat(stopLoss) : null,
        target_price: targetPrice ? parseFloat(targetPrice) : null,
      })
      .then(() => {
        setSymbol("");
        setQuantity("");
        setEntryPrice("");
        setStopLoss("");
        setTargetPrice("");
        fetchSummary();
      })
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  };

  const closeTrade = (id: number) => {
    const price = closePrice[id];
    if (!price) return;
    setLoading(true);
    api
      .post(`/paper/trades/${id}/close`, { exit_price: parseFloat(price) })
      .then(() => {
        setClosePrice((prev) => {
          const next = { ...prev };
          delete next[id];
          return next;
        });
        fetchSummary();
      })
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  };

  const fmt = (n: number) => `$${n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  return (
    <div>
      <h1>Paper Trading</h1>

      {/* Account Summary */}
      {summary && (
        <div className="paper-stats">
          <div className="paper-stat">
            <span className="stat-label">Cash</span>
            <span className="stat-value">{fmt(summary.account.current_cash)}</span>
          </div>
          <div className="paper-stat">
            <span className="stat-label">Total P&L</span>
            <span className={`stat-value ${summary.total_pnl >= 0 ? "positive" : "negative"}`}>
              {fmt(summary.total_pnl)}
            </span>
          </div>
          <div className="paper-stat">
            <span className="stat-label">Win Rate</span>
            <span className="stat-value">{summary.win_rate.toFixed(1)}%</span>
          </div>
          <div className="paper-stat">
            <span className="stat-label">Closed Trades</span>
            <span className="stat-value">{summary.total_trades}</span>
          </div>
        </div>
      )}

      {/* Open Trade Form */}
      <div className="trade-form">
        <h2>Open Trade</h2>
        <div className="trade-form-row">
          <input
            type="text"
            placeholder="Symbol"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="trade-input"
          />
          <select
            value={direction}
            onChange={(e) => setDirection(e.target.value)}
            className="trade-select"
          >
            <option value="buy">Buy</option>
            <option value="sell">Sell (Short)</option>
          </select>
          <input
            type="number"
            placeholder="Qty"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            className="trade-input trade-input-sm"
          />
          <input
            type="number"
            placeholder="Entry $"
            value={entryPrice}
            onChange={(e) => setEntryPrice(e.target.value)}
            className="trade-input trade-input-sm"
          />
          <input
            type="number"
            placeholder="Stop $"
            value={stopLoss}
            onChange={(e) => setStopLoss(e.target.value)}
            className="trade-input trade-input-sm"
          />
          <input
            type="number"
            placeholder="Target $"
            value={targetPrice}
            onChange={(e) => setTargetPrice(e.target.value)}
            className="trade-input trade-input-sm"
          />
          <button onClick={openTrade} disabled={loading} className="trade-btn">
            Open
          </button>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      {/* Open Trades */}
      {summary && summary.open_trades.length > 0 && (
        <div className="trades-section">
          <h2>Open Positions</h2>
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Dir</th>
                <th>Qty</th>
                <th>Entry</th>
                <th>Stop</th>
                <th>Target</th>
                <th>Close At</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {summary.open_trades.map((t) => (
                <tr key={t.id}>
                  <td className="symbol">{t.symbol}</td>
                  <td className={t.direction === "buy" ? "positive" : "negative"}>
                    {t.direction.toUpperCase()}
                  </td>
                  <td>{t.quantity}</td>
                  <td>{fmt(t.entry_price)}</td>
                  <td>{t.stop_loss != null ? fmt(t.stop_loss) : "—"}</td>
                  <td>{t.target_price != null ? fmt(t.target_price) : "—"}</td>
                  <td>
                    <input
                      type="number"
                      placeholder="Exit $"
                      value={closePrice[t.id] || ""}
                      onChange={(e) =>
                        setClosePrice((prev) => ({ ...prev, [t.id]: e.target.value }))
                      }
                      className="trade-input trade-input-sm"
                    />
                  </td>
                  <td>
                    <button
                      onClick={() => closeTrade(t.id)}
                      disabled={!closePrice[t.id]}
                      className="close-btn"
                    >
                      Close
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Closed Trades */}
      {summary && summary.closed_trades.length > 0 && (
        <div className="trades-section">
          <h2>Trade History</h2>
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Dir</th>
                <th>Qty</th>
                <th>Entry</th>
                <th>Exit</th>
                <th>P&L</th>
                <th>P&L %</th>
              </tr>
            </thead>
            <tbody>
              {summary.closed_trades.map((t) => (
                <tr key={t.id}>
                  <td className="symbol">{t.symbol}</td>
                  <td className={t.direction === "buy" ? "positive" : "negative"}>
                    {t.direction.toUpperCase()}
                  </td>
                  <td>{t.quantity}</td>
                  <td>{fmt(t.entry_price)}</td>
                  <td>{t.exit_price != null ? fmt(t.exit_price) : "—"}</td>
                  <td className={t.pnl != null && t.pnl >= 0 ? "positive" : "negative"}>
                    {t.pnl != null ? fmt(t.pnl) : "—"}
                  </td>
                  <td className={t.pnl_pct != null && t.pnl_pct >= 0 ? "positive" : "negative"}>
                    {t.pnl_pct != null ? `${t.pnl_pct.toFixed(2)}%` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {summary && summary.open_trades.length === 0 && summary.closed_trades.length === 0 && (
        <p className="no-data">No trades yet. Open a paper trade above.</p>
      )}
    </div>
  );
}
