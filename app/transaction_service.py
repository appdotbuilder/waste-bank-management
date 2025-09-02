"""Service layer for transaction management (Setoran, Tarik, Pengepul)."""

from decimal import Decimal
from datetime import date
from typing import Optional, List
from sqlmodel import select, desc, cast, Date
from app.database import get_session
from app.models import (
    TransaksiSetoran,
    TransaksiSetoranCreate,
    TransaksiTarik,
    TransaksiTarikCreate,
    TransaksiPengepul,
    TransaksiPengepulCreate,
    Nasabah,
    JenisSampah,
)


class TransaksiSetoranService:
    """Service for managing deposit transactions."""

    @staticmethod
    def create_setoran(data: TransaksiSetoranCreate) -> Optional[TransaksiSetoran]:
        """Create a deposit transaction."""
        with get_session() as session:
            # Get waste type for price calculation
            jenis_sampah = session.get(JenisSampah, data.jenis_sampah_id)
            if jenis_sampah is None:
                return None

            # Calculate total value
            nilai = data.berat * jenis_sampah.harga_beli

            # Create transaction
            transaksi = TransaksiSetoran(
                nasabah_id=data.nasabah_id,
                petugas_id=data.petugas_id,
                jenis_sampah_id=data.jenis_sampah_id,
                berat=data.berat,
                nilai=nilai,
            )
            session.add(transaksi)

            # Update customer balance
            nasabah = session.get(Nasabah, data.nasabah_id)
            if nasabah is None:
                session.rollback()
                return None

            nasabah.saldo += nilai
            session.add(nasabah)

            session.commit()
            session.refresh(transaksi)
            return transaksi

    @staticmethod
    def get_setoran_by_id(transaksi_id: int) -> Optional[TransaksiSetoran]:
        """Get deposit transaction by ID."""
        with get_session() as session:
            return session.get(TransaksiSetoran, transaksi_id)

    @staticmethod
    def get_all_setoran() -> List[TransaksiSetoran]:
        """Get all deposit transactions."""
        with get_session() as session:
            stmt = select(TransaksiSetoran).order_by(desc(TransaksiSetoran.tanggal))
            return list(session.exec(stmt).all())

    @staticmethod
    def get_setoran_by_nasabah(nasabah_id: int) -> List[TransaksiSetoran]:
        """Get deposit transactions by customer."""
        with get_session() as session:
            stmt = (
                select(TransaksiSetoran)
                .where(TransaksiSetoran.nasabah_id == nasabah_id)
                .order_by(desc(TransaksiSetoran.tanggal))
            )
            return list(session.exec(stmt).all())

    @staticmethod
    def get_setoran_by_date_range(start_date: date, end_date: date) -> List[TransaksiSetoran]:
        """Get deposit transactions by date range."""
        with get_session() as session:
            stmt = (
                select(TransaksiSetoran)
                .where(
                    cast(TransaksiSetoran.tanggal, Date) >= start_date, cast(TransaksiSetoran.tanggal, Date) <= end_date
                )
                .order_by(desc(TransaksiSetoran.tanggal))
            )
            return list(session.exec(stmt).all())

    @staticmethod
    def get_total_count() -> int:
        """Get total number of deposit transactions."""
        with get_session() as session:
            stmt = select(TransaksiSetoran)
            return len(list(session.exec(stmt).all()))

    @staticmethod
    def get_total_waste_stock() -> Decimal:
        """Calculate total waste stock (deposited but not yet sold to collectors)."""
        with get_session() as session:
            # Get all deposit transactions
            setoran_stmt = select(TransaksiSetoran)
            setoran_list = list(session.exec(setoran_stmt).all())

            # Get all collector transactions
            pengepul_stmt = select(TransaksiPengepul)
            pengepul_list = list(session.exec(pengepul_stmt).all())

            # Calculate net stock by waste type
            stock_by_type = {}

            # Add deposits
            for setoran in setoran_list:
                type_id = setoran.jenis_sampah_id
                if type_id not in stock_by_type:
                    stock_by_type[type_id] = Decimal("0")
                stock_by_type[type_id] += setoran.berat

            # Subtract sales to collectors
            for pengepul in pengepul_list:
                type_id = pengepul.jenis_sampah_id
                if type_id not in stock_by_type:
                    stock_by_type[type_id] = Decimal("0")
                stock_by_type[type_id] -= pengepul.berat

            # Sum positive stocks only
            total_stock = (
                sum(max(stock, Decimal("0")) for stock in stock_by_type.values()) if stock_by_type else Decimal("0")
            )
            return Decimal(str(total_stock))


class TransaksiTarikService:
    """Service for managing withdrawal transactions."""

    @staticmethod
    def create_tarik(data: TransaksiTarikCreate) -> Optional[TransaksiTarik]:
        """Create a withdrawal transaction (initially pending)."""
        with get_session() as session:
            # Check customer balance
            nasabah = session.get(Nasabah, data.nasabah_id)
            if nasabah is None or nasabah.saldo < data.jumlah:
                return None

            # Create transaction
            transaksi = TransaksiTarik(
                nasabah_id=data.nasabah_id, petugas_id=data.petugas_id, jumlah=data.jumlah, status="pending"
            )
            session.add(transaksi)
            session.commit()
            session.refresh(transaksi)
            return transaksi

    @staticmethod
    def approve_tarik(transaksi_id: int) -> bool:
        """Approve and complete withdrawal transaction."""
        with get_session() as session:
            transaksi = session.get(TransaksiTarik, transaksi_id)
            if transaksi is None or transaksi.status != "pending":
                return False

            # Check customer balance again
            nasabah = session.get(Nasabah, transaksi.nasabah_id)
            if nasabah is None or nasabah.saldo < transaksi.jumlah:
                return False

            # Deduct balance and mark as completed
            nasabah.saldo -= transaksi.jumlah
            transaksi.status = "completed"

            session.add(nasabah)
            session.add(transaksi)
            session.commit()
            return True

    @staticmethod
    def reject_tarik(transaksi_id: int) -> bool:
        """Reject withdrawal transaction."""
        with get_session() as session:
            transaksi = session.get(TransaksiTarik, transaksi_id)
            if transaksi is None or transaksi.status != "pending":
                return False

            transaksi.status = "rejected"
            session.add(transaksi)
            session.commit()
            return True

    @staticmethod
    def get_tarik_by_id(transaksi_id: int) -> Optional[TransaksiTarik]:
        """Get withdrawal transaction by ID."""
        with get_session() as session:
            return session.get(TransaksiTarik, transaksi_id)

    @staticmethod
    def get_all_tarik() -> List[TransaksiTarik]:
        """Get all withdrawal transactions."""
        with get_session() as session:
            stmt = select(TransaksiTarik).order_by(desc(TransaksiTarik.tanggal))
            return list(session.exec(stmt).all())

    @staticmethod
    def get_pending_tarik() -> List[TransaksiTarik]:
        """Get pending withdrawal transactions."""
        with get_session() as session:
            stmt = (
                select(TransaksiTarik).where(TransaksiTarik.status == "pending").order_by(desc(TransaksiTarik.tanggal))
            )
            return list(session.exec(stmt).all())

    @staticmethod
    def get_tarik_by_nasabah(nasabah_id: int) -> List[TransaksiTarik]:
        """Get withdrawal transactions by customer."""
        with get_session() as session:
            stmt = (
                select(TransaksiTarik)
                .where(TransaksiTarik.nasabah_id == nasabah_id)
                .order_by(desc(TransaksiTarik.tanggal))
            )
            return list(session.exec(stmt).all())

    @staticmethod
    def get_tarik_by_date_range(start_date: date, end_date: date) -> List[TransaksiTarik]:
        """Get withdrawal transactions by date range."""
        with get_session() as session:
            stmt = (
                select(TransaksiTarik)
                .where(cast(TransaksiTarik.tanggal, Date) >= start_date, cast(TransaksiTarik.tanggal, Date) <= end_date)
                .order_by(desc(TransaksiTarik.tanggal))
            )
            return list(session.exec(stmt).all())

    @staticmethod
    def get_pending_count() -> int:
        """Get number of pending withdrawal requests."""
        with get_session() as session:
            stmt = select(TransaksiTarik).where(TransaksiTarik.status == "pending")
            return len(list(session.exec(stmt).all()))


class TransaksiPengepulService:
    """Service for managing collector transactions."""

    @staticmethod
    def create_pengepul_transaction(data: TransaksiPengepulCreate) -> Optional[TransaksiPengepul]:
        """Create a collector transaction."""
        with get_session() as session:
            # Calculate total value
            total = data.berat * data.harga_jual

            # Create transaction
            transaksi = TransaksiPengepul(
                pengepul_id=data.pengepul_id,
                jenis_sampah_id=data.jenis_sampah_id,
                berat=data.berat,
                harga_jual=data.harga_jual,
                total=total,
            )
            session.add(transaksi)
            session.commit()
            session.refresh(transaksi)
            return transaksi

    @staticmethod
    def get_pengepul_transaction_by_id(transaksi_id: int) -> Optional[TransaksiPengepul]:
        """Get collector transaction by ID."""
        with get_session() as session:
            return session.get(TransaksiPengepul, transaksi_id)

    @staticmethod
    def get_all_pengepul_transactions() -> List[TransaksiPengepul]:
        """Get all collector transactions."""
        with get_session() as session:
            stmt = select(TransaksiPengepul).order_by(desc(TransaksiPengepul.tanggal))
            return list(session.exec(stmt).all())

    @staticmethod
    def get_pengepul_transactions_by_date_range(start_date: date, end_date: date) -> List[TransaksiPengepul]:
        """Get collector transactions by date range."""
        with get_session() as session:
            stmt = (
                select(TransaksiPengepul)
                .where(
                    cast(TransaksiPengepul.tanggal, Date) >= start_date,
                    cast(TransaksiPengepul.tanggal, Date) <= end_date,
                )
                .order_by(desc(TransaksiPengepul.tanggal))
            )
            return list(session.exec(stmt).all())

    @staticmethod
    def get_total_waste_sent() -> Decimal:
        """Get total weight of waste sent to collectors."""
        with get_session() as session:
            stmt = select(TransaksiPengepul)
            pengepul_list = list(session.exec(stmt).all())
            total_weight = sum(t.berat for t in pengepul_list) if pengepul_list else Decimal("0")
            return Decimal(str(total_weight))

    @staticmethod
    def calculate_total_profit() -> Decimal:
        """Calculate total profit (difference between collector sale and customer purchase prices)."""
        with get_session() as session:
            # Get all setoran transactions
            setoran_stmt = select(TransaksiSetoran)
            setoran_list = list(session.exec(setoran_stmt).all())

            # Get all pengepul transactions
            pengepul_stmt = select(TransaksiPengepul)
            pengepul_list = list(session.exec(pengepul_stmt).all())

            # Calculate costs (what we paid customers)
            total_cost = sum(t.nilai for t in setoran_list)

            # Calculate revenue (what collectors paid us)
            total_revenue = sum(t.total for t in pengepul_list)

            profit = total_revenue - total_cost
            return Decimal(str(profit))
