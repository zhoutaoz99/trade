"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from decimal import Decimal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_env: str = "dev"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://trade:trade_password@localhost:5432/trade"

    # Binance
    binance_api_key: str = ""
    binance_api_secret: str = ""
    binance_recv_window: int = 5000
    binance_rest_base_url: str = "https://fapi.binance.com"
    binance_ws_base_url: str = "wss://fstream.binance.com"
    binance_verify_ssl: bool = True  # 公司网络有 TLS 代理时可设为 False

    # Trading defaults
    default_quote_asset: str = "USDT"
    default_account_initial_balance: Decimal = Decimal("10000")
    default_taker_fee_rate: Decimal = Decimal("0.0005")
    default_maker_fee_rate: Decimal = Decimal("0.0002")
    default_slippage_bps: int = 2  # basis points, 2 = 0.02%

    # Risk limits
    risk_max_leverage: int = 10
    risk_max_position_notional: Decimal = Decimal("50000")
    risk_max_order_notional: Decimal = Decimal("10000")

    # Encryption
    secret_key: str = "change-me-in-production-use-a-real-secret-key"


settings = Settings()
