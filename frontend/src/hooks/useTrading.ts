import { useMutation, useQueryClient } from '@tanstack/react-query';
import { placeOrder, closePosition, setLeverage } from '../api/futures';
import { toast } from 'sonner';
import type { ClosePositionRequest, PlaceOrderRequest, SetLeverageRequest } from '../types';

export function usePlaceOrder(accountId: string) {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (data: PlaceOrderRequest) => placeOrder(data),
    onSuccess: (result) => {
      toast.success(`Order ${result.status}: ${result.side} ${result.executed_qty} ${result.symbol}`);
      qc.invalidateQueries({ queryKey: ['positions', accountId] });
      qc.invalidateQueries({ queryKey: ['account-summary', accountId] });
    },
  });
}

export function useClosePosition(accountId: string) {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (data: ClosePositionRequest) => closePosition(data),
    onSuccess: (result) => {
      toast.success(`Position closed: ${result.symbol} qty=${result.executed_qty}`);
      qc.invalidateQueries({ queryKey: ['positions', accountId] });
      qc.invalidateQueries({ queryKey: ['account-summary', accountId] });
    },
  });
}

export function useSetLeverage(accountId: string) {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (data: SetLeverageRequest) => setLeverage(data),
    onSuccess: (result) => {
      toast.success(`Leverage set: ${result.symbol} ${result.leverage}x`);
      qc.invalidateQueries({ queryKey: ['positions', accountId] });
    },
  });
}
