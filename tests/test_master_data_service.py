"""Tests for master data services."""

import pytest
from decimal import Decimal
from app.master_data_service import NasabahService, PetugasService, JenisSampahService, PengepulService
from app.models import NasabahCreate, NasabahUpdate, PetugasCreate, JenisSampahCreate, JenisSampahUpdate, PengepulCreate
from app.database import reset_db


@pytest.fixture
def new_db():
    reset_db()
    yield
    reset_db()


class TestNasabahService:
    """Test NasabahService functionality."""

    def test_create_nasabah(self, new_db):
        data = NasabahCreate(
            kode="NAS001", nama="John Doe", nik="1234567890123456", alamat="Jl. Nasabah No. 1", instansi="RT 01 RW 02"
        )

        nasabah = NasabahService.create_nasabah(data)
        assert nasabah.id is not None
        assert nasabah.kode == "NAS001"
        assert nasabah.nama == "John Doe"
        assert nasabah.saldo == Decimal("0")

    def test_get_nasabah_by_id(self, new_db):
        data = NasabahCreate(
            kode="NAS002", nama="Jane Doe", nik="9876543210987654", alamat="Jl. Nasabah No. 2", instansi="RT 02 RW 01"
        )

        nasabah = NasabahService.create_nasabah(data)
        retrieved = NasabahService.get_nasabah_by_id(nasabah.id if nasabah.id else 0)

        assert retrieved is not None
        assert retrieved.kode == "NAS002"

        # Test non-existent ID
        non_existent = NasabahService.get_nasabah_by_id(9999)
        assert non_existent is None

    def test_get_nasabah_by_kode(self, new_db):
        data = NasabahCreate(
            kode="NAS003", nama="Bob Smith", nik="1111222233334444", alamat="Jl. Bob No. 3", instansi="RT 03"
        )

        NasabahService.create_nasabah(data)
        retrieved = NasabahService.get_nasabah_by_kode("NAS003")

        assert retrieved is not None
        assert retrieved.nama == "Bob Smith"

        # Test non-existent kode
        non_existent = NasabahService.get_nasabah_by_kode("NONEXISTENT")
        assert non_existent is None

    def test_get_all_nasabah(self, new_db):
        # Initially empty
        nasabah_list = NasabahService.get_all_nasabah()
        assert len(nasabah_list) == 0

        # Create multiple nasabah
        for i in range(3):
            data = NasabahCreate(
                kode=f"NAS{i:03d}", nama=f"Nasabah {i}", nik=f"{i:016d}", alamat=f"Address {i}", instansi=f"RT {i:02d}"
            )
            NasabahService.create_nasabah(data)

        nasabah_list = NasabahService.get_all_nasabah()
        assert len(nasabah_list) == 3
        assert all(n.kode.startswith("NAS") for n in nasabah_list)

    def test_update_nasabah(self, new_db):
        data = NasabahCreate(
            kode="NAS004",
            nama="Original Name",
            nik="5555666677778888",
            alamat="Original Address",
            instansi="Original Instansi",
        )

        nasabah = NasabahService.create_nasabah(data)

        # Update data
        update_data = NasabahUpdate(nama="Updated Name", alamat="Updated Address")

        updated = NasabahService.update_nasabah(nasabah.id if nasabah.id else 0, update_data)
        assert updated is not None
        assert updated.nama == "Updated Name"
        assert updated.alamat == "Updated Address"
        assert updated.instansi == "Original Instansi"  # Unchanged

        # Update non-existent
        non_updated = NasabahService.update_nasabah(9999, update_data)
        assert non_updated is None

    def test_update_saldo(self, new_db):
        data = NasabahCreate(
            kode="NAS005", nama="Saldo Test", nik="9999000011112222", alamat="Saldo Address", instansi="Saldo RT"
        )

        nasabah = NasabahService.create_nasabah(data)

        # Add to balance
        success = NasabahService.update_saldo(nasabah.id if nasabah.id else 0, Decimal("50.00"), "add")
        assert success

        updated = NasabahService.get_nasabah_by_id(nasabah.id if nasabah.id else 0)
        assert updated is not None
        assert updated.saldo == Decimal("50.00")

        # Subtract from balance
        success = NasabahService.update_saldo(nasabah.id if nasabah.id else 0, Decimal("20.00"), "subtract")
        assert success

        updated = NasabahService.get_nasabah_by_id(nasabah.id if nasabah.id else 0)
        assert updated is not None
        assert updated.saldo == Decimal("30.00")

        # Try to subtract more than available
        success = NasabahService.update_saldo(nasabah.id if nasabah.id else 0, Decimal("50.00"), "subtract")
        assert not success

        # Invalid operation
        success = NasabahService.update_saldo(nasabah.id if nasabah.id else 0, Decimal("10.00"), "invalid")
        assert not success

        # Non-existent nasabah
        success = NasabahService.update_saldo(9999, Decimal("10.00"), "add")
        assert not success

    def test_delete_nasabah(self, new_db):
        data = NasabahCreate(
            kode="NAS006", nama="To Delete", nik="1111000022223333", alamat="Delete Address", instansi="Delete RT"
        )

        nasabah = NasabahService.create_nasabah(data)

        # Verify exists
        retrieved = NasabahService.get_nasabah_by_id(nasabah.id if nasabah.id else 0)
        assert retrieved is not None

        # Delete
        success = NasabahService.delete_nasabah(nasabah.id if nasabah.id else 0)
        assert success

        # Verify deleted
        retrieved = NasabahService.get_nasabah_by_id(nasabah.id if nasabah.id else 0)
        assert retrieved is None

        # Delete non-existent
        success = NasabahService.delete_nasabah(9999)
        assert not success

    def test_get_total_count(self, new_db):
        assert NasabahService.get_total_count() == 0

        # Create 2 nasabah
        for i in range(2):
            data = NasabahCreate(
                kode=f"COUNT{i:03d}",
                nama=f"Count {i}",
                nik=f"{i:016d}",
                alamat=f"Count Address {i}",
                instansi=f"Count RT {i}",
            )
            NasabahService.create_nasabah(data)

        assert NasabahService.get_total_count() == 2

    def test_get_total_balance(self, new_db):
        assert NasabahService.get_total_balance() == Decimal("0")

        # Create nasabah with balances
        data1 = NasabahCreate(
            kode="BAL001", nama="Balance 1", nik="1111111111111111", alamat="Bal Address 1", instansi="Bal RT 1"
        )
        nasabah1 = NasabahService.create_nasabah(data1)
        NasabahService.update_saldo(nasabah1.id if nasabah1.id else 0, Decimal("100.00"), "add")

        data2 = NasabahCreate(
            kode="BAL002", nama="Balance 2", nik="2222222222222222", alamat="Bal Address 2", instansi="Bal RT 2"
        )
        nasabah2 = NasabahService.create_nasabah(data2)
        NasabahService.update_saldo(nasabah2.id if nasabah2.id else 0, Decimal("50.00"), "add")

        total_balance = NasabahService.get_total_balance()
        assert total_balance == Decimal("150.00")


class TestPetugasService:
    """Test PetugasService functionality."""

    def test_create_petugas(self, new_db):
        data = PetugasCreate(
            kode="PET001",
            nama="Officer One",
            nik="1122334455667788",
            alamat="Jl. Officer No. 1",
            instansi="Bank Sampah Kelurahan",
        )

        petugas = PetugasService.create_petugas(data)
        assert petugas.id is not None
        assert petugas.kode == "PET001"
        assert petugas.nama == "Officer One"

    def test_get_petugas_by_kode(self, new_db):
        data = PetugasCreate(
            kode="PET002",
            nama="Officer Two",
            nik="8877665544332211",
            alamat="Jl. Officer No. 2",
            instansi="Bank Sampah",
        )

        PetugasService.create_petugas(data)
        retrieved = PetugasService.get_petugas_by_kode("PET002")

        assert retrieved is not None
        assert retrieved.nama == "Officer Two"

        # Non-existent
        non_existent = PetugasService.get_petugas_by_kode("NONEXISTENT")
        assert non_existent is None

    def test_get_total_count(self, new_db):
        assert PetugasService.get_total_count() == 0

        # Create 2 petugas
        for i in range(2):
            data = PetugasCreate(
                kode=f"COUNT{i:03d}",
                nama=f"Officer Count {i}",
                nik=f"{i + 1000:016d}",
                alamat=f"Officer Address {i}",
                instansi=f"Bank Sampah {i}",
            )
            PetugasService.create_petugas(data)

        assert PetugasService.get_total_count() == 2


class TestJenisSampahService:
    """Test JenisSampahService functionality."""

    def test_create_jenis_sampah(self, new_db):
        data = JenisSampahCreate(
            kode="JS001", nama="Plastik PET", harga_beli=Decimal("2000"), harga_jual=Decimal("2500")
        )

        jenis_sampah = JenisSampahService.create_jenis_sampah(data)
        assert jenis_sampah.id is not None
        assert jenis_sampah.kode == "JS001"
        assert jenis_sampah.nama == "Plastik PET"
        assert jenis_sampah.harga_beli == Decimal("2000")
        assert jenis_sampah.harga_jual == Decimal("2500")

    def test_update_jenis_sampah(self, new_db):
        data = JenisSampahCreate(
            kode="JS002", nama="Original Name", harga_beli=Decimal("1000"), harga_jual=Decimal("1200")
        )

        jenis_sampah = JenisSampahService.create_jenis_sampah(data)

        # Update prices
        update_data = JenisSampahUpdate(harga_beli=Decimal("1500"), harga_jual=Decimal("1800"))

        updated = JenisSampahService.update_jenis_sampah(jenis_sampah.id if jenis_sampah.id else 0, update_data)
        assert updated is not None
        assert updated.harga_beli == Decimal("1500")
        assert updated.harga_jual == Decimal("1800")
        assert updated.nama == "Original Name"  # Unchanged

    def test_get_total_count(self, new_db):
        assert JenisSampahService.get_total_count() == 0

        # Create 3 jenis sampah
        for i in range(3):
            data = JenisSampahCreate(
                kode=f"JS{i:03d}",
                nama=f"Sampah Type {i}",
                harga_beli=Decimal(f"{1000 + i * 100}"),
                harga_jual=Decimal(f"{1200 + i * 100}"),
            )
            JenisSampahService.create_jenis_sampah(data)

        assert JenisSampahService.get_total_count() == 3


class TestPengepulService:
    """Test PengepulService functionality."""

    def test_create_pengepul(self, new_db):
        data = PengepulCreate(kode="PNG001", nama="Pengepul Utama", alamat="Jl. Pengepul No. 1")

        pengepul = PengepulService.create_pengepul(data)
        assert pengepul.id is not None
        assert pengepul.kode == "PNG001"
        assert pengepul.nama == "Pengepul Utama"
        assert pengepul.alamat == "Jl. Pengepul No. 1"

    def test_get_pengepul_by_kode(self, new_db):
        data = PengepulCreate(kode="PNG002", nama="Pengepul Kedua", alamat="Jl. Pengepul No. 2")

        PengepulService.create_pengepul(data)
        retrieved = PengepulService.get_pengepul_by_kode("PNG002")

        assert retrieved is not None
        assert retrieved.nama == "Pengepul Kedua"

        # Non-existent
        non_existent = PengepulService.get_pengepul_by_kode("NONEXISTENT")
        assert non_existent is None
