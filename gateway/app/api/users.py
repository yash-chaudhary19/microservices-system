from uuid import UUID
from fastapi import APIRouter, Request, status, Depends
from app.core.security import get_current_user, AuthenticatedUser
from app.schemas.user import CreateUserRequest, UserResponse
from app.clients.nats_client import GatewayNATSDispatcher
from shared.messaging.subjects import SUBJECT_USER_CREATE_V1, SUBJECT_USER_GET_V1
from shared.schemas.user import UserCreateRPCRequest, UserGetRPCRequest

router = APIRouter(prefix="/users", tags=["Users"])


def get_dispatcher(request: Request) -> GatewayNATSDispatcher:
    return request.app.state.nats_dispatcher


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user (Protected)",
    description="Requires a valid Bearer JWT. Dispatches user creation via NATS RPC to User Service.",
)
async def create_user(
    req: CreateUserRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    dispatcher: GatewayNATSDispatcher = Depends(get_dispatcher),
) -> UserResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    rpc_payload = UserCreateRPCRequest(
        name=req.name,
        email=req.email,
        password=req.password,
        correlation_id=correlation_id,
    )

    user_data = await dispatcher.call(SUBJECT_USER_CREATE_V1, rpc_payload)
    return UserResponse.model_validate(user_data)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user profile by ID (Protected)",
    description="Requires a valid Bearer JWT. Retrieves user information via NATS RPC from User Service.",
)
async def get_user_by_id(
    user_id: UUID,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    dispatcher: GatewayNATSDispatcher = Depends(get_dispatcher),
) -> UserResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    rpc_payload = UserGetRPCRequest(
        user_id=user_id,
        correlation_id=correlation_id,
    )

    user_data = await dispatcher.call(SUBJECT_USER_GET_V1, rpc_payload)
    return UserResponse.model_validate(user_data)
