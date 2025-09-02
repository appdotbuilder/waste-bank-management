"""Transaction management UI module."""

import logging
from decimal import Decimal
from nicegui import ui
from app.auth_ui import require_login, create_header_with_auth, AuthManager
from app.transaction_service import TransaksiSetoranService, TransaksiTarikService, TransaksiPengepulService
from app.master_data_service import NasabahService, PetugasService, JenisSampahService, PengepulService
from app.models import TransaksiSetoranCreate, TransaksiPengepulCreate, UserRole


@ui.refreshable
def setoran_form():
    """Refreshable deposit transaction form."""
    try:
        user = AuthManager.get_current_user()
        if user is None:
            ui.label("User tidak ditemukan").classes("text-red-500")
            return

        # Get current officer data
        petugas_list = PetugasService.get_all_petugas()
        current_petugas = next((p for p in petugas_list if p.nik == user.nik), None) if petugas_list else None

        if current_petugas is None:
            ui.label("Data petugas tidak ditemukan. Hubungi administrator.").classes("text-red-500")
            return

        # Get data for form options
        nasabah_list = NasabahService.get_all_nasabah()
        jenis_sampah_list = JenisSampahService.get_all_jenis_sampah()

        if not nasabah_list:
            ui.label("Belum ada data nasabah. Tambahkan data nasabah terlebih dahulu.").classes("text-yellow-600")
            return

        if not jenis_sampah_list:
            ui.label("Belum ada data jenis sampah. Tambahkan data jenis sampah terlebih dahulu.").classes(
                "text-yellow-600"
            )
            return

        with ui.card().classes("w-full max-w-2xl p-6 shadow-lg rounded-xl"):
            ui.label("Transaksi Setoran Sampah").classes("text-2xl font-bold text-gray-800 mb-6")

            # Officer info (read-only)
            with ui.row().classes("w-full mb-4"):
                ui.label("Petugas:").classes("font-semibold text-gray-700 w-24")
                ui.label(f"{current_petugas.nama} ({current_petugas.kode})").classes("text-gray-800")

            ui.separator().classes("mb-4")

            # Customer selection
            nasabah_options = {n.id: f"{n.kode} - {n.nama}" for n in nasabah_list if n.id}
            nasabah_select = ui.select(label="Pilih Nasabah", options=nasabah_options, value=None).classes(
                "w-full mb-4"
            )

            # Show customer balance when selected
            balance_label = ui.label("").classes("text-sm text-blue-600 mb-4")

            def update_balance_display():
                if nasabah_select.value:
                    nasabah = NasabahService.get_nasabah_by_id(nasabah_select.value)
                    if nasabah:
                        balance_label.set_text(f"Saldo saat ini: Rp {nasabah.saldo:,.0f}")
                    else:
                        balance_label.set_text("")
                else:
                    balance_label.set_text("")

            nasabah_select.on("update:model-value", lambda: update_balance_display())

            # Waste type selection
            jenis_options = {
                j.id: f"{j.kode} - {j.nama} (Rp {j.harga_beli:,.0f}/kg)" for j in jenis_sampah_list if j.id
            }
            jenis_select = ui.select(label="Pilih Jenis Sampah", options=jenis_options, value=None).classes(
                "w-full mb-4"
            )

            # Weight input
            berat_input = ui.number(label="Berat (kg)", min=0.001, step=0.1, format="%.3f").classes("w-full mb-4")

            # Calculated value display
            nilai_label = ui.label("Nilai: Rp 0").classes("text-xl font-semibold text-green-600 mb-4")

            def calculate_value():
                if jenis_select.value and berat_input.value:
                    jenis_sampah = JenisSampahService.get_jenis_sampah_by_id(jenis_select.value)
                    if jenis_sampah:
                        total_value = float(berat_input.value) * float(jenis_sampah.harga_beli)
                        nilai_label.set_text(f"Nilai: Rp {total_value:,.0f}")
                    else:
                        nilai_label.set_text("Nilai: Rp 0")
                else:
                    nilai_label.set_text("Nilai: Rp 0")

            jenis_select.on("update:model-value", lambda: calculate_value())
            berat_input.on("update:model-value", lambda: calculate_value())

            # Error message
            error_label = ui.label("").classes("text-red-500 text-sm mb-4")

            # Submit button
            async def process_setoran():
                try:
                    # Validate inputs
                    if not all([nasabah_select.value, jenis_select.value, berat_input.value]):
                        error_label.set_text("Semua field harus diisi")
                        return

                    if berat_input.value <= 0:
                        error_label.set_text("Berat harus lebih dari 0")
                        return

                    # Create transaction
                    data = TransaksiSetoranCreate(
                        nasabah_id=int(nasabah_select.value) if nasabah_select.value else 0,
                        petugas_id=current_petugas.id if current_petugas.id else 0,
                        jenis_sampah_id=int(jenis_select.value) if jenis_select.value else 0,
                        berat=Decimal(str(berat_input.value)),
                    )

                    result = TransaksiSetoranService.create_setoran(data)
                    if result:
                        # Clear form
                        nasabah_select.set_value(None)
                        jenis_select.set_value(None)
                        berat_input.set_value(None)
                        error_label.set_text("")
                        balance_label.set_text("")
                        nilai_label.set_text("Nilai: Rp 0")

                        ui.notify(f"Transaksi berhasil! Nilai: Rp {result.nilai:,.0f}", type="positive")

                        # Refresh recent transactions
                        recent_transactions.refresh()
                    else:
                        error_label.set_text("Gagal memproses transaksi")

                except Exception as e:
                    logging.error(f"Error processing transaction: {e}")
                    error_label.set_text(f"Error: {e}")

            ui.button("Proses Setoran", on_click=process_setoran, icon="savings").classes(
                "w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-semibold"
            )

    except Exception as e:
        ui.label(f"Error loading form: {e}").classes("text-red-500")
        logging.error(f"Setoran form error: {e}")


@ui.refreshable
def recent_transactions():
    """Show recent deposit transactions."""
    try:
        transactions = TransaksiSetoranService.get_all_setoran()[:10]  # Latest 10

        if not transactions:
            ui.label("Belum ada transaksi setoran").classes("text-gray-500 text-center p-8")
            return

        with ui.card().classes("w-full p-6 shadow-lg rounded-xl mt-6"):
            ui.label("Transaksi Terbaru").classes("text-xl font-bold text-gray-800 mb-4")

            columns = [
                {"name": "tanggal", "label": "Tanggal", "field": "tanggal"},
                {"name": "nasabah", "label": "Nasabah", "field": "nasabah"},
                {"name": "jenis_sampah", "label": "Jenis Sampah", "field": "jenis_sampah"},
                {"name": "berat", "label": "Berat (kg)", "field": "berat"},
                {"name": "nilai", "label": "Nilai", "field": "nilai"},
            ]

            rows = []
            for t in transactions:
                try:
                    nasabah = NasabahService.get_nasabah_by_id(t.nasabah_id)
                    jenis_sampah = JenisSampahService.get_jenis_sampah_by_id(t.jenis_sampah_id)

                    rows.append(
                        {
                            "tanggal": t.tanggal.strftime("%d/%m/%Y %H:%M"),
                            "nasabah": f"{nasabah.kode} - {nasabah.nama}" if nasabah else "Unknown",
                            "jenis_sampah": jenis_sampah.nama if jenis_sampah else "Unknown",
                            "berat": f"{t.berat:.3f}",
                            "nilai": f"Rp {t.nilai:,.0f}",
                        }
                    )
                except Exception as e:
                    logging.warning(f"Error loading transaction data: {e}")
                    continue

            ui.table(columns=columns, rows=rows).classes("w-full")

    except Exception as e:
        ui.label(f"Error loading recent transactions: {e}").classes("text-red-500")
        logging.error(f"Recent transactions error: {e}")


@ui.refreshable
def withdrawal_requests_table():
    """Show pending withdrawal requests for approval."""
    try:
        pending_requests = TransaksiTarikService.get_pending_tarik()

        if not pending_requests:
            ui.label("Tidak ada permintaan penarikan yang menunggu persetujuan").classes(
                "text-gray-500 text-center p-8"
            )
            return

        columns = [
            {"name": "tanggal", "label": "Tanggal Request", "field": "tanggal"},
            {"name": "nasabah", "label": "Nasabah", "field": "nasabah"},
            {"name": "saldo_tersedia", "label": "Saldo Tersedia", "field": "saldo_tersedia"},
            {"name": "jumlah_tarik", "label": "Jumlah Penarikan", "field": "jumlah_tarik"},
            {"name": "actions", "label": "Aksi", "field": "actions"},
        ]

        rows = []
        for request in pending_requests:
            try:
                nasabah = NasabahService.get_nasabah_by_id(request.nasabah_id)
                if nasabah:
                    rows.append(
                        {
                            "id": request.id,
                            "tanggal": request.tanggal.strftime("%d/%m/%Y %H:%M"),
                            "nasabah": f"{nasabah.kode} - {nasabah.nama}",
                            "saldo_tersedia": f"Rp {nasabah.saldo:,.0f}",
                            "jumlah_tarik": f"Rp {request.jumlah:,.0f}",
                            "can_approve": nasabah.saldo >= request.jumlah,
                        }
                    )
            except Exception as e:
                logging.warning(f"Error loading withdrawal request data: {e}")
                continue

        table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")

        # Add action buttons
        table.add_slot(
            "body-cell-actions",
            """
            <q-td :props="props">
                <div class="flex gap-2">
                    <q-btn size="sm" icon="check" color="positive" dense unelevated
                           :disable="!props.row.can_approve"
                           @click="$parent.$emit('approve_withdrawal', props.row)" 
                           label="Setujui" />
                    <q-btn size="sm" icon="close" color="negative" dense unelevated
                           @click="$parent.$emit('reject_withdrawal', props.row)"
                           label="Tolak" />
                </div>
            </q-td>
        """,
        )

        async def approve_withdrawal(e):
            request_id = e.args["id"]
            success = TransaksiTarikService.approve_tarik(request_id)
            if success:
                ui.notify("Penarikan disetujui dan diproses", type="positive")
                withdrawal_requests_table.refresh()
            else:
                ui.notify("Gagal memproses penarikan", type="negative")

        async def reject_withdrawal(e):
            request_id = e.args["id"]
            success = TransaksiTarikService.reject_tarik(request_id)
            if success:
                ui.notify("Penarikan ditolak", type="warning")
                withdrawal_requests_table.refresh()
            else:
                ui.notify("Gagal menolak penarikan", type="negative")

        table.on("approve_withdrawal", approve_withdrawal)
        table.on("reject_withdrawal", reject_withdrawal)

    except Exception as e:
        ui.label(f"Error loading withdrawal requests: {e}").classes("text-red-500")
        logging.error(f"Withdrawal requests error: {e}")


def create_setoran_page():
    """Create deposit transaction page."""

    @ui.page("/transaksi/setoran")
    @require_login(UserRole.PETUGAS)
    def setoran_page():
        with ui.column().classes("w-full min-h-screen bg-gray-50"):
            create_header_with_auth()

            # Breadcrumb navigation
            with ui.row().classes("w-full px-6 py-4 bg-white shadow-sm"):
                ui.button("Dashboard", on_click=lambda: ui.navigate.to("/dashboard")).props("flat dense")
                ui.label("/").classes("mx-2 text-gray-400")
                ui.label("Transaksi Setoran").classes("font-semibold text-gray-700")

            # Main content
            with ui.column().classes("flex-1 p-6 max-w-4xl mx-auto w-full"):
                setoran_form()
                recent_transactions()


def create_tarik_page():
    """Create withdrawal transaction page."""

    @ui.page("/transaksi/tarik")
    @require_login(UserRole.PETUGAS)
    def tarik_page():
        with ui.column().classes("w-full min-h-screen bg-gray-50"):
            create_header_with_auth()

            # Breadcrumb navigation
            with ui.row().classes("w-full px-6 py-4 bg-white shadow-sm"):
                ui.button("Dashboard", on_click=lambda: ui.navigate.to("/dashboard")).props("flat dense")
                ui.label("/").classes("mx-2 text-gray-400")
                ui.label("Penarikan Saldo").classes("font-semibold text-gray-700")

            # Main content
            with ui.column().classes("flex-1 p-6 max-w-6xl mx-auto w-full"):
                ui.label("Permintaan Penarikan Saldo").classes("text-2xl font-bold text-gray-800 mb-6")

                with ui.card().classes("w-full p-6 shadow-lg rounded-xl"):
                    withdrawal_requests_table()

                    # Auto-refresh every 60 seconds
                    ui.timer(60.0, withdrawal_requests_table.refresh)


@ui.refreshable
def pengepul_transaction_form():
    """Refreshable collector transaction form (Admin only)."""
    try:
        # Get data for form options
        pengepul_list = PengepulService.get_all_pengepul()
        jenis_sampah_list = JenisSampahService.get_all_jenis_sampah()

        if not pengepul_list:
            ui.label("Belum ada data pengepul. Tambahkan data pengepul terlebih dahulu.").classes("text-yellow-600")
            return

        if not jenis_sampah_list:
            ui.label("Belum ada data jenis sampah. Tambahkan data jenis sampah terlebih dahulu.").classes(
                "text-yellow-600"
            )
            return

        with ui.card().classes("w-full max-w-2xl p-6 shadow-lg rounded-xl"):
            ui.label("Transaksi Penjualan ke Pengepul").classes("text-2xl font-bold text-gray-800 mb-6")

            # Collector selection
            pengepul_options = {p.id: f"{p.kode} - {p.nama}" for p in pengepul_list if p.id}
            pengepul_select = ui.select(label="Pilih Pengepul", options=pengepul_options, value=None).classes(
                "w-full mb-4"
            )

            # Waste type selection
            jenis_options = {
                j.id: f"{j.kode} - {j.nama} (Rp {j.harga_jual:,.0f}/kg)" for j in jenis_sampah_list if j.id
            }
            jenis_select = ui.select(label="Pilih Jenis Sampah", options=jenis_options, value=None).classes(
                "w-full mb-4"
            )

            # Weight input
            berat_input = ui.number(label="Berat (kg)", min=0.001, step=0.1, format="%.3f").classes("w-full mb-4")

            # Selling price input (can override default)
            harga_jual_input = ui.number(label="Harga Jual (Rp/kg)", min=0, step=100).classes("w-full mb-4")

            # Auto-fill selling price when waste type is selected
            def update_selling_price():
                if jenis_select.value:
                    jenis_sampah = JenisSampahService.get_jenis_sampah_by_id(jenis_select.value)
                    if jenis_sampah:
                        harga_jual_input.set_value(float(jenis_sampah.harga_jual))

            jenis_select.on("update:model-value", lambda: update_selling_price())

            # Calculated total display
            total_label = ui.label("Total: Rp 0").classes("text-xl font-semibold text-green-600 mb-4")

            def calculate_total():
                if berat_input.value and harga_jual_input.value:
                    total_value = float(berat_input.value) * float(harga_jual_input.value)
                    total_label.set_text(f"Total: Rp {total_value:,.0f}")
                else:
                    total_label.set_text("Total: Rp 0")

            berat_input.on("update:model-value", lambda: calculate_total())
            harga_jual_input.on("update:model-value", lambda: calculate_total())

            # Error message
            error_label = ui.label("").classes("text-red-500 text-sm mb-4")

            # Submit button
            async def process_pengepul_transaction():
                try:
                    # Validate inputs
                    if not all([pengepul_select.value, jenis_select.value, berat_input.value, harga_jual_input.value]):
                        error_label.set_text("Semua field harus diisi")
                        return

                    if berat_input.value <= 0 or harga_jual_input.value <= 0:
                        error_label.set_text("Berat dan harga harus lebih dari 0")
                        return

                    # Create transaction
                    data = TransaksiPengepulCreate(
                        pengepul_id=int(pengepul_select.value) if pengepul_select.value else 0,
                        jenis_sampah_id=int(jenis_select.value) if jenis_select.value else 0,
                        berat=Decimal(str(berat_input.value)),
                        harga_jual=Decimal(str(harga_jual_input.value)),
                    )

                    result = TransaksiPengepulService.create_pengepul_transaction(data)
                    if result:
                        # Clear form
                        pengepul_select.set_value(None)
                        jenis_select.set_value(None)
                        berat_input.set_value(None)
                        harga_jual_input.set_value(None)
                        error_label.set_text("")
                        total_label.set_text("Total: Rp 0")

                        ui.notify(f"Transaksi berhasil! Total: Rp {result.total:,.0f}", type="positive")

                        # Refresh recent transactions
                        recent_pengepul_transactions.refresh()
                    else:
                        error_label.set_text("Gagal memproses transaksi")

                except Exception as e:
                    logging.error(f"Error processing transaction: {e}")
                    error_label.set_text(f"Error: {e}")

            ui.button("Proses Transaksi", on_click=process_pengepul_transaction, icon="local_shipping").classes(
                "w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-semibold"
            )

    except Exception as e:
        ui.label(f"Error loading form: {e}").classes("text-red-500")
        logging.error(f"Pengepul transaction form error: {e}")


@ui.refreshable
def recent_pengepul_transactions():
    """Show recent collector transactions."""
    try:
        transactions = TransaksiPengepulService.get_all_pengepul_transactions()[:10]  # Latest 10

        if not transactions:
            ui.label("Belum ada transaksi pengepul").classes("text-gray-500 text-center p-8")
            return

        with ui.card().classes("w-full p-6 shadow-lg rounded-xl mt-6"):
            ui.label("Transaksi Pengepul Terbaru").classes("text-xl font-bold text-gray-800 mb-4")

            columns = [
                {"name": "tanggal", "label": "Tanggal", "field": "tanggal"},
                {"name": "pengepul", "label": "Pengepul", "field": "pengepul"},
                {"name": "jenis_sampah", "label": "Jenis Sampah", "field": "jenis_sampah"},
                {"name": "berat", "label": "Berat (kg)", "field": "berat"},
                {"name": "harga_jual", "label": "Harga/kg", "field": "harga_jual"},
                {"name": "total", "label": "Total", "field": "total"},
            ]

            rows = []
            for t in transactions:
                try:
                    pengepul = PengepulService.get_pengepul_by_id(t.pengepul_id)
                    jenis_sampah = JenisSampahService.get_jenis_sampah_by_id(t.jenis_sampah_id)

                    rows.append(
                        {
                            "tanggal": t.tanggal.strftime("%d/%m/%Y %H:%M"),
                            "pengepul": f"{pengepul.kode} - {pengepul.nama}" if pengepul else "Unknown",
                            "jenis_sampah": jenis_sampah.nama if jenis_sampah else "Unknown",
                            "berat": f"{t.berat:.3f}",
                            "harga_jual": f"Rp {t.harga_jual:,.0f}",
                            "total": f"Rp {t.total:,.0f}",
                        }
                    )
                except Exception as e:
                    logging.warning(f"Error loading transaction data: {e}")
                    continue

            ui.table(columns=columns, rows=rows).classes("w-full")

    except Exception as e:
        ui.label(f"Error loading recent pengepul transactions: {e}").classes("text-red-500")
        logging.error(f"Recent pengepul transactions error: {e}")


def create_pengepul_page():
    """Create collector transaction page (Admin only)."""

    @ui.page("/transaksi/pengepul")
    @require_login(UserRole.ADMIN)
    def pengepul_page():
        with ui.column().classes("w-full min-h-screen bg-gray-50"):
            create_header_with_auth()

            # Breadcrumb navigation
            with ui.row().classes("w-full px-6 py-4 bg-white shadow-sm"):
                ui.button("Dashboard", on_click=lambda: ui.navigate.to("/dashboard")).props("flat dense")
                ui.label("/").classes("mx-2 text-gray-400")
                ui.label("Transaksi Pengepul").classes("font-semibold text-gray-700")

            # Main content
            with ui.column().classes("flex-1 p-6 max-w-4xl mx-auto w-full"):
                pengepul_transaction_form()
                recent_pengepul_transactions()


def create():
    """Initialize transaction UI module."""
    create_setoran_page()
    create_tarik_page()
    create_pengepul_page()
