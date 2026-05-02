# Binance U本位合约模拟交易系统设计文档

## 1. 目标与范围

本系统用于实现一个基于 Binance USD-M Futures（U本位合约）的后端交易系统，通过 REST API 对外开放统一交易接口；账户创建时通过 `account_type` 确定该账户是模拟账户还是真实账户，后续所有交易和查询只传 `account_id`，系统按账户类型自动路由。行情、交易规则、资金费率、标记价格和合约信息必须完全使用币安官方数据。

默认技术栈：

- Python 3.11+
- FastAPI 或同类 Python REST 框架
- PostgreSQL
- SQLAlchemy + Alembic
- asyncio/httpx/websockets 或官方 Binance Connector
- Decimal 定点数计算，禁止使用 float 处理价格、数量、金额和盈亏

首期范围：

- Binance USD-M Futures 永续合约
- USDT 保证金
- 单账户
- 纯后端 REST API 服务
- 统一对外 REST 交易接口
- 账户级 `account_type` 控制模拟/真实交易
- 单向持仓模式（One-way Mode）
- 只实现最简单的合约杠杆交易：设置杠杆、MARKET 开仓、MARKET 平仓
- 支持手续费、滑点、已实现盈亏、未实现盈亏
- 真实交易只对接 Binance 真实 U本位合约接口

暂不纳入首期：

- 现货、币本位合约、期权
- K线、行情 tick、资金费率等市场数据入库
- 多资产模式
- Hedge Mode 双向持仓
- LIMIT、STOP_MARKET、TAKE_PROFIT_MARKET 等高级订单
- 资金费率自动结算
- 前台页面、Web UI、移动端页面
- CLI 交易客户端
- 网格策略、复制交易、组合保证金
- 高频完整订单簿撮合

## 2. 官方数据来源

所有外部数据必须来自 Binance 官方接口或官方公开数据文件。

### 2.1 REST 数据

U本位合约 REST 基地址：

```text
https://fapi.binance.com
```

核心接口：

- `GET /fapi/v1/exchangeInfo`：交易规则、合约状态、精度、过滤器、支持订单类型
- `GET /fapi/v1/time`：服务器时间，用于签名请求时间校准
- `GET /fapi/v1/klines`：K线数据
- `GET /fapi/v1/premiumIndex`：标记价格、指数价格、预测资金费率
- `GET /fapi/v1/fundingRate`：历史资金费率
- `GET /fapi/v1/ticker/bookTicker`：最优买卖价
- `GET /fapi/v1/ticker/24hr`：24小时行情统计

真实交易适配目标：

- `POST /fapi/v1/order`：真实下单接口
- `GET /fapi/v1/order`：查询订单
- `POST /fapi/v1/leverage`：调整指定 symbol 的初始杠杆
- `GET /fapi/v2/account` 或后续官方推荐账户接口：账户信息
- `GET /fapi/v2/positionRisk` 或后续官方推荐仓位接口：仓位风险

当账户 `account_type=simulated` 时，系统不得调用任何真实下单、撤单、调整杠杆或更改仓位的接口。

### 2.2 WebSocket 数据

U本位合约 WebSocket 基地址：

```text
wss://fstream.binance.com
```

市场数据流：

- `<symbol>@bookTicker`：最优买卖价，用于模拟 MARKET 成交和限价单触发判断
- `<symbol>@markPrice`：标记价格，用于未实现盈亏、强平风险和条件单触发
- `<symbol>@kline_<interval>`：实时K线
- `<symbol>@aggTrade`：聚合成交，可用于更细粒度回放和滑点估计

用户数据流：

- `ACCOUNT_UPDATE`：账户余额、仓位变化
- `ORDER_TRADE_UPDATE`：订单状态与成交更新

用户数据流只在真实账户使用。模拟账户由本地撮合引擎生成等价的订单、成交、账户和仓位事件。

### 2.3 历史公开数据

首期不将历史行情写入数据库。若需要回放测试，可临时从 Binance 官方公开数据读取：

```text
https://data.binance.vision/data/futures/um/
```

可选读取来源：

- `daily/klines`
- `monthly/klines`
- `daily/aggTrades`
- `monthly/aggTrades`
- 资金费率通过 REST 查询或内存缓存，不写入 PostgreSQL

## 3. 总体架构

```text
              +---------------------------+
              | External REST Client      |
              +-------------+-------------+
                            |
                            v
              +---------------------------+
              | REST API                  |
              | - account_id              |
              | - order/leverage request  |
              +-------------+-------------+
                            |
                            v
              +---------------------------+
              | Trading Service           |
              | - order validation        |
              | - risk check              |
              | - account-level routing   |
              +-------------+-------------+
                            |
              +-------------+-------------+
              |                           |
              v                           v
+---------------------------+  +---------------------------+
| SimulatedExchangeGateway  |  | BinanceFuturesGateway     |
| - local order matching    |  | - live REST order         |
| - local account updates   |  | - signed requests         |
| - local event generation  |  | - user data stream sync   |
+-------------+-------------+  +-------------+-------------+
              |                           |
              +-------------+-------------+
                            |
                            v
              +---------------------------+
              | PostgreSQL                |
              | simulated trade records   |
              | balances/positions/ledger |
              +---------------------------+
                            ^
                            |
              +-------------+-------------+
              | Market Data Service       |
              | - REST sync               |
              | - WebSocket subscribe     |
              | - historical import       |
              +---------------------------+
```

系统以账户类型决定订单流向：

- `account_type=simulated`：只写本地 PostgreSQL，由模拟撮合引擎生成成交。
- `account_type=live`：调用币安真实交易接口。

查询接口同样使用 `account_id` 对应的账户类型决定数据来源：

- `account_type=simulated`：查询本地 PostgreSQL 中保存的模拟交易记录、模拟仓位和模拟账户余额。
- `account_type=live`：查询 Binance 真实账户、真实订单和真实仓位数据，不写入模拟交易记录表。

## 4. 配置设计

配置示例：

```env
APP_ENV=dev
DATABASE_URL=postgresql+psycopg://trade:trade_password@localhost:5432/trade

BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_RECV_WINDOW=5000

DEFAULT_QUOTE_ASSET=USDT
DEFAULT_ACCOUNT_INITIAL_BALANCE=10000
DEFAULT_TAKER_FEE_RATE=0.0005
DEFAULT_MAKER_FEE_RATE=0.0002
DEFAULT_SLIPPAGE_BPS=2

RISK_MAX_LEVERAGE=10
RISK_MAX_POSITION_NOTIONAL=50000
RISK_MAX_ORDER_NOTIONAL=10000
```

安全约束：

- 对外交易和查询请求必须传入 `account_id`。
- 系统必须先读取 `accounts.account_type`，再决定路由到模拟网关还是真实网关。
- `account_type=simulated` 时禁止调用真实交易接口。
- `account_type=live` 时必须配置 API key 和 secret。
- 系统启动时必须在日志中明确记录账户标识、账户类型、交易网关和风险配置。
- 禁止在日志中输出 API secret、完整签名字符串或敏感请求头。

## 5. 核心模块设计

### 5.1 MarketDataService

职责：

- 从 Binance `exchangeInfo` 获取交易规则，运行期使用内存缓存。
- 订阅实时行情 WebSocket。
- 维护最新 `bookTicker`、`markPrice` 的内存缓存。
- 提供当前可用价格查询接口。
- 首期不将 K线、行情 tick、资金费率写入 PostgreSQL。

关键接口：

```python
class MarketDataProvider:
    async def sync_exchange_info(self) -> None: ...
    async def get_symbol(self, symbol: str) -> SymbolInfo: ...
    async def get_latest_book_ticker(self, symbol: str) -> BookTicker: ...
    async def get_latest_mark_price(self, symbol: str) -> Decimal: ...
```

### 5.2 REST API

系统是纯后端服务，不提供前台页面。对外只开放 REST API，调用方不直接选择 `SimulatedExchangeGateway` 或 `BinanceFuturesGateway`，也不在每个请求中传模拟/真实标志。调用方只传 `account_id`，系统读取账户的 `account_type` 后自动路由。

首期接口：

```text
POST /api/v1/accounts
GET  /api/v1/accounts/{account_id}
POST /api/v1/futures/leverage
POST /api/v1/futures/orders
POST /api/v1/futures/close-position
GET  /api/v1/futures/orders/{client_order_id}?account_id=...
GET  /api/v1/futures/positions?account_id=...&symbol=BTCUSDT
GET  /api/v1/futures/account?account_id=...
```

创建账户请求：

```json
{
  "name": "demo-account",
  "account_type": "simulated",
  "quote_asset": "USDT",
  "initial_balance": "10000"
}
```

真实账户创建请求：

```json
{
  "name": "binance-live-main",
  "account_type": "live",
  "quote_asset": "USDT",
  "api_key": "binance-api-key",
  "api_secret": "binance-api-secret"
}
```

真实账户的 `api_secret` 必须加密保存或接入外部密钥管理服务，禁止明文落库。

设置杠杆请求：

```json
{
  "account_id": "uuid",
  "symbol": "BTCUSDT",
  "leverage": 5
}
```

MARKET 开仓请求：

```json
{
  "account_id": "uuid",
  "client_order_id": "sim-btcusdt-001",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "order_type": "MARKET",
  "quantity": "0.001",
  "leverage": 5
}
```

MARKET 平仓请求：

```json
{
  "account_id": "uuid",
  "client_order_id": "sim-btcusdt-close-001",
  "symbol": "BTCUSDT",
  "quantity": "0.001"
}
```

首期约束：

- `account_id` 为必填字段。
- 模拟/真实由 `accounts.account_type` 决定，接口不得暴露请求级模拟/真实切换参数。
- `order_type` 首期只允许 `MARKET`。
- `side` 只允许 `BUY` 或 `SELL`。
- `position_side` 固定为 `BOTH`，不对外暴露 Hedge Mode。
- `leverage` 必须为 1 到 125 的整数，并受本地风险配置限制。
- 平仓接口自动根据当前仓位方向生成反向 MARKET reduce-only 订单。

统一响应：

```json
{
  "account_id": "uuid",
  "account_type": "simulated",
  "client_order_id": "sim-btcusdt-001",
  "exchange_order_id": null,
  "symbol": "BTCUSDT",
  "side": "BUY",
  "order_type": "MARKET",
  "status": "FILLED",
  "executed_qty": "0.001",
  "avg_price": "65000.00",
  "leverage": 5,
  "realized_pnl": "0",
  "fee_amount": "0.0325",
  "created_at": "2026-05-02T10:00:00Z"
}
```

统一查询行为：

- 查询订单：
  - `account_type=simulated`：按 `account_id + client_order_id` 查询本地 `orders`、`fills`。
  - `account_type=live`：调用 Binance `GET /fapi/v1/order` 查询真实订单；结果直接返回，不写入本地交易记录表。
- 查询仓位：
  - `account_type=simulated`：查询本地 `positions`，并使用最新 mark price 计算未实现盈亏。
  - `account_type=live`：调用 Binance 仓位风险接口查询真实仓位；结果直接返回。
- 查询账户：
  - `account_type=simulated`：查询本地 `balances`、`positions` 和 `ledger_entries` 汇总。
  - `account_type=live`：调用 Binance 账户接口查询真实余额和保证金信息；结果直接返回。

### 5.3 TradingService

职责：

- 接收 REST API 层传入的下单、平仓和设置杠杆请求。
- 标准化订单参数。
- 执行 symbol filter 校验。
- 调用 RiskService 做风险检查。
- 根据 `account_id` 读取账户类型，路由到模拟网关或真实网关。
- 保证订单请求和本地记录具备幂等性。

关键接口：

```python
class LeverageRequest:
    account_id: str
    symbol: str
    leverage: int

class OrderRequest:
    account_id: str
    client_order_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    order_type: Literal["MARKET"]
    quantity: Decimal
    leverage: int | None

class TradingService:
    async def set_leverage(self, request: LeverageRequest) -> LeverageResult: ...
    async def place_order(self, request: OrderRequest) -> OrderResult: ...
    async def close_position(self, request: ClosePositionRequest) -> OrderResult: ...
    async def get_order(self, query: OrderQuery) -> OrderView: ...
    async def get_positions(self, query: PositionQuery) -> list[PositionView]: ...
    async def get_account(self, query: AccountQuery) -> AccountView: ...
```

### 5.4 ExchangeGateway

交易网关抽象：

```python
class ExchangeGateway:
    async def set_leverage(self, request: LeverageRequest) -> LeverageResult: ...
    async def place_order(self, request: OrderRequest) -> OrderResult: ...
    async def query_order(self, request: QueryOrderRequest) -> OrderResult: ...
```

实现：

- `SimulatedExchangeGateway`
- `BinanceFuturesGateway`

`SimulatedExchangeGateway` 只访问本地数据库和行情缓存，不调用真实交易接口。

`BinanceFuturesGateway` 负责签名、时间戳、重试、限频、真实接口错误处理和用户数据流同步。

### 5.5 SimulatedMatchingEngine

职责：

- 校验订单能否进入本地订单簿。
- 根据最新行情或回放行情判断订单是否成交。
- 生成成交记录、手续费、账本流水、仓位变化。
- 生成本地等价的订单事件和账户事件。

首期撮合规则：

- MARKET：
  - BUY 使用 best ask 或 fallback 价格。
  - SELL 使用 best bid 或 fallback 价格。
  - 按 `DEFAULT_SLIPPAGE_BPS` 增加滑点。
  - 首期按一次性全部成交处理，行情缺失则拒单。
- close-position：
  - 查询当前 `BOTH` 仓位。
  - 根据仓位方向生成反向 MARKET reduce-only 订单。
  - 平仓数量不得超过当前仓位绝对数量。

LIMIT、STOP_MARKET、TAKE_PROFIT_MARKET 和部分成交留到后续版本。

### 5.6 PortfolioService

职责：

- 维护账户余额、冻结保证金、仓位、均价、杠杆、保证金类型。
- 根据成交更新仓位。
- 根据标记价格计算未实现盈亏。
- 计算可用余额、保证金占用和强平风险。
- 首期不自动处理资金费率扣收或收入；资金费率需要时从 Binance REST 查询或使用内存缓存。

单向持仓更新规则：

- 当前仓位为 0：新成交建立仓位，entry_price 为成交均价。
- 同向加仓：按名义价值加权更新 entry_price。
- 反向减仓：按减少数量计算已实现盈亏。
- 反向超过当前仓位：先平旧仓，再用剩余数量开反向新仓。
- 手续费立即进入账本并影响 wallet balance。

### 5.7 RiskService

职责：

- 校验订单名义价值、杠杆、保证金是否足够。
- 校验 reduce-only 订单不会增加风险暴露。
- 校验单笔订单、单品种仓位、账户总风险限制。
- 计算强平预警状态。

首期风控：

- 最大杠杆：`RISK_MAX_LEVERAGE`
- 单笔最大名义价值：`RISK_MAX_ORDER_NOTIONAL`
- 单合约最大仓位名义价值：`RISK_MAX_POSITION_NOTIONAL`
- 下单后保证金余额不得为负
- reduce-only 订单不得扩大仓位

## 6. PostgreSQL 数据库设计

PostgreSQL 只保存账户、凭证和模拟账户交易查询所需的数据，不保存 K线、行情 tick、资金费率、历史公开行情或交易规则快照。交易规则和价格由 Binance 官方接口实时读取，并可在进程内短期缓存。

所有金额、价格、数量、费率使用 `NUMERIC`。时间字段保留 Binance 毫秒时间戳和数据库 `timestamptz`，便于排序和查询。

### 6.1 accounts

```sql
CREATE TABLE accounts (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    account_type TEXT NOT NULL CHECK (account_type IN ('simulated', 'live')),
    quote_asset TEXT NOT NULL DEFAULT 'USDT',
    initial_balance NUMERIC NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6.2 account_credentials

真实账户 API 凭证单独保存。模拟账户不得创建凭证记录。

```sql
CREATE TABLE account_credentials (
    account_id UUID PRIMARY KEY REFERENCES accounts(id),
    api_key TEXT NOT NULL,
    encrypted_api_secret TEXT NOT NULL,
    key_provider TEXT NOT NULL DEFAULT 'local_encrypted',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6.3 balances

仅保存模拟账户余额。真实账户余额通过 Binance 账户接口实时查询，不写入该表。

```sql
CREATE TABLE balances (
    account_id UUID NOT NULL REFERENCES accounts(id),
    asset TEXT NOT NULL,
    wallet_balance NUMERIC NOT NULL,
    available_balance NUMERIC NOT NULL,
    margin_balance NUMERIC NOT NULL,
    unrealized_pnl NUMERIC NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (account_id, asset)
);
```

### 6.4 positions

仅保存模拟账户仓位。真实账户仓位通过 Binance 仓位接口实时查询，不写入该表。

```sql
CREATE TABLE positions (
    account_id UUID NOT NULL REFERENCES accounts(id),
    symbol TEXT NOT NULL,
    position_side TEXT NOT NULL DEFAULT 'BOTH',
    quantity NUMERIC NOT NULL DEFAULT 0,
    entry_price NUMERIC NOT NULL DEFAULT 0,
    breakeven_price NUMERIC NOT NULL DEFAULT 0,
    leverage INTEGER NOT NULL,
    margin_type TEXT NOT NULL CHECK (margin_type IN ('cross', 'isolated')),
    isolated_margin NUMERIC NOT NULL DEFAULT 0,
    unrealized_pnl NUMERIC NOT NULL DEFAULT 0,
    realized_pnl NUMERIC NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (account_id, symbol, position_side)
);
```

### 6.5 orders

仅保存模拟账户订单。真实账户订单通过 Binance 查询接口实时查询，不写入该表。

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES accounts(id),
    symbol TEXT NOT NULL,
    client_order_id TEXT NOT NULL,
    exchange_order_id TEXT,
    side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
    position_side TEXT NOT NULL DEFAULT 'BOTH',
    type TEXT NOT NULL CHECK (type IN ('MARKET')),
    time_in_force TEXT,
    status TEXT NOT NULL,
    orig_qty NUMERIC NOT NULL,
    executed_qty NUMERIC NOT NULL DEFAULT 0,
    requested_leverage INTEGER,
    price NUMERIC,
    stop_price NUMERIC,
    avg_price NUMERIC NOT NULL DEFAULT 0,
    reduce_only BOOLEAN NOT NULL DEFAULT false,
    close_position BOOLEAN NOT NULL DEFAULT false,
    working_type TEXT NOT NULL DEFAULT 'MARK_PRICE',
    raw_request JSONB NOT NULL,
    raw_response JSONB,
    error_code TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (account_id, client_order_id)
);

CREATE INDEX idx_orders_account_symbol_status
    ON orders(account_id, symbol, status);
```

### 6.6 fills

仅保存模拟账户成交。真实账户成交首期不入库。

```sql
CREATE TABLE fills (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id),
    account_id UUID NOT NULL REFERENCES accounts(id),
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    price NUMERIC NOT NULL,
    quantity NUMERIC NOT NULL,
    quote_quantity NUMERIC NOT NULL,
    fee_asset TEXT NOT NULL,
    fee_amount NUMERIC NOT NULL,
    realized_pnl NUMERIC NOT NULL DEFAULT 0,
    liquidity TEXT NOT NULL CHECK (liquidity IN ('maker', 'taker')),
    trade_time_ms BIGINT NOT NULL,
    raw_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_fills_account_symbol_time
    ON fills(account_id, symbol, trade_time_ms DESC);
```

### 6.7 ledger_entries

账本表是模拟账户资金变化的最终审计来源。真实账户资金变化首期不入库。

```sql
CREATE TABLE ledger_entries (
    id UUID PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES accounts(id),
    asset TEXT NOT NULL,
    event_type TEXT NOT NULL,
    amount NUMERIC NOT NULL,
    balance_after NUMERIC NOT NULL,
    order_id UUID REFERENCES orders(id),
    fill_id UUID REFERENCES fills(id),
    symbol TEXT,
    description TEXT,
    event_time_ms BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ledger_account_asset_time
    ON ledger_entries(account_id, asset, event_time_ms DESC);
```

### 6.8 strategy_runs

```sql
CREATE TABLE strategy_runs (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    account_id UUID NOT NULL REFERENCES accounts(id),
    status TEXT NOT NULL,
    config JSONB NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    stopped_at TIMESTAMPTZ
);
```

### 6.9 system_events

```sql
CREATE TABLE system_events (
    id BIGSERIAL PRIMARY KEY,
    level TEXT NOT NULL,
    component TEXT NOT NULL,
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 7. 订单生命周期

### 7.1 统一下单流程

```text
PlaceOrder request
  -> require account_id
  -> load account and account_type
  -> validate required fields
  -> load symbol filters
  -> normalize price/quantity by tickSize/stepSize
  -> risk check
  -> if account_type=simulated:
       insert orders(status=NEW)
       matching engine checks latest market data
       insert fills
       update positions
       update balances
       insert ledger_entries
       update orders(status=FILLED, avg_price, executed_qty)
     else:
       signed POST /fapi/v1/order
       return Binance response
  -> commit transaction
  -> return OrderResult
```

模拟交易的订单、成交、仓位、余额、账本写入必须在一个 PostgreSQL 事务内完成。任一环节失败必须回滚。真实交易请求不写入本地模拟交易记录表，直接调用 Binance 接口并返回真实响应。

### 7.2 设置杠杆流程

```text
SetLeverage request
  -> require account_id
  -> load account and account_type
  -> validate symbol and leverage
  -> if account_type=simulated:
       update local positions.leverage for account + symbol
       write system event
     else:
       signed POST /fapi/v1/leverage
       update local positions.leverage from response
  -> return LeverageResult
```

真实交易请求异常处理：

- 网络超时或 Binance 返回执行状态未知时，不立即重试下单。
- 先通过 `client_order_id` 查询订单状态。
- 只有确认订单不存在或失败后才允许重新提交。
- 所有真实订单必须带唯一 `newClientOrderId`。
- 设置真实杠杆失败时，不更新本地仓位杠杆。

## 8. 仓位与盈亏计算

### 8.1 名义价值

```text
notional = abs(quantity) * price
```

### 8.2 初始保证金

```text
initial_margin = notional / leverage
```

### 8.3 未实现盈亏

多仓：

```text
unrealized_pnl = quantity * (mark_price - entry_price)
```

空仓：

```text
unrealized_pnl = abs(quantity) * (entry_price - mark_price)
```

### 8.4 已实现盈亏

平多：

```text
realized_pnl = closed_qty * (exit_price - entry_price)
```

平空：

```text
realized_pnl = closed_qty * (entry_price - exit_price)
```

### 8.5 手续费

```text
fee = fill_notional * fee_rate
```

MARKET 默认按 taker fee。

### 8.6 资金费率

首期不自动结算资金费率。资金费率需要时从 Binance 官方 REST 查询或进程内缓存，不写入 PostgreSQL。

## 9. 精度与过滤器

从 `exchangeInfo` 提取并在进程内缓存：

- `PRICE_FILTER.tickSize`
- `LOT_SIZE.stepSize`
- `LOT_SIZE.minQty`
- `MARKET_LOT_SIZE`
- `MIN_NOTIONAL.notional`
- `orderTypes`

校验规则：

- quantity 必须符合 step size。
- quantity 不得小于 min qty。
- 最新成交价格或最优盘口价格 * quantity 不得小于 min notional。
- 不支持的订单类型直接拒绝。
- 首期只允许 MARKET。

所有校验失败必须返回明确错误码和错误信息，并记录到 `system_events`。

## 10. 账户级路由设计

### 10.1 `account_type=simulated`

特征：

- 不需要 Binance API key。
- 不调用真实交易接口。
- 账户、订单、成交、仓位、账本全部由本地数据库维护。
- 行情数据仍来自 Binance 官方 REST/WebSocket/公开数据。

适用：

- 策略开发
- 本地模拟
- 回放测试
- 风控验证

### 10.2 `account_type=live`

特征：

- 使用 Binance 真实 U本位合约接口。
- 查询操作读取 Binance 真实账户、订单和仓位数据，不读取本地模拟记录。
- 查询、下单、平仓、设置杠杆都必须配置 API key 和 secret。
- 必须启用严格风控。
- 必须完整记录审计日志。

真实交易请求禁止事项：

- 禁止使用默认账户余额初始化逻辑覆盖真实账户。
- 禁止在无法确认订单状态时盲目重复下单。
- 禁止打印 secret。
- 禁止绕过 RiskService。

## 11. 错误处理与幂等

### 11.1 幂等键

每个订单必须有 `client_order_id`。生成规则建议：

```text
<sim|live>-<strategy>-<symbol>-<timestamp_ms>-<random>
```

数据库唯一约束：

```text
(account_id, client_order_id)
```

重复提交时：

- 如果本地已存在订单，返回已有订单状态。
- 如果真实交易请求本地状态不确定，先查询 Binance 订单状态。

### 11.2 Binance 异常处理

处理原则：

- 429：触发限频退避，不继续压测接口。
- 418：停止外部请求并报警。
- -1008：系统级限流，降低并发，reduce-only 平仓请求可按官方建议优先处理。
- 执行状态未知：查询订单或等待用户数据流，不立即重复下单。
- listenKey 失效：重新创建用户数据流并触发账户/订单对账。

## 12. 对账设计

`account_type=simulated`：

- 以本地 `orders`、`fills`、`ledger_entries` 为准。
- 每次成交后校验仓位、余额和账本是否平衡。

`account_type=live`：

- 不使用本地模拟交易记录作为状态来源。
- 查询订单、仓位、账户时直接调用 Binance REST 或用户数据流维护的内存状态。
- 本地数据库只保存账户配置和加密凭证，不保存真实交易记录、真实仓位快照或真实账户余额。

发现差异时：

- 返回明确错误并记录应用日志。
- 不写入模拟账户交易记录表。

## 13. 测试计划

### 13.1 单元测试

- symbol filter 校验：
  - price tick size
  - quantity step size
  - min notional
  - unsupported order type
- 订单状态机：
  - MARKET 下单即成交
  - MARKET 开多、开空
  - close-position 生成反向 reduce-only MARKET
  - 非 MARKET 订单直接拒绝
- 杠杆：
  - `account_type=simulated` 只更新本地杠杆
  - `account_type=live` 调用 `/fapi/v1/leverage`
  - 杠杆超过本地风险上限时拒绝
- 仓位计算：
  - 开多、加多、减多、反手做空
  - 开空、加空、减空、反手做多
  - 手续费扣减
  - 已实现盈亏
  - 未实现盈亏
- reduce-only：
  - 允许减仓
  - 禁止增加仓位
### 13.2 集成测试

- 使用 PostgreSQL 测试库执行完整下单、成交、账本事务。
- 模拟事务中途失败，确认订单、成交、余额、仓位全部回滚。
- 使用录制 Binance book ticker/mark price 回放撮合。
- `account_type=simulated` mock HTTP client，确认不会调用 `/fapi/v1/order` 或 `/fapi/v1/leverage`。
- `account_type=live` 查询接口调用 Binance 真实查询接口，确认不会写入本地交易记录表。
- `account_type=live` 写接口调用 Binance 真实写接口。
- `client_order_id` 重复提交返回已有订单。

### 13.3 验收标准

- `account_type=simulated` 可以在无 Binance API key 情况下运行。
- 行情与交易规则来自 Binance 官方数据。
- PostgreSQL 中能查到模拟账户的完整订单、成交、仓位、余额和账本。
- PostgreSQL 不保存 K线、行情 tick、资金费率、交易规则快照或真实账户交易记录。
- 所有金额和数量使用 Decimal/NUMERIC。
- 项目只提供 REST API，不交付前台页面、Web UI 或 CLI 交易客户端。
- 真实查询请求通过同一套 REST API 返回 Binance 真实数据。
- 真实写请求由 `account_type=live` 的账户触发，不使用额外 `LIVE_TRADING_ENABLED` 全局开关。
- 文档中的表结构、模块和流程足以指导第一版实现。

## 14. 推荐实现顺序

1. 初始化 Python 项目、配置管理、日志和 PostgreSQL 连接。
2. 建立 SQLAlchemy models 和 Alembic migrations。
3. 实现 Binance `exchangeInfo` 同步和 symbol filter 校验。
4. 实现账户初始化、余额、仓位和账本服务。
5. 实现统一对外 API，请求必须包含 `account_id`。
6. 实现 `SimulatedExchangeGateway` 和 MARKET 撮合。
7. 实现设置杠杆和 close-position。
8. 实现 Binance live 网关，通过 `account_type=live` 路由。
9. 实现回放测试和集成测试。
10. 完成真实账户对账、限频、幂等和审计日志。

## 15. 官方资料链接

- Binance USD-M Futures General Info: https://developers.binance.com/docs/derivatives/usds-margined-futures/general-info
- Exchange Information: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Exchange-Information
- Kline/Candlestick Data: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data
- Mark Price: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Mark-Price
- Funding Rate History: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History
- New Order: https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/New-Order
- Change Initial Leverage: https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Change-Initial-Leverage
- WebSocket Market Streams: https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams
- User Data Streams: https://developers.binance.com/docs/derivatives/usds-margined-futures/user-data-streams
- Order Update Event: https://developers.binance.com/docs/derivatives/usds-margined-futures/user-data-streams/Event-Order-Update
- Balance and Position Update Event: https://developers.binance.com/docs/derivatives/usds-margined-futures/user-data-streams/Event-Balance-and-Position-Update
- Binance Public Data: https://github.com/binance/binance-public-data
