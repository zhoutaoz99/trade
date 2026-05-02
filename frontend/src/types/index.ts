// ─── Enums ───

export type AccountType = 'simulated' | 'live';
export type OrderSide = 'BUY' | 'SELL';
export type OrderType = 'MARKET';
export type OrderStatus = 'NEW' | 'FILLED' | 'REJECTED' | 'EXPIRED';
export type MarginType = 'cross' | 'isolated';

// ─── Account ───

export interface Account {
  id: string;
  name: string;
  account_type: AccountType;
  quote_asset: string;
  initial_balance: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CreateAccountRequest {
  name: string;
  account_type: AccountType;
  quote_asset?: string;
  initial_balance?: string;
  api_key?: string;
  api_secret?: string;
}

// ─── Balance ───

export interface Balance {
  asset: string;
  wallet_balance: string;
  available_balance: string;
  margin_balance: string;
  unrealized_pnl: string;
}

// ─── Position ───

export interface Position {
  account_id: string;
  symbol: string;
  position_side: string;
  quantity: string;
  entry_price: string;
  breakeven_price: string;
  leverage: number;
  margin_type: MarginType;
  isolated_margin: string;
  unrealized_pnl: string;
  realized_pnl: string;
}

// ─── Order ───

export interface PlaceOrderRequest {
  account_id: string;
  client_order_id: string;
  symbol: string;
  side: OrderSide;
  order_type: OrderType;
  quantity: string;
  leverage?: number;
  reduce_only?: boolean;
}

export interface ClosePositionRequest {
  account_id: string;
  client_order_id: string;
  symbol: string;
  quantity: string;
}

export interface SetLeverageRequest {
  account_id: string;
  symbol: string;
  leverage: number;
}

export interface OrderResponse {
  account_id: string;
  account_type: string;
  client_order_id: string;
  exchange_order_id: string | null;
  symbol: string;
  side: string;
  order_type: string;
  status: string;
  executed_qty: string;
  avg_price: string;
  leverage: number | null;
  realized_pnl: string;
  fee_amount: string;
  reduce_only: boolean;
  created_at: string;
}

// ─── Account Summary ───

export interface AccountSummary {
  account_id: string;
  account_type: string;
  quote_asset: string;
  balances: Balance[];
  positions: Position[];
  total_unrealized_pnl: string;
  total_realized_pnl: string;
  total_pnl: string;
  daily_pnl: string;
  monthly_pnl: string;
  total_margin_used: string;
}

// ─── API Wrapper ───

export interface PositionsResponse {
  positions: Position[];
}

export interface ListOrdersParams {
  account_id: string;
  symbol?: string;
  limit?: number;
  offset?: number;
}
