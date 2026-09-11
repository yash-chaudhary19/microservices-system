import logging
from typing import Any
from fastapi import HTTPException
from app.core.config import settings
from app.core.exceptions import service_error_to_http_status
from shared.messaging.nats_client import NATSManager
from shared.schemas.common import ServiceResponse

logger = logging.getLogger("gateway.nats_client")


class GatewayNATSDispatcher:
    """Dispatches HTTP requests to internal microservices via NATS Request/Reply."""

    def __init__(self, nats_manager: NATSManager):
        self.nats_manager = nats_manager

    async def call(
        self,
        subject: str,
        payload: Any,
        timeout: float | None = None,
    ) -> Any:
        """Send RPC request to NATS subject and unpack ServiceResponse."""
        if timeout is None:
            timeout = settings.NATS_REQUEST_TIMEOUT_SECONDS

        raw_response = await self.nats_manager.request(
            subject=subject,
            payload=payload,
            timeout=timeout,
        )

        response = ServiceResponse.model_validate(raw_response)

        if not response.success:
            err = response.error
            status_code = service_error_to_http_status(err.code if err else "INTERNAL_ERROR")
            raise HTTPException(
                status_code=status_code,
                detail={
                    "code": err.code if err else "INTERNAL_ERROR",
                    "message": err.message if err else "An error occurred",
                    "details": err.details if err else None,
                },
            )

        return response.data
