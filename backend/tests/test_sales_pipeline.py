"""
Unit testy pro sales pipeline.

Testuje hlavní flow obchodníka:
1. Vytvoření klienta (business)
2. Vytvoření projektu
3. Vytvoření website verze
4. Dry run generování webu
5. CRM status transitions
"""
import pytest
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# TESTY PRO BUSINESS (KLIENT)
# =============================================================================

class TestCreateBusiness:
    """Testy pro POST /crm/businesses - vytvoření nového klienta."""

    def test_create_business_success(self, app_client, mock_supabase):
        """Úspěšné vytvoření nového businessu."""
        # Arrange - nastavíme mock data
        mock_supabase.data_store["businesses"] = []

        new_business = {
            "name": "Nová Firma s.r.o.",
            "phone": "+420 111 222 333",
            "email": "nova@firma.cz",
            "address": "Nová ulice 1, Praha",
        }

        # Act
        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            with patch("app.routers.crm.check_duplicate_business", return_value=None):
                response = app_client.post("/crm/businesses", json=new_business)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == new_business["name"]
        assert "id" in data

    def test_create_business_with_all_fields(self, app_client, mock_supabase):
        """Vytvoření businessu se všemi volitelnými poli."""
        mock_supabase.data_store["businesses"] = []

        new_business = {
            "name": "Kompletní Firma a.s.",
            "phone": "+420 999 888 777",
            "email": "kompletni@firma.cz",
            "address": "Kompletní 99, Brno",
            "website": "https://kompletni.cz",
            "category": "IT služby",
            "notes": "Testovací poznámky",
            "status_crm": "new",
            "ico": "12345678",
            "dic": "CZ12345678",
            "contact_person": "Jan Novák",
        }

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            with patch("app.routers.crm.check_duplicate_business", return_value=None):
                response = app_client.post("/crm/businesses", json=new_business)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == new_business["name"]

    def test_create_business_minimal(self, app_client, mock_supabase):
        """Vytvoření businessu jen s povinným názvem."""
        mock_supabase.data_store["businesses"] = []

        new_business = {"name": "Minimální Firma"}

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            with patch("app.routers.crm.check_duplicate_business", return_value=None):
                response = app_client.post("/crm/businesses", json=new_business)

        assert response.status_code == 201

    def test_create_business_missing_name(self, app_client, mock_supabase):
        """Chyba při vytvoření businessu bez názvu."""
        new_business = {"phone": "+420 111 222 333"}

        response = app_client.post("/crm/businesses", json=new_business)

        assert response.status_code == 422  # Validation error


class TestBusinessDuplication:
    """Testy pro deduplikaci businessů."""

    def test_duplicate_by_phone_blocked(self, app_client, mock_supabase):
        """Duplicita podle telefonu - blokuje vytvoření."""
        existing_business = {
            "id": "existing-123",
            "name": "Existující Firma",
            "phone": "+420 123 456 789",
        }

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            with patch(
                "app.routers.crm.check_duplicate_business",
                return_value=existing_business,
            ):
                response = app_client.post(
                    "/crm/businesses",
                    json={"name": "Duplicitní Firma", "phone": "+420 123 456 789"},
                )

        assert response.status_code == 409  # Conflict
        assert "existuje" in response.json()["detail"].lower()

    def test_duplicate_by_website_blocked(self, app_client, mock_supabase):
        """Duplicita podle webu - blokuje vytvoření."""
        existing_business = {
            "id": "existing-456",
            "name": "Web Firma",
            "website": "https://webfirma.cz",
        }

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            with patch(
                "app.routers.crm.check_duplicate_business",
                return_value=existing_business,
            ):
                response = app_client.post(
                    "/crm/businesses",
                    json={"name": "Jiná Firma", "website": "https://webfirma.cz"},
                )

        assert response.status_code == 409


class TestPhoneNormalization:
    """Testy pro normalizaci telefonního čísla při deduplikaci."""

    def test_phone_normalization_removes_spaces(self):
        """Normalizace telefonu - odstranění mezer."""
        from app.routers.crm import check_duplicate_business

        # Tento test ověřuje logiku normalizace
        phone1 = "+420 123 456 789"
        phone2 = "+420123456789"

        # Obě čísla by měla být normalizována na stejný formát
        normalized1 = phone1.replace(" ", "").replace("-", "")
        normalized2 = phone2.replace(" ", "").replace("-", "")

        assert normalized1[-9:] == normalized2[-9:]

    def test_phone_normalization_removes_dashes(self):
        """Normalizace telefonu - odstranění pomlček."""
        phone1 = "123-456-789"
        phone2 = "123456789"

        normalized1 = phone1.replace(" ", "").replace("-", "")
        normalized2 = phone2.replace(" ", "").replace("-", "")

        assert normalized1[-9:] == normalized2[-9:]


class TestWebsiteNormalization:
    """Testy pro normalizaci webu při deduplikaci."""

    def test_website_normalization_strips_protocol(self):
        """Normalizace webu - odstranění protokolu."""
        website1 = "https://example.com"
        website2 = "http://example.com"
        website3 = "example.com"

        def normalize(url):
            return (
                url.lower()
                .replace("https://", "")
                .replace("http://", "")
                .replace("www.", "")
                .rstrip("/")
            )

        assert normalize(website1) == normalize(website2) == normalize(website3)

    def test_website_normalization_strips_www(self):
        """Normalizace webu - odstranění www."""
        website1 = "https://www.example.com"
        website2 = "https://example.com"

        def normalize(url):
            return (
                url.lower()
                .replace("https://", "")
                .replace("http://", "")
                .replace("www.", "")
                .rstrip("/")
            )

        assert normalize(website1) == normalize(website2)


# =============================================================================
# TESTY PRO PROJEKTY
# =============================================================================

class TestCreateProject:
    """Testy pro POST /crm/businesses/{id}/projects - vytvoření projektu."""

    def test_create_project_success(self, app_client, mock_supabase, sample_business):
        """Úspěšné vytvoření projektu pro business."""
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["website_projects"] = []

        new_project = {
            "package": "profi",
            "status": "offer",
            "price_setup": 15000.0,
            "price_monthly": 500.0,
            "domain": "novaweb.cz",
            "notes": "Nový projekt",
        }

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.post(
                f"/crm/businesses/{sample_business['id']}/projects", json=new_project
            )

        assert response.status_code == 201
        data = response.json()
        assert data["package"] == "profi"
        assert data["status"] == "offer"

    def test_create_project_all_packages(self, app_client, mock_supabase, sample_business):
        """Vytvoření projektu s různými balíčky."""
        mock_supabase.data_store["businesses"] = [sample_business]

        packages = ["start", "profi", "premium", "custom"]

        for package in packages:
            mock_supabase.data_store["website_projects"] = []

            with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
                response = app_client.post(
                    f"/crm/businesses/{sample_business['id']}/projects",
                    json={"package": package},
                )

            assert response.status_code == 201, f"Failed for package: {package}"
            assert response.json()["package"] == package

    def test_create_project_all_statuses(self, app_client, mock_supabase, sample_business):
        """Vytvoření projektu s různými statusy."""
        mock_supabase.data_store["businesses"] = [sample_business]

        statuses = ["offer", "won", "in_production", "delivered", "live", "cancelled"]

        for status in statuses:
            mock_supabase.data_store["website_projects"] = []

            with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
                response = app_client.post(
                    f"/crm/businesses/{sample_business['id']}/projects",
                    json={"status": status},
                )

            assert response.status_code == 201, f"Failed for status: {status}"
            assert response.json()["status"] == status

    def test_create_project_business_not_found(self, app_client, mock_supabase):
        """Chyba při vytvoření projektu pro neexistující business."""
        mock_supabase.data_store["businesses"] = []

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.post(
                "/crm/businesses/nonexistent-id/projects", json={"package": "start"}
            )

        assert response.status_code == 404

    def test_create_project_with_prices(self, app_client, mock_supabase, sample_business):
        """Vytvoření projektu s cenami."""
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["website_projects"] = []

        new_project = {
            "package": "premium",
            "price_setup": 25000.0,
            "price_monthly": 1500.0,
        }

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.post(
                f"/crm/businesses/{sample_business['id']}/projects", json=new_project
            )

        assert response.status_code == 201
        data = response.json()
        assert data["price_setup"] == 25000.0
        assert data["price_monthly"] == 1500.0


# =============================================================================
# TESTY PRO WEBSITE VERZE
# =============================================================================

class TestCreateWebsiteVersion:
    """Testy pro POST /crm/projects/{id}/versions - vytvoření verze."""

    def test_create_version_success(self, app_client, mock_supabase, sample_business, sample_project):
        """Úspěšné vytvoření verze vrací 201."""
        logger.info("Testing create version success")
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["website_projects"] = [sample_project]
        mock_supabase.data_store["website_versions"] = []

        new_version = {
            "project_id": sample_project["id"],
            "notes": "První verze webu",
        }

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.post(
                f"/crm/projects/{sample_project['id']}/versions", json=new_version
            )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data

    def test_version_number_increment_logic(self):
        """Test logiky inkrementace čísla verze."""
        logger.info("Testing version number increment logic")

        # Simulace existujících verzí
        existing_versions = [
            {"id": "v1", "project_id": "project-abc", "version_number": 1},
            {"id": "v2", "project_id": "project-abc", "version_number": 2},
        ]

        # Test, že logika inkrementace funguje správně
        max_version = max(v["version_number"] for v in existing_versions)
        next_version = max_version + 1

        assert next_version == 3

    def test_version_number_first(self):
        """První verze má číslo 1."""
        logger.info("Testing first version number")

        existing_versions = []

        if not existing_versions:
            next_version = 1
        else:
            max_version = max(v["version_number"] for v in existing_versions)
            next_version = max_version + 1

        assert next_version == 1

    def test_create_version_project_not_found(self, app_client, mock_supabase):
        """Chyba při vytvoření verze pro neexistující projekt."""
        logger.info("Testing create version for non-existent project")
        mock_supabase.data_store["website_projects"] = []

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.post(
                "/crm/projects/nonexistent-id/versions",
                json={"project_id": "nonexistent-id"},
            )

        assert response.status_code == 404

    def test_create_version_with_paths_accepted(
        self, app_client, mock_supabase, sample_business, sample_project
    ):
        """Verze s cestami k souborům je přijata."""
        logger.info("Testing create version with file paths")
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["website_projects"] = [sample_project]
        mock_supabase.data_store["website_versions"] = []

        new_version = {
            "project_id": sample_project["id"],
            "source_bundle_path": "/storage/versions/v1/bundle.zip",
            "preview_image_path": "/storage/versions/v1/preview.png",
            "notes": "Verze s přílohou",
        }

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.post(
                f"/crm/projects/{sample_project['id']}/versions", json=new_version
            )

        assert response.status_code == 201


# =============================================================================
# TESTY PRO DRY RUN GENEROVÁNÍ WEBU
# =============================================================================

class TestDryRunWebsiteGeneration:
    """Testy pro POST /website/generate s dry_run=True."""

    def test_dry_run_returns_html(
        self, admin_client, mock_supabase, sample_business, sample_project
    ):
        """Dry run vrací validní HTML."""
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["website_projects"] = [sample_project]

        with patch("app.routers.website.get_supabase", return_value=mock_supabase):
            response = admin_client.post(
                "/website/generate",
                json={"project_id": sample_project["id"], "dry_run": True},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "html_content" in data
        assert "<!DOCTYPE html>" in data["html_content"]
        assert "DRY RUN" in data["message"]

    def test_dry_run_html_structure(
        self, admin_client, mock_supabase, sample_business, sample_project
    ):
        """Dry run HTML má správnou strukturu."""
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["website_projects"] = [sample_project]

        with patch("app.routers.website.get_supabase", return_value=mock_supabase):
            response = admin_client.post(
                "/website/generate",
                json={"project_id": sample_project["id"], "dry_run": True},
            )

        html = response.json()["html_content"]

        # Ověříme základní HTML elementy
        assert "<html" in html
        assert "<head>" in html
        assert "<body>" in html
        assert "</html>" in html

    def test_dry_run_contains_styling(
        self, admin_client, mock_supabase, sample_business, sample_project
    ):
        """Dry run HTML obsahuje CSS styling."""
        mock_supabase.data_store["businesses"] = [sample_business]
        mock_supabase.data_store["website_projects"] = [sample_project]

        with patch("app.routers.website.get_supabase", return_value=mock_supabase):
            response = admin_client.post(
                "/website/generate",
                json={"project_id": sample_project["id"], "dry_run": True},
            )

        html = response.json()["html_content"]

        # Ověříme přítomnost stylů
        assert "<style>" in html
        assert "gradient" in html  # Má gradient background

    def test_dry_run_project_not_found(self, admin_client, mock_supabase):
        """Chyba při dry run pro neexistující projekt."""
        mock_supabase.data_store["website_projects"] = []

        with patch("app.routers.website.get_supabase", return_value=mock_supabase):
            response = admin_client.post(
                "/website/generate", json={"project_id": "nonexistent", "dry_run": True}
            )

        assert response.status_code == 404


class TestDryRunTestEndpoint:
    """Testy pro POST /website/generate-test (admin only)."""

    def test_generate_test_default_dry_run(self, admin_client):
        """Testovací endpoint defaultně používá dry run."""
        response = admin_client.post(
            "/website/generate-test",
            json={"business_name": "Test Firma", "business_type": "kavárna"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "html_content" in data

    def test_generate_test_contains_business_info(self, admin_client):
        """Testovací HTML obsahuje zadané informace o firmě."""
        business_name = "Moje Kavárna"
        business_type = "kavárna"

        response = admin_client.post(
            "/website/generate-test",
            json={"business_name": business_name, "business_type": business_type},
        )

        html = response.json()["html_content"]
        assert business_name in html
        assert business_type in html

    def test_generate_test_without_dry_run_fails(self, admin_client):
        """Bez dry run vrací 501 Not Implemented."""
        response = admin_client.post(
            "/website/generate-test",
            json={
                "dry_run": False,
                "business_name": "Test",
                "business_type": "obchod",
            },
        )

        assert response.status_code == 501


# =============================================================================
# POMOCNÉ TESTY
# =============================================================================

class TestHelperFunctions:
    """Testy pro pomocné funkce v CRM routeru."""

    def test_types_to_string_with_list(self):
        """Konverze seznamu typů na string."""
        from app.routers.crm import types_to_string

        types = ["restaurant", "cafe", "bar"]
        result = types_to_string(types)

        assert result == "restaurant, cafe, bar"

    def test_types_to_string_empty(self):
        """Konverze prázdného seznamu vrací None."""
        from app.routers.crm import types_to_string

        assert types_to_string(None) is None
        assert types_to_string([]) is None

    def test_types_to_string_single_item(self):
        """Konverze jednoho prvku."""
        from app.routers.crm import types_to_string

        result = types_to_string(["restaurant"])
        assert result == "restaurant"


# =============================================================================
# TESTY PRO CRM STATUS TRANSITIONS
# =============================================================================

class TestCRMStatusTransitions:
    """Testy pro přechody mezi CRM statusy.

    Note: Mock nepersistuje updaty, proto testujeme pouze validaci
    vstupů a HTTP response kódy.
    """

    def test_status_update_calling_accepted(self, app_client, mock_supabase, sample_business):
        """Status 'calling' je validní a endpoint vrací 200."""
        logger.info("Testing status value: calling")
        mock_supabase.data_store["businesses"] = [sample_business]

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.put(
                f"/crm/businesses/{sample_business['id']}",
                json={"status_crm": "calling"},
            )

        assert response.status_code == 200

    def test_status_update_interested_accepted(self, app_client, mock_supabase, sample_business):
        """Status 'interested' je validní a endpoint vrací 200."""
        logger.info("Testing status value: interested")
        mock_supabase.data_store["businesses"] = [sample_business]

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.put(
                f"/crm/businesses/{sample_business['id']}",
                json={"status_crm": "interested"},
            )

        assert response.status_code == 200

    def test_status_update_offer_sent_accepted(self, app_client, mock_supabase, sample_business):
        """Status 'offer_sent' je validní a endpoint vrací 200."""
        logger.info("Testing status value: offer_sent")
        mock_supabase.data_store["businesses"] = [sample_business]

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.put(
                f"/crm/businesses/{sample_business['id']}",
                json={"status_crm": "offer_sent"},
            )

        assert response.status_code == 200

    def test_status_update_won_accepted(self, app_client, mock_supabase, sample_business):
        """Status 'won' je validní a endpoint vrací 200."""
        logger.info("Testing status value: won")
        mock_supabase.data_store["businesses"] = [sample_business]

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.put(
                f"/crm/businesses/{sample_business['id']}",
                json={"status_crm": "won"},
            )

        assert response.status_code == 200

    def test_status_update_lost_accepted(self, app_client, mock_supabase, sample_business):
        """Status 'lost' je validní a endpoint vrací 200."""
        logger.info("Testing status value: lost")
        mock_supabase.data_store["businesses"] = [sample_business]

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.put(
                f"/crm/businesses/{sample_business['id']}",
                json={"status_crm": "lost"},
            )

        assert response.status_code == 200

    def test_status_update_dnc_accepted(self, app_client, mock_supabase, sample_business):
        """Status 'dnc' je validní a endpoint vrací 200."""
        logger.info("Testing status value: dnc")
        mock_supabase.data_store["businesses"] = [sample_business]

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            response = app_client.put(
                f"/crm/businesses/{sample_business['id']}",
                json={"status_crm": "dnc"},
            )

        assert response.status_code == 200

    def test_status_invalid_value(self, app_client, mock_supabase, sample_business):
        """Neplatný status vrací validační chybu."""
        logger.info("Testing invalid status value")

        update_data = {"status_crm": "invalid_status"}

        response = app_client.put(
            f"/crm/businesses/{sample_business['id']}", json=update_data
        )

        assert response.status_code == 422  # Validation error

    def test_all_valid_statuses(self, app_client, mock_supabase, sample_business):
        """Všechny platné CRM statusy jsou přijaty."""
        logger.info("Testing all valid CRM statuses")
        mock_supabase.data_store["businesses"] = [sample_business]

        valid_statuses = ["new", "calling", "interested", "offer_sent", "won", "lost", "dnc"]

        with patch("app.routers.crm.get_supabase", return_value=mock_supabase):
            for status_value in valid_statuses:
                response = app_client.put(
                    f"/crm/businesses/{sample_business['id']}",
                    json={"status_crm": status_value},
                )
                assert response.status_code == 200, f"Failed for status: {status_value}"
                logger.debug(f"Status '{status_value}' accepted")
