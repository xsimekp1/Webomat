"""
PDF invoice generation service.

Uses WeasyPrint + Jinja2 for HTML to PDF conversion.
Supports QR payment codes (SPAYD format) for Czech banks.
"""
import os
import base64
import logging
from io import BytesIO
from pathlib import Path
from typing import Optional
from datetime import date

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

# Template directory
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


def get_jinja_env() -> Environment:
    """Get Jinja2 environment with custom filters."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True
    )

    # Custom filter for Czech currency formatting
    def format_currency(value: float, currency: str = "CZK") -> str:
        """Format number as Czech currency."""
        if value is None:
            return "0,00"
        # Czech format: 12 500,00
        formatted = f"{value:,.2f}".replace(",", " ").replace(".", ",")
        return formatted

    def format_date_cs(value: str | date) -> str:
        """Format date as Czech format (DD.MM.YYYY)."""
        if isinstance(value, str):
            # Parse YYYY-MM-DD
            parts = value.split("-")
            if len(parts) == 3:
                return f"{parts[2]}.{parts[1]}.{parts[0]}"
            return value
        elif isinstance(value, date):
            return value.strftime("%d.%m.%Y")
        return str(value)

    env.filters["format_currency"] = format_currency
    env.filters["format_date_cs"] = format_date_cs

    return env


def generate_payment_qr(
    iban: str,
    amount: float,
    variable_symbol: str,
    message: str = "",
    currency: str = "CZK"
) -> Optional[str]:
    """
    Generate SPAYD QR code for Czech bank payments.

    Args:
        iban: IBAN of recipient account
        amount: Payment amount
        variable_symbol: Variable symbol (VS) - crucial for Czech payments
        message: Optional payment message
        currency: Currency code (default CZK)

    Returns:
        Base64 encoded PNG image or None if qrcode not available
    """
    try:
        import qrcode
        from qrcode.image.pil import PilImage
    except ImportError:
        logger.warning("qrcode library not installed. Run: pip install qrcode[pil]")
        return None

    # Clean IBAN - remove spaces
    iban_clean = iban.replace(" ", "")

    # Build SPAYD string
    # Format: SPD*1.0*ACC:IBAN*AM:amount*CC:currency*X-VS:variable_symbol*MSG:message
    spayd_parts = [
        "SPD*1.0",
        f"ACC:{iban_clean}",
        f"AM:{amount:.2f}",
        f"CC:{currency}",
        f"X-VS:{variable_symbol}"
    ]

    if message:
        # Truncate message to 60 chars (SPAYD limit)
        msg_clean = message[:60].replace("*", "")
        spayd_parts.append(f"MSG:{msg_clean}")

    spayd_string = "*".join(spayd_parts)

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(spayd_string)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        logger.error(f"QR code generation failed: {e}")
        return None


def render_invoice_pdf(
    template_name: str,
    invoice: dict,
    business: dict,
    platform: dict,
    project: Optional[dict] = None,
    seller: Optional[dict] = None,
    qr_code_base64: Optional[str] = None
) -> bytes:
    """
    Render invoice HTML template to PDF.

    Args:
        template_name: Template filename (e.g., 'invoices/invoice_issued.html')
        invoice: Invoice data dict
        business: Business/client data dict
        platform: Platform billing info dict
        project: Optional project data dict
        seller: Optional seller data dict
        qr_code_base64: Optional base64 encoded QR code image

    Returns:
        PDF file as bytes
    """
    try:
        from weasyprint import HTML, CSS
    except ImportError as e:
        logger.error(f"WeasyPrint not installed: {e}")
        raise ImportError("WeasyPrint is required for PDF generation. Run: pip install weasyprint")

    env = get_jinja_env()
    template = env.get_template(template_name)

    # Render HTML
    html_content = template.render(
        invoice=invoice,
        business=business,
        platform=platform,
        project=project,
        seller=seller,
        qr_code=qr_code_base64
    )

    # Convert to PDF
    html = HTML(string=html_content, base_url=str(TEMPLATES_DIR))
    pdf_bytes = html.write_pdf()

    return pdf_bytes


def generate_invoice_issued_pdf(
    invoice: dict,
    business: dict,
    platform_billing: dict,
    project: Optional[dict] = None
) -> bytes:
    """
    Generate PDF for issued invoice (Webomat -> Client).

    Args:
        invoice: Invoice data from database
        business: Business (client) data
        platform_billing: Platform billing info from settings
        project: Optional website project data

    Returns:
        PDF file as bytes
    """
    # Generate QR code if we have IBAN
    qr_code = None
    if platform_billing.get("iban") and invoice.get("amount_total"):
        vs = invoice.get("variable_symbol", "")
        if vs:
            qr_code = generate_payment_qr(
                iban=platform_billing["iban"],
                amount=float(invoice["amount_total"]),
                variable_symbol=vs,
                message=f"Faktura {invoice.get('invoice_number', '')}",
                currency=invoice.get("currency", "CZK")
            )

    return render_invoice_pdf(
        template_name="invoices/invoice_issued.html",
        invoice=invoice,
        business=business,
        platform=platform_billing,
        project=project,
        qr_code_base64=qr_code
    )


def generate_invoice_received_pdf(
    invoice: dict,
    seller: dict,
    platform_billing: dict
) -> bytes:
    """
    Generate PDF for received invoice (Seller -> Webomat).

    Args:
        invoice: Invoice data from database
        seller: Seller data
        platform_billing: Platform billing info

    Returns:
        PDF file as bytes
    """
    return render_invoice_pdf(
        template_name="invoices/invoice_received.html",
        invoice=invoice,
        business=platform_billing,  # Platform is the "customer" here
        platform=platform_billing,
        seller=seller,
        qr_code_base64=None  # No QR for received invoices
    )


async def upload_pdf_to_storage(
    supabase_client,
    pdf_bytes: bytes,
    storage_path: str,
    bucket: str = "webomat"
) -> Optional[str]:
    """
    Upload PDF to Supabase Storage.

    Args:
        supabase_client: Supabase client instance
        pdf_bytes: PDF file content
        storage_path: Path within bucket (e.g., 'invoices/issued/2025/2025-0001.pdf')
        bucket: Storage bucket name

    Returns:
        Public URL of uploaded file or None on failure
    """
    try:
        # Upload file
        result = supabase_client.storage.from_(bucket).upload(
            path=storage_path,
            file=pdf_bytes,
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )

        # Get public URL
        public_url = supabase_client.storage.from_(bucket).get_public_url(storage_path)

        logger.info(f"PDF uploaded to storage: {storage_path}")
        return public_url
    except Exception as e:
        logger.error(f"Failed to upload PDF to storage: {e}")
        return None
