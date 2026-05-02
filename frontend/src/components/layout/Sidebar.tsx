import { NavLink, useParams } from 'react-router-dom';
import { LayoutDashboard, CandlestickChart, ScrollText, Plus } from 'lucide-react';
import { useState } from 'react';
import { useAccountList } from '../../hooks/useAccounts';
import CreateAccountModal from '../account/CreateAccountModal';

export default function Sidebar() {
  const { accountId } = useParams();
  const { data: accounts } = useAccountList();
  const [showCreate, setShowCreate] = useState(false);

  const navItems = accountId
    ? [
        { to: `/accounts/${accountId}`, icon: LayoutDashboard, label: 'Overview' },
        { to: `/accounts/${accountId}/trade`, icon: CandlestickChart, label: 'Trade' },
        { to: `/accounts/${accountId}/orders`, icon: ScrollText, label: 'Orders' },
      ]
    : [];

  return (
    <aside className="w-64 bg-[#12141d] border-r border-[#2a2e3f] flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-[#2a2e3f]">
        <h1 className="text-lg font-bold text-white tracking-tight">UM Futures</h1>
        <p className="text-xs text-gray-500 mt-0.5">Sim Trading System</p>
      </div>

      {/* Account selector */}
      <div className="px-3 py-3 border-b border-[#2a2e3f]">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">Accounts</span>
          <button
            onClick={() => setShowCreate(true)}
            className="text-gray-500 hover:text-white transition-colors cursor-pointer"
            title="Create Account"
          >
            <Plus size={16} />
          </button>
        </div>
        {accounts?.map((a) => (
          <NavLink
            key={a.id}
            to={`/accounts/${a.id}`}
            className={({ isActive }) =>
              `block px-3 py-2 rounded-lg text-sm mb-1 transition-colors ${
                isActive
                  ? 'bg-blue-600/20 text-blue-400 font-medium'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`
            }
          >
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${a.account_type === 'live' ? 'bg-green-500' : 'bg-blue-500'}`}
              />
              <span className="truncate">{a.name}</span>
            </div>
          </NavLink>
        ))}
        {(!accounts || accounts.length === 0) && (
          <p className="text-xs text-gray-600 px-3 py-2">No accounts yet</p>
        )}
      </div>

      {/* Navigation */}
      {accountId && (
        <nav className="flex-1 px-3 py-4">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={label === 'Overview'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm mb-1 transition-colors ${
                  isActive
                    ? 'bg-white/10 text-white font-medium'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
      )}

      {/* Create Account Modal */}
      <CreateAccountModal open={showCreate} onClose={() => setShowCreate(false)} />
    </aside>
  );
}
