export interface IVMetrics {
  current_iv: number;
  iv_rank: number;
  iv_percentile: number;
  iv_high: number;
  iv_low: number;
}

export interface SkewPoint {
  strike: number;
  call_iv: number | null;
  put_iv: number | null;
}

export interface Skew {
  skew_ratio: number;
  points: SkewPoint[];
}

export interface TermStructurePoint {
  expiration: string;
  days_to_expiry: number;
  atm_iv: number;
}

export interface OptionsAnalysis {
  symbol: string;
  spot_price: number;
  expirations: string[];
  iv_metrics: IVMetrics;
  skew: Skew;
  term_structure: TermStructurePoint[];
}

export interface ThetaEfficiency {
  delta_per_dollar: number;
  theta_per_delta: number;
}

export interface LeapsCandidate {
  strike: number;
  expiration: string;
  option_type: string;
  days_to_expiry: number;
  market_price: number;
  delta: number;
  theta: number;
  vega: number;
  iv: number;
  intrinsic: number;
  extrinsic: number;
  extrinsic_pct: number;
  theta_efficiency: ThetaEfficiency;
  stock_replacement_cost: number;
  roll_recommendation: string;
}

export interface LeapsAnalysis {
  symbol: string;
  spot_price: number;
  leaps_expirations: string[];
  candidates: LeapsCandidate[];
}
