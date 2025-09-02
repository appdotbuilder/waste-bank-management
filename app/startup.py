"""Application startup configuration."""

import logging
from decimal import Decimal
from app.database import create_tables
from app.auth_service import create_user
from app.master_data_service import NasabahService, PetugasService, JenisSampahService, PengepulService
from app.models import UserRole, NasabahCreate, PetugasCreate, JenisSampahCreate, PengepulCreate
import app.auth_ui
import app.dashboard_ui
import app.master_data_ui
import app.transaction_ui
import app.reports_ui


def create_initial_data():
    """Create initial data for demo purposes."""
    try:
        # Create admin user
        create_user(
            username="admin",
            password="admin123",
            role=UserRole.ADMIN,
            nama="Administrator",
            nik="1111111111111111",
            alamat="Jl. Admin No. 1",
            instansi="Bank Sampah Kelurahan Seberang Mesjid",
        )

        # Create petugas user and data
        create_user(
            username="petugas",
            password="petugas123",
            role=UserRole.PETUGAS,
            nama="Petugas Utama",
            nik="2222222222222222",
            alamat="Jl. Petugas No. 1",
            instansi="Bank Sampah Kelurahan Seberang Mesjid",
        )

        # Create corresponding petugas data
        petugas_data = PetugasCreate(
            kode="PET001",
            nama="Petugas Utama",
            nik="2222222222222222",
            alamat="Jl. Petugas No. 1",
            instansi="Bank Sampah Kelurahan Seberang Mesjid",
        )
        PetugasService.create_petugas(petugas_data)

        # Create sample nasabah users and data
        nasabah_users = [
            ("nasabah1", "Ibu Sari", "3333333333333333", "Jl. Mawar No. 12", "RT 01 RW 02"),
            ("nasabah2", "Bapak Joko", "4444444444444444", "Jl. Melati No. 25", "RT 02 RW 01"),
            ("nasabah3", "Ibu Dewi", "5555555555555555", "Jl. Kenanga No. 8", "RT 01 RW 01"),
        ]

        for i, (username, nama, nik, alamat, instansi) in enumerate(nasabah_users, 1):
            # Create user account
            create_user(
                username=username,
                password="nasabah123",
                role=UserRole.NASABAH,
                nama=nama,
                nik=nik,
                alamat=alamat,
                instansi=instansi,
            )

            # Create nasabah data
            nasabah_data = NasabahCreate(kode=f"NAS{i:03d}", nama=nama, nik=nik, alamat=alamat, instansi=instansi)
            NasabahService.create_nasabah(nasabah_data)

        # Create sample jenis sampah
        jenis_sampah_list = [
            ("JS001", "Plastik PET", Decimal("2000"), Decimal("2500")),
            ("JS002", "Plastik PP", Decimal("1800"), Decimal("2200")),
            ("JS003", "Kertas HVS", Decimal("1500"), Decimal("1800")),
            ("JS004", "Kertas Koran", Decimal("1200"), Decimal("1500")),
            ("JS005", "Kardus", Decimal("1300"), Decimal("1600")),
            ("JS006", "Kaleng Aluminium", Decimal("8000"), Decimal("10000")),
            ("JS007", "Botol Kaca", Decimal("1000"), Decimal("1200")),
            ("JS008", "Besi", Decimal("3000"), Decimal("3500")),
        ]

        for kode, nama, harga_beli, harga_jual in jenis_sampah_list:
            jenis_data = JenisSampahCreate(kode=kode, nama=nama, harga_beli=harga_beli, harga_jual=harga_jual)
            JenisSampahService.create_jenis_sampah(jenis_data)

        # Create sample pengepul
        pengepul_list = [
            ("PNG001", "CV. Maju Jaya", "Jl. Industri No. 15, Medan"),
            ("PNG002", "UD. Berkah Sampah", "Jl. Perdagangan No. 28, Medan"),
            ("PNG003", "PT. Daur Ulang Nusantara", "Kawasan Industri Medan, Blok A-12"),
        ]

        for kode, nama, alamat in pengepul_list:
            pengepul_data = PengepulCreate(kode=kode, nama=nama, alamat=alamat)
            PengepulService.create_pengepul(pengepul_data)

        logging.info("Initial data created successfully")

    except Exception as e:
        logging.info(f"Error creating initial data (might already exist): {e}")


def startup() -> None:
    """Main startup function called before the first request."""
    # Create database tables
    create_tables()

    # Create initial demo data
    create_initial_data()

    # Initialize UI modules
    app.auth_ui.create()
    app.dashboard_ui.create()
    app.master_data_ui.create()
    app.transaction_ui.create()
    app.reports_ui.create()
