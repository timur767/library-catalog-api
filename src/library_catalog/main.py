"""
Точка входа FastAPI приложения Library Catalog.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .core.config import settings
from .core.database import dispose_engine, init_db
from .core.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db()
    yield
    await dispose_engine()


app = FastAPI(
    title=settings.app_name,
    description="REST API для управления библиотечным каталогом",
    version="1.0.0",
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {"message": "Welcome to Library Catalog API"}


@app.get("/health")
async def health_check():
    """Health check эндпоинт."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
