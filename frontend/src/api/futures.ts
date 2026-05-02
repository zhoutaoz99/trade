import apiClient from './client';
import type {
  AccountSummary,
  ClosePositionRequest,
  OrderResponse,
  PlaceOrderRequest,
  PositionsResponse,
  SetLeverageRequest,
} from '../types';

export const getAccountSummary = async (accountId: string): Promise<AccountSummary> => {
  const res = await apiClient.get('/api/v1/futures/account', {
    params: { account_id: accountId },
  });
  return res.data;
};

export const getPositions = async (
  accountId: string,
  symbol?: string,
): Promise<PositionsResponse> => {
  const res = await apiClient.get('/api/v1/futures/positions', {
    params: { account_id: accountId, ...(symbol ? { symbol } : {}) },
  });
  return res.data;
};

export const placeOrder = async (data: PlaceOrderRequest): Promise<OrderResponse> => {
  const res = await apiClient.post('/api/v1/futures/orders', data);
  return res.data;
};

export const closePosition = async (data: ClosePositionRequest): Promise<OrderResponse> => {
  const res = await apiClient.post('/api/v1/futures/close-position', data);
  return res.data;
};

export const setLeverage = async (data: SetLeverageRequest): Promise<{ account_id: string; symbol: string; leverage: number }> => {
  const res = await apiClient.post('/api/v1/futures/leverage', data);
  return res.data;
};

export const getOrder = async (
  accountId: string,
  clientOrderId: string,
): Promise<OrderResponse> => {
  const res = await apiClient.get(`/api/v1/futures/orders/${clientOrderId}`, {
    params: { account_id: accountId },
  });
  return res.data;
};
