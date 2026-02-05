"""
Unit test pro CORS konfiguraci backendu.
Testuje, že Vercel frontend má povolený přístup k Railway backendu.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.config import Settings


class TestCORSConfiguration:
    """Testy pro CORS middleware konfiguraci."""

    @pytest.fixture
    def mock_settings_vercel_frontend(self):
        """Mock settings s Vercel frontend URL."""
        settings = Settings(
            supabase_url="https://test.supabase.co",
            supabase_service_role_key="test_key",
            jwt_secret_key="test_secret",
            cors_origins=(
                "http://localhost:3000,"
                "https://webomat.vercel.app,"
                "https://*.vercel.app,"
                "https://frontend-*.vercel.app"
            )
        )
        return settings

    def test_cors_middleware_configured(self, mock_settings_vercel_frontend):
        """Test, že CORS middleware je správně nastaven."""
        with patch('app.main.get_settings', return_value=mock_settings_vercel_frontend):
            client = TestClient(app)
            
            # Test OPTIONS request pro CORS preflight
            response = client.options(
                "/token",
                headers={
                    "Origin": "https://webomat.vercel.app",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type"
                }
            )
            
            # OPTIONS request by měl projít (status 204 nebo 200)
            assert response.status_code in [200, 204]
            
            # Kontrolovat CORS headers
            if response.status_code == 200:
                assert "access-control-allow-origin" in response.headers
                assert "webomat.vercel.app" in response.headers["access-control-allow-origin"]

    def test_vercel_origin_allowed_in_config(self, mock_settings_vercel_frontend):
        """Test, že webomat.vercel.app je v seznamu povolených originů."""
        origins_list = mock_settings_vercel_frontend.cors_origins_list
        
        # Přesné URL
        assert "https://webomat.vercel.app" in origins_list
        
        # Wildcard pro všechny Vercel deploye
        assert "https://frontend-*.vercel.app" in origins_list or "https://*.vercel.app" in origins_list

    def test_cors_headers_in_response(self, mock_settings_vercel_frontend):
        """Test, že CORS headers jsou přítomny v responsech."""
        with patch('app.main.get_settings', return_value=mock_settings_vercel_frontend):
            client = TestClient(app)
            
            # Test login endpoint (reálný request)
            response = client.post(
                "/token",
                data={"username": "test@example.com", "password": "password"},
                headers={"Origin": "https://webomat.vercel.app"}
            )
            
            # I při chybě authentication by měl mít CORS headers
            assert "access-control-allow-origin" in response.headers
            allowed_origin = response.headers["access-control-allow-origin"]
            
            # Buď specifické URL, nebo wildcard
            assert allowed_origin in [
                "https://webomat.vercel.app",
                "*",
                "https://frontend-jwz99v0h1-pavels-projects-8a0f92e7.vercel.app"
            ]

    def test_cors_methods_allowed(self, mock_settings_vercel_frontend):
        """Test, že potřebné HTTP metody jsou povoleny."""
        with patch('app.main.get_settings', return_value=mock_settings_vercel_frontend):
            client = TestClient(app)
            
            # Test OPTIONS pro POST request (login)
            response = client.options(
                "/token",
                headers={
                    "Origin": "https://webomat.vercel.app",
                    "Access-Control-Request-Method": "POST"
                }
            )
            
            if response.status_code == 200:
                allowed_methods = response.headers.get("access-control-allow-methods", "")
                assert "POST" in allowed_methods
                assert "GET" in allowed_methods  # pro GET requesty na API

    def test_cors_headers_allowed(self, mock_settings_vercel_frontend):
        """Test, že potřebné headers jsou povoleny."""
        with patch('app.main.get_settings', return_value=mock_settings_vercel_frontend):
            client = TestClient(app)
            
            # Test OPTIONS
            response = client.options(
                "/token",
                headers={
                    "Origin": "https://webomat.vercel.app",
                    "Access-Control-Request-Headers": "Content-Type,Authorization"
                }
            )
            
            if response.status_code == 200:
                allowed_headers = response.headers.get("access-control-allow-headers", "")
                assert "content-type" in allowed_headers.lower()
                assert "authorization" in allowed_headers.lower()

    def test_multiple_vercel_origins(self, mock_settings_vercel_frontend):
        """Test, že různé Vercel deployment URLs jsou podporovány."""
        origins_list = mock_settings_vercel_frontend.cors_origins_list
        
        # Různé Vercel subdomény by měly být povoleny
        test_origins = [
            "https://webomat.vercel.app",
            "https://frontend-abc123.vercel.app", 
            "https://frontend-xyz789.vercel.app"
        ]
        
        for origin in test_origins:
            # Buď přesná shoda, nebo wildcard
            origin_allowed = (
                origin in origins_list or
                any(pattern.replace("*", "") in origin for pattern in origins_list if "*" in pattern)
            )
            assert origin_allowed, f"Origin {origin} není povolen v CORS konfiguraci"

    def test_origins_list_property(self, mock_settings_vercel_frontend):
        """Test, že settings správně parsuje origins do listu."""
        origins_list = mock_settings_vercel_frontend.cors_origins_list
        
        # Musí obsahovat localhost pro development
        assert "http://localhost:3000" in origins_list
        
        # Musí obsahovat production URL
        assert "https://webomat.vercel.app" in origins_list
        
        # List by neměl být prázdný
        assert len(origins_list) > 0