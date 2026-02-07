import { useState } from "react";
import api from "../api/client";
import "./Import.css";

interface ImportResult {
  imported: number;
  skipped: number;
  errors: string[];
  positions_created: { symbol: string; asset_type: string; quantity: number; price: number }[];
}

export default function Import() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setError(null);
    api
      .post<ImportResult>("/portfolio/import", formData)
      .then((res) => setResult(res.data))
      .catch((err) => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  };

  return (
    <div>
      <h1>Import Portfolio</h1>
      <p className="import-desc">
        Upload a CSV file with columns: <code>symbol, quantity, price</code>.
        Optional: <code>asset_type, date, option_type, strike, expiration</code>.
      </p>

      <div className="import-controls">
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="file-input"
        />
        <button onClick={handleUpload} disabled={!file || loading} className="import-btn">
          {loading ? "Importing..." : "Import"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className="import-result">
          <div className="import-stats">
            <span className="stat-ok">{result.imported} imported</span>
            {result.skipped > 0 && <span className="stat-skip">{result.skipped} skipped</span>}
          </div>

          {result.errors.length > 0 && (
            <div className="import-errors">
              <h3>Warnings</h3>
              <ul>
                {result.errors.map((e, i) => (
                  <li key={i}>{e}</li>
                ))}
              </ul>
            </div>
          )}

          {result.positions_created.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Type</th>
                  <th>Qty</th>
                  <th>Price</th>
                </tr>
              </thead>
              <tbody>
                {result.positions_created.map((p, i) => (
                  <tr key={i}>
                    <td className="symbol">{p.symbol}</td>
                    <td>{p.asset_type}</td>
                    <td>{p.quantity}</td>
                    <td>${p.price.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
