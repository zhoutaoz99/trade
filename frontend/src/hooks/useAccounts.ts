import { useQuery, useMutation } from '@tanstack/react-query';
import { getAccount, createAccount } from '../api/accounts';
import { getAccountSummary } from '../api/futures';
import type { CreateAccountRequest } from '../types';

const STORAGE_KEY = 'trade_account_ids';

function getStoredAccountIds(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function addStoredAccountId(id: string) {
  const ids = getStoredAccountIds();
  if (!ids.includes(id)) {
    ids.push(id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
  }
}

export function useAccountList() {
  const ids = getStoredAccountIds();

  return useQuery({
    queryKey: ['accounts'],
    queryFn: async () => {
      if (ids.length === 0) return [];
      const results = await Promise.allSettled(ids.map((id) => getAccount(id)));
      return results
        .filter((r): r is PromiseFulfilledResult<Awaited<ReturnType<typeof getAccount>>> => r.status === 'fulfilled')
        .map((r) => r.value);
    },
    staleTime: 10_000,
  });
}

export function useAccount(id: string | undefined) {
  return useQuery({
    queryKey: ['account', id],
    queryFn: () => getAccount(id!),
    enabled: !!id,
    staleTime: 10_000,
  });
}

export function useAccountSummary(accountId: string | undefined) {
  return useQuery({
    queryKey: ['account-summary', accountId],
    queryFn: () => getAccountSummary(accountId!),
    enabled: !!accountId,
    refetchInterval: 5_000,
    staleTime: 3_000,
  });
}

export function useCreateAccount() {
  return useMutation({
    mutationFn: (data: CreateAccountRequest) => createAccount(data),
  });
}

export function useAccountSummaries(accountIds: string[]) {
  return useQuery({
    queryKey: ['account-summaries', accountIds],
    queryFn: async () => {
      if (accountIds.length === 0) return {};
      const results = await Promise.allSettled(
        accountIds.map((id) => getAccountSummary(id))
      );
      const map: Record<string, import('../types').AccountSummary> = {};
      results.forEach((r, i) => {
        if (r.status === 'fulfilled') {
          map[accountIds[i]] = r.value;
        }
      });
      return map;
    },
    enabled: accountIds.length > 0,
    refetchInterval: 10_000,
    staleTime: 5_000,
  });
}
