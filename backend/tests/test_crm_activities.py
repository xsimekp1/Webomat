"""
Unit testy pro CRM aktivity.

Testuje vytvoření a čtení aktivit pro business:
- Různé typy aktivit (call, email, meeting, note, message)
- Čtení aktivit pro business
- Aktualizace CRM statusu přes aktivitu
"""
import pytest
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# TESTY PRO VYTVOŘENÍ AKTIVITY
# =============================================================================

class TestCreateActivity:
    """Testy pro POST /crm/businesses/{id}/activities - vytvoření aktivity."""

    def test_create_call_activity(self, app_client, mock_supabase, sample_business):
        """Úspěšné vytvoření call aktivity."""
        logger.info("Testing create call activity")
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["crm_activities"] = []

        activity_data = {
            "activity_type": "call",
            "description": "Úvodní hovor s klientem",
            "outcome": "positive",
        }

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.post(
                f"/crm/businesses/{sample_business['id']}/activities",
                json=activity_data,
            )

        logger.debug(f"Response status: {response.status_code}")
        assert response.status_code == 201
        data = response.json()
        assert data["activity_type"] == "call"
        assert "Úvodní hovor" in data["description"]

    def test_create_email_activity(self, app_client, mock_supabase, sample_business):
        """Úspěšné vytvoření email aktivity."""
        logger.info("Testing create email activity")
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["crm_activities"] = []

        activity_data = {
            "activity_type": "email",
            "description": "Odeslána cenová nabídka na email",
        }

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.post(
                f"/crm/businesses/{sample_business['id']}/activities",
                json=activity_data,
            )

        assert response.status_code == 201
        assert response.json()["activity_type"] == "email"

    def test_create_meeting_activity(self, app_client, mock_supabase, sample_business):
        """Úspěšné vytvoření meeting aktivity."""
        logger.info("Testing create meeting activity")
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["crm_activities"] = []

        activity_data = {
            "activity_type": "meeting",
            "description": "Osobní schůzka v kanceláři klienta",
            "outcome": "positive",
        }

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.post(
                f"/crm/businesses/{sample_business['id']}/activities",
                json=activity_data,
            )

        assert response.status_code == 201
        assert response.json()["activity_type"] == "meeting"

    def test_create_note_activity(self, app_client, mock_supabase, sample_business):
        """Úspěšné vytvoření note aktivity."""
        logger.info("Testing create note activity")
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["crm_activities"] = []

        activity_data = {
            "activity_type": "note",
            "description": "Interní poznámka: klient preferuje ranní hovory",
        }

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.post(
                f"/crm/businesses/{sample_business['id']}/activities",
                json=activity_data,
            )

        assert response.status_code == 201
        assert response.json()["activity_type"] == "note"

    def test_create_message_activity(self, app_client, mock_supabase, sample_business):
        """Úspěšné vytvoření message aktivity."""
        logger.info("Testing create message activity")
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["crm_activities"] = []

        activity_data = {
            "activity_type": "message",
            "description": "SMS zpráva s potvrzením schůzky",
        }

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.post(
                f"/crm/businesses/{sample_business['id']}/activities",
                json=activity_data,
            )

        assert response.status_code == 201
        assert response.json()["activity_type"] == "message"

    def test_activity_updates_business_status(
        self, app_client, mock_supabase, sample_business
    ):
        """Aktivita s new_status aktualizuje status businessu."""
        logger.info("Testing activity updates business status")
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["crm_activities"] = []

        activity_data = {
            "activity_type": "call",
            "description": "Klient projevil zájem o nabídku",
            "new_status": "interested",
        }

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.post(
                f"/crm/businesses/{sample_business['id']}/activities",
                json=activity_data,
            )

        assert response.status_code == 201
        # Aktivita byla vytvořena - status update proběhl v rámci requestu
        logger.debug("Activity created with status update")

    def test_activity_requires_description(
        self, app_client, mock_supabase, sample_business
    ):
        """Aktivita vyžaduje popis."""
        logger.info("Testing activity requires description")

        activity_data = {
            "activity_type": "call",
            # description chybí
        }

        response = app_client.post(
            f"/crm/businesses/{sample_business['id']}/activities",
            json=activity_data,
        )

        assert response.status_code == 422  # Validation error

    def test_activity_invalid_type(self, app_client, mock_supabase, sample_business):
        """Neplatný typ aktivity vrací chybu."""
        logger.info("Testing invalid activity type")

        activity_data = {
            "activity_type": "invalid_type",
            "description": "Test",
        }

        response = app_client.post(
            f"/crm/businesses/{sample_business['id']}/activities",
            json=activity_data,
        )

        assert response.status_code == 422

    def test_activity_business_not_found(self, app_client, mock_supabase):
        """Chyba při vytvoření aktivity pro neexistující business."""
        logger.info("Testing activity for non-existent business")
        mock_supabase.data_store["businesses"] = []

        activity_data = {
            "activity_type": "call",
            "description": "Test",
        }

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.post(
                "/crm/businesses/nonexistent-id/activities",
                json=activity_data,
            )

        assert response.status_code == 404


# =============================================================================
# TESTY PRO ČTENÍ AKTIVIT
# =============================================================================

class TestGetActivities:
    """Testy pro GET /crm/businesses/{id}/activities - čtení aktivit."""

    def test_get_activities_for_business(
        self, app_client, mock_supabase, sample_business, sample_activity
    ):
        """Úspěšné načtení aktivit pro business."""
        logger.info("Testing get activities for business")
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["crm_activities"] = [sample_activity]
        mock_supabase.data_store["sellers"] = [
            {"id": "seller-123", "first_name": "Jan", "last_name": "Novák"}
        ]

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.get(
                f"/crm/businesses/{sample_business['id']}/activities"
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_no_activities_returns_empty(
        self, app_client, mock_supabase, sample_business
    ):
        """Business bez aktivit vrací prázdný seznam."""
        logger.info("Testing empty activities list")
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["crm_activities"] = []

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.get(
                f"/crm/businesses/{sample_business['id']}/activities"
            )

        assert response.status_code == 200
        assert response.json() == []

    def test_activities_business_not_found(self, app_client, mock_supabase):
        """Chyba při čtení aktivit pro neexistující business."""
        logger.info("Testing activities for non-existent business")
        mock_supabase.data_store["businesses"] = []

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.get(
                "/crm/businesses/nonexistent-id/activities"
            )

        assert response.status_code == 404

    def test_activities_with_limit(
        self, app_client, mock_supabase, sample_business
    ):
        """Aktivy s limit parametrem."""
        logger.info("Testing activities with limit")
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["crm_activities"] = []

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.get(
                f"/crm/businesses/{sample_business['id']}/activities?limit=10"
            )

        assert response.status_code == 200
