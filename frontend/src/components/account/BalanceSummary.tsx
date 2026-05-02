import type { Balance } from '../../types';
import { fmtMoney } from '../../utils/format';
import PriceLabel from '../ui/PriceLabel';

interface Props {
  balances: Balance[];
  totalUnrealizedPnl: string;
  totalRealizedPnl: string;
  totalPnl: string;
  dailyPnl: string;
  monthlyPnl: string;
  totalMarginUsed: string;
}

export default function BalanceSummary({
  balances,
  totalUnrealizedPnl,
  totalRealizedPnl,
  totalPnl,
  dailyPnl,
  monthlyPnl,
  totalMarginUsed,
}: Props) {
  const usdt = balances.find((b) => b.asset === 'USDT');

  if (!usdt) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatCard label="Wallet Balance" value={fmtMoney(usdt.wallet_balance)} />
      <StatCard label="Available" value={fmtMoney(usdt.available_balance)} />
      <StatCard label="Margin Used" value={fmtMoney(totalMarginUsed)} />
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4">
        <div className="text-xs text-[var(--color-text-dim)] mb-1">Total P&L</div>
        <PriceLabel value={totalPnl} className="text-xl font-bold" />
      </div>
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4">
        <div className="text-xs text-[var(--color-text-dim)] mb-1">Realized P&L</div>
        <PriceLabel value={totalRealizedPnl} className="text-xl font-bold" />
      </div>
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4">
        <div className="text-xs text-[var(--color-text-dim)] mb-1">Unrealized P&L</div>
        <PriceLabel value={totalUnrealizedPnl} className="text-xl font-bold" />
      </div>
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4">
        <div className="text-xs text-[var(--color-text-dim)] mb-1">Today's P&L</div>
        <PriceLabel value={dailyPnl} className="text-xl font-bold" />
      </div>
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4">
        <div className="text-xs text-[var(--color-text-dim)] mb-1">Monthly P&L</div>
        <PriceLabel value={monthlyPnl} className="text-xl font-bold" />
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4">
      <div className="text-xs text-[var(--color-text-dim)] mb-1">{label}</div>
      <div className="text-xl font-bold text-[var(--color-text-heading)] font-mono">{value}</div>
    </div>
  );
}
