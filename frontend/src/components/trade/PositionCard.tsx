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

export default function PositionCard({ position: p, onClose, isClosing }: Props) {
  const qty = parseFloat(p.quantity);
  const isLong = qty > 0;
  const pnl = parseFloat(p.unrealized_pnl);
  const pctOptions = [25, 50, 75, 100];

  return (
    <div className="bg-[#1a1d2e] border border-[#2a2e3f] rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white">Current Position</h3>
        <Badge variant={isLong ? 'green' : 'red'}>
          {isLong ? 'LONG' : 'SHORT'} · {p.leverage}x
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
        <div>
          <div className="text-xs text-gray-500 mb-0.5">Size</div>
          <div className="text-white font-mono">{fmtCrypto(Math.abs(qty))} {p.symbol.replace('USDT', '')}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-0.5">Entry Price</div>
          <div className="text-white font-mono">{fmtMoney(p.entry_price)}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-0.5">Breakeven</div>
          <div className="text-white font-mono">{fmtMoney(p.breakeven_price)}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-0.5">Unrealized PnL</div>
          <PriceLabel value={pnl} className="font-mono" />
        </div>
      </div>

      {/* Close buttons */}
      <div className="space-y-2">
        <div className="flex gap-2">
          {pctOptions.map((pct) => (
            <button
              key={pct}
              onClick={() => onClose(p.symbol, String(Math.abs(qty) * pct / 100))}
              className="flex-1 py-1 text-xs rounded border border-[#2a2e3f] text-gray-400 hover:text-white hover:border-gray-500 transition-colors cursor-pointer"
            >
              {pct}%
            </button>
          ))}
        </div>
        <Button
          variant="danger"
          size="sm"
          className="w-full"
          onClick={() => onClose(p.symbol, String(Math.abs(qty)))}
          loading={isClosing}
        >
          Close Entire Position
        </Button>
      </div>
    </div>
  );
}
