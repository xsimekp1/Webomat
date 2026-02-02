"""
Main Streamlit application
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path to import from webomat
sys.path.append(str(Path(__file__).parent.parent))

# Page configuration
st.set_page_config(
    page_title="Webomat - Business Discovery & Website Generator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .quick-action-btn {
        background: #4CAF50;
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
    }
    .quick-action-btn:hover {
        background: #45a049;
        transform: translateY(-2px);
    }
</style>
""",
    unsafe_allow_html=True,
)


# Sidebar navigation
def sidebar_navigation():
    """Create sidebar navigation"""
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-header">🌐 Webomat</div>', unsafe_allow_html=True
        )

        # Navigation menu
        page = st.selectbox(
            "Navigation",
            [
                "Dashboard",
                "Businesses",
                "CRM",
                "Map",
                "Search",
                "Quick Generate",
                "Settings",
                "Help",
            ],
            key="page_select",
        )

        st.markdown("---")

        # Quick stats
        st.subheader("📊 Quick Stats")
        try:
            from utils.stats import get_dashboard_stats

            stats = get_dashboard_stats()

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Businesses", stats["total_businesses"])
                st.metric("Coverage", f"{stats['coverage_percentage']:.1f}%")
            with col2:
                st.metric("No Website", stats["businesses_without_website"])
                st.metric("Avg Rating", f"{stats['avg_rating']:.1f}")
        except Exception as e:
            st.error(f"Error loading stats: {e}")

        st.markdown("---")

        # Running tasks
        if "tasks" in st.session_state:
            running_tasks = [
                t for t in st.session_state.tasks.values() if t["status"] == "running"
            ]
            if running_tasks:
                st.subheader("🔄 Running Tasks")
                for task in running_tasks:
                    st.progress(task["progress"])
                    st.caption(task["message"])

    return page


# Main header
def main_header():
    """Display main header"""
    st.markdown('<h1 class="main-header">🌐 Webomat</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align: center; color: #666;">Business Discovery & Website Generator</p>',
        unsafe_allow_html=True,
    )


# Page functions
def load_page(page_name):
    """Load the selected page"""
    try:
        if page_name == "Dashboard":
            from pages.dashboard import dashboard_page

            dashboard_page()
        elif page_name == "Businesses":
            from pages.businesses import businesses_page

            businesses_page()
        elif page_name == "CRM":
            from pages.crm import crm_page

            crm_page()
        elif page_name == "Map":
            from pages.map import map_page

            map_page()
        elif page_name == "Search":
            from pages.search import search_page

            search_page()
        elif page_name == "Quick Generate":
            from pages.quick_generate import quick_generator_page

            quick_generator_page()
        elif page_name == "Settings":
            from pages.settings import settings_page

            settings_page()
        elif page_name == "Help":
            from pages.help import help_page

            help_page()
        else:
            st.error(f"Page '{page_name}' not found.")
    except ImportError as e:
        st.error(f"Error loading page '{page_name}': ImportError: {e}")
    except Exception as e:
        st.error(f"Unexpected error loading page '{page_name}': {e}")
        import traceback

        st.error(traceback.format_exc())


# Main app
def main():
    """Main application entry point"""
    # Initialize session state
    if "api_keys" not in st.session_state:
        from utils.config import get_api_keys

        st.session_state.api_keys = get_api_keys()

    # Check API keys only once and show warning
    missing_keys = []
    if not st.session_state.api_keys.get("google_maps"):
        missing_keys.append("Google Maps API Key")
    if not st.session_state.api_keys.get("openai"):
        missing_keys.append("OpenAI API Key")

    # Navigation
    main_header()
    page = sidebar_navigation()

    # Show API keys warning only once per session
    if missing_keys and not st.session_state.get("api_warning_shown", False):
        st.warning("⚠️ Missing API Keys:")
        for key in missing_keys:
            st.warning(f"• {key}")
        st.info("Please configure API keys in Settings to use all features.")
        st.session_state.api_warning_shown = True

    # Load selected page
    load_page(page)


if __name__ == "__main__":
    main()
