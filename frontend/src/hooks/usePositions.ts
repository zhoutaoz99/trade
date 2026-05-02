import { useQuery } from '@tanstack/react-query';
import { getPositions } from '../api/futures';

export function usePositions(accountId: string | undefined, symbol?: string) {
  return useQuery({
    queryKey: symbol ? ['positions', accountId, symbol] : ['positions', accountId],
    queryFn: () => getPositions(accountId!, symbol),
    enabled: !!accountId,
    refetchInterval: 5_000,
    staleTime: 3_000,
  });
}
