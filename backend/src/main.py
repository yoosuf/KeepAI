import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request as StarletteRequest
from starlette.responses import JSONResponse

from src.core.config import settings
from src.core.database import engine, get_db
from src.core.logging_config import setup_logging
from src.core.middleware import RequestIDMiddleware
from src.core.rate_limit import limiter
from src.infrastructure.llm.ollama_client import OllamaClient
from src.modules.admin import router as admin_router
from src.modules.analytics import router as analytics_router
from src.modules.api_keys import router as api_keys_router
from src.modules.auth import router as auth_router
from src.modules.conversations import router as conversations_router
from src.modules.documents import router as documents_router
from src.modules.models import router as models_router
from src.modules.prompts import router as prompts_router
from src.modules.ws import router as ws_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting up...")

    # Singleton LLM client — one connection pool shared across all requests
    app.state.llm_client = OllamaClient(base_url=settings.OLLAMA_BASE_URL)

    yield

    logger.info("Shutting down...")
    await app.state.llm_client.close()
    await engine.dispose()  # drain DB pool gracefully


app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)

# Rate limiter
app.state.limiter = limiter


async def rate_limit_handler(request: StarletteRequest, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Please slow down."})


app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Middleware (outermost registered last, executes first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)

# Routers
app.include_router(auth_router.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(admin_router.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(models_router.router, prefix=f"{settings.API_V1_STR}/models", tags=["models"])
app.include_router(prompts_router.router, prefix=f"{settings.API_V1_STR}", tags=["prompts"])
app.include_router(conversations_router.router, prefix=f"{settings.API_V1_STR}", tags=["conversations"])
app.include_router(api_keys_router.router, prefix=f"{settings.API_V1_STR}", tags=["api-keys"])
app.include_router(analytics_router.router, prefix=f"{settings.API_V1_STR}", tags=["analytics"])
app.include_router(documents_router.router, prefix=f"{settings.API_V1_STR}", tags=["documents"])
app.include_router(ws_router.router, prefix="", tags=["websocket"])


@app.get("/health/live", tags=["health"])
async def liveness():
    """Liveness probe — always 200 if the process is running."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
async def readiness(db: AsyncSession = Depends(get_db)):
    """Readiness probe — verifies DB and LLM connectivity before accepting traffic."""
    errors: dict = {}

    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        errors["db"] = str(e)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
    except Exception as e:
        errors["llm"] = str(e)

    if errors:
        raise HTTPException(status_code=503, detail={"status": "unavailable", **errors})

    return {"status": "ready", "db": "ok", "llm": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEV_MODE,
        loop="uvloop",
        http="httptools",
    )
