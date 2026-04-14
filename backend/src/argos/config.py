from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ARGOS_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Database
    database_url: str = "postgresql+asyncpg://argos:argos_dev@localhost:5432/argos"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # LLM
    anthropic_api_key: str = ""
    match_model: str = "claude-sonnet-4-20250514"
    extract_model: str = "claude-haiku-4-5-20251001"

    # Search
    search_max_results: int = 10
    search_blocked_domains: list[str] = [
        "reddit.com",
        "youtube.com",
        "quora.com",
        "twitter.com",
        "facebook.com",
    ]

    # Fetcher
    fetch_timeout: int = 15
    js_heavy_domains: list[str] = ["amazon.com", "walmart.com", "bestbuy.com", "target.com"]

    # Scheduler
    check_interval_hours: int = 6

    # Alerts
    alert_price_drop_pct: float = 5.0
    discord_webhook_url: str = ""


settings = Settings()
