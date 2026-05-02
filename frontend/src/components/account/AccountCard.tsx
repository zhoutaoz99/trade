import { useNavigate } from 'react-router-dom';
import type { Account, AccountSummary } from '../../types';
import Badge from '../ui/Badge';

interface Props {
  account: Account;
  summary?: AccountSummary;
}

function fmtPnl(value: string): { text: string; cls: string } {
  const n = parseFloat(value);
  if (isNaN(n)) return { text: '$0.00', cls: '' };
  const prefix = n >= 0 ? '+' : '';
  return {
    text: `${prefix}$${n.toFixed(2)}`,
    cls: n > 0 ? 'text-[var(--color-green-text)]' : n < 0 ? 'text-[var(--color-red-text)]' : '',
  };
}

function PnlRow({ label, value }: { label: string; value: string }) {
  const { text, cls } = fmtPnl(value);
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-[var(--color-text-dim)]">{label}</span>
      <span className={`font-mono font-medium ${cls}`}>{text}</span>
    </div>
  );
}

export default function AccountCard({ account, summary }: Props) {
  const navigate = useNavigate();

  const hasPnl = summary !== undefined;

  return (
    <div
      onClick={() => navigate(`/accounts/${account.id}`)}
      className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 hover:border-blue-500/50 transition-colors cursor-pointer group"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[var(--color-text-heading)] font-semibold group-hover:text-[var(--color-blue-text)] transition-colors">
          {account.name}
        </h3>
        <Badge variant={account.account_type === 'live' ? 'green' : 'blue'}>
          {account.account_type}
        </Badge>
      </div>

      {hasPnl ? (
        <>
          <div className="flex items-baseline gap-1 mb-1">
            <span className={`text-2xl font-bold font-mono ${fmtPnl(summary.total_pnl).cls}`}>
              {fmtPnl(summary.total_pnl).text}
            </span>
            <span className="text-xs text-[var(--color-text-dim)]">total P&L</span>
          </div>
          <div className="space-y-0.5 mb-3">
            <PnlRow label="Today" value={summary.daily_pnl} />
            <PnlRow label="This month" value={summary.monthly_pnl} />
          </div>
        </>
      ) : (
        <div className="text-2xl font-bold text-[var(--color-text-heading)] font-mono mb-3">
          ${parseFloat(account.initial_balance).toLocaleString()}
        </div>
      )}

      <div className="text-xs text-[var(--color-text-dim)]">
        {account.quote_asset} · Created {new Date(account.created_at).toLocaleDateString()}
      </div>
    </div>
  );
}
