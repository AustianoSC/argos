from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ARGOS_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"

    # Database
    database_url: str = "postgresql+asyncpg://argos:argos_dev@localhost:5432/argos"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # LLM (via LiteLLM proxy)
    litellm_base_url: str = "http://localhost:4000"
    litellm_api_key: str = "sk-unused"  # LiteLLM handles upstream auth
    match_model: str = "match-model"
    extract_model: str = "extract-model"

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
