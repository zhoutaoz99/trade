import { useNavigate } from 'react-router-dom';
import type { Account } from '../../types';
import Badge from '../ui/Badge';

interface Props {
  account: Account;
}

export default function AccountCard({ account }: Props) {
  const navigate = useNavigate();

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
      <div className="text-2xl font-bold text-[var(--color-text-heading)] font-mono">
        ${parseFloat(account.initial_balance).toLocaleString()}
      </div>
      <div className="text-xs text-[var(--color-text-dim)] mt-2">
        {account.quote_asset} · Created {new Date(account.created_at).toLocaleDateString()}
      </div>
    </div>
  );
}
