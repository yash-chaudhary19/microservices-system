import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password
from app.messaging.event_publisher import EventPublisher
from shared.events.user_events import UserCreatedEventV1
from shared.schemas.user import (
    UserCreateRPCRequest,
    UserDTO,
    UserAuthResultDTO,
)
from shared.schemas.common import ServiceResponse

logger = logging.getLogger("user_service.service")


class UserService:
    """Core domain logic for User Service."""

    def __init__(self, session: AsyncSession, event_publisher: EventPublisher | None = None):
        self.repo = UserRepository(session)
        self.event_publisher = event_publisher

    async def create_user(self, req: UserCreateRPCRequest) -> ServiceResponse[UserDTO]:
        """Validate, hash password, persist user, and publish UserCreated event."""
        # 1. Check duplicate email
        existing = await self.repo.get_by_email(req.email)
        if existing:
            logger.warning(f"Registration failed: email '{req.email}' already exists.")
            return ServiceResponse.fail(
                code="EMAIL_ALREADY_EXISTS",
                message=f"A user with email '{req.email}' already exists.",
            )

        # 2. Hash password
        pwd_hash = hash_password(req.password)

        # 3. Persist to DB
        user = await self.repo.create(
            name=req.name,
            email=req.email,
            password_hash=pwd_hash,
        )
        logger.info(f"User created in database: id={user.id}, email={user.email}")

        # 4. Asynchronously publish UserCreated event to NATS JetStream
        if self.event_publisher:
            try:
                event = UserCreatedEventV1(
                    user_id=user.id,
                    email=user.email,
                    name=user.name,
                    correlation_id=req.correlation_id,
                )
                await self.event_publisher.publish_user_created(event)
            except Exception as e:
                # Log critical event publishing error (in production, outbox pattern is an option)
                logger.error(f"Failed to publish UserCreated event for user_id={user.id}: {e}", exc_info=True)

        user_dto = UserDTO.model_validate(user)
        return ServiceResponse.ok(user_dto)

    async def get_user(self, user_id: UUID) -> ServiceResponse[UserDTO]:
        """Fetch user by ID."""
        user = await self.repo.get_by_id(user_id)
        if not user:
            logger.warning(f"User not found: id={user_id}")
            return ServiceResponse.fail(
                code="USER_NOT_FOUND",
                message=f"User with ID '{user_id}' was not found.",
            )
        return ServiceResponse.ok(UserDTO.model_validate(user))

    async def authenticate_user(self, email: str, password: str) -> ServiceResponse[UserAuthResultDTO]:
        """Verify user credentials."""
        user = await self.repo.get_by_email(email)
        if not user:
            logger.warning(f"Authentication failed: user with email '{email}' not found.")
            return ServiceResponse.fail(
                code="INVALID_CREDENTIALS",
                message="Invalid email or password.",
            )

        if not verify_password(password, user.password_hash):
            logger.warning(f"Authentication failed: invalid password for email '{email}'.")
            return ServiceResponse.fail(
                code="INVALID_CREDENTIALS",
                message="Invalid email or password.",
            )

        return ServiceResponse.ok(
            UserAuthResultDTO(
                id=user.id,
                name=user.name,
                email=user.email,
            )
        )
