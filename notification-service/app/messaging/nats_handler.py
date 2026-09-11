import json
import logging
from nats.aio.client import Client as NATSClient
from nats.aio.msg import Msg
from app.core.database import async_session_factory
from app.services.notification_service import NotificationService
from shared.messaging.subjects import SUBJECT_NOTIFICATION_LIST_V1
from shared.schemas.notification import NotificationListRPCRequest
from shared.schemas.common import ServiceResponse

logger = logging.getLogger("notification_service.nats_handler")


class NotificationNATSHandler:
    """Subscribes to NATS RPC subjects for Notification operations."""

    def __init__(self, nc: NATSClient):
        self.nc = nc

    async def register_subscriptions(self) -> None:
        """Register RPC subject subscriptions."""
        await self.nc.subscribe(SUBJECT_NOTIFICATION_LIST_V1, cb=self.handle_list_notifications)
        logger.info(f"Registered Notification Service RPC subscription on '{SUBJECT_NOTIFICATION_LIST_V1}'.")

    async def handle_list_notifications(self, msg: Msg) -> None:
        """Handle notification listing RPC request."""
        try:
            payload = json.loads(msg.data.decode("utf-8"))
            req = NotificationListRPCRequest.model_validate(payload)
            logger.info(f"Received notification list RPC request: user_id={req.user_id}, corr_id={req.correlation_id}")

            async with async_session_factory() as session:
                service = NotificationService(session)
                response = await service.get_user_notifications(req.user_id)

            await self.nc.publish(msg.reply, response.model_dump_json().encode("utf-8"))
        except Exception as e:
            logger.error(f"Error handling notification list RPC: {e}", exc_info=True)
            err_resp = ServiceResponse.fail(code="INTERNAL_ERROR", message=str(e))
            await self.nc.publish(msg.reply, err_resp.model_dump_json().encode("utf-8"))
