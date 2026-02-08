export interface WavePivot {
  index: number;
  date: string;
  price: number;
  type: "high" | "low";
  wave_label: string;
}

export interface FibLevel {
  level: number;
  ratio: string;
  label: string;
}

export interface WaveAnalysis {
  pattern: string;
  current_wave: string;
  confidence: number;
  wave_pivots: WavePivot[];
  fib_levels: FibLevel[];
}

export interface IndividualSignal {
  name: string;
  score: number;
  description: string;
}

export interface RiskContext {
  stop_loss: number | null;
  target_price: number | null;
  risk_reward: number | null;
  position_size: number;
  position_pct: number;
}

export interface ElliottWaveResult {
  symbol: string;
  current_price: number;
  wave_analysis: WaveAnalysis;
  signals: IndividualSignal[];
  direction: "buy" | "sell" | "hold";
  conviction: "low" | "medium" | "high";
  risk: RiskContext;
}
