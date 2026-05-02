import { useQuery } from '@tanstack/react-query';
import { getMarketPrice } from '../api/futures';

export function useMarketPrice(symbol: string | undefined) {
  return useQuery({
    queryKey: ['market-price', symbol],
    queryFn: () => getMarketPrice(symbol!),
    enabled: !!symbol,
    refetchInterval: 5_000,
    staleTime: 3_000,
  });
}
