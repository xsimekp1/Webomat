"""
LLM služba pro překlady a generování obsahu.

Podporuje OpenAI API (GPT-4, GPT-3.5) pro překlady textů.
Připraveno na rozšíření o Claude API.
"""
import os
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Lazy import - OpenAI se načte jen když je potřeba
_openai_client = None


def get_openai_client():
    """Lazy initialization OpenAI klienta."""
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            from openai import OpenAI
            _openai_client = OpenAI(api_key=api_key)
        except ImportError:
            logger.warning("OpenAI library not installed. Run: pip install openai")
            return None
    return _openai_client


def is_llm_available() -> bool:
    """Zkontroluje, zda je LLM služba dostupná (má API klíč)."""
    return os.getenv("OPENAI_API_KEY") is not None


async def translate_text(
    text: str,
    source_lang: str = "cs",
    target_lang: str = "en",
    context: Optional[str] = None
) -> Optional[str]:
    """
    Přeloží text pomocí LLM.

    Args:
        text: Text k překladu
        source_lang: Zdrojový jazyk (default: cs = čeština)
        target_lang: Cílový jazyk (default: en = angličtina)
        context: Volitelný kontext pro lepší překlad (např. "website for restaurant")

    Returns:
        Přeložený text nebo None při chybě
    """
    client = get_openai_client()
    if not client:
        logger.warning("OpenAI client not available - translation skipped")
        return None

    system_prompt = f"""You are a professional translator. Translate the following text from {source_lang} to {target_lang}.
Keep the same tone and style. If there are HTML tags, preserve them exactly.
{f'Context: {context}' if context else ''}
Only return the translated text, nothing else."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Levnější model pro překlady
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3,  # Nižší teplota pro konzistentní překlady
            max_tokens=4000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return None


async def translate_html_content(
    html: str,
    source_lang: str = "cs",
    target_lang: str = "en",
    business_type: Optional[str] = None
) -> Optional[str]:
    """
    Přeloží obsah HTML stránky, zachová strukturu a tagy.

    Args:
        html: HTML dokument k překladu
        source_lang: Zdrojový jazyk
        target_lang: Cílový jazyk
        business_type: Typ podnikání pro lepší kontext

    Returns:
        Přeložené HTML nebo None při chybě
    """
    client = get_openai_client()
    if not client:
        logger.warning("OpenAI client not available - HTML translation skipped")
        return None

    context = f"This is a website for a {business_type}." if business_type else "This is a business website."

    system_prompt = f"""You are a professional translator specializing in website localization.
Translate the text content of this HTML from Czech to English.

IMPORTANT RULES:
1. Keep ALL HTML tags, attributes, and structure EXACTLY as they are
2. Only translate the visible text content between tags
3. Keep brand names, company names, and proper nouns as-is unless they have standard English versions
4. Translate meta titles and descriptions appropriately
5. Keep CSS, JavaScript, and code comments unchanged
6. {context}

Return the complete HTML with translated text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": html}
            ],
            temperature=0.2,
            max_tokens=8000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"HTML translation error: {e}")
        return None


def extract_translatable_strings(html: str) -> list[str]:
    """
    Extrahuje přeložitelné řetězce z HTML.
    Užitečné pro ruční překlad klientem.
    """
    # Jednoduchá extrakce textů mezi tagy (bez atributů)
    text_pattern = r'>([^<]+)<'
    matches = re.findall(text_pattern, html)

    # Filtruj prázdné a whitespace-only
    texts = [t.strip() for t in matches if t.strip() and len(t.strip()) > 2]

    # Deduplikuj
    return list(dict.fromkeys(texts))


class TranslationResult:
    """Výsledek překladu."""
    def __init__(
        self,
        success: bool,
        translated_content: Optional[str] = None,
        error: Optional[str] = None,
        strings_for_client: Optional[list[str]] = None
    ):
        self.success = success
        self.translated_content = translated_content
        self.error = error
        self.strings_for_client = strings_for_client  # Pro mode="client"


async def process_translation_request(
    html_content: str,
    mode: str,  # "no", "auto", "client"
    business_type: Optional[str] = None
) -> TranslationResult:
    """
    Zpracuje požadavek na překlad podle zvoleného režimu.

    Args:
        html_content: HTML k překladu
        mode: Režim překladu (no/auto/client)
        business_type: Typ podnikání pro kontext

    Returns:
        TranslationResult s výsledkem
    """
    if mode == "no":
        return TranslationResult(success=True)

    if mode == "client":
        # Extrahuj texty pro klienta
        strings = extract_translatable_strings(html_content)
        return TranslationResult(
            success=True,
            strings_for_client=strings
        )

    if mode == "auto":
        if not is_llm_available():
            return TranslationResult(
                success=False,
                error="Překladová služba není dostupná (chybí API klíč)"
            )

        translated = await translate_html_content(
            html_content,
            source_lang="cs",
            target_lang="en",
            business_type=business_type
        )

        if translated:
            return TranslationResult(
                success=True,
                translated_content=translated
            )
        else:
            return TranslationResult(
                success=False,
                error="Překlad selhal"
            )

    return TranslationResult(success=False, error=f"Neznámý režim: {mode}")
