import { NavLink, useParams } from 'react-router-dom';
import { LayoutDashboard, CandlestickChart, ScrollText, Plus, Sun, Moon } from 'lucide-react';
import { useState } from 'react';
import { useAccountList } from '../../hooks/useAccounts';
import { useTheme } from '../../context/ThemeContext';
import CreateAccountModal from '../account/CreateAccountModal';

export default function Sidebar() {
  const { accountId } = useParams();
  const { data: accounts } = useAccountList();
  const [showCreate, setShowCreate] = useState(false);
  const { theme, toggleTheme } = useTheme();

  const navItems = accountId
    ? [
        { to: `/accounts/${accountId}`, icon: LayoutDashboard, label: 'Overview' },
        { to: `/accounts/${accountId}/trade`, icon: CandlestickChart, label: 'Trade' },
        { to: `/accounts/${accountId}/orders`, icon: ScrollText, label: 'Orders' },
      ]
    : [];

  return (
    <aside className="w-64 bg-[var(--color-sidebar)] border-r border-[var(--color-border)] flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-[var(--color-border)]">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-[var(--color-text-heading)] tracking-tight">UM Futures</h1>
            <p className="text-xs text-[var(--color-text-dim)] mt-0.5">Sim Trading System</p>
          </div>
          <button
            onClick={toggleTheme}
            className="text-[var(--color-text-dim)] hover:text-[var(--color-text-heading)] transition-colors cursor-pointer"
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </div>

      {/* Account selector */}
      <div className="px-3 py-3 border-b border-[var(--color-border)]">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-[var(--color-text-dim)] font-medium uppercase tracking-wider">Accounts</span>
          <button
            onClick={() => setShowCreate(true)}
            className="text-[var(--color-text-dim)] hover:text-[var(--color-text-heading)] transition-colors cursor-pointer"
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
                  ? 'bg-[var(--color-blue-bg)] text-[var(--color-blue-text)] font-medium'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-heading)] hover:bg-[var(--color-hover-item)]'
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
          <p className="text-xs text-[var(--color-text-subtle)] px-3 py-2">No accounts yet</p>
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
                    ? 'bg-[var(--color-active-item)] text-[var(--color-text-heading)] font-medium'
                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-heading)] hover:bg-[var(--color-hover-item)]'
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
