import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

import app.models.models  # ensure models are registered with Base.metadata
from app.api.agent import router as agent_router
from app.api.analytics import router as analytics_router
from app.api.health import router as health_router
from app.api.insights import router as insights_router
from app.api.observability import router as observability_router
from app.api.privacy import router as privacy_router
from app.api.statements import router as statements_router
from app.api.transactions import router as transactions_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.privacy import PrivacyHeadersMiddleware, setup_privacy_logging
from app.core.telemetry import ObservabilityMiddleware, correlation_id_ctx

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure privacy filter on logging
    setup_privacy_logging()
    # Ensure database schema tables exist on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="FinLens AI Production Backend & Financial Intelligence Engine",
    lifespan=lifespan,
)

# Observability Middleware (measures duration, sets correlation ID, tracks metrics)
app.add_middleware(ObservabilityMiddleware)

# Privacy & Security Headers Middleware (zero-retention headers)
app.add_middleware(PrivacyHeadersMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Centralized Error Handlers (Prevents raw tracebacks / DB schema leaking)
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    cid = correlation_id_ctx.get() or "none"
    logger.error("Database query failure [cid=%s]: %s", cid, str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "detail": "A secure database error occurred. Internal database details are protected.",
            "correlation_id": cid,
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    cid = correlation_id_ctx.get() or "none"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "correlation_id": cid,
        },
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    cid = correlation_id_ctx.get() or "none"
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "correlation_id": cid,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    cid = correlation_id_ctx.get() or "none"
    logger.error("Unhandled server exception [cid=%s]: %s", cid, str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred.",
            "correlation_id": cid,
        },
    )


# Routers
app.include_router(health_router)
app.include_router(statements_router, prefix=settings.API_V1_PREFIX)
app.include_router(transactions_router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)
app.include_router(agent_router, prefix=settings.API_V1_PREFIX)
app.include_router(insights_router, prefix=settings.API_V1_PREFIX)
app.include_router(privacy_router, prefix=settings.API_V1_PREFIX)
app.include_router(observability_router, prefix=settings.API_V1_PREFIX)
app.include_router(observability_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "app": settings.PROJECT_NAME,
        "tagline": "Understand Your Spending with AI",
        "status": "online",
        "docs_url": "/docs",
    }
