import { useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useAccountSummary } from '../hooks/useAccounts';
import { usePositions } from '../hooks/usePositions';
import { usePlaceOrder, useClosePosition, useSetLeverage } from '../hooks/useTrading';
import SymbolSelector from '../components/trade/SymbolSelector';
import PriceBar from '../components/trade/PriceBar';
import OrderForm from '../components/trade/OrderForm';
import LeverageSettings from '../components/trade/LeverageSettings';
import PositionCard from '../components/trade/PositionCard';
import { generateClientOrderId } from '../utils/clientOrderId';
import type { OrderSide } from '../types';
import { CardSkeleton } from '../components/ui/LoadingSkeleton';

export default function TradePage() {
  const { accountId } = useParams<{ accountId: string }>();
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [leverage, setLeverage] = useState(5);

  const { isLoading: sumLoading } = useAccountSummary(accountId);
  const { data: posData } = usePositions(accountId, symbol);

  const placeOrder = usePlaceOrder(accountId || '');
  const closePos = useClosePosition(accountId || '');
  const setLev = useSetLeverage(accountId || '');

  const currentPosition = posData?.positions?.find(
    (p) => p.symbol === symbol && parseFloat(p.quantity) !== 0,
  );

  // Update leverage from position when symbol changes
  const displayLeverage = currentPosition ? currentPosition.leverage : leverage;

  const handlePlaceOrder = useCallback(
    (side: OrderSide, qty: string) => {
      if (!accountId) return;
      placeOrder.mutate({
        account_id: accountId,
        client_order_id: generateClientOrderId(symbol),
        symbol,
        side,
        order_type: 'MARKET',
        quantity: qty,
        leverage: displayLeverage,
      });
    },
    [accountId, symbol, displayLeverage, placeOrder],
  );

  const handleClosePosition = useCallback(
    (sym: string, qty: string) => {
      if (!accountId) return;
      closePos.mutate({
        account_id: accountId,
        client_order_id: generateClientOrderId(sym),
        symbol: sym,
        quantity: qty,
      });
    },
    [accountId, closePos],
  );

  const handleSetLeverage = useCallback(
    (lev: number) => {
      if (!accountId) return;
      setLev.mutate({
        account_id: accountId,
        symbol,
        leverage: lev,
      });
      setLeverage(lev);
    },
    [accountId, symbol, setLev],
  );

  if (sumLoading) {
    return (
      <div className="space-y-4">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Trade</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Symbol + Chart + Leverage */}
        <div className="lg:col-span-2 space-y-4">
          <SymbolSelector value={symbol} onChange={setSymbol} />
          <PriceBar symbol={symbol} />

          {/* Order form */}
          <OrderForm
            leverage={displayLeverage}
            onPlaceOrder={handlePlaceOrder}
            isPlacing={placeOrder.isPending}
          />
        </div>

        {/* Right column: Leverage + Position */}
        <div className="space-y-4">
          <LeverageSettings
            currentLeverage={displayLeverage}
            onSetLeverage={handleSetLeverage}
            isSetting={setLev.isPending}
          />

          {currentPosition ? (
            <PositionCard
              position={currentPosition}
              onClose={handleClosePosition}
              isClosing={closePos.isPending}
            />
          ) : (
            <div className="bg-[#1a1d2e] border border-[#2a2e3f] rounded-xl p-5 text-center">
              <p className="text-sm text-gray-500">No open position on {symbol}</p>
              <p className="text-xs text-gray-600 mt-1">Place an order to open a position</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
