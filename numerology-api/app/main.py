"""FastAPI application factory with CORS, static media, and all routers."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.jobs import scheduler as job_scheduler
from app.middleware.rate_limit import limiter

# ---------------------------------------------------------------------------
# Sentry — init before app creation so all exceptions are captured.
# Skipped when SENTRY_DSN is empty (local dev / CI).
# ---------------------------------------------------------------------------
if settings.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    def _before_send(event: dict, hint: dict) -> dict | None:
        """Filter out 4xx client errors and health-check noise."""
        exc_info = hint.get("exc_info")
        if exc_info:
            from fastapi import HTTPException as _HTTPException
            exc = exc_info[1]
            if isinstance(exc, _HTTPException) and exc.status_code < 500:
                return None
        # Drop events from health endpoints
        request = event.get("request", {})
        url = request.get("url", "")
        if "/health" in url:
            return None
        return event

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.1,
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
        ],
        before_send=_before_send,
    )
    logging.getLogger(__name__).info("Sentry initialized (env=%s)", settings.environment)

logger = logging.getLogger(__name__)
from app.routers.admin import admin_router
from app.routers.auth import router as auth_router
from app.routers.chat import addons_router as chat_addons_router
from app.routers.chat import conversations_router as chat_conversations_router
from app.routers.chat import messages_router as chat_messages_router
from app.routers.chat import pdf_upload_router as chat_pdf_upload_router
from app.routers.chat import quota_router as chat_quota_router
from app.routers.banks import banks_router
from app.routers.news import news_router
from app.routers.numerology import numerology_router
from app.routers.orders import orders_router
from app.routers.packages import packages_router
from app.routers.payments import payments_router
from app.routers.profile import profile_router
from app.routers.my_account import my_account_router
from app.routers.health import health_router
from app.routers.shop import shop_router
from app.routers.webhooks import webhooks_router


def _assert_production_config() -> None:
    """Fail fast if required production settings are missing."""
    if settings.environment == "production":
        if not settings.turnstile_secret_key:
            raise RuntimeError(
                "TURNSTILE_SECRET_KEY must be set in production. "
                "Leave ENVIRONMENT=development to skip CAPTCHA in dev/CI."
            )


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Start background scheduler at boot, stop it cleanly on shutdown."""
    _assert_production_config()
    try:
        job_scheduler.start()
    except Exception:  # noqa: BLE001
        logger.exception("Scheduler failed to start; continuing without jobs")
    # Wire KB auto-sync listeners — only when a Gemini key is configured,
    # so dev/CI without the key boots cleanly.
    kb_enabled = bool(settings.gemini_api_key)
    if kb_enabled:
        try:
            from app.db.models import numerology_content as _nc
            from app.services.chat.kb_sync import register_kb_sync_listeners
            register_kb_sync_listeners([
                getattr(_nc, name) for name in _nc.__all__ if name != "PhoneMasterDataModel"
            ])
        except Exception:  # noqa: BLE001
            logger.exception("kb_sync listener registration failed")
            kb_enabled = False
    yield
    if kb_enabled:
        try:
            from app.services.chat.kb_sync import shutdown_kb_sync
            await shutdown_kb_sync()
        except Exception:  # noqa: BLE001
            logger.exception("kb_sync shutdown error")
    try:
        job_scheduler.shutdown()
    except Exception:  # noqa: BLE001
        logger.exception("Scheduler shutdown error")


def create_app() -> FastAPI:
    application = FastAPI(
        title="Numerology API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=_lifespan,
    )

    # Attach limiter state so slowapi can read it per-request
    application.state.limiter = limiter

    # 429 JSON handler — returns {"error": "Rate limit exceeded: ..."} consistently
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # slowapi middleware must be added before CORS to intercept early
    if settings.rate_limit_enabled:
        application.add_middleware(SlowAPIMiddleware)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(profile_router)
    application.include_router(news_router)
    application.include_router(packages_router)
    application.include_router(banks_router)
    application.include_router(payments_router)
    application.include_router(numerology_router)
    application.include_router(shop_router)
    application.include_router(orders_router)
    application.include_router(webhooks_router)
    application.include_router(my_account_router)
    application.include_router(chat_conversations_router)
    application.include_router(chat_messages_router)
    application.include_router(chat_pdf_upload_router)
    application.include_router(chat_addons_router)
    application.include_router(chat_quota_router)
    application.include_router(admin_router)

    os.makedirs(settings.media_root, exist_ok=True)
    application.mount(
        "/media",
        StaticFiles(directory=settings.media_root),
        name="media",
    )

    return application


app = create_app()
