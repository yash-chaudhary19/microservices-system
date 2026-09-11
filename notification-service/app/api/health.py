from fastapi import APIRouter, status, Response
from sqlalchemy import text
from app.core.database import async_session_factory

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    """Basic liveness probe."""
    return {"status": "ok", "service": "notification-service"}


@router.get("/ready")
async def readiness_check(response: Response) -> dict[str, str]:
    """Readiness probe checking database connectivity."""
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "service": "notification-service", "database": "connected"}
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", "service": "notification-service", "error": str(e)}
