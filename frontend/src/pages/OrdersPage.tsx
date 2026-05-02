import { useParams } from 'react-router-dom';
import OrderTable from '../components/order/OrderTable';
import { useOrders } from '../hooks/useTrading';

export default function OrdersPage() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: orders = [], isLoading } = useOrders(accountId);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-heading)]">Orders</h1>
          <p className="text-sm text-[var(--color-text-dim)] mt-1">
            Order history for this account
          </p>
        </div>
      </div>

      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
        <OrderTable orders={orders} isLoading={isLoading} />
      </div>
    </div>
  );
}
