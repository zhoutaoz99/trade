import { useState, useMemo } from 'react';
import type { OrderSide } from '../../types';
import { fmtMoney } from '../../utils/format';
import Input from '../ui/Input';
import Button from '../ui/Button';

interface Props {
  leverage: number;
  price?: { ask_price: string; bid_price: string };
  onPlaceOrder: (side: OrderSide, qty: string) => void;
  isPlacing: boolean;
}

export default function OrderForm({ leverage, price, onPlaceOrder, isPlacing }: Props) {
  const [side, setSide] = useState<OrderSide>('BUY');
  const [qty, setQty] = useState('0.001');

  const orderAmount = useMemo(() => {
    const q = parseFloat(qty);
    if (!q || q <= 0 || !price) return null;
    const execPrice = side === 'BUY' ? parseFloat(price.ask_price) : parseFloat(price.bid_price);
    if (!execPrice || execPrice <= 0) return null;
    return q * execPrice;
  }, [qty, side, price]);

  const handleSubmit = () => {
    if (!qty || parseFloat(qty) <= 0) return;
    onPlaceOrder(side, qty);
  };

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
      <h3 className="text-sm font-semibold text-[var(--color-text-heading)] mb-4">Market Order</h3>

      {/* Side tabs */}
      <div className="flex mb-4">
        <button
          onClick={() => setSide('BUY')}
          className={`flex-1 py-2 text-sm font-semibold rounded-l-lg transition-colors cursor-pointer ${
            side === 'BUY' ? 'bg-green-600 text-white' : 'bg-[var(--color-bg)] text-[var(--color-text-muted)] hover:text-[var(--color-text-heading)]'
          }`}
        >
          BUY / LONG
        </button>
        <button
          onClick={() => setSide('SELL')}
          className={`flex-1 py-2 text-sm font-semibold rounded-r-lg transition-colors cursor-pointer ${
            side === 'SELL' ? 'bg-red-600 text-white' : 'bg-[var(--color-bg)] text-[var(--color-text-muted)] hover:text-[var(--color-text-heading)]'
          }`}
        >
          SELL / SHORT
        </button>
      </div>

      {/* Quantity */}
      <div className="mb-4">
        <Input
          label="Quantity"
          type="number"
          value={qty}
          onChange={(e) => setQty(e.target.value)}
          step="0.001"
          min="0.001"
        />
        <div className="flex gap-2 mt-2">
          {['0.001', '0.01', '0.1', '1'].map((preset) => (
            <button
              key={preset}
              onClick={() => setQty(preset)}
              className={`px-2 py-1 text-xs rounded border transition-colors cursor-pointer ${
                qty === preset
                  ? 'border-blue-500 text-[var(--color-blue-text)] bg-[var(--color-blue-bg)]'
                  : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-[var(--color-text-dim)]'
              }`}
            >
              {preset}
            </button>
          ))}
        </div>
      </div>

      {/* Order estimate */}
      <div className="bg-[var(--color-bg)] rounded-lg p-3 mb-4 space-y-1 text-xs">
        <div className="flex justify-between text-[var(--color-text-muted)]">
          <span>Leverage</span>
          <span className="text-[var(--color-text-heading)]">{leverage}x</span>
        </div>
        <div className="flex justify-between text-[var(--color-text-muted)]">
          <span>Est. Price</span>
          <span className="text-[var(--color-text-heading)]">
            {price ? fmtMoney(side === 'BUY' ? parseFloat(price.ask_price) : parseFloat(price.bid_price)) : '--'}
          </span>
        </div>
        <div className="flex justify-between text-[var(--color-text-muted)]">
          <span>Est. Order Amount</span>
          <span className="text-[var(--color-text-heading)] font-semibold">
            {orderAmount !== null ? fmtMoney(orderAmount) : '--'}
          </span>
        </div>
        <div className="flex justify-between text-[var(--color-text-muted)]">
          <span>Est. Fee (taker)</span>
          <span className="text-[var(--color-text-heading)]">0.05%</span>
        </div>
      </div>

      {/* Submit */}
      <Button
        variant={side === 'BUY' ? 'buy' : 'sell'}
        size="lg"
        className="w-full"
        onClick={handleSubmit}
        loading={isPlacing}
        disabled={!qty || parseFloat(qty) <= 0}
      >
        Place MARKET {side}
      </Button>
    </div>
  );
}
