from fastapi import APIRouter, status as http_status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from ...dependencies import DbSessionDep

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/", summary="Health Check", description="Проверить состояние сервиса и подключение к БД")
async def health_check(db: DbSessionDep):
    """
    Проверить здоровье сервиса.

    Проверяет:
    - Сервис запущен
    - Подключение к БД работает
    """
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    status_str = "healthy" if db_ok else "unhealthy"
    db_str = "connected" if db_ok else "disconnected"
    http_code = http_status.HTTP_200_OK if db_ok else http_status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=http_code,
        content={"status": status_str, "database": db_str},
    )
