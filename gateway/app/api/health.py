from fastapi import APIRouter, status, Response, Request
import nats.errors

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    """Basic liveness probe."""
    return {"status": "ok", "service": "api-gateway"}


@router.get("/ready")
async def readiness_check(request: Request, response: Response) -> dict[str, str]:
    """Readiness probe checking NATS connectivity."""
    nats_manager = request.app.state.nats_manager
    if not nats_manager or not nats_manager.nc or nats_manager.nc.is_closed:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", "service": "api-gateway", "nats": "disconnected"}

    return {"status": "ready", "service": "api-gateway", "nats": "connected"}
