import { useState } from 'react';
import { Plus } from 'lucide-react';
import { useAccountList, useAccountSummaries } from '../hooks/useAccounts';
import AccountCard from '../components/account/AccountCard';
import CreateAccountModal from '../components/account/CreateAccountModal';
import { CardSkeleton } from '../components/ui/LoadingSkeleton';

export default function DashboardPage() {
  const { data: accounts, isLoading } = useAccountList();
  const [showCreate, setShowCreate] = useState(false);

  const accountIds = accounts?.map((a) => a.id) ?? [];
  const { data: summaries } = useAccountSummaries(accountIds);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-heading)]">Accounts</h1>
          <p className="text-sm text-[var(--color-text-dim)] mt-1">Manage your simulated and live trading accounts</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors cursor-pointer"
        >
          <Plus size={18} />
          Create Account
        </button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : accounts && accounts.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {accounts.map((a) => (
            <AccountCard key={a.id} account={a} summary={summaries?.[a.id]} />
          ))}
        </div>
      ) : (
        <div className="text-center py-20">
          <div className="text-6xl mb-4">📊</div>
          <h2 className="text-xl font-semibold text-[var(--color-text-heading)] mb-2">Welcome to UM Futures Sim Trading</h2>
          <p className="text-[var(--color-text-dim)] mb-6 max-w-md mx-auto">
            Create your first account to start trading. Simulated accounts use virtual funds,
            live accounts connect to Binance via API keys.
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold transition-colors cursor-pointer"
          >
            <Plus size={20} />
            Create Your First Account
          </button>
        </div>
      )}

      <CreateAccountModal open={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  );
}
