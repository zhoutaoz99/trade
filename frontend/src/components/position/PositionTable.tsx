import type { Position } from '../../types';
import PositionRow from './PositionRow';
import EmptyState from '../ui/EmptyState';
import { TableSkeleton } from '../ui/LoadingSkeleton';

interface Props {
  positions: Position[];
  isLoading: boolean;
  onClosePosition: (symbol: string, qty: string) => void;
  closingSymbol?: string;
}

export default function PositionTable({ positions, isLoading, onClosePosition, closingSymbol }: Props) {
  if (isLoading) return <TableSkeleton rows={3} cols={7} />;

  const openPositions = positions.filter((p) => parseFloat(p.quantity) !== 0);

  if (openPositions.length === 0) {
    return <EmptyState title="No open positions" description="Place an order to open a position" />;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[var(--color-border)] text-[var(--color-text-dim)] text-xs uppercase tracking-wider">
            <th className="text-left py-3 px-3">Symbol</th>
            <th className="text-right py-3 px-3">Side</th>
            <th className="text-right py-3 px-3">Quantity</th>
            <th className="text-right py-3 px-3">Entry Price</th>
            <th className="text-right py-3 px-3">Mark Price</th>
            <th className="text-right py-3 px-3">PnL (USDT)</th>
            <th className="text-right py-3 px-3">Leverage</th>
            <th className="text-right py-3 px-3">Action</th>
          </tr>
        </thead>
        <tbody>
          {openPositions.map((p) => (
            <PositionRow
              key={p.symbol}
              position={p}
              onClose={onClosePosition}
              isClosing={closingSymbol === p.symbol}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
