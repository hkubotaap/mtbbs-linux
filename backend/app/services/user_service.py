"""
User Service - Business logic for user operations
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from app.models.user import User
from app.core.database import async_session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """User service for authentication and user management"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return pwd_context.verify(plain_password, hashed_password)

    async def authenticate(self, user_id: str, password: str) -> Optional[User]:
        """Authenticate user"""
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id, User.is_active == True)
            )
            user = result.scalar_one_or_none()

            if user and self.verify_password(password, user.password_hash):
                return user

            return None

    async def create_user(
        self,
        user_id: str,
        password: str,
        handle_name: str,
        email: Optional[str] = None,
        level: int = 1,
    ) -> User:
        """Create new user"""
        async with async_session() as session:
            user = User(
                user_id=user_id,
                password_hash=self.hash_password(password),
                handle_name=handle_name,
                email=email,
                level=level,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        async with async_session() as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            return result.scalar_one_or_none()

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users"""
        async with async_session() as session:
            result = await session.execute(select(User).offset(skip).limit(limit))
            return list(result.scalars().all())

    async def get_recent_users(self, limit: int = 20) -> List[User]:
        """Get recently logged in users"""
        async with async_session() as session:
            result = await session.execute(
                select(User)
                .where(User.last_login.isnot(None))
                .order_by(User.last_login.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user"""
        async with async_session() as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            user = result.scalar_one_or_none()

            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)

                user.updated_at = datetime.now()
                await session.commit()
                await session.refresh(user)

            return user

    async def record_login(self, user_id: str, ip_address: str):
        """Record user login"""
        async with async_session() as session:
            await session.execute(
                update(User)
                .where(User.user_id == user_id)
                .values(last_login=datetime.now())
            )
            await session.commit()

    async def record_logout(self, user_id: str):
        """Record user logout"""
        # Can add logout logging here if needed
        pass

    async def get_access_count(self) -> int:
        """Get total access count"""
        async with async_session() as session:
            result = await session.execute(select(func.count()).select_from(User))
            return result.scalar() or 0

    async def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete)"""
        user = await self.update_user(user_id, is_active=False, is_banned=True)
        return user is not None
