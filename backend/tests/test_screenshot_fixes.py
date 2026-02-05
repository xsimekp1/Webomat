import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.database import get_supabase
from unittest.mock import patch, AsyncMock


class TestScreenshotFunctionality:
    """Testy pro screenshot funkčnost a opravy."""

    @pytest.fixture
    async def app_client(self):
        """Async test client s FastAPI app."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase klient."""
        mock = AsyncMock()
        mock.table.return_value.select.return_value.execute.return_value.data = []
        return mock

    @pytest.fixture
    def auth_headers(self):
        """Testovací auth headers."""
        return {"Authorization": "Bearer test-token"}

    @pytest.mark.asyncio
    async def test_screenshot_payload_viewport_success(self, app_client, mock_supabase, auth_headers):
        """Test screenshot endpoint s viewport parametrem - úspěšný případ."""
        
        # Mock data
        test_html = "<html><body><h1>Test Web</h1></body></html>"
        expected_response = {
            "screenshot_url": "https://example.com/screenshots/test-thumbnail.png",
            "thumbnail_url": "https://example.com/screenshots/test-thumbnail.png",
            "screenshot_full_url": "https://example.com/screenshots/test.png"
        }

        # Mock Supabase a screenshot službu
        with patch("app.routers.website.get_supabase", return_value=mock_supabase), \
             patch("app.routers.website.capture_screenshot", new=AsyncMock(return_value=expected_response)):
            
            response = await app_client.post(
                "/website/screenshot-test",
                json={
                    "html_content": test_html,
                    "viewport": "thumbnail"
                },
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["screenshot_url"] == expected_response["screenshot_url"]
        assert data["thumbnail_url"] == expected_response["thumbnail_url"]

    @pytest.mark.asyncio
    async def test_screenshot_payload_desktop_viewport(self, app_client, mock_supabase, auth_headers):
        """Test screenshot endpoint s desktop viewport parametrem."""
        
        test_html = "<html><body><h1>Desktop Test</h1></body></html>"
        expected_response = {
            "screenshot_url": "https://example.com/screenshots/test-desktop.png",
            "thumbnail_url": "https://example.com/screenshots/test-desktop-thumbnail.png",
            "screenshot_full_url": "https://example.com/screenshots/test-desktop.png"
        }

        with patch("app.routers.website.get_supabase", return_value=mock_supabase), \
             patch("app.routers.website.capture_screenshot", new=AsyncMock(return_value=expected_response)):
            
            response = await app_client.post(
                "/website/screenshot-test",
                json={
                    "html_content": test_html,
                    "viewport": "desktop"
                },
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "desktop" in data["screenshot_url"]

    @pytest.mark.asyncio
    async def test_screenshot_payload_type_fails(self, app_client, mock_supabase, auth_headers):
        """Test že 'type' pole selže s 422 validation error."""
        
        test_html = "<html><body><h1>Test</h1></body></html>"

        with patch("app.routers.website.get_supabase", return_value=mock_supabase):
            
            response = await app_client.post(
                "/website/screenshot-test",
                json={
                    "html_content": test_html,
                    "type": "thumbnail"  # Špatné pole name
                },
                headers=auth_headers
            )

        assert response.status_code == 422
        error_detail = response.json()["detail"][0]
        assert error_detail["loc"] == ["body", "viewport"]
        assert error_detail["msg"] == "Field required"
        assert error_detail["type"] == "missing"

    @pytest.mark.asyncio
    async def test_screenshot_missing_html_content(self, app_client, mock_supabase, auth_headers):
        """Test že chybí html_content pole selže."""
        
        with patch("app.routers.website.get_supabase", return_value=mock_supabase):
            
            response = await app_client.post(
                "/website/screenshot-test",
                json={
                    "viewport": "thumbnail"
                    # Chybí html_content
                },
                headers=auth_headers
            )

        assert response.status_code == 422
        error_detail = response.json()["detail"][0]
        assert error_detail["loc"] == ["body", "html_content"]
        assert error_detail["msg"] == "Field required"

    @pytest.mark.asyncio
    async def test_screenshot_invalid_viewport_value(self, app_client, mock_supabase, auth_headers):
        """Test že neplatná hodnota viewportu selže."""
        
        test_html = "<html><body><h1>Test</h1></body></html>"

        with patch("app.routers.website.get_supabase", return_value=mock_supabase):
            
            response = await app_client.post(
                "/website/screenshot-test",
                json={
                    "html_content": test_html,
                    "viewport": "invalid_size"
                },
                headers=auth_headers
            )

        assert response.status_code == 422
        error_detail = response.json()["detail"][0]
        assert error_detail["loc"] == ["body", "viewport"]
        assert "not a valid enumeration member" in error_detail["msg"]

    @pytest.mark.asyncio
    async def test_screenshot_unauthorized(self, app_client, mock_supabase):
        """Test že bez auth header vrátí 401."""
        
        test_html = "<html><body><h1>Test</h1></body></html>"

        with patch("app.routers.website.get_supabase", return_value=mock_supabase):
            
            response = await app_client.post(
                "/website/screenshot-test",
                json={
                    "html_content": test_html,
                    "viewport": "thumbnail"
                }
                # Bez auth headers
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_screenshot_method_not_allowed_get(self, app_client, mock_supabase, auth_headers):
        """Test že GET request vrátí 405 Method Not Allowed."""
        
        with patch("app.routers.website.get_supabase", return_value=mock_supabase):
            
            response = await app_client.get(
                "/website/screenshot-test",
                headers=auth_headers
            )

        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_screenshot_service_error_handling(self, app_client, mock_supabase, auth_headers):
        """Test handling chyb ve screenshot službě."""
        
        test_html = "<html><body><h1>Test</h1></body></html>"

        # Mock screenshot service error
        with patch("app.routers.website.get_supabase", return_value=mock_supabase), \
             patch("app.routers.website.capture_screenshot", new=AsyncMock(side_effect=Exception("Screenshot service failed"))):
            
            response = await app_client.post(
                "/website/screenshot-test",
                json={
                    "html_content": test_html,
                    "viewport": "thumbnail"
                },
                headers=auth_headers
            )

        assert response.status_code == 500
        assert "Screenshot service failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_screenshot_empty_html_content(self, app_client, mock_supabase, auth_headers):
        """Test screenshot s prázdným HTML obsahem."""
        
        expected_response = {
            "screenshot_url": "https://example.com/screenshots/empty-thumbnail.png",
            "thumbnail_url": "https://example.com/screenshots/empty-thumbnail.png",
            "screenshot_full_url": "https://example.com/screenshots/empty.png"
        }

        with patch("app.routers.website.get_supabase", return_value=mock_supabase), \
             patch("app.routers.website.capture_screenshot", new=AsyncMock(return_value=expected_response)):
            
            response = await app_client.post(
                "/website/screenshot-test",
                json={
                    "html_content": "",
                    "viewport": "thumbnail"
                },
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["screenshot_url"] == expected_response["screenshot_url"]

    @pytest.mark.asyncio
    async def test_screenshot_large_html_content(self, app_client, mock_supabase, auth_headers):
        """Test screenshot s velkým HTML obsahem."""
        
        # Velký HTML obsah (50KB)
        large_html = "<html><body>" + "<p>Large content</p>" * 1000 + "</body></html>"
        
        expected_response = {
            "screenshot_url": "https://example.com/screenshots/large-thumbnail.png",
            "thumbnail_url": "https://example.com/screenshots/large-thumbnail.png",
            "screenshot_full_url": "https://example.com/screenshots/large.png"
        }

        with patch("app.routers.website.get_supabase", return_value=mock_supabase), \
             patch("app.routers.website.capture_screenshot", new=AsyncMock(return_value=expected_response)):
            
            response = await app_client.post(
                "/website/screenshot-test",
                json={
                    "html_content": large_html,
                    "viewport": "thumbnail"
                },
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["screenshot_url"] == expected_response["screenshot_url"]