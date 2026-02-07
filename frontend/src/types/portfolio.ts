export type AssetType = "stock" | "option" | "leap";
export type TransactionType = "buy" | "sell";

export interface Asset {
  id: number;
  symbol: string;
  name: string | null;
  asset_type: AssetType;
  strike: number | null;
  expiration: string | null;
  option_type: string | null;
}

export interface Position {
  id: number;
  asset: Asset;
  quantity: number;
  avg_cost: number;
  opened_at: string;
}

export interface Transaction {
  id: number;
  position_id: number;
  transaction_type: TransactionType;
  quantity: number;
  price: number;
  timestamp: string;
}
