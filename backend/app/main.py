from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
import app.models.models  # ensure models are registered with Base.metadata
from app.api.health import router as health_router
from app.api.statements import router as statements_router
from app.api.transactions import router as transactions_router
from app.api.analytics import router as analytics_router
from app.api.agent import router as agent_router
from app.api.insights import router as insights_router


@asynccontextmanager
async def lifespan(app: FastAPI):
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

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router)
app.include_router(statements_router, prefix=settings.API_V1_PREFIX)
app.include_router(transactions_router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)
app.include_router(agent_router, prefix=settings.API_V1_PREFIX)
app.include_router(insights_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "app": settings.PROJECT_NAME,
        "tagline": "Understand Your Spending with AI",
        "status": "online",
        "docs_url": "/docs",
    }
