# U本位合约模拟交易系统 — 前端设计文档

## 1. 目标与范围

为后端 REST API 提供 Web 前端界面，支持模拟/真实账户的统一管理、合约交易、仓位查询和订单历史。前端是纯 SPA（Single Page Application），通过 HTTP 与后端 REST API 通信。

### 首期范围

- 账户管理：创建账户、切换账户、查看账户详情
- 交易界面：MARKET 开多/开空、设置杠杆、一键平仓
- 仓位看板：当前持仓列表、未实现/已实现盈亏
- 订单历史：按账户查询历史订单
- 账户总览：余额、保证金、总盈亏

### 暂不纳入

- K线图表（可使用 TradingView 轻量图表展示价格，但不做深度 K 线分析）
- WebSocket 实时行情推送至前端（首期使用轮询刷新）
- 移动端适配
- 多语言/国际化
- 策略回测、网格交易等高级功能

---

## 2. 技术选型

| 层级 | 技术 | 理由 |
|------|------|------|
| 框架 | React 18 + TypeScript | 类型安全、生态成熟 |
| 构建 | Vite 5 | 快速 HMR、ESBuild 打包 |
| 路由 | React Router v6 | 嵌套路由、URL 参数传递 accountId |
| 服务端状态 | TanStack Query (React Query) v5 | 缓存、去重、后台刷新、乐观更新 |
| HTTP | Axios | 拦截器、请求取消、错误统一处理 |
| 样式 | Tailwind CSS | 原子化 CSS，快速构建交易 UI |
| 图标 | Lucide React | 轻量图标库 |
| 通知 | Sonner (react-hot-toast 替代) | 交易结果反馈 |
| 价格展示 | 自定义 PriceLabel 组件 | 颜色标识涨跌、精度控制 |

> **不引入**: Ant Design / MUI 等重型组件库。交易系统界面简洁，使用 Tailwind CSS 原子类手写组件即可。

---

## 3. 总体架构

```
┌──────────────────────────────────────────────────────┐
│                    Browser (SPA)                     │
├──────────────────────────────────────────────────────┤
│  React Router v6                                    │
│  ┌──────────────────────────────────────────────┐   │
│  │              AppLayout                       │   │
│  │  ┌──────────┐  ┌────────────────────────┐   │   │
│  │  │ Sidebar  │  │   <Outlet />            │   │   │
│  │  │ - nav    │  │   (page content)        │   │   │
│  │  │ - accts  │  │                         │   │   │
│  │  └──────────┘  └────────────────────────┘   │   │
│  └──────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────┤
│  State Layer                                        │
│  ┌─────────────┐  ┌───────────────────────────┐    │
│  │ TanStack    │  │ React Context              │    │
│  │ Query       │  │ - selectedAccountId        │    │
│  │ (cache)     │  │ - selectedSymbol           │    │
│  └─────────────┘  └───────────────────────────┘    │
├──────────────────────────────────────────────────────┤
│  API Layer (axios instance + interceptors)          │
│  /api/v1/accounts/*   /api/v1/futures/*             │
└──────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Backend REST API    │
              │   localhost:8000      │
              └───────────────────────┘
```

---

## 4. 路由设计

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | DashboardPage | 账户列表 + 创建账户 |
| `/accounts/:accountId` | AccountPage | 账户总览（余额、持仓、快捷交易） |
| `/accounts/:accountId/trade` | TradePage | 完整交易界面（选币、下单、杠杆、平仓） |
| `/accounts/:accountId/orders` | OrdersPage | 当前账户订单历史 |

路由通过 URL 参数 `:accountId` 传递当前账户，页面间切换账户时仅需改变 URL。

---

## 5. 组件树

```
App
└── QueryClientProvider
    └── BrowserRouter
        └── AppLayout
            ├── Sidebar
            │   ├── Logo / AppTitle
            │   ├── AccountSwitcher (下拉选择账户)
            │   ├── NavLinks
            │   │   ├── "Overview" → /accounts/:id
            │   │   ├── "Trade"    → /accounts/:id/trade
            │   │   └── "Orders"   → /accounts/:id/orders
            │   └── CreateAccountButton
            └── <Outlet />
                ├── DashboardPage (/)
                │   ├── PageHeader ("Accounts")
                │   ├── AccountGrid
                │   │   └── AccountCard[] (name, type, balance, status)
                │   └── CreateAccountModal
                │       ├── NameInput
                │       ├── TypeSelect (simulated / live)
                │       ├── BalanceInput (simulated only)
                │       ├── ApiKeyInput (live only)
                │       └── SubmitButton
                │
                ├── AccountPage (/accounts/:accountId)
                │   ├── PageHeader (account name)
                │   ├── StatsBar
                │   │   ├── WalletBalance
                │   │   ├── AvailableBalance
                │   │   ├── MarginUsed
                │   │   └── UnrealizedPnL
                │   ├── PositionTable
                │   │   └── PositionRow[]
                │   │       ├── Symbol
                │   │       ├── Quantity + Side (LONG/SHORT)
                │   │       ├── EntryPrice
                │   │       ├── MarkPrice
                │   │       ├── UnrealizedPnL (color coded)
                │   │       ├── Leverage
                │   │       └── CloseButton
                │   └── QuickTradeWidget
                │       ├── SymbolInput
                │       ├── SideToggle (BUY / SELL)
                │       ├── QuantityInput (with step validation)
                │       ├── LeverageInput
                │       └── PlaceOrderButton
                │
                ├── TradePage (/accounts/:accountId/trade)
                │   ├── SymbolSelector (searchable dropdown)
                │   ├── PriceBar
                │   │   ├── LastPrice (large, green/red)
                │   │   ├── MarkPrice
                │   │   ├── 24h Change%
                │   │   └── Bid / Ask spread
                │   ├── TradingPanel
                │   │   ├── OrderForm
                │   │   │   ├── SideTabs (BUY | SELL)
                │   │   │   ├── QuantityInput
                │   │   │   ├── LeverageSlider (1-125)
                │   │   │   ├── CostEstimate (margin + fee)
                │   │   │   └── PlaceOrderButton
                │   │   └── PositionCard (current position on this symbol)
                │   │       ├── PositionSize + Direction
                │   │       ├── Entry / Mark / Liq Price
                │   │       ├── UnrealizedPnL
                │   │       ├── ClosePercentButtons (25%, 50%, 75%, 100%)
                │   │       └── CloseAllButton
                │   └── LeverageSettings (modal or inline)
                │
                └── OrdersPage (/accounts/:accountId/orders)
                    ├── FilterBar (symbol, status)
                    ├── OrderTable
                    │   └── OrderRow[]
                    │       ├── Time
                    │       ├── ClientOrderId
                    │       ├── Symbol
                    │       ├── Side + Type
                    │       ├── Quantity / Executed
                    │       ├── AvgPrice
                    │       ├── Status (badge)
                    │       └── Fee + PnL
                    └── EmptyState
```

---

## 6. 数据流设计

### 6.1 TanStack Query Key 设计

```typescript
// 账户
['accounts']                              → GET /api/v1/accounts (list all)
['account', accountId]                    → GET /api/v1/accounts/:id
['account-summary', accountId]            → GET /api/v1/futures/account?account_id=

// 仓位
['positions', accountId]                  → GET /api/v1/futures/positions?account_id=
['positions', accountId, symbol]          → GET /api/v1/futures/positions?account_id=&symbol=

// 订单
['order', accountId, clientOrderId]       → GET /api/v1/futures/orders/:coid?account_id=
```

### 6.2 Mutation 设计（写操作后失效相关查询）

| 操作 | Mutation | 失效的 Query Keys |
|------|----------|-------------------|
| 创建账户 | `createAccount` | `['accounts']` |
| 下单 | `placeOrder` | `['positions', accountId]`, `['account-summary', accountId]` |
| 平仓 | `closePosition` | `['positions', accountId]`, `['account-summary', accountId]` |
| 设置杠杆 | `setLeverage` | `['positions', accountId]` |

### 6.3 自动刷新策略

- 仓位 & 账户汇总：每 15 秒后台轮询（`refetchInterval: 15_000`）
- 订单历史：手动刷新或页面聚焦时刷新
- 价格数据：每 3 秒从后端行情接口轮询（首期不使用前端 WebSocket）

---

## 7. API 层设计

### 7.1 Axios 实例配置

```typescript
// src/api/client.ts
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// 响应拦截器：统一错误处理 + toast 通知
apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    const msg = error.response?.data?.detail || error.message;
    toast.error(msg);
    return Promise.reject(error);
  }
);
```

### 7.2 API 函数

```typescript
// src/api/accounts.ts
export const createAccount = (data: CreateAccountRequest) =>
  apiClient.post('/api/v1/accounts', data);

export const getAccount = (id: string) =>
  apiClient.get(`/api/v1/accounts/${id}`);

// src/api/futures.ts
export const getAccountSummary = (accountId: string) =>
  apiClient.get('/api/v1/futures/account', { params: { account_id: accountId } });

export const getPositions = (accountId: string, symbol?: string) =>
  apiClient.get('/api/v1/futures/positions', { params: { account_id: accountId, symbol } });

export const placeOrder = (data: PlaceOrderRequest) =>
  apiClient.post('/api/v1/futures/orders', data);

export const closePosition = (data: ClosePositionRequest) =>
  apiClient.post('/api/v1/futures/close-position', data);

export const setLeverage = (data: SetLeverageRequest) =>
  apiClient.post('/api/v1/futures/leverage', data);

export const getOrder = (accountId: string, clientOrderId: string) =>
  apiClient.get(`/api/v1/futures/orders/${clientOrderId}`, { params: { account_id: accountId } });
```

---

## 8. 目录结构

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── .env.example
└── src/
    ├── main.tsx                    # ReactDOM.createRoot
    ├── App.tsx                     # Router + QueryClientProvider
    ├── api/
    │   ├── client.ts               # Axios instance + interceptors
    │   ├── accounts.ts             # Account API functions
    │   └── futures.ts              # Futures trading API functions
    ├── hooks/
    │   ├── useAccounts.ts          # TanStack Query: accounts list
    │   ├── useAccountSummary.ts    # TanStack Query: balances + positions
    │   ├── usePositions.ts         # TanStack Query: positions
    │   ├── useOrders.ts            # TanStack Query: order query
    │   └── useMutation.ts          # TanStack Query: place/close/leverage mutations
    ├── context/
    │   └── SelectedAccount.tsx     # Currently selected account context
    ├── components/
    │   ├── layout/
    │   │   ├── AppLayout.tsx       # Sidebar + Outlet
    │   │   └── Sidebar.tsx         # Nav + account switcher
    │   ├── account/
    │   │   ├── AccountCard.tsx
    │   │   ├── CreateAccountModal.tsx
    │   │   ├── AccountSwitcher.tsx
    │   │   └── BalanceSummary.tsx
    │   ├── trade/
    │   │   ├── SymbolSelector.tsx
    │   │   ├── PriceBar.tsx
    │   │   ├── OrderForm.tsx
    │   │   ├── LeverageSettings.tsx
    │   │   └── PositionCard.tsx
    │   ├── position/
    │   │   ├── PositionTable.tsx
    │   │   └── PositionRow.tsx
    │   ├── order/
    │   │   ├── OrderTable.tsx
    │   │   └── OrderRow.tsx
    │   └── ui/
    │       ├── Button.tsx
    │       ├── Input.tsx
    │       ├── Select.tsx
    │       ├── Modal.tsx
    │       ├── Badge.tsx
    │       ├── Spinner.tsx
    │       ├── EmptyState.tsx
    │       └── PriceLabel.tsx      # 颜色标识涨跌 + 精度格式化
    ├── pages/
    │   ├── DashboardPage.tsx
    │   ├── AccountPage.tsx
    │   ├── TradePage.tsx
    │   └── OrdersPage.tsx
    ├── utils/
    │   ├── format.ts               # 数值格式化、精度处理
    │   ├── pnl.ts                  # 盈亏计算工具函数
    │   └── clientOrderId.ts        # 生成唯一 client_order_id
    └── types/
        └── index.ts                # 前端类型定义（对应后端 schema）
```

---

## 9. 核心交互流程

### 9.1 下单流程

```
1. 用户选择账户 → 进入 TradePage
2. 选择交易对 (SymbolSelector: BTCUSDT)
3. 查看实时价格 (PriceBar: last price, bid/ask)
4. 选择方向: BUY / SELL (SideTabs)
5. 输入数量 (QuantityInput, 校验 stepSize)
6. 调整杠杆 (LeverageSlider 1-125)
7. 查看预估: 保证金 = notional / leverage, 手续费 = notional * 0.05%
8. 点击 "Place MARKET Buy/Sell"
9. 弹出确认框 (价格、数量、方向、预估成本)
10. 确认 → API 调用 → Toast 成功/失败
11. 自动刷新持仓和账户余额
```

### 9.2 平仓流程

```
1. 在 AccountPage 或 TradePage 查看当前持仓
2. 可选: 点击 25%/50%/75%/100% 快速填入数量
3. 点击 "Close Position"
4. 确认 → API 调用 → 自动生成反向 MARKET reduce-only
5. 自动刷新持仓列表
```

### 9.3 创建账户流程

```
1. DashboardPage → 点击 "Create Account"
2. Modal 弹出
3. 选择 account_type: simulated 或 live
4. 填写 name
5. simulated: 填写 initial_balance (默认 10000 USDT)
6. live: 填写 api_key + api_secret
7. 提交 → API → 账户列表刷新
8. 自动跳转到新账户详情页
```

---

## 10. UI/UX 设计原则

### 10.1 颜色语义

| 场景 | 颜色 | 用途 |
|------|------|------|
| 买入/做多/盈利 | 绿色 `#22c55e` | BUY 按钮、正 PnL、多头标识 |
| 卖出/做空/亏损 | 红色 `#ef4444` | SELL 按钮、负 PnL、空头标识 |
| 背景 | 深灰 `#0f1117` | 主背景（暗色主题） |
| 卡片 | `#1a1d2e` | 面板、卡片背景 |
| 边框 | `#2a2e3f` | 分隔线、输入框边框 |

### 10.2 交易表单布局

交易表单采用纵向布局，移动端友好：

```
┌─────────────────────┐
│  Symbol: [BTCUSDT ▼]│
│                     │
│  Price: 65,000.50   │
│  Mark:  65,001.20   │
│  Spread: 0.50       │
│                     │
│  ┌────────┐ ┌──────┐│
│  │  BUY   │ │ SELL ││  ← SideTabs
│  └────────┘ └──────┘│
│                     │
│  Qty: [0.001     ]  │
│  Leverage: [──●──] 5│  ← Slider
│                     │
│  Margin: 13.00 USDT │
│  Fee:    0.03 USDT  │
│                     │
│  ┌─────────────────┐│
│  │ Place BUY Order ││  ← 绿色大按钮
│  └─────────────────┘│
└─────────────────────┘
```

### 10.3 响应式布局

- 大屏 (>1024px): 侧边栏 + 主内容区双栏布局
- 中屏 (768-1024px): 侧边栏折叠为汉堡菜单
- 小屏 (<768px): 单栏布局，底部 Tab 导航

---

## 11. 类型定义（TypeScript）

```typescript
// src/types/index.ts

// ─── Enums ───
type AccountType = 'simulated' | 'live';
type OrderSide = 'BUY' | 'SELL';
type OrderType = 'MARKET';
type OrderStatus = 'NEW' | 'FILLED' | 'REJECTED' | 'EXPIRED';
type MarginType = 'cross' | 'isolated';

// ─── Account ───
interface Account {
  id: string;
  name: string;
  account_type: AccountType;
  quote_asset: string;
  initial_balance: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface CreateAccountRequest {
  name: string;
  account_type: AccountType;
  quote_asset?: string;
  initial_balance?: string;
  api_key?: string;
  api_secret?: string;
}

// ─── Balance ───
interface Balance {
  asset: string;
  wallet_balance: string;
  available_balance: string;
  margin_balance: string;
  unrealized_pnl: string;
}

// ─── Position ───
interface Position {
  account_id: string;
  symbol: string;
  position_side: string;
  quantity: string;
  entry_price: string;
  breakeven_price: string;
  leverage: number;
  margin_type: MarginType;
  isolated_margin: string;
  unrealized_pnl: string;
  realized_pnl: string;
}

// ─── Order ───
interface PlaceOrderRequest {
  account_id: string;
  client_order_id: string;
  symbol: string;
  side: OrderSide;
  order_type: OrderType;
  quantity: string;
  leverage?: number;
  reduce_only?: boolean;
}

interface ClosePositionRequest {
  account_id: string;
  client_order_id: string;
  symbol: string;
  quantity: string;
}

interface SetLeverageRequest {
  account_id: string;
  symbol: string;
  leverage: number;
}

interface OrderResponse {
  account_id: string;
  account_type: string;
  client_order_id: string;
  exchange_order_id: string | null;
  symbol: string;
  side: string;
  order_type: string;
  status: string;
  executed_qty: string;
  avg_price: string;
  leverage: number | null;
  realized_pnl: string;
  fee_amount: string;
  reduce_only: boolean;
  created_at: string;
}

// ─── Account Summary ───
interface AccountSummary {
  account_id: string;
  account_type: string;
  quote_asset: string;
  balances: Balance[];
  positions: Position[];
  total_unrealized_pnl: string;
  total_margin_used: string;
}

// ─── API Responses ───
interface PositionsResponse {
  positions: Position[];
}
```

---

## 12. 状态管理细则

### 12.1 Query 配置

```typescript
// 默认 staleTime: 5s（账户数据不太频繁变化）
// 仓位轮询间隔: 15s
// 订单数据: 不自动轮询，手动刷新

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5_000,
      retry: 1,
      refetchOnWindowFocus: true,
    },
  },
});
```

### 12.2 SelectedAccount Context

```typescript
// 轻量 Context，仅存当前选中的 accountId
// 各页面从 URL params 读取 accountId
// 不需要全局状态管理库

interface AccountContextType {
  selectedAccountId: string | null;
  setSelectedAccountId: (id: string) => void;
}
```

---

## 13. 错误处理与边界状态

每个数据展示组件覆盖以下状态：

| 状态 | UI 表现 |
|------|---------|
| Loading | Skeleton / Spinner |
| Empty | EmptyState 组件 + 引导文案 |
| Error | ErrorState 组件 + 重试按钮 |
| Success | 正常数据展示 |

交易操作失败时：
- Toast 通知具体错误信息（来自 API `detail` 字段）
- 订单表单不清空，允许用户修改后重试
- 网络超时不重试下单（由幂等键保证安全）

---

## 14. 实施顺序

1. 项目脚手架: Vite + React + TypeScript + Tailwind + Router
2. 基础 UI 组件: Button, Input, Select, Modal, Badge, Spinner, EmptyState, PriceLabel
3. API 层: Axios 实例 + 拦截器 + API 函数
4. 类型定义 + Hooks (TanStack Query)
5. AppLayout + Sidebar + 路由骨架
6. DashboardPage: 账户列表 + 创建账户
7. AccountPage: 余额概览 + 持仓表格
8. TradePage: 交易面板 + 下单 + 杠杆设置
9. OrdersPage: 订单历史
10. 价格实时刷新 + 最终集成测试
```

---

## 15. 与后端接口对照表

| 前端功能 | 后端接口 | Method |
|----------|----------|--------|
| 账户列表 | `/api/v1/accounts/{id}` | GET (逐个查询) |
| 创建账户 | `/api/v1/accounts` | POST |
| 账户总览 | `/api/v1/futures/account?account_id=` | GET |
| 持仓列表 | `/api/v1/futures/positions?account_id=` | GET |
| 下单 | `/api/v1/futures/orders` | POST |
| 平仓 | `/api/v1/futures/close-position` | POST |
| 设置杠杆 | `/api/v1/futures/leverage` | POST |
| 查询订单 | `/api/v1/futures/orders/{coid}?account_id=` | GET |

> 注: 后端没有"列出所有账户"的接口。前端在 DashboardPage 初始化时需逐个查询账户（从 localStorage 存储已创建的 account IDs），或迭代查询。更好的方案：前端在创建账户后将 ID 存入 localStorage，Dashboard 从 localStorage 读取 ID 列表后逐个查询。
