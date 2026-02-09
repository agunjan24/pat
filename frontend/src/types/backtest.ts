export interface DailySignal {
  date: string;
  composite_score: number;
  direction: string;
  conviction: string;
  confidence: number;
  forward_1d: number | null;
  forward_5d: number | null;
  forward_21d: number | null;
  signal_return_1d: number | null;
  signal_return_5d: number | null;
  signal_return_21d: number | null;
}

export interface HorizonMetrics {
  hit_rate: number;
  avg_signal_return: number;
  profit_factor: number | null;
  total_signals: number;
  wins: number;
  losses: number;
}

export interface ConvictionBreakdown {
  conviction: string;
  count: number;
  hit_rate_1d: number;
  hit_rate_5d: number;
  hit_rate_21d: number;
  avg_return_1d: number;
  avg_return_5d: number;
  avg_return_21d: number;
}

export interface EquityCurvePoint {
  date: string;
  cum_1d: number;
  cum_5d: number;
  cum_21d: number;
}

export interface BacktestResult {
  symbol: string;
  start_date: string;
  end_date: string;
  total_trading_days: number;
  horizon_1d: HorizonMetrics;
  horizon_5d: HorizonMetrics;
  horizon_21d: HorizonMetrics;
  conviction_breakdown: ConvictionBreakdown[];
  daily_signals: DailySignal[];
  equity_curve: EquityCurvePoint[];
  max_drawdown_1d: number;
  max_drawdown_5d: number;
  max_drawdown_21d: number;
}
