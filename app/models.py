from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    PETUGAS = "petugas"
    NASABAH = "nasabah"


# Persistent models (stored in database)
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    role: UserRole = Field(description="User role: admin, petugas, or nasabah")
    nama: str = Field(max_length=100)
    nik: str = Field(max_length=20, unique=True, description="NIK/NIP")
    alamat: str = Field(max_length=255)
    instansi: str = Field(max_length=100)
    username: str = Field(max_length=50, unique=True)
    password: str = Field(max_length=255, description="Hashed password")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Nasabah(SQLModel, table=True):
    __tablename__ = "nasabah"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    kode: str = Field(max_length=20, unique=True, description="Customer code")
    nama: str = Field(max_length=100)
    nik: str = Field(max_length=20, unique=True)
    alamat: str = Field(max_length=255)
    instansi: str = Field(max_length=100)
    saldo: Decimal = Field(default=Decimal("0"), decimal_places=2, description="Customer balance")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    transaksi_setoran: List["TransaksiSetoran"] = Relationship(back_populates="nasabah")
    transaksi_tarik: List["TransaksiTarik"] = Relationship(back_populates="nasabah")


class Petugas(SQLModel, table=True):
    __tablename__ = "petugas"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    kode: str = Field(max_length=20, unique=True, description="Officer code")
    nama: str = Field(max_length=100)
    nik: str = Field(max_length=20, unique=True)
    alamat: str = Field(max_length=255)
    instansi: str = Field(max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    transaksi_setoran: List["TransaksiSetoran"] = Relationship(back_populates="petugas")
    transaksi_tarik: List["TransaksiTarik"] = Relationship(back_populates="petugas")


class JenisSampah(SQLModel, table=True):
    __tablename__ = "jenis_sampah"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    kode: str = Field(max_length=20, unique=True, description="Waste type code")
    nama: str = Field(max_length=100, description="Waste type name")
    harga_beli: Decimal = Field(decimal_places=2, description="Purchase price from customer per kg")
    harga_jual: Decimal = Field(decimal_places=2, description="Sale price to collector per kg")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    transaksi_setoran: List["TransaksiSetoran"] = Relationship(back_populates="jenis_sampah")
    transaksi_pengepul: List["TransaksiPengepul"] = Relationship(back_populates="jenis_sampah")


class Pengepul(SQLModel, table=True):
    __tablename__ = "pengepul"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    kode: str = Field(max_length=20, unique=True, description="Collector code")
    nama: str = Field(max_length=100)
    alamat: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    transaksi_pengepul: List["TransaksiPengepul"] = Relationship(back_populates="pengepul")


class TransaksiSetoran(SQLModel, table=True):
    __tablename__ = "transaksi_setoran"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    nasabah_id: int = Field(foreign_key="nasabah.id")
    petugas_id: int = Field(foreign_key="petugas.id")
    jenis_sampah_id: int = Field(foreign_key="jenis_sampah.id")
    berat: Decimal = Field(decimal_places=3, description="Weight in kg")
    nilai: Decimal = Field(decimal_places=2, description="Total value (berat × harga_beli)")
    tanggal: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    nasabah: Nasabah = Relationship(back_populates="transaksi_setoran")
    petugas: Petugas = Relationship(back_populates="transaksi_setoran")
    jenis_sampah: JenisSampah = Relationship(back_populates="transaksi_setoran")


class TransaksiTarik(SQLModel, table=True):
    __tablename__ = "transaksi_tarik"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    nasabah_id: int = Field(foreign_key="nasabah.id")
    petugas_id: int = Field(foreign_key="petugas.id")
    jumlah: Decimal = Field(decimal_places=2, description="Withdrawal amount")
    tanggal: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending", description="pending, approved, completed")

    # Relationships
    nasabah: Nasabah = Relationship(back_populates="transaksi_tarik")
    petugas: Petugas = Relationship(back_populates="transaksi_tarik")


class TransaksiPengepul(SQLModel, table=True):
    __tablename__ = "transaksi_pengepul"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    pengepul_id: int = Field(foreign_key="pengepul.id")
    jenis_sampah_id: int = Field(foreign_key="jenis_sampah.id")
    berat: Decimal = Field(decimal_places=3, description="Weight sold to collector in kg")
    harga_jual: Decimal = Field(decimal_places=2, description="Sale price per kg to collector")
    total: Decimal = Field(decimal_places=2, description="Total value (berat × harga_jual)")
    tanggal: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    pengepul: Pengepul = Relationship(back_populates="transaksi_pengepul")
    jenis_sampah: JenisSampah = Relationship(back_populates="transaksi_pengepul")


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    role: UserRole
    nama: str = Field(max_length=100)
    nik: str = Field(max_length=20)
    alamat: str = Field(max_length=255)
    instansi: str = Field(max_length=100)
    username: str = Field(max_length=50)
    password: str = Field(max_length=255)


class UserUpdate(SQLModel, table=False):
    nama: Optional[str] = Field(default=None, max_length=100)
    alamat: Optional[str] = Field(default=None, max_length=255)
    instansi: Optional[str] = Field(default=None, max_length=100)
    password: Optional[str] = Field(default=None, max_length=255)


class NasabahCreate(SQLModel, table=False):
    kode: str = Field(max_length=20)
    nama: str = Field(max_length=100)
    nik: str = Field(max_length=20)
    alamat: str = Field(max_length=255)
    instansi: str = Field(max_length=100)


class NasabahUpdate(SQLModel, table=False):
    nama: Optional[str] = Field(default=None, max_length=100)
    alamat: Optional[str] = Field(default=None, max_length=255)
    instansi: Optional[str] = Field(default=None, max_length=100)


class PetugasCreate(SQLModel, table=False):
    kode: str = Field(max_length=20)
    nama: str = Field(max_length=100)
    nik: str = Field(max_length=20)
    alamat: str = Field(max_length=255)
    instansi: str = Field(max_length=100)


class PetugasUpdate(SQLModel, table=False):
    nama: Optional[str] = Field(default=None, max_length=100)
    alamat: Optional[str] = Field(default=None, max_length=255)
    instansi: Optional[str] = Field(default=None, max_length=100)


class JenisSampahCreate(SQLModel, table=False):
    kode: str = Field(max_length=20)
    nama: str = Field(max_length=100)
    harga_beli: Decimal = Field(decimal_places=2)
    harga_jual: Decimal = Field(decimal_places=2)


class JenisSampahUpdate(SQLModel, table=False):
    nama: Optional[str] = Field(default=None, max_length=100)
    harga_beli: Optional[Decimal] = Field(default=None, decimal_places=2)
    harga_jual: Optional[Decimal] = Field(default=None, decimal_places=2)


class PengepulCreate(SQLModel, table=False):
    kode: str = Field(max_length=20)
    nama: str = Field(max_length=100)
    alamat: str = Field(max_length=255)


class PengepulUpdate(SQLModel, table=False):
    nama: Optional[str] = Field(default=None, max_length=100)
    alamat: Optional[str] = Field(default=None, max_length=255)


class TransaksiSetoranCreate(SQLModel, table=False):
    nasabah_id: int
    petugas_id: int
    jenis_sampah_id: int
    berat: Decimal = Field(decimal_places=3)


class TransaksiTarikCreate(SQLModel, table=False):
    nasabah_id: int
    petugas_id: int
    jumlah: Decimal = Field(decimal_places=2)


class TransaksiTarikUpdate(SQLModel, table=False):
    status: Optional[str] = Field(default=None)


class TransaksiPengepulCreate(SQLModel, table=False):
    pengepul_id: int
    jenis_sampah_id: int
    berat: Decimal = Field(decimal_places=3)
    harga_jual: Decimal = Field(decimal_places=2)


# Dashboard summary schemas
class DashboardSummary(SQLModel, table=False):
    total_customers: int
    total_officers: int
    total_waste_types: int
    total_deposit_transactions: int
    total_customer_balance: Decimal
    pending_withdrawal_requests: int
    total_waste_stock: Decimal
    total_waste_sent_to_collectors: Decimal
    total_profit: Decimal


# Report schemas
class TransactionReport(SQLModel, table=False):
    transaction_id: int
    transaction_type: str  # "setoran", "tarik", "pengepul"
    nasabah_nama: Optional[str] = Field(default=None)
    petugas_nama: Optional[str] = Field(default=None)
    pengepul_nama: Optional[str] = Field(default=None)
    jenis_sampah_nama: Optional[str] = Field(default=None)
    berat: Optional[Decimal] = Field(default=None)
    nilai: Decimal
    tanggal: datetime


class CustomerBalanceReport(SQLModel, table=False):
    nasabah_kode: str
    nasabah_nama: str
    total_setoran: Decimal
    total_tarik: Decimal
    saldo_current: Decimal
    last_transaction: datetime
