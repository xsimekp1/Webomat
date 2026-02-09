"""Tests for Playwright/screenshot availability.

These tests verify the Playwright package is importable.
On local dev machines without Playwright installed, tests are skipped.
On Railway (Docker), Playwright + Chromium should be available.
"""
import pytest

try:
    import playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


@pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright not installed locally")
class TestPlaywrightAvailability:
    """Test that Playwright is installed and importable."""

    def test_playwright_importable(self):
        """Playwright package should be importable."""
        import playwright
        assert playwright is not None

    def test_playwright_sync_api_importable(self):
        """Playwright sync API should be importable."""
        from playwright.sync_api import sync_playwright
        assert sync_playwright is not None

    def test_playwright_async_api_importable(self):
        """Playwright async API should be importable."""
        from playwright.async_api import async_playwright
        assert async_playwright is not None
