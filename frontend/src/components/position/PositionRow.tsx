import type { Position } from '../../types';
import { fmtCrypto, fmtMoney } from '../../utils/format';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import PriceLabel from '../ui/PriceLabel';

interface Props {
  position: Position;
  onClose: (symbol: string, qty: string) => void;
  isClosing: boolean;
}

export default function PositionRow({ position: p, onClose, isClosing }: Props) {
  const qty = parseFloat(p.quantity);
  const isLong = qty > 0;
  const markPrice = parseFloat(p.entry_price);
  const pnl = parseFloat(p.unrealized_pnl);

  return (
    <tr className="border-b border-[var(--color-border)] hover:bg-[var(--color-hover-row)] transition-colors">
      <td className="py-3 px-3">
        <span className="text-[var(--color-text-heading)] font-medium">{p.symbol}</span>
      </td>
      <td className="py-3 px-3 text-right">
        <Badge variant={isLong ? 'green' : 'red'}>
          {isLong ? 'LONG' : 'SHORT'}
        </Badge>
      </td>
      <td className="py-3 px-3 text-right font-mono text-[var(--color-text-heading)]">{fmtCrypto(Math.abs(qty))}</td>
      <td className="py-3 px-3 text-right font-mono text-[var(--color-text-secondary)]">{fmtMoney(p.entry_price)}</td>
      <td className="py-3 px-3 text-right font-mono text-[var(--color-text-secondary)]">{fmtMoney(markPrice)}</td>
      <td className="py-3 px-3 text-right font-mono">
        <PriceLabel value={pnl} />
      </td>
      <td className="py-3 px-3 text-right font-mono text-[var(--color-text-secondary)]">{p.leverage}x</td>
      <td className="py-3 px-3 text-right">
        <Button
          variant="danger"
          size="sm"
          onClick={() => onClose(p.symbol, p.quantity)}
          loading={isClosing}
        >
          Close
        </Button>
      </td>
    </tr>
  );
}
