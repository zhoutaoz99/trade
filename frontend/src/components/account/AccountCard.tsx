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
      className="bg-[#1a1d2e] border border-[#2a2e3f] rounded-xl p-5 hover:border-blue-500/50 transition-colors cursor-pointer group"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-white font-semibold group-hover:text-blue-400 transition-colors">
          {account.name}
        </h3>
        <Badge variant={account.account_type === 'live' ? 'green' : 'blue'}>
          {account.account_type}
        </Badge>
      </div>
      <div className="text-2xl font-bold text-white font-mono">
        ${parseFloat(account.initial_balance).toLocaleString()}
      </div>
      <div className="text-xs text-gray-500 mt-2">
        {account.quote_asset} · Created {new Date(account.created_at).toLocaleDateString()}
      </div>
    </div>
  );
}
