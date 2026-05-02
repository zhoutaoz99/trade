# Backend

币安 USDⓈ-M 合约模拟交易系统后端，基于 FastAPI + SQLAlchemy (async) + PostgreSQL。

## 环境要求

- Python 3.11+
- PostgreSQL 16+

## 一、配置 PostgreSQL

`.env` 中的 `DATABASE_URL` 格式：

```
postgresql+asyncpg://用户名:密码@主机:端口/数据库名
```

本项目默认值：`postgresql+asyncpg://trade:trade_password@localhost:5432/trade`

| 部分 | 值 | 含义 |
|------|-----|------|
| 协议/驱动 | `postgresql+asyncpg` | SQLAlchemy 异步方言，底层使用 asyncpg |
| 用户名 | `trade` | 数据库登录用户 |
| 密码 | `trade_password` | 登录密码 |
| 主机 | `localhost` | 数据库运行在本机 |
| 端口 | `5432` | PostgreSQL 默认端口 |
| 数据库名 | `trade` | 连接的目标数据库 |

### 命令行初始化

```bash
# 创建登录角色
sudo -u postgres psql -c "CREATE USER trade WITH PASSWORD 'trade_password';"

# 创建数据库并指定 owner
sudo -u postgres psql -c "CREATE DATABASE trade OWNER trade;"
```

### 验证连接

```bash
psql 'postgresql://trade:trade_password@localhost:5432/trade'
```

进入 `trade=>` 提示符即表示配置成功。

### 认证问题排查

如果连接时报 `FATAL: password authentication failed`，说明 `pg_hba.conf` 未允许密码登录：

**macOS (Homebrew)：**

```bash
psql -U postgres -c "SHOW hba_file;"
# 编辑文件，将 local 连接的认证方式从 peer 改为 md5，然后重启
brew services restart postgresql@16
```

**Linux (apt)：**

```bash
sudo sed -i.bak 's/local\s\+all\s\+all\s\+peer/local   all   all   md5/' \
  /etc/postgresql/*/main/pg_hba.conf
sudo systemctl restart postgresql
```

## 二、启动

```bash
# 1. 创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# 2. 配置环境变量（如 .env 不存在）
cp .env.example .env

# 3. 运行数据库迁移
alembic upgrade head

# 4. 启动服务（端口 8000，开启热重载）
uvicorn app.main:app --reload
```

启动后 API 文档可通过 `http://localhost:8000/docs` 访问。

## 运行测试

```bash
pytest
```

## 环境变量参考

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `APP_ENV` | 运行环境 | `dev` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `DATABASE_URL` | 数据库连接串 | 见上 |
| `BINANCE_API_KEY` | 币安 API Key | (可选) |
| `BINANCE_API_SECRET` | 币安 API Secret | (可选) |
| `DEFAULT_QUOTE_ASSET` | 基准计价资产 | `USDT` |
| `DEFAULT_ACCOUNT_INITIAL_BALANCE` | 账户初始余额 | `10000` |
| `DEFAULT_TAKER_FEE_RATE` | Taker 手续费率 | `0.0005` |
| `DEFAULT_MAKER_FEE_RATE` | Maker 手续费率 | `0.0002` |
| `DEFAULT_SLIPPAGE_BPS` | 默认滑点 (bps) | `2` |
| `RISK_MAX_LEVERAGE` | 最大杠杆倍数 | `10` |
| `RISK_MAX_POSITION_NOTIONAL` | 最大持仓名义价值 | `50000` |
| `RISK_MAX_ORDER_NOTIONAL` | 最大订单名义价值 | `10000` |
| `SECRET_KEY` | 应用密钥 | 生产环境务必更换 |
