from uuid import UUID
from fastapi import APIRouter, Request, status, Depends
from app.core.security import get_current_user, AuthenticatedUser
from app.schemas.notification import NotificationListResponse
from app.clients.nats_client import GatewayNATSDispatcher
from shared.messaging.subjects import SUBJECT_NOTIFICATION_LIST_V1
from shared.schemas.notification import NotificationListRPCRequest

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_dispatcher(request: Request) -> GatewayNATSDispatcher:
    return request.app.state.nats_dispatcher


@router.get(
    "/{user_id}",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user notifications (Protected)",
    description="Requires a valid Bearer JWT. Retrieves asynchronous notification records for the user from Notification Service via NATS RPC.",
)
async def get_user_notifications(
    user_id: UUID,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    dispatcher: GatewayNATSDispatcher = Depends(get_dispatcher),
) -> NotificationListResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    rpc_payload = NotificationListRPCRequest(
        user_id=user_id,
        correlation_id=correlation_id,
    )

    notifications_data = await dispatcher.call(SUBJECT_NOTIFICATION_LIST_V1, rpc_payload)
    return NotificationListResponse.model_validate(notifications_data)
