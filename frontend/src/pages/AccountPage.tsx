import { useParams } from 'react-router-dom';
import { useAccount, useAccountSummary } from '../hooks/useAccounts';
import { useClosePosition } from '../hooks/useTrading';
import BalanceSummary from '../components/account/BalanceSummary';
import PositionTable from '../components/position/PositionTable';
import { generateClientOrderId } from '../utils/clientOrderId';
import { CardSkeleton } from '../components/ui/LoadingSkeleton';

export default function AccountPage() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: account, isLoading: accLoading } = useAccount(accountId);
  const { data: summary, isLoading: sumLoading } = useAccountSummary(accountId);
  const closePos = useClosePosition(accountId || '');

  const handleClosePosition = (symbol: string, qty: string) => {
    if (!accountId) return;
    const absQty = Math.abs(parseFloat(qty));
    closePos.mutate({
      account_id: accountId,
      client_order_id: generateClientOrderId(symbol),
      symbol,
      quantity: String(absQty),
    });
  };

  if (accLoading) {
    return (
      <div className="space-y-4">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  if (!account) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-semibold text-[var(--color-text-heading)]">Account not found</h2>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-heading)]">{account.name}</h1>
          <p className="text-sm text-[var(--color-text-dim)]">
            {account.account_type === 'simulated' ? '📝 Simulated' : '🔴 Live'} ·{' '}
            {account.quote_asset} · Created {new Date(account.created_at).toLocaleDateString()}
          </p>
        </div>
        <div className="text-right">
          <div className="text-xs text-[var(--color-text-dim)]">Account ID</div>
          <div className="text-sm font-mono text-[var(--color-text-muted)]">{account.id.substring(0, 8)}...</div>
        </div>
      </div>

      <div className="mb-6">
        {sumLoading ? (
          <CardSkeleton />
        ) : summary ? (
          <BalanceSummary
            balances={summary.balances}
            totalUnrealizedPnl={summary.total_unrealized_pnl}
            totalMarginUsed={summary.total_margin_used}
          />
        ) : null}
      </div>

      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
        <h2 className="text-lg font-semibold text-[var(--color-text-heading)] mb-4">Positions</h2>
        <PositionTable
          positions={summary?.positions || []}
          isLoading={sumLoading}
          onClosePosition={handleClosePosition}
          closingSymbol={closePos.isPending ? undefined : undefined}
        />
      </div>
    </div>
  );
}
