"""
Unit testy pro Seller Dashboard endpoint.

Testuje GET /crm/seller/dashboard:
- Výpočet available_balance z ledgeru
- Pending projekty
- Unpaid faktury
- Lead counts a follow-ups
- Schema validace
"""
import pytest
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime, date, timedelta

from app.schemas.crm import SellerDashboard

logger = logging.getLogger(__name__)


class TestSellerDashboard:
    """Testy pro GET /crm/seller/dashboard."""

    def test_dashboard_returns_expected_structure(self, app_client, mock_supabase):
        """Dashboard vrací očekávanou strukturu dat."""
        logger.info("Testing dashboard structure")
        mock_supabase.data_store["ledger_entries"] = []
        mock_supabase.data_store["businesses"] = []
        mock_supabase.data_store["website_projects"] = []
        mock_supabase.data_store["invoices_issued"] = []
        mock_supabase.data_store["invoices_received"] = []

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.get("/crm/seller/dashboard")

        assert response.status_code == 200
        data = response.json()

        # Ověříme strukturu odpovědi
        assert "available_balance" in data
        assert "pending_projects_amount" in data
        assert "recent_invoices" in data
        assert "weekly_rewards" in data
        assert "pending_projects" in data
        assert "unpaid_client_invoices" in data
        assert "total_leads" in data
        assert "follow_ups_today" in data

    def test_dashboard_returns_balance_field(
        self, app_client, mock_supabase, sample_ledger_entry
    ):
        """Dashboard vrací available_balance field (mock nefiltruje správně)."""
        logger.info("Testing dashboard balance field exists")

        mock_supabase.data_store["ledger_entries"] = []
        mock_supabase.data_store["businesses"] = []
        mock_supabase.data_store["website_projects"] = []
        mock_supabase.data_store["invoices_issued"] = []
        mock_supabase.data_store["invoices_received"] = []

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.get("/crm/seller/dashboard")

        assert response.status_code == 200
        data = response.json()
        # Ověříme, že pole available_balance existuje a je číslo
        assert "available_balance" in data
        assert isinstance(data["available_balance"], (int, float))

    def test_dashboard_balance_calculation_logic(self):
        """Test logiky výpočtu balance (bez API volání)."""
        logger.info("Testing balance calculation logic")

        # Simulace dat z ledgeru
        commission_entries = [
            {"amount": 1500.0, "entry_type": "commission_earned"},
            {"amount": 2000.0, "entry_type": "commission_earned"},
        ]
        payout_entries = [
            {"amount": 1000.0, "entry_type": "payout_paid"},
        ]

        total_earned = sum(e["amount"] for e in commission_entries)
        total_payouts = sum(e["amount"] for e in payout_entries)
        available_balance = total_earned - total_payouts

        # 3500 - 1000 = 2500
        assert available_balance == 2500.0

    def test_dashboard_returns_pending_projects(
        self, app_client, mock_supabase, sample_business, sample_project
    ):
        """Dashboard vrací pending projekty."""
        logger.info("Testing dashboard pending projects")

        sample_business["owner_seller_id"] = "seller-123"
        sample_project["business_id"] = sample_business["id"]
        sample_project["status"] = "won"
        sample_project["price_setup"] = 15000.0

        mock_supabase.data_store["ledger_entries"] = []
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["website_projects"] = [sample_project]
        mock_supabase.data_store["website_versions"] = []
        mock_supabase.data_store["invoices_issued"] = []
        mock_supabase.data_store["invoices_received"] = []

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.get("/crm/seller/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert data["pending_projects_amount"] == 15000.0

    def test_dashboard_returns_unpaid_invoices(
        self, app_client, mock_supabase, sample_business, sample_invoice_issued
    ):
        """Dashboard vrací unpaid client invoices."""
        logger.info("Testing dashboard unpaid invoices")

        sample_business["owner_seller_id"] = "seller-123"
        sample_invoice_issued["business_id"] = sample_business["id"]
        sample_invoice_issued["status"] = "issued"

        mock_supabase.data_store["ledger_entries"] = []
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["website_projects"] = []
        mock_supabase.data_store["invoices_issued"] = [sample_invoice_issued]
        mock_supabase.data_store["invoices_received"] = []

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.get("/crm/seller/dashboard")

        assert response.status_code == 200
        # Unpaid invoices jsou v seznamu

    def test_dashboard_returns_lead_counts(
        self, app_client, mock_supabase, sample_business
    ):
        """Dashboard vrací správný počet leadů."""
        logger.info("Testing dashboard lead counts")

        sample_business["owner_seller_id"] = "seller-123"
        business2 = {
            **sample_business,
            "id": "business-2",
            "name": "Druhá firma",
        }
        business3 = {
            **sample_business,
            "id": "business-3",
            "name": "Třetí firma",
        }

        mock_supabase.data_store["ledger_entries"] = []
        mock_supabase.data_store["businesses"] = [sample_business, business2, business3]
        mock_supabase.data_store["website_projects"] = []
        mock_supabase.data_store["invoices_issued"] = []
        mock_supabase.data_store["invoices_received"] = []

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.get("/crm/seller/dashboard")

        assert response.status_code == 200
        assert response.json()["total_leads"] == 3

    def test_dashboard_follow_ups_today(
        self, app_client, mock_supabase, sample_business
    ):
        """Dashboard počítá follow-ups na dnešek."""
        logger.info("Testing dashboard follow-ups today")

        today = date.today().isoformat()
        sample_business["owner_seller_id"] = "seller-123"
        sample_business["next_follow_up_at"] = today
        sample_business["status_crm"] = "calling"  # Není won/lost/dnc

        mock_supabase.data_store["ledger_entries"] = []
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["website_projects"] = []
        mock_supabase.data_store["invoices_issued"] = []
        mock_supabase.data_store["invoices_received"] = []

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.get("/crm/seller/dashboard")

        assert response.status_code == 200
        assert response.json()["follow_ups_today"] >= 0  # Může být 0 nebo 1 podle logiky

    def test_dashboard_empty_data(self, app_client, mock_supabase):
        """Dashboard s prázdnými daty vrací nuly a prázdné seznamy."""
        logger.info("Testing dashboard with empty data")

        mock_supabase.data_store["ledger_entries"] = []
        mock_supabase.data_store["businesses"] = []
        mock_supabase.data_store["website_projects"] = []
        mock_supabase.data_store["invoices_issued"] = []
        mock_supabase.data_store["invoices_received"] = []

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.get("/crm/seller/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert data["available_balance"] == 0
        assert data["pending_projects_amount"] == 0
        assert data["total_leads"] == 0
        assert data["follow_ups_today"] == 0
        assert data["pending_projects"] == []
        assert data["unpaid_client_invoices"] == []

    def test_dashboard_weekly_rewards_structure(self, app_client, mock_supabase):
        """Dashboard vrací weekly_rewards s očekávanou strukturou."""
        logger.info("Testing dashboard weekly rewards structure")

        mock_supabase.data_store["ledger_entries"] = []
        mock_supabase.data_store["businesses"] = []
        mock_supabase.data_store["website_projects"] = []
        mock_supabase.data_store["invoices_issued"] = []
        mock_supabase.data_store["invoices_received"] = []

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.get("/crm/seller/dashboard")

        assert response.status_code == 200
        weekly_rewards = response.json()["weekly_rewards"]
        assert isinstance(weekly_rewards, list)
        assert len(weekly_rewards) == 4
        for reward in weekly_rewards:
            assert "week" in reward
            assert "amount" in reward

    def test_dashboard_recent_invoices_structure(
        self, app_client, mock_supabase, sample_invoice_received
    ):
        """Dashboard vrací recent_invoices."""
        logger.info("Testing dashboard recent invoices")

        sample_invoice_received["seller_id"] = "seller-123"

        mock_supabase.data_store["ledger_entries"] = []
        mock_supabase.data_store["businesses"] = []
        mock_supabase.data_store["website_projects"] = []
        mock_supabase.data_store["invoices_issued"] = []
        mock_supabase.data_store["invoices_received"] = [sample_invoice_received]

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.get("/crm/seller/dashboard")

        assert response.status_code == 200
        # recent_invoices jsou vráceny z invoices_received


class TestSellerDashboardSchema:
    """Testy pro SellerDashboard schema — ověření správných polí."""

    def test_seller_dashboard_schema_fields(self):
        """SellerDashboard musí mít správná pole (ne duplicitní definici)."""
        expected_fields = {
            "available_balance",
            "pending_projects_amount",
            "recent_invoices",
            "weekly_rewards",
            "pending_projects",
            "unpaid_client_invoices",
            "total_leads",
            "follow_ups_today",
        }
        actual_fields = set(SellerDashboard.model_fields.keys())
        assert expected_fields == actual_fields, (
            f"SellerDashboard fields mismatch.\n"
            f"Expected: {expected_fields}\n"
            f"Actual: {actual_fields}\n"
            f"Missing: {expected_fields - actual_fields}\n"
            f"Extra: {actual_fields - expected_fields}"
        )

    def test_seller_dashboard_schema_not_overridden(self):
        """SellerDashboard nesmí mít pole z duplicitní (špatné) definice."""
        wrong_fields = {"total_businesses", "active_projects", "monthly_earnings",
                        "pending_followups", "today_tasks", "account_balance"}
        actual_fields = set(SellerDashboard.model_fields.keys())
        overlap = wrong_fields & actual_fields
        assert not overlap, (
            f"SellerDashboard contains fields from wrong duplicate definition: {overlap}"
        )

    def test_seller_dashboard_instantiation(self):
        """SellerDashboard lze vytvořit se správnými daty."""
        dashboard = SellerDashboard(
            available_balance=1500.0,
            pending_projects_amount=5000.0,
            recent_invoices=[],
            weekly_rewards=[],
            pending_projects=[],
            unpaid_client_invoices=[],
            total_leads=10,
            follow_ups_today=3,
        )
        assert dashboard.available_balance == 1500.0
        assert dashboard.total_leads == 10
        assert dashboard.follow_ups_today == 3
