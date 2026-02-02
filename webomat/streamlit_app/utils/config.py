"""
Config utilities for Streamlit app
"""

import streamlit as st
from pathlib import Path
import os


def get_api_keys():
    """Get API keys from secrets or environment variables"""
    api_keys = {}

    # Try to get from Streamlit secrets first
    try:
        if hasattr(st, "secrets"):
            api_keys["google_maps"] = st.secrets.get("GOOGLE_MAPS_API_KEY", "")
            api_keys["openai"] = st.secrets.get("OPENAI_API_KEY", "")
    except:
        # If secrets fail, continue with empty values
        api_keys["google_maps"] = ""
        api_keys["openai"] = ""

    # Fallback to environment variables (support both naming conventions)
    if not api_keys["google_maps"]:
        api_keys["google_maps"] = os.getenv("GOOGLE_MAPS_API_KEY", "") or os.getenv(
            "GOOGLE_PLACES_API_KEY", ""
        )

    if not api_keys["openai"]:
        api_keys["openai"] = os.getenv("OPENAI_API_KEY", "")

    return api_keys


def validate_api_keys(api_keys):
    """Check if required API keys are configured"""
    missing = []
    if not api_keys.get("google_maps"):
        missing.append("Google Maps API Key")
    if not api_keys.get("openai"):
        missing.append("OpenAI API Key")

    return missing


def get_business_data_dir():
    """Get business data directory path"""
    return Path(__file__).parent.parent / "businesses_data"
