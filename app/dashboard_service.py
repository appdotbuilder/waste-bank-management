"""Service layer for dashboard data aggregation."""

from app.models import DashboardSummary
from app.master_data_service import NasabahService, PetugasService, JenisSampahService
from app.transaction_service import TransaksiSetoranService, TransaksiTarikService, TransaksiPengepulService


class DashboardService:
    """Service for dashboard data aggregation."""

    @staticmethod
    def get_dashboard_summary() -> DashboardSummary:
        """Get comprehensive dashboard summary."""
        return DashboardSummary(
            total_customers=NasabahService.get_total_count(),
            total_officers=PetugasService.get_total_count(),
            total_waste_types=JenisSampahService.get_total_count(),
            total_deposit_transactions=TransaksiSetoranService.get_total_count(),
            total_customer_balance=NasabahService.get_total_balance(),
            pending_withdrawal_requests=TransaksiTarikService.get_pending_count(),
            total_waste_stock=TransaksiSetoranService.get_total_waste_stock(),
            total_waste_sent_to_collectors=TransaksiPengepulService.get_total_waste_sent(),
            total_profit=TransaksiPengepulService.calculate_total_profit(),
        )
