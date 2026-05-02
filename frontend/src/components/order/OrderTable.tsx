import type { OrderResponse } from '../../types';
import Badge from '../ui/Badge';
import EmptyState from '../ui/EmptyState';

interface Props {
  orders: (OrderResponse & { id?: string })[];
  isLoading: boolean;
}

const statusVariant: Record<string, 'green' | 'red' | 'yellow' | 'gray'> = {
  FILLED: 'green',
  NEW: 'yellow',
  REJECTED: 'red',
  EXPIRED: 'gray',
};

export default function OrderTable({ orders, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="animate-pulse space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-12 bg-[var(--color-border)] rounded" />
        ))}
      </div>
    );
  }

  if (orders.length === 0) {
    return <EmptyState title="No orders yet" description="Orders will appear here after you place them" />;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[var(--color-border)] text-[var(--color-text-dim)] text-xs uppercase tracking-wider">
            <th className="text-left py-3 px-3">Time</th>
            <th className="text-left py-3 px-3">Order ID</th>
            <th className="text-left py-3 px-3">Symbol</th>
            <th className="text-left py-3 px-3">Side</th>
            <th className="text-right py-3 px-3">Qty</th>
            <th className="text-right py-3 px-3">Avg Price</th>
            <th className="text-center py-3 px-3">Status</th>
            <th className="text-right py-3 px-3">Fee</th>
            <th className="text-right py-3 px-3">PnL</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((o) => (
            <tr key={o.client_order_id} className="border-b border-[var(--color-border)] hover:bg-[var(--color-hover-row)] transition-colors">
              <td className="py-3 px-3 text-[var(--color-text-muted)] whitespace-nowrap">
                {new Date(o.created_at).toLocaleString()}
              </td>
              <td className="py-3 px-3 font-mono text-xs text-[var(--color-text-dim)] max-w-[120px] truncate" title={o.client_order_id}>
                {o.client_order_id}
              </td>
              <td className="py-3 px-3 text-[var(--color-text-heading)] font-medium">{o.symbol}</td>
              <td className="py-3 px-3">
                <Badge variant={o.side === 'BUY' ? 'green' : 'red'}>{o.side}</Badge>
              </td>
              <td className="py-3 px-3 text-right font-mono text-[var(--color-text-secondary)]">{parseFloat(o.executed_qty).toFixed(6)}</td>
              <td className="py-3 px-3 text-right font-mono text-[var(--color-text-secondary)]">${parseFloat(o.avg_price).toFixed(2)}</td>
              <td className="py-3 px-3 text-center">
                <Badge variant={statusVariant[o.status] || 'gray'}>{o.status}</Badge>
              </td>
              <td className="py-3 px-3 text-right font-mono text-[var(--color-text-muted)]">${parseFloat(o.fee_amount).toFixed(4)}</td>
              <td className={`py-3 px-3 text-right font-mono ${parseFloat(o.realized_pnl) >= 0 ? 'text-[var(--color-green-text)]' : 'text-[var(--color-red-text)]'}`}>
                ${parseFloat(o.realized_pnl).toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
