import { useState } from 'react';
import type { OrderSide } from '../../types';
import Input from '../ui/Input';
import Button from '../ui/Button';

interface Props {
  leverage: number;
  onPlaceOrder: (side: OrderSide, qty: string) => void;
  isPlacing: boolean;
}

export default function OrderForm({ leverage, onPlaceOrder, isPlacing }: Props) {
  const [side, setSide] = useState<OrderSide>('BUY');
  const [qty, setQty] = useState('0.001');

  const handleSubmit = () => {
    if (!qty || parseFloat(qty) <= 0) return;
    onPlaceOrder(side, qty);
  };

  return (
    <div className="bg-[#1a1d2e] border border-[#2a2e3f] rounded-xl p-5">
      <h3 className="text-sm font-semibold text-white mb-4">Market Order</h3>

      {/* Side tabs */}
      <div className="flex mb-4">
        <button
          onClick={() => setSide('BUY')}
          className={`flex-1 py-2 text-sm font-semibold rounded-l-lg transition-colors cursor-pointer ${
            side === 'BUY' ? 'bg-green-600 text-white' : 'bg-[#0f1117] text-gray-400 hover:text-white'
          }`}
        >
          BUY / LONG
        </button>
        <button
          onClick={() => setSide('SELL')}
          className={`flex-1 py-2 text-sm font-semibold rounded-r-lg transition-colors cursor-pointer ${
            side === 'SELL' ? 'bg-red-600 text-white' : 'bg-[#0f1117] text-gray-400 hover:text-white'
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
                  ? 'border-blue-500 text-blue-400 bg-blue-500/10'
                  : 'border-[#2a2e3f] text-gray-400 hover:border-gray-500'
              }`}
            >
              {preset}
            </button>
          ))}
        </div>
      </div>

      {/* Order estimate */}
      <div className="bg-[#0f1117] rounded-lg p-3 mb-4 space-y-1 text-xs">
        <div className="flex justify-between text-gray-400">
          <span>Leverage</span>
          <span className="text-white">{leverage}x</span>
        </div>
        <div className="flex justify-between text-gray-400">
          <span>Est. Fee (taker)</span>
          <span className="text-white">0.05%</span>
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
