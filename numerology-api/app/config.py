"""Application settings loaded from environment variables via pydantic-settings."""

from typing import Annotated, Literal, Optional, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://numerology:numerology@db:5432/numerology"

    # JWT
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # App
    debug: bool = False
    allowed_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    # Frontend
    frontend_url: str = "http://localhost:3000"

    # Phase 05 additions
    media_root: str = "./media"
    media_url: str = "/media"
    static_root: str = "./static"

    # Password reset
    password_reset_token_expire_minutes: int = 30
    # Frontend path that handles ?token=<raw>
    password_reset_url_path: str = "/reset-password"

    # SMTP (optional — falls back to log when host empty)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "no-reply@numerology.local"
    smtp_use_tls: bool = True

    # SePay webhook
    sepay_api_key: str = ""
    sepay_amount_tolerance_vnd: int = 1000
    # Optional comma-separated allowlist (e.g. "1.2.3.4,5.6.7.8")
    sepay_webhook_ip_whitelist: Annotated[list[str], NoDecode] = []

    # Cloudflare Turnstile — backend secret only; leave empty to skip in dev/CI
    turnstile_secret_key: Optional[str] = None  # noqa: UP045

    # Rate limiting — disable in test env to avoid flaky tests
    rate_limit_enabled: bool = True
    # Proxy trust mode: "cloudflare" → only trust CF-Connecting-IP (recommended for prod);
    # "direct" → use request.client.host (use when traffic hits nginx directly, no Cloudflare).
    trusted_proxy_mode: Literal["cloudflare", "direct"] = "cloudflare"

    # Observability
    sentry_dsn: Optional[str] = None  # noqa: UP045
    environment: str = "production"

    # Reconcile cron window (hours to look back for pending orders + SePay tx)
    reconcile_window_hours: int = 24

    # Bank info (for QR + checkout display) — fill via env in production
    bank_account_number: str = ""
    bank_account_holder: str = ""
    bank_code: str = ""  # vd "VCB", "MB", "ACB" — SePay bank code
    bank_name: str = ""

    embedding_model: str = "text-embedding-004"  # chat RAG embeddings, 768-dim

    # Google genai auth (chat embeddings + report image generation) — Vertex AI
    # via service account (runs on GCP billing). Set google_application_credentials
    # to the service-account JSON path; project is read from the JSON if
    # google_cloud_project is blank.
    google_application_credentials: str = ""
    google_cloud_project: str = ""
    google_cloud_location: str = "us-central1"
    report_image_model: str = "imagen-4.0-generate-001"

    # DeepSeek — chat generation (OpenAI-compatible API)
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_chat_model: str = "deepseek-chat"
    # Embedding batch & chunking
    embedding_batch_size: int = 100
    chunk_max_tokens: int = 500
    chunk_overlap_tokens: int = 50
    # Chat quota (Phase 05)
    chat_free_daily_limit: int = 3

    # RAG retrieval (Phase 02)
    rag_top_k_free: int = 3
    rag_top_k_paid: int = 8
    rag_sim_threshold: float = 0.6  # min cosine similarity (1 - distance)
    history_max_messages: int = 5   # last N conversation messages in prompt
    llm_timeout_seconds: int = 30

    # Semantic cache (Phase 06)
    semantic_cache_threshold: float = 0.92   # min cosine similarity for cache hit
    semantic_cache_ttl_hours: int = 24        # TTL for cached answers

    # Rate limit — token bucket (Phase 06)
    # Free tier: 1 msg/10s sustained, 100/day
    rate_limit_free_capacity: float = 1.0
    rate_limit_free_refill_per_sec: float = 0.1
    rate_limit_free_daily_cap: int = 100
    # Pro tier: 1 msg/3s sustained, 1000/day
    rate_limit_pro_capacity: float = 1.0
    rate_limit_pro_refill_per_sec: float = 0.33
    rate_limit_pro_daily_cap: int = 1000
    # IP-wide limit: 5 burst, 50/day
    rate_limit_ip_capacity: float = 5.0
    rate_limit_ip_refill_per_sec: float = 0.05
    rate_limit_ip_daily_cap: int = 50

    @field_validator("sepay_webhook_ip_whitelist", mode="before")
    @classmethod
    def parse_ip_whitelist(cls, v: Union[str, list[str]]) -> list[str]:  # noqa: UP007
        if isinstance(v, str):
            return [ip.strip() for ip in v.split(",") if ip.strip()]
        return v

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: Union[str, list[str]]) -> list[str]:  # noqa: UP007
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


settings = Settings()
