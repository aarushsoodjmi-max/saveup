import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    achievements,
    admin,
    auth,
    challenges,
    dashboard,
    emergency_contacts,
    goals,
    notifications,
    payments,
    transactions,
    users,
    withdrawals,
)
from app.core.config import settings
from app.core.error_handlers import register_exception_handlers
from app.core.middleware import RequestContextMiddleware, configure_logging
from app.core import redis as redis_module
from app.core.database import engine

configure_logging(settings.log_level)
logger = logging.getLogger("saveup.startup")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup: verify (but don't hard-fail on) DB/Redis connectivity so
    # a misconfigured deployment is loud in the logs immediately rather
    # than surfacing as a mysterious 500 on the first request.
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        logger.info("Database connection OK")
    except Exception:
        logger.exception("Database connection FAILED at startup")

    if redis_module.ping():
        logger.info("Redis connection OK")
    else:
        logger.error("Redis connection FAILED at startup")

    logger.info("%s v%s starting in %s mode", settings.app_name, settings.app_version, settings.environment)
    yield
    logger.info("%s shutting down", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# --- Middleware (order matters: outermost added last is outermost) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)

# --- Exception handlers ---
register_exception_handlers(app)

# --- Routers ---
API_PREFIX = settings.api_v1_prefix
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(goals.router, prefix=API_PREFIX)
app.include_router(emergency_contacts.router, prefix=API_PREFIX)
app.include_router(payments.router, prefix=API_PREFIX)
app.include_router(transactions.router, prefix=API_PREFIX)
app.include_router(withdrawals.router, prefix=API_PREFIX)
app.include_router(notifications.router, prefix=API_PREFIX)
app.include_router(achievements.router, prefix=API_PREFIX)
app.include_router(challenges.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {"message": "SaveUp API is running 🚀", "version": settings.app_version}


@app.get("/health")
def health_check():
    """Liveness + dependency check: verifies the app can actually reach
    MySQL and Redis, not just that the process is up.
    """
    db_ok = True
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
    except Exception:
        db_ok = False

    redis_ok = redis_module.ping()

    status = "ok" if (db_ok and redis_ok) else "degraded"
    return {
        "status": status,
        "database": "up" if db_ok else "down",
        "redis": "up" if redis_ok else "down",
        "version": settings.app_version,
        "environment": settings.environment,
    }
