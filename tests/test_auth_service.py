"""Tests for authentication service."""

import pytest
from app.auth_service import (
    hash_password,
    verify_password,
    authenticate_user,
    create_user,
    get_user_by_id,
    get_all_users,
    update_user_password,
    delete_user,
    has_permission,
)
from app.models import UserRole
from app.database import reset_db


@pytest.fixture
def new_db():
    reset_db()
    yield
    reset_db()


def test_hash_password():
    password = "test123"
    hashed = hash_password(password)

    assert hashed != password
    assert len(hashed) == 64  # SHA-256 produces 64 character hex string

    # Same password should produce same hash
    assert hash_password(password) == hashed


def test_verify_password():
    password = "test123"
    hashed = hash_password(password)

    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)


def test_create_user(new_db):
    user = create_user(
        username="admin1",
        password="password123",
        role=UserRole.ADMIN,
        nama="Admin User",
        nik="1234567890",
        alamat="Jl. Admin No. 1",
        instansi="Bank Sampah",
    )

    assert user.id is not None
    assert user.username == "admin1"
    assert user.role == UserRole.ADMIN
    assert user.nama == "Admin User"
    assert user.password != "password123"  # Should be hashed


def test_authenticate_user(new_db):
    # Create user
    create_user(
        username="petugas1",
        password="pass123",
        role=UserRole.PETUGAS,
        nama="Petugas Test",
        nik="9876543210",
        alamat="Jl. Petugas No. 1",
        instansi="Bank Sampah",
    )

    # Valid authentication
    user = authenticate_user("petugas1", "pass123")
    assert user is not None
    assert user.username == "petugas1"
    assert user.role == UserRole.PETUGAS

    # Invalid password
    user = authenticate_user("petugas1", "wrong_pass")
    assert user is None

    # Non-existent user
    user = authenticate_user("nonexistent", "pass123")
    assert user is None


def test_get_user_by_id(new_db):
    user = create_user(
        username="nasabah1",
        password="pass123",
        role=UserRole.NASABAH,
        nama="Nasabah Test",
        nik="1111222233",
        alamat="Jl. Nasabah No. 1",
        instansi="RT 01",
    )

    retrieved = get_user_by_id(user.id if user.id else 0)
    assert retrieved is not None
    assert retrieved.username == "nasabah1"

    # Non-existent ID
    non_existent = get_user_by_id(9999)
    assert non_existent is None


def test_get_all_users(new_db):
    # Initially empty
    users = get_all_users()
    assert len(users) == 0

    # Create multiple users
    create_user("admin", "pass1", UserRole.ADMIN, "Admin", "111", "Addr1", "Inst1")
    create_user("petugas", "pass2", UserRole.PETUGAS, "Petugas", "222", "Addr2", "Inst2")
    create_user("nasabah", "pass3", UserRole.NASABAH, "Nasabah", "333", "Addr3", "Inst3")

    users = get_all_users()
    assert len(users) == 3
    assert any(u.role == UserRole.ADMIN for u in users)
    assert any(u.role == UserRole.PETUGAS for u in users)
    assert any(u.role == UserRole.NASABAH for u in users)


def test_update_user_password(new_db):
    user = create_user(
        username="test_user",
        password="old_pass",
        role=UserRole.ADMIN,
        nama="Test User",
        nik="1234567890",
        alamat="Test Address",
        instansi="Test Inst",
    )

    # Update password
    success = update_user_password(user.id if user.id else 0, "new_pass")
    assert success

    # Verify new password works
    auth_user = authenticate_user("test_user", "new_pass")
    assert auth_user is not None

    # Verify old password doesn't work
    auth_user = authenticate_user("test_user", "old_pass")
    assert auth_user is None

    # Update non-existent user
    success = update_user_password(9999, "new_pass")
    assert not success


def test_delete_user(new_db):
    user = create_user(
        username="to_delete",
        password="pass123",
        role=UserRole.NASABAH,
        nama="Delete Me",
        nik="9999888877",
        alamat="Delete Address",
        instansi="Delete Inst",
    )

    # Verify user exists
    retrieved = get_user_by_id(user.id if user.id else 0)
    assert retrieved is not None

    # Delete user
    success = delete_user(user.id if user.id else 0)
    assert success

    # Verify user no longer exists
    retrieved = get_user_by_id(user.id if user.id else 0)
    assert retrieved is None

    # Delete non-existent user
    success = delete_user(9999)
    assert not success


def test_has_permission():
    # Admin has all permissions
    assert has_permission(UserRole.ADMIN, UserRole.ADMIN)
    assert has_permission(UserRole.ADMIN, UserRole.PETUGAS)
    assert has_permission(UserRole.ADMIN, UserRole.NASABAH)

    # Petugas has petugas and nasabah permissions
    assert not has_permission(UserRole.PETUGAS, UserRole.ADMIN)
    assert has_permission(UserRole.PETUGAS, UserRole.PETUGAS)
    assert has_permission(UserRole.PETUGAS, UserRole.NASABAH)

    # Nasabah only has nasabah permissions
    assert not has_permission(UserRole.NASABAH, UserRole.ADMIN)
    assert not has_permission(UserRole.NASABAH, UserRole.PETUGAS)
    assert has_permission(UserRole.NASABAH, UserRole.NASABAH)
