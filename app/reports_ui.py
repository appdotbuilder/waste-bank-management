"""Reports UI module for generating and viewing various reports."""

import logging
from datetime import date, datetime, timedelta
from nicegui import ui
from app.auth_ui import require_login, create_header_with_auth
from app.report_service import ReportService


@ui.refreshable
def transaction_report_viewer():
    """Transaction report viewer with date range selection."""
    try:
        # Date range selectors
        with ui.row().classes("w-full gap-4 mb-6"):
            today = date.today()

            start_date_input = ui.date(
                value=today.replace(day=1).isoformat()  # First day of current month
            ).classes("w-48")

            end_date_input = ui.date(value=today.isoformat()).classes("w-48")

            # Quick date range buttons
            with ui.column().classes("gap-2"):
                ui.label("Pilihan Cepat:").classes("text-sm font-semibold text-gray-700")

                def set_today():
                    start_date_input.set_value(today.isoformat())
                    end_date_input.set_value(today.isoformat())
                    load_report()

                def set_this_month():
                    start_date_input.set_value(today.replace(day=1).isoformat())
                    end_date_input.set_value(today.isoformat())
                    load_report()

                def set_last_month():
                    last_month = today.replace(day=1) - timedelta(days=1)
                    start_date_input.set_value(last_month.replace(day=1).isoformat())
                    end_date_input.set_value(last_month.isoformat())
                    load_report()

                with ui.row().classes("gap-2"):
                    ui.button("Hari Ini", on_click=set_today).props("size=sm outline")
                    ui.button("Bulan Ini", on_click=set_this_month).props("size=sm outline")
                    ui.button("Bulan Lalu", on_click=set_last_month).props("size=sm outline")

        # Load report button
        ui.button("Muat Laporan", on_click=lambda: load_report(), icon="search").classes(
            "bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg mb-6"
        )

        # Report container
        report_container = ui.column().classes("w-full")

        def load_report():
            """Load and display transaction report."""
            try:
                if not start_date_input.value or not end_date_input.value:
                    ui.notify("Pilih tanggal mulai dan akhir", type="warning")
                    return

                start_date = date.fromisoformat(start_date_input.value)
                end_date = date.fromisoformat(end_date_input.value)

                if start_date > end_date:
                    ui.notify("Tanggal mulai tidak boleh lebih besar dari tanggal akhir", type="warning")
                    return

                # Clear previous report
                report_container.clear()

                with report_container:
                    ui.label(
                        f"Laporan Transaksi: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
                    ).classes("text-xl font-bold text-gray-800 mb-4")

                    # Get report data
                    transactions = ReportService.generate_transaction_report(start_date, end_date)

                    if not transactions:
                        ui.label("Tidak ada transaksi dalam periode tersebut").classes("text-gray-500 text-center p-8")
                        return

                    # Summary statistics
                    total_setoran = len([t for t in transactions if t.transaction_type == "setoran"])
                    total_tarik = len([t for t in transactions if t.transaction_type == "tarik"])
                    total_pengepul = len([t for t in transactions if t.transaction_type == "pengepul"])

                    nilai_setoran = sum(t.nilai for t in transactions if t.transaction_type == "setoran")
                    nilai_tarik = sum(t.nilai for t in transactions if t.transaction_type == "tarik")
                    nilai_pengepul = sum(t.nilai for t in transactions if t.transaction_type == "pengepul")

                    with ui.card().classes("w-full p-6 shadow-lg rounded-xl mb-6"):
                        ui.label("Ringkasan").classes("text-lg font-bold text-gray-800 mb-4")

                        with ui.grid(columns=3).classes("gap-6"):
                            # Setoran summary
                            with ui.column().classes("text-center"):
                                ui.label(str(total_setoran)).classes("text-2xl font-bold text-green-600")
                                ui.label("Transaksi Setoran").classes("text-sm text-gray-600")
                                ui.label(f"Rp {nilai_setoran:,.0f}").classes("text-lg font-semibold text-green-600")

                            # Tarik summary
                            with ui.column().classes("text-center"):
                                ui.label(str(total_tarik)).classes("text-2xl font-bold text-red-600")
                                ui.label("Penarikan Saldo").classes("text-sm text-gray-600")
                                ui.label(f"Rp {nilai_tarik:,.0f}").classes("text-lg font-semibold text-red-600")

                            # Pengepul summary
                            with ui.column().classes("text-center"):
                                ui.label(str(total_pengepul)).classes("text-2xl font-bold text-blue-600")
                                ui.label("Penjualan ke Pengepul").classes("text-sm text-gray-600")
                                ui.label(f"Rp {nilai_pengepul:,.0f}").classes("text-lg font-semibold text-blue-600")

                    # Detailed transaction table
                    with ui.card().classes("w-full p-6 shadow-lg rounded-xl"):
                        ui.label("Detail Transaksi").classes("text-lg font-bold text-gray-800 mb-4")

                        columns = [
                            {"name": "tanggal", "label": "Tanggal", "field": "tanggal", "sortable": True},
                            {"name": "tipe", "label": "Tipe", "field": "tipe", "sortable": True},
                            {"name": "nasabah", "label": "Nasabah/Pengepul", "field": "participant"},
                            {"name": "petugas", "label": "Petugas", "field": "petugas"},
                            {"name": "detail", "label": "Detail", "field": "detail"},
                            {"name": "nilai", "label": "Nilai", "field": "nilai", "sortable": True},
                        ]

                        rows = []
                        for t in transactions:
                            tipe_display = {"setoran": "Setoran", "tarik": "Penarikan", "pengepul": "Penjualan"}.get(
                                t.transaction_type, t.transaction_type.title()
                            )

                            participant = t.nasabah_nama or t.pengepul_nama or "Unknown"

                            detail = ""
                            if t.jenis_sampah_nama and t.berat:
                                detail = f"{t.jenis_sampah_nama} - {t.berat:.3f} kg"
                            elif t.transaction_type == "tarik":
                                detail = "Penarikan saldo"

                            rows.append(
                                {
                                    "tanggal": t.tanggal.strftime("%d/%m/%Y %H:%M"),
                                    "tipe": tipe_display,
                                    "participant": participant,
                                    "petugas": t.petugas_nama or "-",
                                    "detail": detail,
                                    "nilai": f"Rp {t.nilai:,.0f}",
                                }
                            )

                        ui.table(columns=columns, rows=rows).classes("w-full")

            except Exception as e:
                ui.notify(f"Error loading report: {e}", type="negative")
                logging.error(f"Report loading error: {e}")

        # Load current month report by default
        load_report()

    except Exception as e:
        ui.label(f"Error initializing report viewer: {e}").classes("text-red-500")
        logging.error(f"Report viewer error: {e}")


@ui.refreshable
def customer_balance_report():
    """Customer balance report showing all customers."""
    try:
        ui.label("Laporan Saldo Nasabah").classes("text-xl font-bold text-gray-800 mb-6")

        # Get customer reports
        customer_reports = ReportService.get_all_customer_reports()

        if not customer_reports:
            ui.label("Belum ada data nasabah").classes("text-gray-500 text-center p-8")
            return

        # Summary card
        total_customers = len(customer_reports)
        total_balance = sum(r.saldo_current for r in customer_reports)
        total_deposits = sum(r.total_setoran for r in customer_reports)
        total_withdrawals = sum(r.total_tarik for r in customer_reports)

        with ui.card().classes("w-full p-6 shadow-lg rounded-xl mb-6"):
            ui.label("Ringkasan Saldo Nasabah").classes("text-lg font-bold text-gray-800 mb-4")

            with ui.grid(columns=4).classes("gap-6"):
                with ui.column().classes("text-center"):
                    ui.label(str(total_customers)).classes("text-2xl font-bold text-blue-600")
                    ui.label("Total Nasabah").classes("text-sm text-gray-600")

                with ui.column().classes("text-center"):
                    ui.label(f"Rp {total_balance:,.0f}").classes("text-2xl font-bold text-green-600")
                    ui.label("Total Saldo").classes("text-sm text-gray-600")

                with ui.column().classes("text-center"):
                    ui.label(f"Rp {total_deposits:,.0f}").classes("text-2xl font-bold text-blue-600")
                    ui.label("Total Setoran").classes("text-sm text-gray-600")

                with ui.column().classes("text-center"):
                    ui.label(f"Rp {total_withdrawals:,.0f}").classes("text-2xl font-bold text-red-600")
                    ui.label("Total Penarikan").classes("text-sm text-gray-600")

        # Detailed customer table
        with ui.card().classes("w-full p-6 shadow-lg rounded-xl"):
            ui.label("Detail Saldo per Nasabah").classes("text-lg font-bold text-gray-800 mb-4")

            columns = [
                {"name": "kode", "label": "Kode", "field": "kode", "sortable": True},
                {"name": "nama", "label": "Nama", "field": "nama", "sortable": True},
                {"name": "total_setoran", "label": "Total Setoran", "field": "total_setoran", "sortable": True},
                {"name": "total_tarik", "label": "Total Penarikan", "field": "total_tarik", "sortable": True},
                {"name": "saldo_current", "label": "Saldo Saat Ini", "field": "saldo_current", "sortable": True},
                {
                    "name": "last_transaction",
                    "label": "Transaksi Terakhir",
                    "field": "last_transaction",
                    "sortable": True,
                },
            ]

            rows = []
            for r in customer_reports:
                rows.append(
                    {
                        "kode": r.nasabah_kode,
                        "nama": r.nasabah_nama,
                        "total_setoran": f"Rp {r.total_setoran:,.0f}",
                        "total_tarik": f"Rp {r.total_tarik:,.0f}",
                        "saldo_current": f"Rp {r.saldo_current:,.0f}",
                        "last_transaction": r.last_transaction.strftime("%d/%m/%Y %H:%M")
                        if r.last_transaction != datetime.min
                        else "Belum ada",
                    }
                )

            ui.table(columns=columns, rows=rows).classes("w-full")

    except Exception as e:
        ui.label(f"Error loading customer balance report: {e}").classes("text-red-500")
        logging.error(f"Customer balance report error: {e}")


def create_reports_page():
    """Create reports page with various report types."""

    @ui.page("/laporan")
    @require_login()
    def reports_page():
        with ui.column().classes("w-full min-h-screen bg-gray-50"):
            create_header_with_auth()

            # Breadcrumb navigation
            with ui.row().classes("w-full px-6 py-4 bg-white shadow-sm"):
                ui.button("Dashboard", on_click=lambda: ui.navigate.to("/dashboard")).props("flat dense")
                ui.label("/").classes("mx-2 text-gray-400")
                ui.label("Laporan").classes("font-semibold text-gray-700")

            # Main content
            with ui.column().classes("flex-1 p-6 max-w-7xl mx-auto w-full"):
                ui.label("Laporan dan Analisis").classes("text-3xl font-bold text-gray-800 mb-6")

                # Report type tabs
                with ui.tabs().classes("w-full") as tabs:
                    tab1 = ui.tab("Transaksi", icon="receipt_long")
                    tab2 = ui.tab("Saldo Nasabah", icon="account_balance_wallet")

                with ui.tab_panels(tabs, value=tab1).classes("w-full"):
                    with ui.tab_panel(tab1):
                        transaction_report_viewer()

                    with ui.tab_panel(tab2):
                        customer_balance_report()


def create():
    """Initialize reports UI module."""
    create_reports_page()
