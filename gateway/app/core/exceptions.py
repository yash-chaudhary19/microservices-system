import logging
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
import nats.errors

logger = logging.getLogger("gateway.exceptions")


def service_error_to_http_status(error_code: str) -> int:
    """Map internal service error codes to HTTP status codes."""
    mapping = {
        "USER_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "EMAIL_ALREADY_EXISTS": status.HTTP_409_CONFLICT,
        "INVALID_CREDENTIALS": status.HTTP_401_UNAUTHORIZED,
        "INVALID_INPUT": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
    }
    return mapping.get(error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format Pydantic request validation errors cleanly."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.warning(f"[{correlation_id}] Request validation error: {exc.errors()}")
    return JSONResponse(
        status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The request body or parameters failed validation.",
                "details": exc.errors(),
            }
        },
    )


async def nats_timeout_exception_handler(request: Request, exc: nats.errors.TimeoutError):
    """Handle NATS RPC timeouts."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.error(f"[{correlation_id}] Internal service timeout: {exc}")
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={
            "error": {
                "code": "SERVICE_TIMEOUT",
                "message": "The downstream service timed out while processing your request.",
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all handler hiding internal stack traces from clients."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.error(f"[{correlation_id}] Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            }
        },
    )
