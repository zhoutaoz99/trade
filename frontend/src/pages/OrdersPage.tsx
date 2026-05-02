import { useState } from 'react';
import OrderTable from '../components/order/OrderTable';
import type { OrderResponse } from '../types';

export default function OrdersPage() {
  // In v1, orders are fetched individually by client_order_id.
  // For a full order history, the backend would need a list endpoint.
  // Here we show the concept with a note about the v1 limitation.
  const [orders] = useState<(OrderResponse & { id?: string })[]>([]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Orders</h1>
          <p className="text-sm text-gray-500 mt-1">
            Order history for this account
          </p>
        </div>
      </div>

      <div className="bg-[#1a1d2e] border border-[#2a2e3f] rounded-xl p-5">
        {orders.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-3">📋</div>
            <h3 className="text-lg font-medium text-white mb-2">Order History</h3>
            <p className="text-sm text-gray-500 max-w-md mx-auto mb-4">
              In v1, orders are queryable by client_order_id via the API.
              Go to the Trade page to place an order, then query it using the order ID.
            </p>
            <div className="inline-block bg-[#0f1117] rounded-lg px-4 py-2 text-xs font-mono text-gray-400">
              GET /api/v1/futures/orders/{'{client_order_id}'}?account_id={'{account_id}'}
            </div>
          </div>
        ) : (
          <OrderTable orders={orders} isLoading={false} />
        )}
      </div>
    </div>
  );
}
