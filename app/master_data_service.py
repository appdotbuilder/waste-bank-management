"""Service layer for master data management (Nasabah, Petugas, JenisSampah, Pengepul)."""

from decimal import Decimal
from typing import Optional
from sqlmodel import select
from app.database import get_session
from app.models import (
    Nasabah,
    NasabahCreate,
    NasabahUpdate,
    Petugas,
    PetugasCreate,
    PetugasUpdate,
    JenisSampah,
    JenisSampahCreate,
    JenisSampahUpdate,
    Pengepul,
    PengepulCreate,
    PengepulUpdate,
)


class NasabahService:
    """Service for managing customer (Nasabah) data."""

    @staticmethod
    def create_nasabah(data: NasabahCreate) -> Nasabah:
        """Create a new customer."""
        with get_session() as session:
            nasabah = Nasabah(**data.model_dump())
            session.add(nasabah)
            session.commit()
            session.refresh(nasabah)
            return nasabah

    @staticmethod
    def get_nasabah_by_id(nasabah_id: int) -> Optional[Nasabah]:
        """Get customer by ID."""
        with get_session() as session:
            return session.get(Nasabah, nasabah_id)

    @staticmethod
    def get_nasabah_by_kode(kode: str) -> Optional[Nasabah]:
        """Get customer by code."""
        with get_session() as session:
            stmt = select(Nasabah).where(Nasabah.kode == kode)
            return session.exec(stmt).first()

    @staticmethod
    def get_all_nasabah() -> list[Nasabah]:
        """Get all customers."""
        with get_session() as session:
            stmt = select(Nasabah).order_by(Nasabah.kode)
            return list(session.exec(stmt).all())

    @staticmethod
    def update_nasabah(nasabah_id: int, data: NasabahUpdate) -> Optional[Nasabah]:
        """Update customer data."""
        with get_session() as session:
            nasabah = session.get(Nasabah, nasabah_id)
            if nasabah is None:
                return None

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(nasabah, field, value)

            session.add(nasabah)
            session.commit()
            session.refresh(nasabah)
            return nasabah

    @staticmethod
    def update_saldo(nasabah_id: int, amount: Decimal, operation: str = "add") -> bool:
        """Update customer balance. Operation: 'add' or 'subtract'."""
        with get_session() as session:
            nasabah = session.get(Nasabah, nasabah_id)
            if nasabah is None:
                return False

            if operation == "add":
                nasabah.saldo += amount
            elif operation == "subtract":
                if nasabah.saldo < amount:
                    return False  # Insufficient balance
                nasabah.saldo -= amount
            else:
                return False  # Invalid operation

            session.add(nasabah)
            session.commit()
            return True

    @staticmethod
    def delete_nasabah(nasabah_id: int) -> bool:
        """Delete customer."""
        with get_session() as session:
            nasabah = session.get(Nasabah, nasabah_id)
            if nasabah is None:
                return False

            session.delete(nasabah)
            session.commit()
            return True

    @staticmethod
    def get_total_count() -> int:
        """Get total number of customers."""
        with get_session() as session:
            stmt = select(Nasabah)
            return len(list(session.exec(stmt).all()))

    @staticmethod
    def get_total_balance() -> Decimal:
        """Get sum of all customer balances."""
        with get_session() as session:
            stmt = select(Nasabah)
            nasabah_list = list(session.exec(stmt).all())
            return Decimal(str(sum(n.saldo for n in nasabah_list))) if nasabah_list else Decimal("0")


class PetugasService:
    """Service for managing officer (Petugas) data."""

    @staticmethod
    def create_petugas(data: PetugasCreate) -> Petugas:
        """Create a new officer."""
        with get_session() as session:
            petugas = Petugas(**data.model_dump())
            session.add(petugas)
            session.commit()
            session.refresh(petugas)
            return petugas

    @staticmethod
    def get_petugas_by_id(petugas_id: int) -> Optional[Petugas]:
        """Get officer by ID."""
        with get_session() as session:
            return session.get(Petugas, petugas_id)

    @staticmethod
    def get_petugas_by_kode(kode: str) -> Optional[Petugas]:
        """Get officer by code."""
        with get_session() as session:
            stmt = select(Petugas).where(Petugas.kode == kode)
            return session.exec(stmt).first()

    @staticmethod
    def get_all_petugas() -> list[Petugas]:
        """Get all officers."""
        with get_session() as session:
            stmt = select(Petugas).order_by(Petugas.kode)
            return list(session.exec(stmt).all())

    @staticmethod
    def update_petugas(petugas_id: int, data: PetugasUpdate) -> Optional[Petugas]:
        """Update officer data."""
        with get_session() as session:
            petugas = session.get(Petugas, petugas_id)
            if petugas is None:
                return None

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(petugas, field, value)

            session.add(petugas)
            session.commit()
            session.refresh(petugas)
            return petugas

    @staticmethod
    def delete_petugas(petugas_id: int) -> bool:
        """Delete officer."""
        with get_session() as session:
            petugas = session.get(Petugas, petugas_id)
            if petugas is None:
                return False

            session.delete(petugas)
            session.commit()
            return True

    @staticmethod
    def get_total_count() -> int:
        """Get total number of officers."""
        with get_session() as session:
            stmt = select(Petugas)
            return len(list(session.exec(stmt).all()))


class JenisSampahService:
    """Service for managing waste type (JenisSampah) data."""

    @staticmethod
    def create_jenis_sampah(data: JenisSampahCreate) -> JenisSampah:
        """Create a new waste type."""
        with get_session() as session:
            jenis_sampah = JenisSampah(**data.model_dump())
            session.add(jenis_sampah)
            session.commit()
            session.refresh(jenis_sampah)
            return jenis_sampah

    @staticmethod
    def get_jenis_sampah_by_id(jenis_sampah_id: int) -> Optional[JenisSampah]:
        """Get waste type by ID."""
        with get_session() as session:
            return session.get(JenisSampah, jenis_sampah_id)

    @staticmethod
    def get_jenis_sampah_by_kode(kode: str) -> Optional[JenisSampah]:
        """Get waste type by code."""
        with get_session() as session:
            stmt = select(JenisSampah).where(JenisSampah.kode == kode)
            return session.exec(stmt).first()

    @staticmethod
    def get_all_jenis_sampah() -> list[JenisSampah]:
        """Get all waste types."""
        with get_session() as session:
            stmt = select(JenisSampah).order_by(JenisSampah.kode)
            return list(session.exec(stmt).all())

    @staticmethod
    def update_jenis_sampah(jenis_sampah_id: int, data: JenisSampahUpdate) -> Optional[JenisSampah]:
        """Update waste type data."""
        with get_session() as session:
            jenis_sampah = session.get(JenisSampah, jenis_sampah_id)
            if jenis_sampah is None:
                return None

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(jenis_sampah, field, value)

            session.add(jenis_sampah)
            session.commit()
            session.refresh(jenis_sampah)
            return jenis_sampah

    @staticmethod
    def delete_jenis_sampah(jenis_sampah_id: int) -> bool:
        """Delete waste type."""
        with get_session() as session:
            jenis_sampah = session.get(JenisSampah, jenis_sampah_id)
            if jenis_sampah is None:
                return False

            session.delete(jenis_sampah)
            session.commit()
            return True

    @staticmethod
    def get_total_count() -> int:
        """Get total number of waste types."""
        with get_session() as session:
            stmt = select(JenisSampah)
            return len(list(session.exec(stmt).all()))


class PengepulService:
    """Service for managing collector (Pengepul) data."""

    @staticmethod
    def create_pengepul(data: PengepulCreate) -> Pengepul:
        """Create a new collector."""
        with get_session() as session:
            pengepul = Pengepul(**data.model_dump())
            session.add(pengepul)
            session.commit()
            session.refresh(pengepul)
            return pengepul

    @staticmethod
    def get_pengepul_by_id(pengepul_id: int) -> Optional[Pengepul]:
        """Get collector by ID."""
        with get_session() as session:
            return session.get(Pengepul, pengepul_id)

    @staticmethod
    def get_pengepul_by_kode(kode: str) -> Optional[Pengepul]:
        """Get collector by code."""
        with get_session() as session:
            stmt = select(Pengepul).where(Pengepul.kode == kode)
            return session.exec(stmt).first()

    @staticmethod
    def get_all_pengepul() -> list[Pengepul]:
        """Get all collectors."""
        with get_session() as session:
            stmt = select(Pengepul).order_by(Pengepul.kode)
            return list(session.exec(stmt).all())

    @staticmethod
    def update_pengepul(pengepul_id: int, data: PengepulUpdate) -> Optional[Pengepul]:
        """Update collector data."""
        with get_session() as session:
            pengepul = session.get(Pengepul, pengepul_id)
            if pengepul is None:
                return None

            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(pengepul, field, value)

            session.add(pengepul)
            session.commit()
            session.refresh(pengepul)
            return pengepul

    @staticmethod
    def delete_pengepul(pengepul_id: int) -> bool:
        """Delete collector."""
        with get_session() as session:
            pengepul = session.get(Pengepul, pengepul_id)
            if pengepul is None:
                return False

            session.delete(pengepul)
            session.commit()
            return True
