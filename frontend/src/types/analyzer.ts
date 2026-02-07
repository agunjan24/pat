export interface PositionSummary {
  position_id: number;
  symbol: string;
  asset_type: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
  market_value: number;
  cost_basis: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
}

export interface AllocationItem {
  symbol: string;
  asset_type: string;
  market_value: number;
  weight: number;
}

export interface PortfolioSummary {
  total_market_value: number;
  total_cost_basis: number;
  total_unrealized_pnl: number;
  total_unrealized_pnl_pct: number;
  position_count: number;
  positions: PositionSummary[];
  allocation: AllocationItem[];
}

export interface PricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface RiskMetrics {
  symbol: string;
  period: string;
  sharpe_ratio: number;
  max_drawdown: number;
  cagr: number;
  volatility: number;
}

export interface PerformanceResponse {
  symbol: string;
  period: string;
  prices: PricePoint[];
  metrics: RiskMetrics;
}
