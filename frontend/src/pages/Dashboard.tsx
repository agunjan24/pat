import { useEffect, useState } from "react";
import api from "../api/client";
import { Position } from "../types/portfolio";

export default function Dashboard() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Position[]>("/portfolio/positions")
      .then((res) => setPositions(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading portfolio...</p>;

  return (
    <div>
      <h1>Portfolio Dashboard</h1>
      {positions.length === 0 ? (
        <p>No positions yet. Add assets to get started.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Type</th>
              <th>Qty</th>
              <th>Avg Cost</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((p) => (
              <tr key={p.id}>
                <td>{p.asset.symbol}</td>
                <td>{p.asset.asset_type}</td>
                <td>{p.quantity}</td>
                <td>${p.avg_cost.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
