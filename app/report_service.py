"""Service layer for generating various reports."""

from datetime import datetime, date
from decimal import Decimal
from typing import List
from sqlmodel import select, cast, Date
from app.database import get_session
from app.models import (
    TransactionReport,
    CustomerBalanceReport,
    TransaksiSetoran,
    TransaksiTarik,
    TransaksiPengepul,
    Nasabah,
    Petugas,
    JenisSampah,
    Pengepul,
)


class ReportService:
    """Service for generating reports."""

    @staticmethod
    def generate_transaction_report(start_date: date, end_date: date) -> List[TransactionReport]:
        """Generate comprehensive transaction report for date range."""
        reports = []

        with get_session() as session:
            # Get deposit transactions
            setoran_stmt = select(TransaksiSetoran).where(
                cast(TransaksiSetoran.tanggal, Date) >= start_date, cast(TransaksiSetoran.tanggal, Date) <= end_date
            )
            setoran_list = list(session.exec(setoran_stmt).all())

            for setoran in setoran_list:
                nasabah = session.get(Nasabah, setoran.nasabah_id)
                petugas = session.get(Petugas, setoran.petugas_id)
                jenis_sampah = session.get(JenisSampah, setoran.jenis_sampah_id)

                reports.append(
                    TransactionReport(
                        transaction_id=setoran.id if setoran.id else 0,
                        transaction_type="setoran",
                        nasabah_nama=nasabah.nama if nasabah else "",
                        petugas_nama=petugas.nama if petugas else "",
                        jenis_sampah_nama=jenis_sampah.nama if jenis_sampah else "",
                        berat=setoran.berat,
                        nilai=setoran.nilai,
                        tanggal=setoran.tanggal,
                    )
                )

            # Get withdrawal transactions
            tarik_stmt = select(TransaksiTarik).where(
                cast(TransaksiTarik.tanggal, Date) >= start_date,
                cast(TransaksiTarik.tanggal, Date) <= end_date,
                TransaksiTarik.status == "completed",
            )
            tarik_list = list(session.exec(tarik_stmt).all())

            for tarik in tarik_list:
                nasabah = session.get(Nasabah, tarik.nasabah_id)
                petugas = session.get(Petugas, tarik.petugas_id)

                reports.append(
                    TransactionReport(
                        transaction_id=tarik.id if tarik.id else 0,
                        transaction_type="tarik",
                        nasabah_nama=nasabah.nama if nasabah else "",
                        petugas_nama=petugas.nama if petugas else "",
                        nilai=tarik.jumlah,
                        tanggal=tarik.tanggal,
                    )
                )

            # Get collector transactions
            pengepul_stmt = select(TransaksiPengepul).where(
                cast(TransaksiPengepul.tanggal, Date) >= start_date, cast(TransaksiPengepul.tanggal, Date) <= end_date
            )
            pengepul_list = list(session.exec(pengepul_stmt).all())

            for pengepul_tx in pengepul_list:
                pengepul = session.get(Pengepul, pengepul_tx.pengepul_id)
                jenis_sampah = session.get(JenisSampah, pengepul_tx.jenis_sampah_id)

                reports.append(
                    TransactionReport(
                        transaction_id=pengepul_tx.id if pengepul_tx.id else 0,
                        transaction_type="pengepul",
                        pengepul_nama=pengepul.nama if pengepul else "",
                        jenis_sampah_nama=jenis_sampah.nama if jenis_sampah else "",
                        berat=pengepul_tx.berat,
                        nilai=pengepul_tx.total,
                        tanggal=pengepul_tx.tanggal,
                    )
                )

        # Sort by date descending
        return sorted(reports, key=lambda x: x.tanggal, reverse=True)

    @staticmethod
    def generate_customer_report(nasabah_id: int) -> CustomerBalanceReport:
        """Generate detailed report for specific customer."""
        with get_session() as session:
            nasabah = session.get(Nasabah, nasabah_id)
            if nasabah is None:
                raise ValueError("Customer not found")

            # Calculate total deposits
            setoran_stmt = select(TransaksiSetoran).where(TransaksiSetoran.nasabah_id == nasabah_id)
            setoran_list = list(session.exec(setoran_stmt).all())
            total_setoran = Decimal(str(sum(s.nilai for s in setoran_list))) if setoran_list else Decimal("0")

            # Calculate total completed withdrawals
            tarik_stmt = select(TransaksiTarik).where(
                TransaksiTarik.nasabah_id == nasabah_id, TransaksiTarik.status == "completed"
            )
            tarik_list = list(session.exec(tarik_stmt).all())
            total_tarik = Decimal(str(sum(t.jumlah for t in tarik_list))) if tarik_list else Decimal("0")

            # Get last transaction date
            last_transaction = datetime.min
            if setoran_list:
                last_setoran = max(setoran_list, key=lambda x: x.tanggal)
                last_transaction = max(last_transaction, last_setoran.tanggal)
            if tarik_list:
                last_tarik = max(tarik_list, key=lambda x: x.tanggal)
                last_transaction = max(last_transaction, last_tarik.tanggal)

            return CustomerBalanceReport(
                nasabah_kode=nasabah.kode,
                nasabah_nama=nasabah.nama,
                total_setoran=total_setoran,
                total_tarik=total_tarik,
                saldo_current=nasabah.saldo,
                last_transaction=last_transaction,
            )

    @staticmethod
    def get_daily_transactions(target_date: date) -> List[TransactionReport]:
        """Get all transactions for a specific day."""
        return ReportService.generate_transaction_report(target_date, target_date)

    @staticmethod
    def get_monthly_transactions(year: int, month: int) -> List[TransactionReport]:
        """Get all transactions for a specific month."""
        from calendar import monthrange

        start_date = date(year, month, 1)
        # Get the last day of the month
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)

        return ReportService.generate_transaction_report(start_date, end_date)

    @staticmethod
    def get_yearly_transactions(year: int) -> List[TransactionReport]:
        """Get all transactions for a specific year."""
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        return ReportService.generate_transaction_report(start_date, end_date)

    @staticmethod
    def get_all_customer_reports() -> List[CustomerBalanceReport]:
        """Get balance reports for all customers."""
        with get_session() as session:
            stmt = select(Nasabah)
            nasabah_list = list(session.exec(stmt).all())

            reports = []
            for nasabah in nasabah_list:
                if nasabah.id is not None:
                    try:
                        report = ReportService.generate_customer_report(nasabah.id)
                        reports.append(report)
                    except ValueError as e:
                        import logging

                        logging.warning(f"Could not generate customer report for ID {nasabah.id}: {e}")
                        continue  # Skip if customer not found

            return sorted(reports, key=lambda x: x.nasabah_kode)
