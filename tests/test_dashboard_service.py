"""Tests for dashboard service."""

import pytest
from decimal import Decimal
from app.dashboard_service import DashboardService
from app.master_data_service import NasabahService, PetugasService, JenisSampahService, PengepulService
from app.transaction_service import TransaksiSetoranService, TransaksiTarikService, TransaksiPengepulService
from app.models import (
    NasabahCreate,
    PetugasCreate,
    JenisSampahCreate,
    PengepulCreate,
    TransaksiSetoranCreate,
    TransaksiTarikCreate,
    TransaksiPengepulCreate,
)
from app.database import reset_db


@pytest.fixture
def new_db():
    reset_db()
    yield
    reset_db()


@pytest.fixture
def sample_data(new_db):
    """Create comprehensive sample data for dashboard testing."""
    # Create nasabah
    nasabah1_data = NasabahCreate(
        kode="NAS001", nama="Customer One", nik="1111111111111111", alamat="Address 1", instansi="RT 01"
    )
    nasabah1 = NasabahService.create_nasabah(nasabah1_data)

    nasabah2_data = NasabahCreate(
        kode="NAS002", nama="Customer Two", nik="2222222222222222", alamat="Address 2", instansi="RT 02"
    )
    nasabah2 = NasabahService.create_nasabah(nasabah2_data)

    # Create petugas
    petugas1_data = PetugasCreate(
        kode="PET001", nama="Officer One", nik="3333333333333333", alamat="Officer Address 1", instansi="Bank Sampah"
    )
    petugas1 = PetugasService.create_petugas(petugas1_data)

    petugas2_data = PetugasCreate(
        kode="PET002", nama="Officer Two", nik="4444444444444444", alamat="Officer Address 2", instansi="Bank Sampah"
    )
    petugas2 = PetugasService.create_petugas(petugas2_data)

    # Create jenis sampah
    jenis1_data = JenisSampahCreate(
        kode="JS001", nama="Plastik PET", harga_beli=Decimal("2000"), harga_jual=Decimal("2500")
    )
    jenis1 = JenisSampahService.create_jenis_sampah(jenis1_data)

    jenis2_data = JenisSampahCreate(kode="JS002", nama="Kertas", harga_beli=Decimal("1500"), harga_jual=Decimal("1800"))
    jenis2 = JenisSampahService.create_jenis_sampah(jenis2_data)

    jenis3_data = JenisSampahCreate(
        kode="JS003", nama="Aluminium", harga_beli=Decimal("5000"), harga_jual=Decimal("6000")
    )
    jenis3 = JenisSampahService.create_jenis_sampah(jenis3_data)

    # Create pengepul
    pengepul_data = PengepulCreate(kode="PNG001", nama="Main Collector", alamat="Collector Address")
    pengepul = PengepulService.create_pengepul(pengepul_data)

    return {
        "nasabah": [nasabah1, nasabah2],
        "petugas": [petugas1, petugas2],
        "jenis_sampah": [jenis1, jenis2, jenis3],
        "pengepul": pengepul,
    }


def test_empty_dashboard_summary(new_db):
    """Test dashboard summary with no data."""
    summary = DashboardService.get_dashboard_summary()

    assert summary.total_customers == 0
    assert summary.total_officers == 0
    assert summary.total_waste_types == 0
    assert summary.total_deposit_transactions == 0
    assert summary.total_customer_balance == Decimal("0")
    assert summary.pending_withdrawal_requests == 0
    assert summary.total_waste_stock == Decimal("0")
    assert summary.total_waste_sent_to_collectors == Decimal("0")
    assert summary.total_profit == Decimal("0")


def test_dashboard_summary_with_data(sample_data):
    """Test dashboard summary with comprehensive data."""
    # Create deposit transactions
    setoran1_data = TransaksiSetoranCreate(
        nasabah_id=sample_data["nasabah"][0].id if sample_data["nasabah"][0].id else 0,
        petugas_id=sample_data["petugas"][0].id if sample_data["petugas"][0].id else 0,
        jenis_sampah_id=sample_data["jenis_sampah"][0].id if sample_data["jenis_sampah"][0].id else 0,
        berat=Decimal("5.0"),  # 5 * 2000 = 10,000
    )
    TransaksiSetoranService.create_setoran(setoran1_data)

    setoran2_data = TransaksiSetoranCreate(
        nasabah_id=sample_data["nasabah"][1].id if sample_data["nasabah"][1].id else 0,
        petugas_id=sample_data["petugas"][1].id if sample_data["petugas"][1].id else 0,
        jenis_sampah_id=sample_data["jenis_sampah"][1].id if sample_data["jenis_sampah"][1].id else 0,
        berat=Decimal("3.0"),  # 3 * 1500 = 4,500
    )
    TransaksiSetoranService.create_setoran(setoran2_data)

    setoran3_data = TransaksiSetoranCreate(
        nasabah_id=sample_data["nasabah"][0].id if sample_data["nasabah"][0].id else 0,
        petugas_id=sample_data["petugas"][0].id if sample_data["petugas"][0].id else 0,
        jenis_sampah_id=sample_data["jenis_sampah"][2].id if sample_data["jenis_sampah"][2].id else 0,
        berat=Decimal("1.0"),  # 1 * 5000 = 5,000
    )
    TransaksiSetoranService.create_setoran(setoran3_data)

    # Create withdrawal transactions (some pending, some completed)
    tarik1_data = TransaksiTarikCreate(
        nasabah_id=sample_data["nasabah"][0].id if sample_data["nasabah"][0].id else 0,
        petugas_id=sample_data["petugas"][0].id if sample_data["petugas"][0].id else 0,
        jumlah=Decimal("3000"),
    )
    tarik1 = TransaksiTarikService.create_tarik(tarik1_data)

    tarik2_data = TransaksiTarikCreate(
        nasabah_id=sample_data["nasabah"][1].id if sample_data["nasabah"][1].id else 0,
        petugas_id=sample_data["petugas"][1].id if sample_data["petugas"][1].id else 0,
        jumlah=Decimal("2000"),
    )
    TransaksiTarikService.create_tarik(tarik2_data)

    # Approve one withdrawal
    TransaksiTarikService.approve_tarik(tarik1.id if tarik1 and tarik1.id else 0)

    # Create collector transactions
    pengepul1_data = TransaksiPengepulCreate(
        pengepul_id=sample_data["pengepul"].id if sample_data["pengepul"].id else 0,
        jenis_sampah_id=sample_data["jenis_sampah"][0].id if sample_data["jenis_sampah"][0].id else 0,
        berat=Decimal("2.0"),  # 2 * 2500 = 5,000
        harga_jual=Decimal("2500"),
    )
    TransaksiPengepulService.create_pengepul_transaction(pengepul1_data)

    pengepul2_data = TransaksiPengepulCreate(
        pengepul_id=sample_data["pengepul"].id if sample_data["pengepul"].id else 0,
        jenis_sampah_id=sample_data["jenis_sampah"][1].id if sample_data["jenis_sampah"][1].id else 0,
        berat=Decimal("1.5"),  # 1.5 * 1800 = 2,700
        harga_jual=Decimal("1800"),
    )
    TransaksiPengepulService.create_pengepul_transaction(pengepul2_data)

    # Get dashboard summary
    summary = DashboardService.get_dashboard_summary()

    # Verify counts
    assert summary.total_customers == 2
    assert summary.total_officers == 2
    assert summary.total_waste_types == 3
    assert summary.total_deposit_transactions == 3

    # Verify balance calculation
    # Customer 1: 10,000 + 5,000 - 3,000 = 12,000
    # Customer 2: 4,500 = 4,500
    # Total: 16,500
    assert summary.total_customer_balance == Decimal("16500")

    # Verify pending withdrawals
    assert summary.pending_withdrawal_requests == 1  # One pending

    # Verify waste stock calculation
    # Deposited: 5.0 (PET) + 3.0 (Kertas) + 1.0 (Aluminium) = 9.0 kg
    # Sold: 2.0 (PET) + 1.5 (Kertas) = 3.5 kg
    # Stock: 9.0 - 3.5 = 5.5 kg
    assert summary.total_waste_stock == Decimal("5.5")

    # Verify total sent to collectors
    assert summary.total_waste_sent_to_collectors == Decimal("3.5")

    # Verify profit calculation
    # Revenue from collectors: 5,000 + 2,700 = 7,700
    # Cost to customers: 10,000 + 4,500 + 5,000 = 19,500
    # Profit: 7,700 - 19,500 = -11,800 (loss)
    assert summary.total_profit == Decimal("-11800")


def test_dashboard_summary_profit_positive(sample_data):
    """Test dashboard with positive profit scenario."""
    # Create setoran with low cost
    setoran_data = TransaksiSetoranCreate(
        nasabah_id=sample_data["nasabah"][0].id if sample_data["nasabah"][0].id else 0,
        petugas_id=sample_data["petugas"][0].id if sample_data["petugas"][0].id else 0,
        jenis_sampah_id=sample_data["jenis_sampah"][0].id if sample_data["jenis_sampah"][0].id else 0,
        berat=Decimal("2.0"),  # 2 * 2000 = 4,000 cost
    )
    TransaksiSetoranService.create_setoran(setoran_data)

    # Create collector transaction with higher revenue
    pengepul_data = TransaksiPengepulCreate(
        pengepul_id=sample_data["pengepul"].id if sample_data["pengepul"].id else 0,
        jenis_sampah_id=sample_data["jenis_sampah"][0].id if sample_data["jenis_sampah"][0].id else 0,
        berat=Decimal("2.0"),  # 2 * 2500 = 5,000 revenue
        harga_jual=Decimal("2500"),
    )
    TransaksiPengepulService.create_pengepul_transaction(pengepul_data)

    summary = DashboardService.get_dashboard_summary()

    # Profit: 5,000 - 4,000 = 1,000
    assert summary.total_profit == Decimal("1000")


def test_dashboard_summary_no_stock_negative(sample_data):
    """Test that waste stock never goes negative."""
    # Create small deposit
    setoran_data = TransaksiSetoranCreate(
        nasabah_id=sample_data["nasabah"][0].id if sample_data["nasabah"][0].id else 0,
        petugas_id=sample_data["petugas"][0].id if sample_data["petugas"][0].id else 0,
        jenis_sampah_id=sample_data["jenis_sampah"][0].id if sample_data["jenis_sampah"][0].id else 0,
        berat=Decimal("1.0"),
    )
    TransaksiSetoranService.create_setoran(setoran_data)

    # Create larger collector transaction (shouldn't be possible in real scenario)
    pengepul_data = TransaksiPengepulCreate(
        pengepul_id=sample_data["pengepul"].id if sample_data["pengepul"].id else 0,
        jenis_sampah_id=sample_data["jenis_sampah"][0].id if sample_data["jenis_sampah"][0].id else 0,
        berat=Decimal("2.0"),  # More than deposited
        harga_jual=Decimal("2500"),
    )
    TransaksiPengepulService.create_pengepul_transaction(pengepul_data)

    summary = DashboardService.get_dashboard_summary()

    # Stock should be 0, not negative
    assert summary.total_waste_stock == Decimal("0")
