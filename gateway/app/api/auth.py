from fastapi import APIRouter, Request, status, Depends
from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.auth import RegisterRequest, LoginRequest, AuthTokenResponse, UserSummary
from app.clients.nats_client import GatewayNATSDispatcher
from shared.messaging.subjects import SUBJECT_USER_CREATE_V1, SUBJECT_USER_AUTHENTICATE_V1
from shared.schemas.user import UserCreateRPCRequest, UserAuthenticateRPCRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_dispatcher(request: Request) -> GatewayNATSDispatcher:
    """Dependency injecting Gateway NATS dispatcher from app state."""
    return request.app.state.nats_dispatcher


@router.post(
    "/register",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Validates input, dispatches creation command to User Service via NATS, and issues a JWT token.",
)
async def register(
    req: RegisterRequest,
    request: Request,
    dispatcher: GatewayNATSDispatcher = Depends(get_dispatcher),
) -> AuthTokenResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    rpc_payload = UserCreateRPCRequest(
        name=req.name,
        email=req.email,
        password=req.password,
        correlation_id=correlation_id,
    )

    user_data = await dispatcher.call(SUBJECT_USER_CREATE_V1, rpc_payload)

    # Generate JWT
    token = create_access_token(
        user_id=user_data["id"],
        email=user_data["email"],
    )

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
        user=UserSummary(
            id=user_data["id"],
            name=user_data["name"],
            email=user_data["email"],
        ),
    )


@router.post(
    "/login",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and receive JWT token",
    description="Verifies user credentials against User Service via NATS RPC and issues a JWT token.",
)
async def login(
    req: LoginRequest,
    request: Request,
    dispatcher: GatewayNATSDispatcher = Depends(get_dispatcher),
) -> AuthTokenResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    rpc_payload = UserAuthenticateRPCRequest(
        email=req.email,
        password=req.password,
        correlation_id=correlation_id,
    )

    user_data = await dispatcher.call(SUBJECT_USER_AUTHENTICATE_V1, rpc_payload)

    # Generate JWT
    token = create_access_token(
        user_id=user_data["id"],
        email=user_data["email"],
    )

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
        user=UserSummary(
            id=user_data["id"],
            name=user_data["name"],
            email=user_data["email"],
        ),
    )
