import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
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
    must_change_password=False
)

MOCK_ADMIN_USER = User(
    id="123e4567-e89b-12d3-a456-426614174001", 
    email="admin@test.com",
    first_name="Admin",
    last_name="User",
    role="admin",
    is_active=True,
    must_change_password=False
)

# Sample version data
SAMPLE_VERSION = {
    "id": "456e7890-e89b-12d3-a456-426614174000",
    "project_id": "789e0123-e89b-12d3-a456-426614174000",
    "version_number": 1,
    "status": "created",
    "is_current": False,
    "deployment_status": "none",
    "created_at": "2024-01-01T00:00:00Z"
}

SAMPLE_VERSION_DEPLOYED = {
    **SAMPLE_VERSION,
    "deployment_status": "deployed"
}

SAMPLE_VERSION_CURRENT = {
    **SAMPLE_VERSION,
    "is_current": True
}


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch('app.routers.web_project.get_supabase') as mock_get_supabase:
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


class TestDeleteVersion:
    """Test DELETE /web-project/versions/{version_id} endpoint."""

    def test_delete_version_success(self, mock_supabase, mock_current_user):
        """Test successful version deletion (soft delete)."""
        # Setup mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = [SAMPLE_VERSION]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"status": "archived"}]
        
        # Override auth dependency
        app.dependency_overrides[require_sales_or_admin] = mock_current_user()
        
        # Make request
        response = client.delete("/web-project/versions/456e7890-e89b-12d3-a456-426614174000")
        
        # Assertions
        assert response.status_code == 200
        assert response.json() == {"message": "Verze byla smazána"}
        
        # Verify Supabase calls
        mock_supabase.table.assert_called_with("website_versions")
        mock_supabase.table.return_value.update.assert_called_once_with({
            "status": "archived",
            "updated_at": mock_supabase.table.return_value.update.return_value.eq.return_value.execute.call_args[0][1]["updated_at"]
        })
        
        # Clean up
        app.dependency_overrides.clear()

    def test_delete_deployed_version_forbidden(self, mock_supabase, mock_current_user):
        """Test deletion of deployed version should fail."""
        # Setup mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = [SAMPLE_VERSION_DEPLOYED]
        
        # Override auth dependency
        app.dependency_overrides[require_sales_or_admin] = mock_current_user()
        
        # Make request
        response = client.delete("/web-project/versions/456e7890-e89b-12d3-a456-426614174000")
        
        # Assertions
        assert response.status_code == 400
        assert "Nasazenou verzi nelze smazat" in response.json()["detail"]
        
        # Clean up
        app.dependency_overrides.clear()

    def test_delete_current_version_forbidden(self, mock_supabase, mock_current_user):
        """Test deletion of current version should fail."""
        # Setup mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = [SAMPLE_VERSION_CURRENT]
        
        # Override auth dependency
        app.dependency_overrides[require_sales_or_admin] = mock_current_user()
        
        # Make request
        response = client.delete("/web-project/versions/456e7890-e89b-12d3-a456-426614174000")
        
        # Assertions
        assert response.status_code == 400
        assert "Aktuální verzi nelze smazat" in response.json()["detail"]
        
        # Clean up
        app.dependency_overrides.clear()

    def test_delete_version_not_found(self, mock_supabase, mock_current_user):
        """Test deletion of non-existent version should fail."""
        # Setup mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        
        # Override auth dependency
        app.dependency_overrides[require_sales_or_admin] = mock_current_user()
        
        # Make request
        response = client.delete("/web-project/versions/non-existent-id")
        
        # Assertions
        assert response.status_code == 404
        assert "Verze nenalezena" in response.json()["detail"]
        
        # Clean up
        app.dependency_overrides.clear()

    def test_delete_version_admin_access(self, mock_supabase, mock_current_user):
        """Test admin can delete any version they have access to."""
        # Setup mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = [SAMPLE_VERSION]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"status": "archived"}]
        
        # Override auth dependency with admin user
        app.dependency_overrides[require_sales_or_admin] = mock_current_user(MOCK_ADMIN_USER)
        
        # Make request
        response = client.delete("/web-project/versions/456e7890-e89b-12d3-a456-426614174000")
        
        # Assertions
        assert response.status_code == 200
        assert response.json() == {"message": "Verze byla smazána"}
        
        # Clean up
        app.dependency_overrides.clear()

    def test_delete_version_unauthorized(self, mock_supabase):
        """Test unauthorized access should fail."""
        # Don't override auth dependency - this should trigger authentication failure
        
        # Make request without auth
        response = client.delete("/web-project/versions/456e7890-e89b-12d3-a456-426614174000")
        
        # Should fail with authentication error
        assert response.status_code in [401, 403]

    def test_delete_version_database_error(self, mock_supabase, mock_current_user):
        """Test database error during deletion should fail."""
        # Setup mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = [SAMPLE_VERSION]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = None
        
        # Override auth dependency
        app.dependency_overrides[require_sales_or_admin] = mock_current_user()
        
        # Make request
        response = client.delete("/web-project/versions/456e7890-e89b-12d3-a456-426614174000")
        
        # Assertions
        assert response.status_code == 500
        assert "Nepodařilo se smazat verzi" in response.json()["detail"]
        
        # Clean up
        app.dependency_overrides.clear()