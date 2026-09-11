from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User


class UserRepository:
    """Repository handling User persistence and querying."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Fetch user by UUID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Fetch user by email (case-insensitive)."""
        stmt = select(User).where(User.email == email.lower().strip())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, name: str, email: str, password_hash: str) -> User:
        """Create and persist a new user."""
        user = User(
            name=name.strip(),
            email=email.lower().strip(),
            password_hash=password_hash,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
