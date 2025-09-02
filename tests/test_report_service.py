"""Tests for report service."""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from app.report_service import ReportService
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
def comprehensive_test_data(new_db):
    """Create comprehensive test data for report testing."""
    # Create master data
    nasabah_data = NasabahCreate(
        kode="NAS001", nama="Test Customer", nik="1234567890123456", alamat="Test Address", instansi="Test RT"
    )
    nasabah = NasabahService.create_nasabah(nasabah_data)

    petugas_data = PetugasCreate(
        kode="PET001", nama="Test Officer", nik="9876543210987654", alamat="Officer Address", instansi="Bank Sampah"
    )
    petugas = PetugasService.create_petugas(petugas_data)

    jenis_sampah_data = JenisSampahCreate(
        kode="JS001", nama="Plastik PET", harga_beli=Decimal("2000"), harga_jual=Decimal("2500")
    )
    jenis_sampah = JenisSampahService.create_jenis_sampah(jenis_sampah_data)

    pengepul_data = PengepulCreate(kode="PNG001", nama="Test Collector", alamat="Collector Address")
    pengepul = PengepulService.create_pengepul(pengepul_data)

    # Create transactions
    # Deposit transaction
    setoran_data = TransaksiSetoranCreate(
        nasabah_id=nasabah.id if nasabah.id else 0,
        petugas_id=petugas.id if petugas.id else 0,
        jenis_sampah_id=jenis_sampah.id if jenis_sampah.id else 0,
        berat=Decimal("5.0"),
    )
    setoran = TransaksiSetoranService.create_setoran(setoran_data)

    # Withdrawal transaction
    tarik_data = TransaksiTarikCreate(
        nasabah_id=nasabah.id if nasabah.id else 0, petugas_id=petugas.id if petugas.id else 0, jumlah=Decimal("3000")
    )
    tarik = TransaksiTarikService.create_tarik(tarik_data)
    if tarik:
        TransaksiTarikService.approve_tarik(tarik.id if tarik.id else 0)

    # Collector transaction
    pengepul_tx_data = TransaksiPengepulCreate(
        pengepul_id=pengepul.id if pengepul.id else 0,
        jenis_sampah_id=jenis_sampah.id if jenis_sampah.id else 0,
        berat=Decimal("3.0"),
        harga_jual=Decimal("2500"),
    )
    pengepul_tx = TransaksiPengepulService.create_pengepul_transaction(pengepul_tx_data)

    return {
        "nasabah": nasabah,
        "petugas": petugas,
        "jenis_sampah": jenis_sampah,
        "pengepul": pengepul,
        "setoran": setoran,
        "tarik": tarik,
        "pengepul_tx": pengepul_tx,
    }


def test_generate_transaction_report_basic(comprehensive_test_data):
    """Test basic transaction report generation."""
    today = date.today()

    # Get report for today
    report = ReportService.generate_transaction_report(today, today)

    # Should have 3 transactions (setoran, tarik, pengepul)
    assert len(report) == 3

    # Check transaction types are represented
    types = {t.transaction_type for t in report}
    assert types == {"setoran", "tarik", "pengepul"}

    # Check data completeness
    for transaction in report:
        assert transaction.transaction_id > 0
        assert transaction.nilai > 0
        assert isinstance(transaction.tanggal, datetime)


def test_generate_transaction_report_date_filtering(comprehensive_test_data):
    """Test transaction report date filtering."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    # Report for today should have transactions
    today_report = ReportService.generate_transaction_report(today, today)
    assert len(today_report) == 3

    # Report for yesterday should be empty
    yesterday_report = ReportService.generate_transaction_report(yesterday, yesterday)
    assert len(yesterday_report) == 0

    # Report for tomorrow should be empty
    tomorrow_report = ReportService.generate_transaction_report(tomorrow, tomorrow)
    assert len(tomorrow_report) == 0


def test_generate_transaction_report_setoran_details(comprehensive_test_data):
    """Test setoran transaction details in report."""
    today = date.today()
    report = ReportService.generate_transaction_report(today, today)

    # Find setoran transaction
    setoran_report = next(t for t in report if t.transaction_type == "setoran")

    assert setoran_report.nasabah_nama == "Test Customer"
    assert setoran_report.petugas_nama == "Test Officer"
    assert setoran_report.jenis_sampah_nama == "Plastik PET"
    assert setoran_report.berat == Decimal("5.0")
    assert setoran_report.nilai == Decimal("10000")  # 5.0 * 2000


def test_generate_transaction_report_tarik_details(comprehensive_test_data):
    """Test withdrawal transaction details in report."""
    today = date.today()
    report = ReportService.generate_transaction_report(today, today)

    # Find tarik transaction
    tarik_report = next(t for t in report if t.transaction_type == "tarik")

    assert tarik_report.nasabah_nama == "Test Customer"
    assert tarik_report.petugas_nama == "Test Officer"
    assert tarik_report.jenis_sampah_nama is None  # No waste type for withdrawal
    assert tarik_report.berat is None  # No weight for withdrawal
    assert tarik_report.nilai == Decimal("3000")


def test_generate_transaction_report_pengepul_details(comprehensive_test_data):
    """Test collector transaction details in report."""
    today = date.today()
    report = ReportService.generate_transaction_report(today, today)

    # Find pengepul transaction
    pengepul_report = next(t for t in report if t.transaction_type == "pengepul")

    assert pengepul_report.pengepul_nama == "Test Collector"
    assert pengepul_report.jenis_sampah_nama == "Plastik PET"
    assert pengepul_report.berat == Decimal("3.0")
    assert pengepul_report.nilai == Decimal("7500")  # 3.0 * 2500


def test_generate_customer_report_basic(comprehensive_test_data):
    """Test basic customer report generation."""
    nasabah_id = comprehensive_test_data["nasabah"].id if comprehensive_test_data["nasabah"].id else 0

    report = ReportService.generate_customer_report(nasabah_id)

    assert report.nasabah_kode == "NAS001"
    assert report.nasabah_nama == "Test Customer"
    assert report.total_setoran == Decimal("10000")  # 5kg * 2000
    assert report.total_tarik == Decimal("3000")  # Completed withdrawal
    assert report.saldo_current == Decimal("7000")  # 10000 - 3000


def test_generate_customer_report_nonexistent(new_db):
    """Test customer report for non-existent customer."""
    with pytest.raises(ValueError, match="Customer not found"):
        ReportService.generate_customer_report(9999)


def test_get_daily_transactions(comprehensive_test_data):
    """Test daily transaction report."""
    today = date.today()

    daily_report = ReportService.get_daily_transactions(today)

    assert len(daily_report) == 3
    assert all(t.tanggal.date() == today for t in daily_report)


def test_get_monthly_transactions(comprehensive_test_data):
    """Test monthly transaction report."""
    today = date.today()

    monthly_report = ReportService.get_monthly_transactions(today.year, today.month)

    assert len(monthly_report) == 3
    assert all(t.tanggal.year == today.year and t.tanggal.month == today.month for t in monthly_report)


def test_get_yearly_transactions(comprehensive_test_data):
    """Test yearly transaction report."""
    today = date.today()

    yearly_report = ReportService.get_yearly_transactions(today.year)

    assert len(yearly_report) == 3
    assert all(t.tanggal.year == today.year for t in yearly_report)


def test_get_all_customer_reports(comprehensive_test_data):
    """Test getting reports for all customers."""
    # Create additional customer
    nasabah2_data = NasabahCreate(
        kode="NAS002", nama="Customer Two", nik="2222333344445555", alamat="Address Two", instansi="RT 02"
    )
    nasabah2 = NasabahService.create_nasabah(nasabah2_data)

    # Create a deposit for the second customer
    setoran2_data = TransaksiSetoranCreate(
        nasabah_id=nasabah2.id if nasabah2.id else 0,
        petugas_id=comprehensive_test_data["petugas"].id if comprehensive_test_data["petugas"].id else 0,
        jenis_sampah_id=comprehensive_test_data["jenis_sampah"].id if comprehensive_test_data["jenis_sampah"].id else 0,
        berat=Decimal("2.0"),
    )
    TransaksiSetoranService.create_setoran(setoran2_data)

    # Get all customer reports
    all_reports = ReportService.get_all_customer_reports()

    assert len(all_reports) == 2

    # Check that reports are sorted by kode
    assert all_reports[0].nasabah_kode == "NAS001"
    assert all_reports[1].nasabah_kode == "NAS002"

    # Verify data for first customer
    report1 = all_reports[0]
    assert report1.nasabah_nama == "Test Customer"
    assert report1.total_setoran == Decimal("10000")
    assert report1.total_tarik == Decimal("3000")
    assert report1.saldo_current == Decimal("7000")

    # Verify data for second customer
    report2 = all_reports[1]
    assert report2.nasabah_nama == "Customer Two"
    assert report2.total_setoran == Decimal("4000")  # 2kg * 2000
    assert report2.total_tarik == Decimal("0")  # No withdrawals
    assert report2.saldo_current == Decimal("4000")


def test_transaction_report_sorting(comprehensive_test_data):
    """Test that transaction reports are sorted by date descending."""
    today = date.today()

    # Wait a bit and create another transaction to ensure different timestamps
    import time

    time.sleep(0.1)

    # Create another setoran transaction
    setoran2_data = TransaksiSetoranCreate(
        nasabah_id=comprehensive_test_data["nasabah"].id if comprehensive_test_data["nasabah"].id else 0,
        petugas_id=comprehensive_test_data["petugas"].id if comprehensive_test_data["petugas"].id else 0,
        jenis_sampah_id=comprehensive_test_data["jenis_sampah"].id if comprehensive_test_data["jenis_sampah"].id else 0,
        berat=Decimal("1.0"),
    )
    TransaksiSetoranService.create_setoran(setoran2_data)

    report = ReportService.generate_transaction_report(today, today)

    # Should have 4 transactions now
    assert len(report) == 4

    # Check that they are sorted by date descending (newest first)
    for i in range(len(report) - 1):
        assert report[i].tanggal >= report[i + 1].tanggal


def test_empty_reports(new_db):
    """Test report generation with no data."""
    today = date.today()

    # Transaction report should be empty
    empty_report = ReportService.generate_transaction_report(today, today)
    assert len(empty_report) == 0

    # All customer reports should be empty
    empty_customers = ReportService.get_all_customer_reports()
    assert len(empty_customers) == 0


def test_report_with_pending_withdrawals(comprehensive_test_data):
    """Test that pending withdrawals are not included in reports."""
    # Create a pending withdrawal
    pending_tarik_data = TransaksiTarikCreate(
        nasabah_id=comprehensive_test_data["nasabah"].id if comprehensive_test_data["nasabah"].id else 0,
        petugas_id=comprehensive_test_data["petugas"].id if comprehensive_test_data["petugas"].id else 0,
        jumlah=Decimal("1000"),
    )
    TransaksiTarikService.create_tarik(pending_tarik_data)

    today = date.today()
    report = ReportService.generate_transaction_report(today, today)

    # Should still have 3 transactions (not 4) because pending withdrawal is excluded
    assert len(report) == 3

    # Verify only the completed withdrawal is in the report
    tarik_transactions = [t for t in report if t.transaction_type == "tarik"]
    assert len(tarik_transactions) == 1
    assert tarik_transactions[0].nilai == Decimal("3000")  # The completed one
