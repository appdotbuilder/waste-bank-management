"""Authentication service for user login/logout and session management."""

import hashlib
from typing import Optional
from sqlmodel import select
from app.database import get_session
from app.models import User, UserRole


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(plain_password) == hashed_password


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password."""
    with get_session() as session:
        stmt = select(User).where(User.username == username)
        user = session.exec(stmt).first()

        if user is None:
            return None

        if not verify_password(password, user.password):
            return None

        return user


def create_user(username: str, password: str, role: UserRole, nama: str, nik: str, alamat: str, instansi: str) -> User:
    """Create a new user account."""
    with get_session() as session:
        hashed_password = hash_password(password)
        user = User(
            username=username, password=hashed_password, role=role, nama=nama, nik=nik, alamat=alamat, instansi=instansi
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def get_user_by_id(user_id: int) -> Optional[User]:
    """Get user by ID."""
    with get_session() as session:
        return session.get(User, user_id)


def get_all_users() -> list[User]:
    """Get all users."""
    with get_session() as session:
        stmt = select(User)
        return list(session.exec(stmt).all())


def update_user_password(user_id: int, new_password: str) -> bool:
    """Update user password."""
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            return False

        user.password = hash_password(new_password)
        session.add(user)
        session.commit()
        return True


def delete_user(user_id: int) -> bool:
    """Delete a user."""
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            return False

        session.delete(user)
        session.commit()
        return True


def has_permission(user_role: UserRole, required_role: UserRole) -> bool:
    """Check if user has required permission level."""
    role_hierarchy = {UserRole.NASABAH: 1, UserRole.PETUGAS: 2, UserRole.ADMIN: 3}

    return role_hierarchy[user_role] >= role_hierarchy[required_role]
