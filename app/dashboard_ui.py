"""Dashboard UI module with real-time key metrics."""

import logging
from nicegui import ui
from app.auth_ui import require_login, create_header_with_auth, AuthManager
from app.dashboard_service import DashboardService
from app.models import UserRole


def create_metric_card(title: str, value: str, subtitle: str = "", icon: str = "analytics", color: str = "blue"):
    """Create a modern metric card component."""
    color_classes = {
        "blue": "border-l-blue-500 bg-blue-50",
        "green": "border-l-green-500 bg-green-50",
        "yellow": "border-l-yellow-500 bg-yellow-50",
        "red": "border-l-red-500 bg-red-50",
        "purple": "border-l-purple-500 bg-purple-50",
        "gray": "border-l-gray-500 bg-gray-50",
    }

    icon_colors = {
        "blue": "text-blue-600",
        "green": "text-green-600",
        "yellow": "text-yellow-600",
        "red": "text-red-600",
        "purple": "text-purple-600",
        "gray": "text-gray-600",
    }

    with ui.card().classes(
        f"p-6 shadow-lg rounded-xl border-l-4 {color_classes.get(color, color_classes['blue'])} hover:shadow-xl transition-shadow"
    ):
        with ui.row().classes("items-center justify-between w-full"):
            with ui.column().classes("gap-1"):
                ui.label(title).classes("text-sm font-medium text-gray-600 uppercase tracking-wide")
                ui.label(value).classes("text-3xl font-bold text-gray-800")
                if subtitle:
                    ui.label(subtitle).classes("text-xs text-gray-500")

            ui.icon(icon).classes(f"text-4xl {icon_colors.get(color, icon_colors['blue'])} opacity-80")


@ui.refreshable
def dashboard_content():
    """Refreshable dashboard content."""
    try:
        summary = DashboardService.get_dashboard_summary()
        user = AuthManager.get_current_user()

        # Page title
        ui.label("Dashboard Overview").classes("text-3xl font-bold text-gray-800 mb-6")

        # Metrics grid
        with ui.grid(columns=4).classes("w-full gap-6 mb-8"):
            # Row 1: Basic counts
            create_metric_card("Total Nasabah", str(summary.total_customers), "Pelanggan terdaftar", "people", "blue")

            create_metric_card("Total Petugas", str(summary.total_officers), "Petugas aktif", "badge", "green")

            create_metric_card(
                "Jenis Sampah", str(summary.total_waste_types), "Kategori tersedia", "category", "purple"
            )

            create_metric_card(
                "Transaksi Setoran", str(summary.total_deposit_transactions), "Total transaksi", "savings", "yellow"
            )

        # Row 2: Financial metrics
        with ui.grid(columns=3).classes("w-full gap-6 mb-8"):
            create_metric_card(
                "Saldo Nasabah",
                f"Rp {summary.total_customer_balance:,.0f}",
                "Total saldo tersimpan",
                "account_balance_wallet",
                "green",
            )

            create_metric_card(
                "Penarikan Pending",
                str(summary.pending_withdrawal_requests),
                "Menunggu persetujuan" if user and user.role == UserRole.ADMIN else "Perlu diproses",
                "pending_actions",
                "red" if summary.pending_withdrawal_requests > 0 else "gray",
            )

            profit_color = "green" if summary.total_profit >= 0 else "red"
            profit_icon = "trending_up" if summary.total_profit >= 0 else "trending_down"
            create_metric_card(
                "Total Keuntungan", f"Rp {summary.total_profit:,.0f}", "Selisih jual-beli", profit_icon, profit_color
            )

        # Row 3: Waste management metrics
        with ui.grid(columns=2).classes("w-full gap-6 mb-8"):
            create_metric_card(
                "Stok Sampah", f"{summary.total_waste_stock:.1f} kg", "Belum dijual ke pengepul", "inventory_2", "blue"
            )

            create_metric_card(
                "Terjual ke Pengepul",
                f"{summary.total_waste_sent_to_collectors:.1f} kg",
                "Total sudah terjual",
                "local_shipping",
                "green",
            )

        # Quick actions section
        ui.separator().classes("my-8")
        ui.label("Aksi Cepat").classes("text-xl font-semibold text-gray-700 mb-4")

        with ui.row().classes("gap-4 flex-wrap"):
            if user and user.role in [UserRole.ADMIN, UserRole.PETUGAS]:
                ui.button(
                    "Transaksi Setoran", on_click=lambda: ui.navigate.to("/transaksi/setoran"), icon="add_circle"
                ).classes("bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold")

                if summary.pending_withdrawal_requests > 0:
                    ui.button(
                        f"Proses Penarikan ({summary.pending_withdrawal_requests})",
                        on_click=lambda: ui.navigate.to("/transaksi/tarik"),
                        icon="approval",
                    ).classes("bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-semibold")

            if user and user.role == UserRole.ADMIN:
                ui.button(
                    "Transaksi Pengepul", on_click=lambda: ui.navigate.to("/transaksi/pengepul"), icon="local_shipping"
                ).classes("bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold")

            ui.button("Cetak Laporan", on_click=lambda: ui.navigate.to("/laporan"), icon="print").classes(
                "bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-semibold"
            )

    except Exception as e:
        ui.label(f"Error loading dashboard: {e}").classes("text-red-500")
        logging.error(f"Dashboard error: {e}")


def create_dashboard_page():
    """Create the main dashboard page."""

    @ui.page("/dashboard")
    @require_login()
    def dashboard_page():
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

        with ui.column().classes("w-full min-h-screen bg-gray-50"):
            # Header
            create_header_with_auth()

            # Navigation
            create_navigation_menu()

            # Main content
            with ui.column().classes("flex-1 p-6 max-w-7xl mx-auto w-full"):
                dashboard_content()

                # Auto-refresh every 30 seconds
                ui.timer(30.0, dashboard_content.refresh)


def create_navigation_menu():
    """Create horizontal navigation menu."""
    user = AuthManager.get_current_user()
    if user is None:
        return

    with ui.row().classes("w-full bg-white shadow-sm border-b px-6 py-3 gap-6"):
        # Dashboard
        ui.button("Dashboard", on_click=lambda: ui.navigate.to("/dashboard"), icon="dashboard").props("flat").classes(
            "text-blue-600 font-semibold"
        )

        # Master Data (Admin/Petugas only)
        if user.role in [UserRole.ADMIN, UserRole.PETUGAS]:
            with ui.menu() as menu:
                ui.menu_item("Data Nasabah", lambda: ui.navigate.to("/master/nasabah"))
                if user.role == UserRole.ADMIN:
                    ui.menu_item("Data Petugas", lambda: ui.navigate.to("/master/petugas"))
                ui.menu_item("Data Jenis Sampah", lambda: ui.navigate.to("/master/jenis-sampah"))
                ui.menu_item("Data Pengepul", lambda: ui.navigate.to("/master/pengepul"))

            with ui.button("Master Data", icon="database").props("flat").classes("text-gray-700"):
                menu

        # Transactions
        if user.role in [UserRole.ADMIN, UserRole.PETUGAS]:
            with ui.menu() as trans_menu:
                ui.menu_item("Setoran Sampah", lambda: ui.navigate.to("/transaksi/setoran"))
                ui.menu_item("Penarikan Saldo", lambda: ui.navigate.to("/transaksi/tarik"))
                if user.role == UserRole.ADMIN:
                    ui.menu_item("Transaksi Pengepul", lambda: ui.navigate.to("/transaksi/pengepul"))

            with ui.button("Transaksi", icon="receipt_long").props("flat").classes("text-gray-700"):
                trans_menu

        # Reports
        ui.button("Laporan", on_click=lambda: ui.navigate.to("/laporan"), icon="assessment").props("flat").classes(
            "text-gray-700"
        )

        # Settings (Admin only)
        if user.role == UserRole.ADMIN:
            ui.button("Pengaturan", on_click=lambda: ui.navigate.to("/pengaturan"), icon="settings").props(
                "flat"
            ).classes("text-gray-700")


def create():
    """Initialize dashboard module."""
    create_dashboard_page()
