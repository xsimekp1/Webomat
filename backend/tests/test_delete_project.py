import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock, ANY
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.dependencies import require_sales_or_admin
from app.schemas.auth import User

client = TestClient(app)

# Mock user for testing
MOCK_SALES_USER = User(
    id="123e4567-e89b-12d3-a456-426614174000",
    email="sales@test.com",
    first_name="Sales",
    last_name="User",
    role="sales",
    is_active=True,
    must_change_password=False,
)

MOCK_ADMIN_USER = User(
    id="123e4567-e89b-12d3-a456-426614174001",
    email="admin@test.com",
    first_name="Admin",
    last_name="User",
    role="admin",
    is_active=True,
    must_change_password=False,
)

# Sample project data
SAMPLE_PROJECT = {
    "id": "789e0123-e89b-12d3-a456-426614174000",
    "business_id": "abc12345-e89b-12d3-a456-426614174000",
    "status": "offer",
    "created_at": "2024-01-01T00:00:00Z",
}

SAMPLE_PROJECT_WITH_DEPLOYED = {**SAMPLE_PROJECT, "status": "in_production"}


class TestDeleteProject:
    """Test DELETE /web-project/{project_id} endpoint."""

    def test_delete_project_success(self, mock_supabase, mock_current_user):
        """Test successful project deletion (soft delete)."""
        # Setup mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            SAMPLE_PROJECT
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []  # No deployed versions
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
            {"status": "cancelled"}
        ]

        # Override auth dependency
        app.dependency_overrides[require_sales_or_admin] = mock_current_user()

        # Make request
        response = client.delete("/web-project/789e0123-e89b-12d3-a456-426614174000")

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"message": "Projekt byl smazán"}

        # Verify project was marked as cancelled
        mock_supabase.table.return_value.update.assert_any_call(
            {"status": "cancelled", "updated_at": ANY},
            {"id": "789e0123-e89b-12d3-a456-426614174000"},
        )

        # Clean up
        app.dependency_overrides.clear()

    def test_delete_project_with_deployed_version_forbidden(
        self, mock_supabase, mock_current_user
    ):
        """Test deletion of project with deployed versions should fail."""
        # Setup mocks - project has deployed version
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            SAMPLE_PROJECT
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {"id": "version123"}
        ]  # Deployed version exists

        # Override auth dependency
        app.dependency_overrides[require_sales_or_admin] = mock_current_user()

        # Make request
        response = client.delete("/web-project/789e0123-e89b-12d3-a456-426614174000")

        # Assertions
        assert response.status_code == 400
        assert "nasazené verze" in response.json()["detail"]
        assert "nejdříve odstraňte nasazení" in response.json()["detail"]

        # Clean up
        app.dependency_overrides.clear()

    def test_delete_project_admin_access(self, mock_supabase, mock_current_user):
        """Test admin can delete any project they have access to."""
        # Setup mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            SAMPLE_PROJECT
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []  # No deployed versions
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
            {"status": "cancelled"}
        ]

        # Override auth dependency with admin user
        app.dependency_overrides[require_sales_or_admin] = mock_current_user(
            MOCK_ADMIN_USER
        )

        # Make request
        response = client.delete("/web-project/789e0123-e89b-12d3-a456-426614174000")

        # Assertions
        assert response.status_code == 200
        assert response.json() == {"message": "Projekt byl smazán"}

        # Clean up
        app.dependency_overrides.clear()

    def test_delete_project_not_found(self, mock_supabase, mock_current_user):
        """Test deletion of non-existent project should fail."""
        # Setup mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []

        # Override auth dependency
        app.dependency_overrides[require_sales_or_admin] = mock_current_user()

        # Make request
        response = client.delete("/web-project/non-existent-id")

        # Assertions
        assert response.status_code == 404
        assert "Projekt nenalezen" in response.json()["detail"]

        # Clean up
        app.dependency_overrides.clear()

    def test_delete_project_unauthorized(self, mock_supabase):
        """Test unauthorized access should fail."""
        # Don't override auth dependency - this should trigger authentication failure

        # Make request without auth
        response = client.delete("/web-project/789e0123-e89b-12d3-a456-426614174000")

        # Should fail with authentication error
        assert response.status_code in [401, 403]

    def test_delete_project_database_error(self, mock_supabase, mock_current_user):
        """Test database error during deletion should fail."""
        # Setup mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            SAMPLE_PROJECT
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []  # No deployed versions
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = None

        # Override auth dependency
        app.dependency_overrides[require_sales_or_admin] = mock_current_user()

        # Make request
        response = client.delete("/web-project/789e0123-e89b-12d3-a456-426614174000")

        # Assertions
        assert response.status_code == 500
        assert "Nepodařilo se smazat projekt" in response.json()["detail"]

        # Clean up
        app.dependency_overrides.clear()

    def test_delete_project_archives_versions(self, mock_supabase, mock_current_user):
        """Test that all versions are archived when project is deleted."""
        # Setup mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            SAMPLE_PROJECT
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []  # No deployed versions
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
            {"status": "cancelled"}
        ]

        # Override auth dependency
        app.dependency_overrides[require_sales_or_admin] = mock_current_user()

        # Make request
        response = client.delete("/web-project/789e0123-e89b-12d3-a456-426614174000")

        # Assertions
        assert response.status_code == 200

        # Verify versions were archived
        mock_supabase.table.return_value.update.assert_any_call(
            {"status": "archived"},
            {"project_id": "789e0123-e89b-12d3-a456-426614174000"},
        )

        # Clean up
        app.dependency_overrides.clear()


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch("app.routers.web_project.get_supabase") as mock_get_supabase:
        mock_client = Mock()
        mock_get_supabase.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_current_user():
    """Mock current user dependency."""

    def _get_user(user=MOCK_SALES_USER):
        def _dependency():
            return user

        return _dependency

    return _get_user
