import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import AppLayout from './components/layout/AppLayout';
import DashboardPage from './pages/DashboardPage';
import AccountPage from './pages/AccountPage';
import TradePage from './pages/TradePage';
import OrdersPage from './pages/OrdersPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5_000,
      retry: 1,
      refetchOnWindowFocus: true,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/accounts/:accountId" element={<AccountPage />} />
            <Route path="/accounts/:accountId/trade" element={<TradePage />} />
            <Route path="/accounts/:accountId/orders" element={<OrdersPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#1a1d2e',
            color: '#e2e8f0',
            border: '1px solid #2a2e3f',
          },
        }}
      />
    </QueryClientProvider>
  );
}
