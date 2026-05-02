import type { Balance } from '../../types';
import { fmtMoney } from '../../utils/format';
import PriceLabel from '../ui/PriceLabel';

interface Props {
  balances: Balance[];
  totalUnrealizedPnl: string;
  totalMarginUsed: string;
}

export default function BalanceSummary({ balances, totalUnrealizedPnl, totalMarginUsed }: Props) {
  const usdt = balances.find((b) => b.asset === 'USDT');

  if (!usdt) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatCard label="Wallet Balance" value={fmtMoney(usdt.wallet_balance)} />
      <StatCard label="Available" value={fmtMoney(usdt.available_balance)} />
      <StatCard label="Margin Used" value={fmtMoney(totalMarginUsed)} />
      <div className="bg-[#1a1d2e] border border-[#2a2e3f] rounded-xl p-4">
        <div className="text-xs text-gray-500 mb-1">Unrealized PnL</div>
        <PriceLabel value={totalUnrealizedPnl} className="text-xl font-bold" />
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-[#1a1d2e] border border-[#2a2e3f] rounded-xl p-4">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className="text-xl font-bold text-white font-mono">{value}</div>
    </div>
  );
}
