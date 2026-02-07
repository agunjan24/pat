export interface SignalDetail {
  name: string;
  score: number;
  weight: number;
  description: string;
}

export interface RiskContext {
  stop_loss: number | null;
  target_price: number | null;
  risk_reward: number | null;
  position_size: number;
  position_pct: number;
}

export interface ScanResult {
  symbol: string;
  current_price: number;
  direction: "buy" | "sell" | "hold";
  conviction: "low" | "medium" | "high";
  composite_score: number;
  confidence: number;
  signals: SignalDetail[];
  risk: RiskContext;
}
