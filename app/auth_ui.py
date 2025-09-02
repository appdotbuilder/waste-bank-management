"""Authentication UI module for login/logout functionality."""

import logging
from typing import Optional
from nicegui import ui, app
from app.auth_service import authenticate_user
from app.models import User, UserRole


class AuthManager:
    """Manages authentication state and UI."""

    @staticmethod
    def get_current_user() -> Optional[User]:
        """Get currently logged-in user from session."""
        return app.storage.user.get("current_user")

    @staticmethod
    def set_current_user(user: User) -> None:
        """Set current user in session."""
        app.storage.user["current_user"] = user

    @staticmethod
    def logout() -> None:
        """Clear user session."""
        app.storage.user.clear()

    @staticmethod
    def is_logged_in() -> bool:
        """Check if user is logged in."""
        return AuthManager.get_current_user() is not None

    @staticmethod
    def has_role(role: UserRole) -> bool:
        """Check if current user has specific role."""
        user = AuthManager.get_current_user()
        if user is None:
            return False
        return user.role == role

    @staticmethod
    def has_permission_level(min_role: UserRole) -> bool:
        """Check if current user has minimum permission level."""
        user = AuthManager.get_current_user()
        if user is None:
            return False

        role_levels = {UserRole.NASABAH: 1, UserRole.PETUGAS: 2, UserRole.ADMIN: 3}

        user_level = role_levels.get(user.role, 0)
        min_level = role_levels.get(min_role, 0)

        return user_level >= min_level


def create_login_page():
    """Create the login page UI."""

    @ui.page("/login")
    async def login_page():
        # Check if already logged in
        if AuthManager.is_logged_in():
            ui.navigate.to("/dashboard")
            return

        # Apply modern theme
        ui.colors(
            primary="#2563eb",
            secondary="#64748b",
            accent="#10b981",
            positive="#10b981",
            negative="#ef4444",
            warning="#f59e0b",
            info="#3b82f6",
        )

        with ui.column().classes(
            "w-full h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100"
        ):
            with ui.card().classes("w-96 p-8 shadow-2xl rounded-xl bg-white"):
                # Header
                ui.label("Bank Sampah Kelurahan").classes("text-2xl font-bold text-center text-gray-800 mb-2")
                ui.label("Seberang Mesjid").classes("text-lg text-center text-gray-600 mb-6")
                ui.separator().classes("mb-6")

                # Login form
                with ui.column().classes("w-full gap-4"):
                    username_input = ui.input(label="Username", placeholder="Masukkan username").classes("w-full")

                    password_input = ui.input(
                        label="Password", placeholder="Masukkan password", password=True, password_toggle_button=True
                    ).classes("w-full")

                    # Error message container
                    error_label = ui.label("").classes("text-red-500 text-sm text-center min-h-6")

                    async def handle_login():
                        """Handle login attempt."""
                        username = username_input.value.strip()
                        password = password_input.value.strip()

                        if not username or not password:
                            error_label.set_text("Username dan password harus diisi")
                            return

                        try:
                            user = authenticate_user(username, password)
                            if user is None:
                                error_label.set_text("Username atau password salah")
                                return

                            # Set user session
                            AuthManager.set_current_user(user)

                            # Navigate to dashboard
                            ui.navigate.to("/dashboard")

                        except Exception as e:
                            error_label.set_text("Terjadi kesalahan sistem")
                            logging.error(f"Login error: {e}")

                    # Login button
                    ui.button("Masuk", on_click=handle_login).classes(
                        "w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-semibold transition-colors"
                    )

                    # Enter key support
                    password_input.on("keydown.enter", handle_login)
                    username_input.on("keydown.enter", lambda: password_input.run_method("focus"))

                # Footer
                ui.separator().classes("mt-6 mb-4")
                ui.label("Sistem Manajemen Bank Sampah").classes("text-xs text-center text-gray-500")

    @ui.page("/")
    def redirect_to_login():
        """Redirect root path to appropriate page."""
        if AuthManager.is_logged_in():
            ui.navigate.to("/dashboard")
        else:
            ui.navigate.to("/login")


def require_login(min_role: Optional[UserRole] = None):
    """Decorator to require login and optional minimum role for pages."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            if not AuthManager.is_logged_in():
                ui.navigate.to("/login")
                return

            if min_role and not AuthManager.has_permission_level(min_role):
                ui.notify("Akses ditolak: Anda tidak memiliki izin untuk halaman ini", type="negative")
                ui.navigate.to("/dashboard")
                return

            return func(*args, **kwargs)

        return wrapper

    return decorator


def create_logout_handler():
    """Create logout functionality."""

    def logout():
        AuthManager.logout()
        ui.navigate.to("/login")
        ui.notify("Anda telah berhasil logout", type="info")

    return logout


def create_header_with_auth():
    """Create header with authentication info and logout button."""
    user = AuthManager.get_current_user()
    if user is None:
        return

    with ui.row().classes("w-full justify-between items-center p-4 bg-white shadow-sm border-b"):
        # Left side - App name
        ui.label("Bank Sampah Kelurahan Seberang Mesjid").classes("text-xl font-bold text-gray-800")

        # Right side - User info and logout
        with ui.row().classes("items-center gap-4"):
            # User info
            with ui.column().classes("text-right gap-0"):
                ui.label(user.nama).classes("font-semibold text-gray-800 text-sm")
                ui.label(f"{user.role.value.title()} • {user.instansi}").classes("text-xs text-gray-500")

            # Logout button
            ui.button("Keluar", on_click=create_logout_handler(), icon="logout").classes(
                "bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg text-sm"
            )


def create():
    """Initialize authentication module."""
    create_login_page()
