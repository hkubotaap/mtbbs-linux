"""
User Service - Business logic for user operations
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt

from app.models.user import User
from app.core.database import async_session


class UserService:
    """User service for authentication and user management"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

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
        is_active: bool = True,
        must_change_password_on_next_login: bool = False,
    ) -> User:
        """Create new user or reactivate deleted user"""
        async with async_session() as session:
            # Check if user already exists (including inactive ones)
            result = await session.execute(select(User).where(User.user_id == user_id))
            existing_user = result.scalar_one_or_none()

            if existing_user:
                # Reactivate deleted user with new data
                existing_user.password_hash = self.hash_password(password)
                existing_user.handle_name = handle_name
                existing_user.email = email
                existing_user.level = level
                existing_user.is_active = is_active
                existing_user.is_banned = False
                existing_user.must_change_password_on_next_login = must_change_password_on_next_login
                existing_user.updated_at = datetime.now()
                await session.commit()
                await session.refresh(existing_user)
                return existing_user
            else:
                # Create new user
                user = User(
                    user_id=user_id,
                    password_hash=self.hash_password(password),
                    handle_name=handle_name,
                    email=email,
                    level=level,
                    is_active=is_active,
                    must_change_password_on_next_login=must_change_password_on_next_login,
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
        """Get all active users"""
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.is_active == True).offset(skip).limit(limit)
            )
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

    async def is_user_id_available(self, user_id: str) -> bool:
        """Check if user ID is available for registration"""
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id, User.is_active == True)
            )
            existing_user = result.scalar_one_or_none()
            return existing_user is None

    async def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete)"""
        user = await self.update_user(user_id, is_active=False, is_banned=True)
        return user is not None
