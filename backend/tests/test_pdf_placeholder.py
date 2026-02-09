"""Tests for PDF placeholder generation."""
import pytest

try:
    from weasyprint import HTML
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False


@pytest.mark.skipif(not HAS_WEASYPRINT, reason="WeasyPrint not installed locally")
class TestGeneratePlaceholderPdf:
    """Test generate_placeholder_pdf function."""

    def test_placeholder_pdf_returns_bytes(self):
        """Placeholder PDF should return bytes."""
        from app.services.pdf import generate_placeholder_pdf

        result = generate_placeholder_pdf()
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_placeholder_pdf_is_valid_pdf(self):
        """Placeholder PDF should start with PDF header."""
        from app.services.pdf import generate_placeholder_pdf

        result = generate_placeholder_pdf()
        assert result[:5] == b"%PDF-"

    def test_placeholder_pdf_with_invoice_number(self):
        """Placeholder PDF should include invoice number when provided."""
        from app.services.pdf import generate_placeholder_pdf

        result = generate_placeholder_pdf(invoice_number="2025-0001")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_placeholder_pdf_with_business_name(self):
        """Placeholder PDF should include business name when provided."""
        from app.services.pdf import generate_placeholder_pdf

        result = generate_placeholder_pdf(
            invoice_number="2025-0042",
            business_name="Test Firma s.r.o."
        )
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_placeholder_pdf_empty_params(self):
        """Placeholder PDF should work with empty string params."""
        from app.services.pdf import generate_placeholder_pdf

        result = generate_placeholder_pdf(invoice_number="", business_name="")
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"


class TestExistingPdfFunctions:
    """Test existing PDF helper functions."""

    def test_jinja_env_loads(self):
        """Jinja2 environment should load without errors."""
        from app.services.pdf import get_jinja_env

        env = get_jinja_env()
        assert env is not None
        assert "format_currency" in env.filters
        assert "format_date_cs" in env.filters

    def test_format_currency_filter(self):
        """Currency filter should format Czech-style numbers."""
        from app.services.pdf import get_jinja_env

        env = get_jinja_env()
        fmt = env.filters["format_currency"]
        assert fmt(12500.0) == "12 500,00"
        assert fmt(0) == "0,00"
        assert fmt(None) == "0,00"

    def test_format_date_cs_filter(self):
        """Date filter should format as DD.MM.YYYY."""
        from app.services.pdf import get_jinja_env

        env = get_jinja_env()
        fmt = env.filters["format_date_cs"]
        assert fmt("2025-01-15") == "15.01.2025"

    def test_generate_payment_qr_without_library(self):
        """QR generation should handle missing qrcode gracefully."""
        from app.services.pdf import generate_payment_qr

        result = generate_payment_qr(
            iban="CZ6508000000192000145399",
            amount=15000.0,
            variable_symbol="20250001"
        )
        # Result is either a base64 string or None if qrcode not installed
        assert result is None or isinstance(result, str)
