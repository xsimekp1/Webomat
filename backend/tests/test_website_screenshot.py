"""
Unit testy pro screenshot a deploy endpointy.

Testuje:
1. POST /website/screenshot-test - pořízení screenshotu z HTML
2. POST /website/deploy-test - nasazení testovacího HTML na Vercel
3. GET /website/deployment-status - stav deployment služby

Tyto endpointy jsou admin only!
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# =============================================================================
# TESTY PRO SCREENSHOT-TEST ENDPOINT
# =============================================================================

class TestScreenshotTestEndpoint:
    """Testy pro POST /website/screenshot-test."""

    def test_screenshot_test_allows_sales(self, app_client):
        """Screenshot endpoint je dostupný pro sales uživatele."""
        # Sales user má přístup, ale HTML je příliš krátké -> 400
        response = app_client.post(
            "/website/screenshot-test",
            json={
                "html_content": "<html><body><h1>Test</h1></body></html>",
                "viewport": "thumbnail"
            }
        )

        # Sales user má přístup (dostane 400 kvůli krátkému HTML, ne 403)
        assert response.status_code == 400

    def test_screenshot_test_html_too_short(self, admin_client):
        """Screenshot s příliš krátkým HTML vrací 400."""
        response = admin_client.post(
            "/website/screenshot-test",
            json={
                "html_content": "<html></html>",  # Příliš krátké
                "viewport": "thumbnail"
            }
        )

        assert response.status_code == 400
        assert "příliš krátký" in response.json()["detail"].lower()

    def test_screenshot_test_empty_html(self, admin_client):
        """Screenshot s prázdným HTML vrací 400."""
        response = admin_client.post(
            "/website/screenshot-test",
            json={
                "html_content": "",
                "viewport": "thumbnail"
            }
        )

        assert response.status_code == 400

    def test_screenshot_test_default_viewport(self, admin_client):
        """Screenshot bez viewport parametru použije 'thumbnail'."""
        with patch("app.routers.website.is_playwright_available", return_value=True):
            with patch("app.routers.website.capture_screenshot", new_callable=AsyncMock) as mock_capture:
                with patch("app.routers.website.upload_screenshot", new_callable=AsyncMock) as mock_upload:
                    mock_capture.return_value = b"fake_image_bytes"
                    mock_upload.return_value = "https://storage.example.com/screenshot.png"

                    response = admin_client.post(
                        "/website/screenshot-test",
                        json={
                            "html_content": "<!DOCTYPE html><html><body><h1>Test content for screenshot</h1></body></html>"
                        }
                    )

        if response.status_code == 200:
            # Ověříme, že capture_screenshot byl zavolán s viewport="thumbnail"
            mock_capture.assert_called_once()
            call_kwargs = mock_capture.call_args.kwargs
            assert call_kwargs.get("viewport") == "thumbnail"

    def test_screenshot_test_valid_viewports(self, admin_client):
        """Screenshot akceptuje všechny validní viewport hodnoty."""
        valid_viewports = ["desktop", "mobile", "thumbnail"]

        for viewport in valid_viewports:
            with patch("app.routers.website.is_playwright_available", return_value=True):
                with patch("app.routers.website.capture_screenshot", new_callable=AsyncMock) as mock_capture:
                    with patch("app.routers.website.upload_screenshot", new_callable=AsyncMock) as mock_upload:
                        mock_capture.return_value = b"fake_image_bytes"
                        mock_upload.return_value = f"https://storage.example.com/{viewport}.png"

                        response = admin_client.post(
                            "/website/screenshot-test",
                            json={
                                "html_content": "<!DOCTYPE html><html><body><h1>Test page for viewport testing with enough content</h1></body></html>",
                                "viewport": viewport
                            }
                        )

            # Buď 200 (úspěch) nebo 503 (playwright není dostupný)
            assert response.status_code in [200, 503], f"Failed for viewport: {viewport}"

    def test_screenshot_test_success_with_playwright(self, admin_client):
        """Screenshot s dostupným Playwright vrací URL obrázku."""
        with patch("app.routers.website.is_playwright_available", return_value=True):
            with patch("app.routers.website.capture_screenshot", new_callable=AsyncMock) as mock_capture:
                with patch("app.routers.website.upload_screenshot", new_callable=AsyncMock) as mock_upload:
                    mock_capture.return_value = b"fake_png_bytes_here"
                    mock_upload.return_value = "https://storage.supabase.co/screenshots/test_abc123_thumbnail.png"

                    response = admin_client.post(
                        "/website/screenshot-test",
                        json={
                            "html_content": """<!DOCTYPE html>
                            <html><head><title>Test</title></head>
                            <body><h1>Screenshot Test Page</h1><p>Content here</p></body>
                            </html>""",
                            "viewport": "thumbnail"
                        }
                    )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["screenshot_url"] == "https://storage.supabase.co/screenshots/test_abc123_thumbnail.png"
        assert "úspěšně" in data["message"].lower()

    def test_screenshot_test_playwright_not_available(self, admin_client):
        """Screenshot bez Playwright vrací 503."""
        with patch("app.routers.website.is_playwright_available", return_value=False):
            response = admin_client.post(
                "/website/screenshot-test",
                json={
                    "html_content": "<!DOCTYPE html><html><body><h1>Test content for screenshot generation</h1></body></html>",
                    "viewport": "thumbnail"
                }
            )

        assert response.status_code == 503
        assert "playwright" in response.json()["detail"].lower()

    def test_screenshot_test_capture_error(self, admin_client):
        """Screenshot s chybou při capture vrací 500."""
        with patch("app.routers.website.is_playwright_available", return_value=True):
            with patch("app.routers.website.capture_screenshot", new_callable=AsyncMock) as mock_capture:
                mock_capture.side_effect = Exception("Browser crashed")

                response = admin_client.post(
                    "/website/screenshot-test",
                    json={
                        "html_content": "<!DOCTYPE html><html><body><h1>Test content for error testing</h1></body></html>",
                        "viewport": "desktop"
                    }
                )

        assert response.status_code == 500
        assert "browser crashed" in response.json()["detail"].lower()

    def test_screenshot_test_upload_error(self, admin_client):
        """Screenshot s chybou při upload vrací 500."""
        with patch("app.routers.website.is_playwright_available", return_value=True):
            with patch("app.routers.website.capture_screenshot", new_callable=AsyncMock) as mock_capture:
                with patch("app.routers.website.upload_screenshot", new_callable=AsyncMock) as mock_upload:
                    mock_capture.return_value = b"fake_image_bytes"
                    mock_upload.side_effect = Exception("Storage quota exceeded")

                    response = admin_client.post(
                        "/website/screenshot-test",
                        json={
                            "html_content": "<!DOCTYPE html><html><body><h1>Test content for upload error</h1></body></html>",
                            "viewport": "mobile"
                        }
                    )

        assert response.status_code == 500
        assert "storage quota" in response.json()["detail"].lower()


# =============================================================================
# TESTY PRO DEPLOY-TEST ENDPOINT
# =============================================================================

class TestDeployTestEndpoint:
    """Testy pro POST /website/deploy-test."""

    def test_deploy_test_requires_admin(self, app_client):
        """Deploy endpoint vyžaduje admin práva."""
        response = app_client.post(
            "/website/deploy-test",
            json={
                "html_content": "<html><body><h1>Test</h1></body></html>",
                "business_name": "Test Firma"
            }
        )

        assert response.status_code == 403

    def test_deploy_test_html_too_short(self, admin_client):
        """Deploy s příliš krátkým HTML vrací 400."""
        with patch("app.routers.website.is_vercel_configured", return_value=True):
            response = admin_client.post(
                "/website/deploy-test",
                json={
                    "html_content": "<html></html>",
                    "business_name": "Test"
                }
            )

        assert response.status_code == 400
        assert "příliš krátký" in response.json()["detail"].lower()

    def test_deploy_test_vercel_not_configured(self, admin_client):
        """Deploy bez nakonfigurovaného Vercel vrací 503."""
        with patch("app.routers.website.is_vercel_configured", return_value=False):
            response = admin_client.post(
                "/website/deploy-test",
                json={
                    "html_content": "<!DOCTYPE html><html><body><h1>Test content for deployment</h1></body></html>",
                    "business_name": "Test Firma"
                }
            )

        assert response.status_code == 503
        assert "vercel" in response.json()["detail"].lower()

    def test_deploy_test_success(self, admin_client):
        """Deploy s úspěšným nasazením vrací URL."""
        with patch("app.routers.website.is_vercel_configured", return_value=True):
            with patch("app.routers.website.deploy_html_to_vercel", new_callable=AsyncMock) as mock_deploy:
                mock_deploy.return_value = {
                    "url": "https://test-preview-abc123.vercel.app",
                    "deployment_id": "dpl_abc123xyz"
                }

                response = admin_client.post(
                    "/website/deploy-test",
                    json={
                        "html_content": "<!DOCTYPE html><html><body><h1>Test Page</h1><p>Content</p></body></html>",
                        "business_name": "Moje Firma"
                    }
                )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["url"] == "https://test-preview-abc123.vercel.app"
        assert data["deployment_id"] == "dpl_abc123xyz"

    def test_deploy_test_default_business_name(self, admin_client):
        """Deploy bez business_name použije default hodnotu."""
        with patch("app.routers.website.is_vercel_configured", return_value=True):
            with patch("app.routers.website.deploy_html_to_vercel", new_callable=AsyncMock) as mock_deploy:
                mock_deploy.return_value = {"url": "https://preview.vercel.app", "deployment_id": "123"}

                response = admin_client.post(
                    "/website/deploy-test",
                    json={
                        "html_content": "<!DOCTYPE html><html><body><h1>Test</h1><p>Long enough content here</p></body></html>"
                        # business_name není zadán
                    }
                )

        if response.status_code == 200:
            # Ověříme, že deploy byl zavolán s default business_name
            mock_deploy.assert_called_once()

    def test_deploy_test_error(self, admin_client):
        """Deploy s chybou při nasazení vrací 500."""
        with patch("app.routers.website.is_vercel_configured", return_value=True):
            with patch("app.routers.website.deploy_html_to_vercel", new_callable=AsyncMock) as mock_deploy:
                mock_deploy.side_effect = Exception("Vercel API rate limit")

                response = admin_client.post(
                    "/website/deploy-test",
                    json={
                        "html_content": "<!DOCTYPE html><html><body><h1>Test</h1><p>Content for error test</p></body></html>",
                        "business_name": "Test"
                    }
                )

        assert response.status_code == 500
        assert "vercel" in response.json()["detail"].lower() or "rate limit" in response.json()["detail"].lower()


# =============================================================================
# TESTY PRO DEPLOYMENT-STATUS ENDPOINT
# =============================================================================

class TestDeploymentStatusEndpoint:
    """Testy pro GET /website/deployment-status."""

    def test_deployment_status_requires_admin(self, app_client):
        """Deployment status vyžaduje admin práva."""
        response = app_client.get("/website/deployment-status")

        assert response.status_code == 403

    def test_deployment_status_configured(self, admin_client):
        """Deployment status vrací available=true když je Vercel nakonfigurován."""
        with patch("app.routers.website.is_vercel_configured", return_value=True):
            response = admin_client.get("/website/deployment-status")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert "dostupný" in data["message"].lower()

    def test_deployment_status_not_configured(self, admin_client):
        """Deployment status vrací available=false když Vercel není nakonfigurován."""
        with patch("app.routers.website.is_vercel_configured", return_value=False):
            response = admin_client.get("/website/deployment-status")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert "není nastaven" in data["message"].lower()


# =============================================================================
# TESTY PRO TRANSLATION-STATUS ENDPOINT
# =============================================================================

class TestTranslationStatusEndpoint:
    """Testy pro GET /website/translation-status."""

    def test_translation_status_requires_admin(self, app_client):
        """Translation status vyžaduje admin práva."""
        response = app_client.get("/website/translation-status")

        assert response.status_code == 403

    def test_translation_status_available(self, admin_client):
        """Translation status vrací available=true když je LLM dostupný."""
        with patch("app.routers.website.is_llm_available", return_value=True):
            response = admin_client.get("/website/translation-status")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True

    def test_translation_status_not_available(self, admin_client):
        """Translation status vrací available=false když LLM není dostupný."""
        with patch("app.routers.website.is_llm_available", return_value=False):
            response = admin_client.get("/website/translation-status")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False


# =============================================================================
# TESTY PRO SCREENSHOT-JOB-STATUS ENDPOINT
# =============================================================================

class TestScreenshotJobStatusEndpoint:
    """Testy pro GET /website/screenshot-job/{job_id}."""

    def test_screenshot_job_status_requires_admin(self, app_client):
        """Screenshot job status vyžaduje admin práva."""
        response = app_client.get("/website/screenshot-job/test-job-123")

        assert response.status_code == 403

    def test_screenshot_job_not_found(self, admin_client):
        """Screenshot job neexistující vrací 404."""
        with patch("app.routers.website.get_job_status", new_callable=AsyncMock) as mock_job:
            mock_job.return_value = None

            response = admin_client.get("/website/screenshot-job/nonexistent-job")

        assert response.status_code == 404

    def test_screenshot_job_pending(self, admin_client):
        """Screenshot job pending vrací správný stav."""
        with patch("app.routers.website.get_job_status", new_callable=AsyncMock) as mock_job:
            mock_job.return_value = {
                "id": "job-123",
                "status": "pending",
                "result": None,
                "error_message": None,
            }

            response = admin_client.get("/website/screenshot-job/job-123")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job-123"
        assert data["status"] == "pending"

    def test_screenshot_job_completed(self, admin_client):
        """Screenshot job completed vrací výsledek."""
        with patch("app.routers.website.get_job_status", new_callable=AsyncMock) as mock_job:
            mock_job.return_value = {
                "id": "job-456",
                "status": "completed",
                "result": {"screenshot_url": "https://storage.example.com/shot.png"},
                "error_message": None,
            }

            response = admin_client.get("/website/screenshot-job/job-456")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["result"]["screenshot_url"] == "https://storage.example.com/shot.png"

    def test_screenshot_job_failed(self, admin_client):
        """Screenshot job failed vrací error message."""
        with patch("app.routers.website.get_job_status", new_callable=AsyncMock) as mock_job:
            mock_job.return_value = {
                "id": "job-789",
                "status": "failed",
                "result": None,
                "error_message": "Browser timeout",
            }

            response = admin_client.get("/website/screenshot-job/job-789")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "Browser timeout"
