import { useEffect, useState } from "react";
import api from "../api/client";
import "./Alerts.css";

interface Alert {
  id: number;
  symbol: string;
  alert_type: string;
  threshold: number | null;
  message: string | null;
  is_active: boolean;
  is_triggered: boolean;
  triggered_at: string | null;
  created_at: string;
}

interface CheckResult {
  alert_id: number;
  symbol: string;
  alert_type: string;
  triggered: boolean;
  current_value: number | null;
  message: string | null;
}

const ALERT_TYPES = [
  { value: "price_above", label: "Price Above" },
  { value: "price_below", label: "Price Below" },
  { value: "iv_rank_above", label: "IV Rank Above" },
  { value: "iv_rank_below", label: "IV Rank Below" },
  { value: "signal_buy", label: "Signal Buy" },
  { value: "signal_sell", label: "Signal Sell" },
];

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [checkResults, setCheckResults] = useState<CheckResult[]>([]);
  const [symbol, setSymbol] = useState("");
  const [alertType, setAlertType] = useState("price_above");
  const [threshold, setThreshold] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = () => {
    api
      .get<Alert[]>("/alerts", { params: { active_only: false } })
      .then((res) => setAlerts(res.data))
      .catch(() => {});
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const createAlert = () => {
    if (!symbol.trim()) return;
    setLoading(true);
    setError(null);
    api
      .post("/alerts", {
        symbol: symbol.trim().toUpperCase(),
        alert_type: alertType,
        threshold: threshold ? parseFloat(threshold) : null,
        message: message || null,
      })
      .then(() => {
        setSymbol("");
        setThreshold("");
        setMessage("");
        fetchAlerts();
      })
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  };

  const deleteAlert = (id: number) => {
    api.delete(`/alerts/${id}`).then(() => fetchAlerts());
  };

  const checkAll = () => {
    setLoading(true);
    api
      .post<CheckResult[]>("/alerts/check")
      .then((res) => {
        setCheckResults(res.data);
        fetchAlerts();
      })
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  };

  return (
    <div>
      <h1>Alerts</h1>

      {/* Create Form */}
      <div className="alert-form">
        <input
          type="text"
          placeholder="Symbol"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          className="alert-input"
        />
        <select
          value={alertType}
          onChange={(e) => setAlertType(e.target.value)}
          className="alert-select"
        >
          {ALERT_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
        <input
          type="number"
          placeholder="Threshold"
          value={threshold}
          onChange={(e) => setThreshold(e.target.value)}
          className="alert-input alert-input-sm"
        />
        <input
          type="text"
          placeholder="Note (optional)"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="alert-input"
        />
        <button onClick={createAlert} disabled={loading} className="alert-btn">
          Add Alert
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="alert-actions">
        <button onClick={checkAll} disabled={loading} className="alert-btn check-btn">
          {loading ? "Checking..." : "Check All Alerts"}
        </button>
      </div>

      {/* Check Results */}
      {checkResults.length > 0 && (
        <div className="check-results">
          <h2>Check Results</h2>
          {checkResults.map((r) => (
            <div key={r.alert_id} className={`check-item ${r.triggered ? "triggered" : ""}`}>
              <span className="check-sym">{r.symbol}</span>
              <span className="check-type">{r.alert_type.replace("_", " ")}</span>
              {r.current_value != null && (
                <span className="check-val">Current: ${r.current_value.toFixed(2)}</span>
              )}
              <span className={`check-status ${r.triggered ? "status-triggered" : "status-ok"}`}>
                {r.triggered ? "TRIGGERED" : "OK"}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Alerts List */}
      {alerts.length > 0 && (
        <table className="alerts-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Type</th>
              <th>Threshold</th>
              <th>Note</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr key={a.id} className={a.is_triggered ? "row-triggered" : ""}>
                <td className="symbol">{a.symbol}</td>
                <td>{a.alert_type.replace("_", " ")}</td>
                <td>{a.threshold != null ? a.threshold : "—"}</td>
                <td className="note-col">{a.message || "—"}</td>
                <td>
                  {a.is_triggered ? (
                    <span className="badge badge-triggered">Triggered</span>
                  ) : a.is_active ? (
                    <span className="badge badge-active">Active</span>
                  ) : (
                    <span className="badge badge-inactive">Inactive</span>
                  )}
                </td>
                <td>
                  <button onClick={() => deleteAlert(a.id)} className="del-btn">
                    &times;
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {alerts.length === 0 && <p className="no-data">No alerts yet. Create one above.</p>}
    </div>
  );
}
