import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getOrders, placeOrder, closePosition, setLeverage } from '../api/futures';
import { toast } from 'sonner';
import type { ClosePositionRequest, PlaceOrderRequest, SetLeverageRequest } from '../types';

export function usePlaceOrder(accountId: string) {
  const qc = useQueryClient();
  const mutation = useMutation({
    mutationFn: (data: PlaceOrderRequest) => placeOrder(data),
  });

  return {
    ...mutation,
    mutate: (data: PlaceOrderRequest) =>
      mutation.mutate(data, {
        onSuccess: (result) => {
          toast.success(`Order ${result.status}: ${result.side} ${result.executed_qty} ${result.symbol}`);
          qc.invalidateQueries({ queryKey: ['positions', accountId] });
          qc.invalidateQueries({ queryKey: ['account-summary', accountId] });
          qc.invalidateQueries({ queryKey: ['orders', accountId] });
        },
      }),
  };
}

export function useClosePosition(accountId: string) {
  const qc = useQueryClient();
  const mutation = useMutation({
    mutationFn: (data: ClosePositionRequest) => closePosition(data),
  });

  return {
    ...mutation,
    mutate: (data: ClosePositionRequest) =>
      mutation.mutate(data, {
        onSuccess: (result) => {
          toast.success(`Position closed: ${result.symbol} qty=${result.executed_qty}`);
          qc.invalidateQueries({ queryKey: ['positions', accountId] });
          qc.invalidateQueries({ queryKey: ['account-summary', accountId] });
        },
      }),
  };
}

export function useSetLeverage(accountId: string) {
  const qc = useQueryClient();
  const mutation = useMutation({
    mutationFn: (data: SetLeverageRequest) => setLeverage(data),
  });

  return {
    ...mutation,
    mutate: (data: SetLeverageRequest) =>
      mutation.mutate(data, {
        onSuccess: (result) => {
          toast.success(`Leverage set: ${result.symbol} ${result.leverage}x`);
          qc.invalidateQueries({ queryKey: ['positions', accountId] });
        },
      }),
  };
}

export function useOrders(accountId: string | undefined, symbol?: string) {
  return useQuery({
    queryKey: ['orders', accountId, symbol],
    queryFn: () => getOrders({ account_id: accountId!, symbol }),
    enabled: !!accountId,
    refetchInterval: 5_000,
  });
}
