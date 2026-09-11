import json
import logging
from uuid import UUID
from nats.aio.client import Client as NATSClient
from nats.aio.msg import Msg
from app.core.database import async_session_factory
from app.services.user_service import UserService
from app.messaging.event_publisher import EventPublisher
from shared.messaging.subjects import (
    SUBJECT_USER_CREATE_V1,
    SUBJECT_USER_GET_V1,
    SUBJECT_USER_AUTHENTICATE_V1,
)
from shared.schemas.user import (
    UserCreateRPCRequest,
    UserGetRPCRequest,
    UserAuthenticateRPCRequest,
)
from shared.schemas.common import ServiceResponse

logger = logging.getLogger("user_service.nats_handler")


class UserNATSHandler:
    """Subscribes to NATS RPC subjects for User operations."""

    def __init__(self, nc: NATSClient, event_publisher: EventPublisher):
        self.nc = nc
        self.event_publisher = event_publisher

    async def register_subscriptions(self) -> None:
        """Register RPC subject subscriptions."""
        await self.nc.subscribe(SUBJECT_USER_CREATE_V1, cb=self.handle_user_create)
        await self.nc.subscribe(SUBJECT_USER_GET_V1, cb=self.handle_user_get)
        await self.nc.subscribe(SUBJECT_USER_AUTHENTICATE_V1, cb=self.handle_user_authenticate)
        logger.info("Registered User Service NATS RPC subscriptions.")

    async def handle_user_create(self, msg: Msg) -> None:
        """Handle user creation RPC."""
        try:
            payload = json.loads(msg.data.decode("utf-8"))
            req = UserCreateRPCRequest.model_validate(payload)
            logger.info(f"Received user creation RPC request: email={req.email}, corr_id={req.correlation_id}")

            async with async_session_factory() as session:
                service = UserService(session, self.event_publisher)
                response = await service.create_user(req)

            await self.nc.publish(msg.reply, response.model_dump_json().encode("utf-8"))
        except Exception as e:
            logger.error(f"Error handling user create RPC: {e}", exc_info=True)
            err_resp = ServiceResponse.fail(code="INTERNAL_ERROR", message=str(e))
            await self.nc.publish(msg.reply, err_resp.model_dump_json().encode("utf-8"))

    async def handle_user_get(self, msg: Msg) -> None:
        """Handle user retrieval RPC."""
        try:
            payload = json.loads(msg.data.decode("utf-8"))
            req = UserGetRPCRequest.model_validate(payload)
            logger.info(f"Received user retrieval RPC request: user_id={req.user_id}")

            async with async_session_factory() as session:
                service = UserService(session)
                response = await service.get_user(req.user_id)

            await self.nc.publish(msg.reply, response.model_dump_json().encode("utf-8"))
        except Exception as e:
            logger.error(f"Error handling user get RPC: {e}", exc_info=True)
            err_resp = ServiceResponse.fail(code="INTERNAL_ERROR", message=str(e))
            await self.nc.publish(msg.reply, err_resp.model_dump_json().encode("utf-8"))

    async def handle_user_authenticate(self, msg: Msg) -> None:
        """Handle user authentication RPC."""
        try:
            payload = json.loads(msg.data.decode("utf-8"))
            req = UserAuthenticateRPCRequest.model_validate(payload)
            logger.info(f"Received user authentication RPC request: email={req.email}")

            async with async_session_factory() as session:
                service = UserService(session)
                response = await service.authenticate_user(req.email, req.password)

            await self.nc.publish(msg.reply, response.model_dump_json().encode("utf-8"))
        except Exception as e:
            logger.error(f"Error handling user authenticate RPC: {e}", exc_info=True)
            err_resp = ServiceResponse.fail(code="INTERNAL_ERROR", message=str(e))
            await self.nc.publish(msg.reply, err_resp.model_dump_json().encode("utf-8"))
