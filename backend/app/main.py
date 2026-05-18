from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.router import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.core.redis import close_redis, get_redis

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await get_redis()

    if settings.SEED_ON_STARTUP:
        from app.core.database import async_session_factory
        from app.db.seed import seed_database

        async with async_session_factory() as session:
            result = await seed_database(session)
            logger.info("Seed complete: {}", result)

    yield
    await close_redis()


app = FastAPI(
    title="EventLens AH",
    description="AI-powered event research system for A-share and Hong Kong stock markets",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
