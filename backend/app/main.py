"""
FastAPI application entry point.

Note: accounts router was previously imported but never registered via
app.include_router, so /account/signup was returning 404 for all calls.
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api import transactions, admin, accounts     # accounts was unused before
from app.models.database import init_db, create_next_month_partition

try:
    from app.services.fraud_service import FraudService, get_redis
    HAS_FRAUD_SERVICE = True
except ImportError:
    HAS_FRAUD_SERVICE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Rate Limiter
# ─────────────────────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing PostgreSQL connection pool…")
    await init_db()

    try:
        await create_next_month_partition()
        logger.info("Monthly partition check complete.")
    except Exception as e:
        logger.warning(f"Partition auto-creation skipped: {e}")

    try:
        r = get_redis()
        await r.ping()
        logger.info("Redis connection verified.")
    except Exception as e:
        logger.warning(f"Redis unavailable at startup: {e}")

    if HAS_FRAUD_SERVICE:
        logger.info("Warming up ML Inference Engine…")
        try:
            FraudService.load_models()
            logger.info("ML models loaded.")
        except Exception as e:
            logger.error(f"ML models failed to load: {e}")
    else:
        logger.warning("FraudService not available. Running in DB-only mode.")

    logger.info("Server ready.")
    yield
    logger.info("⏹️  Shutting down gracefully…")


# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="FraudGuard",
    description="Transaction processing with PostgreSQL ledger and ML fraud detection.",
    version="2.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: read from env var — never hardcode allow_origins=["*"] in production
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS")
if not allowed_origins_raw:
    raise RuntimeError(
        "ALLOWED_ORIGINS environment variable is not set. "
        "Set it to a comma-separated list of allowed frontend origins."
    )
allowed_origins = allowed_origins_raw.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)

app.include_router(transactions.router)
app.include_router(admin.router)
app.include_router(accounts.router)


@app.get("/health", tags=["System Health"])
async def health_check():
    """Uptime + capability ping for load balancer and monitoring."""
    return {
        "status":           "online",
        "service":          "fraudguard",
        "version":          "2.0.0",
        "ml_engine_active": HAS_FRAUD_SERVICE,
    }
