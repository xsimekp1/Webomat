"""
Settings page for Streamlit app
"""

import streamlit as st
from utils.config import get_api_keys, validate_api_keys
from utils.database import db, grid_manager
from utils.tasks import task_manager


def settings_page():
    """Settings page for API configuration and database management"""
    st.header("⚙️ Settings")

    # Tab navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Profile", "API Keys", "Database", "System", "About"]
    )

    with tab1:
        profile_settings()

    with tab2:
        api_keys_settings()

    with tab3:
        database_settings()

    with tab4:
        system_settings()

    with tab5:
        about_settings()


def profile_settings():
    """User profile settings"""
    st.subheader("👤 Profile Settings")

    # Profile photo upload
    st.write("**Profile Photo**")
    uploaded_file = st.file_uploader(
        "Upload profile photo", type=["jpg", "jpeg", "png"]
    )
    if uploaded_file is not None:
        # Save to storage (placeholder)
        st.success("Profile photo uploaded! (Storage implementation needed)")
        st.image(uploaded_file, width=100)

    # Theme toggle
    st.write("**Theme**")
    theme = st.radio("Choose theme", ["Light", "Dark"], index=0)
    if st.button("Apply Theme"):
        st.success(f"Theme set to {theme} (CSS implementation needed)")

    # Other profile fields (placeholder)
    st.write("**Personal Information**")
    name = st.text_input("Full Name")
    email = st.text_input("Email")

    if st.button("Save Profile"):
        st.success("Profile saved!")


def api_keys_settings():
    """API keys configuration"""
    st.subheader("🔑 API Keys")

    # Current API keys
    current_keys = get_api_keys()
    missing_keys = validate_api_keys(current_keys)

    if missing_keys:
        st.warning("⚠️ Missing API Keys:")
        for key in missing_keys:
            st.warning(f"• {key}")

    # API key input forms
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Google Maps API Key**")
        google_key = st.text_input(
            "Google Maps API Key",
            value=current_keys.get("google_maps", ""),
            type="password",
            help="Used for location services and business search",
        )

        if st.button("💾 Save Google Maps Key", use_container_width=True):
            if google_key:
                save_api_key("google_maps", google_key)
                st.success("Google Maps API key saved!")
                st.rerun()

    with col2:
        st.write("**OpenAI API Key**")
        openai_key = st.text_input(
            "OpenAI API Key",
            value=current_keys.get("openai", ""),
            type="password",
            help="Used for website content generation",
        )

        if st.button("💾 Save OpenAI Key", use_container_width=True):
            if openai_key:
                save_api_key("openai", openai_key)
                st.success("OpenAI API key saved!")
                st.rerun()

    # API key status
    st.markdown("---")
    st.subheader("📊 API Key Status")

    status_col1, status_col2 = st.columns(2)

    with status_col1:
        google_status = (
            "✅ Configured" if current_keys.get("google_maps") else "❌ Not Set"
        )
        st.metric("Google Maps", google_status)

    with status_col2:
        openai_status = "✅ Configured" if current_keys.get("openai") else "❌ Not Set"
        st.metric("OpenAI", openai_status)

    # Test API connections
    st.markdown("---")
    st.subheader("🧪 Test API Connections")

    test_col1, test_col2 = st.columns(2)

    with test_col1:
        if st.button("🗺️ Test Google Maps", use_container_width=True):
            test_google_maps_api()

    with test_col2:
        if st.button("🤖 Test OpenAI", use_container_width=True):
            test_openai_api()


def database_settings():
    """Database management settings"""
    st.subheader("🗄️ Database Management")

    # Database statistics
    try:
        db_stats = get_database_statistics()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Businesses", db_stats["total_businesses"])
            st.metric("Grid Cells", db_stats["total_cells"])

        with col2:
            st.metric("With Website", db_stats["businesses_with_website"])
            st.metric("Coverage", f"{db_stats['coverage_percentage']:.1f}%")

        with col3:
            st.metric("No Website", db_stats["businesses_without_website"])
            st.metric("Database Size", f"{db_stats['db_size_mb']:.1f} MB")

    except Exception as e:
        st.error(f"Error loading database statistics: {e}")

    # Database operations
    st.markdown("---")
    st.subheader("🛠️ Database Operations")

    op_col1, op_col2, op_col3 = st.columns(3)

    with op_col1:
        if st.button("🔄 Run Migration", use_container_width=True):
            if st.button("Confirm Migration", key="confirm_migration"):
                run_database_migration()

    with op_col2:
        if st.button("📊 Analyze Data", use_container_width=True):
            run_data_analysis()

    with op_col3:
        if st.button("📥 Export Database", use_container_width=True):
            export_database()

    # Grid management
    st.markdown("---")
    st.subheader("🗺️ Grid Management")

    grid_col1, grid_col2 = st.columns(2)

    with grid_col1:
        if st.button("🔧 Initialize Grid", use_container_width=True):
            if st.button("Confirm Initialize", key="confirm_init_grid"):
                initialize_grid()

    with grid_col2:
        if st.button("🗑️ Reset Grid", use_container_width=True):
            if st.button("Confirm Reset", key="confirm_reset_grid"):
                reset_grid()

    # Cleanup options
    st.markdown("---")
    st.subheader("🧹 Cleanup Operations")

    cleanup_col1, cleanup_col2 = st.columns(2)

    with cleanup_col1:
        cleanup_hours = st.slider(
            "Clean up tasks older than (hours)", min_value=1, max_value=24, value=1
        )

        if st.button("🧹 Clean Up Tasks", use_container_width=True):
            task_manager.cleanup_old_tasks(cleanup_hours)
            st.success(f"Cleaned up tasks older than {cleanup_hours} hours")
            st.rerun()

    with cleanup_col2:
        if st.button("🗑️ Clear Cache", use_container_width=True):
            clear_streamlit_cache()
            st.success("Streamlit cache cleared!")


def system_settings():
    """System configuration settings"""
    st.subheader("⚙️ System Settings")

    # Performance settings
    st.write("**Performance**")

    perf_col1, perf_col2 = st.columns(2)

    with perf_col1:
        max_workers = st.slider(
            "Max Concurrent Operations",
            min_value=1,
            max_value=10,
            value=3,
            help="Maximum number of concurrent search/generation tasks",
        )

        cache_timeout = st.slider(
            "Cache Timeout (minutes)",
            min_value=5,
            max_value=60,
            value=30,
            help="How long to cache search results",
        )

    with perf_col2:
        retry_attempts = st.slider(
            "API Retry Attempts",
            min_value=1,
            max_value=5,
            value=3,
            help="Number of retry attempts for failed API calls",
        )

        rate_limit_delay = st.slider(
            "Rate Limit Delay (seconds)",
            min_value=0,
            max_value=5,
            value=1,
            help="Delay between API calls to avoid rate limiting",
        )

    # Display settings
    st.markdown("---")
    st.write("**Display**")

    display_col1, display_col2 = st.columns(2)

    with display_col1:
        default_map_style = st.selectbox(
            "Default Map Style",
            ["OpenStreetMap", "Satellite", "Terrain"],
            help="Default map style for coverage visualization",
        )

        business_table_rows = st.slider(
            "Business Table Rows per Page",
            min_value=10,
            max_value=100,
            value=25,
            help="Number of rows to display in business tables",
        )

    with display_col2:
        theme_color = st.color_picker(
            "Theme Color",
            value="#1f77b4",
            help="Primary color for the Streamlit interface",
        )

        show_debug_info = st.checkbox(
            "Show Debug Information",
            value=False,
            help="Display additional technical details for troubleshooting",
        )

    # Save system settings
    if st.button("💾 Save System Settings", use_container_width=True):
        system_config = {
            "max_workers": max_workers,
            "cache_timeout": cache_timeout,
            "retry_attempts": retry_attempts,
            "rate_limit_delay": rate_limit_delay,
            "default_map_style": default_map_style,
            "business_table_rows": business_table_rows,
            "theme_color": theme_color,
            "show_debug_info": show_debug_info,
        }

        save_system_settings(system_config)
        st.success("System settings saved!")


def about_settings():
    """About section"""
    st.subheader("ℹ️ About Webomat")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### 🌐 Webomat - Business Discovery & Website Generator
        
        **Version:** 2.0 (Streamlit Edition)
        **Author:** Webomat Team
        
        **Features:**
        - 🗺️ Grid-based business discovery
        - 🌐 Automated website generation
        - 📊 Interactive dashboard and maps
        - 📸 Facebook integration and photo download
        - 🔍 Advanced search and filtering
        - ⚡ Quick website generator
        
        **Technologies:**
        - Backend: Python, SQLite, Google Maps API
        - Frontend: Streamlit, Folium, Plotly
        - AI: OpenAI for content generation
        """)

    with col2:
        st.image(
            "https://via.placeholder.com/150x150/1f77b4/ffffff?text=Webomat", width=150
        )

    st.markdown("---")

    # System information
    st.subheader("📋 System Information")

    try:
        import sys
        import os
        from datetime import datetime

        sys_info_col1, sys_info_col2 = st.columns(2)

        with sys_info_col1:
            st.metric("Python Version", f"{sys.version_info[0]}.{sys.version_info[1]}")
            st.metric("Platform", os.name)

        with sys_info_col2:
            st.metric("Working Directory", os.path.basename(os.getcwd()))
            st.metric("Current Time", datetime.now().strftime("%Y-%m-%d %H:%M"))

    except Exception as e:
        st.error(f"Error getting system info: {e}")


def save_api_key(key_name, key_value):
    """Save API key to session state"""
    if "api_keys" not in st.session_state:
        st.session_state.api_keys = {}

    st.session_state.api_keys[key_name] = key_value


def test_google_maps_api():
    """Test Google Maps API connection"""
    try:
        import requests

        api_key = st.session_state.api_keys.get("google_maps")

        if not api_key:
            st.error("Google Maps API key not configured")
            return

        # Simple API test
        test_url = f"https://maps.googleapis.com/maps/api/geocode/json?address=Prague&key={api_key}"
        response = requests.get(test_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "OK":
                st.success("✅ Google Maps API connection successful!")
            else:
                st.error(f"❌ Google Maps API error: {data.get('status')}")
        else:
            st.error(f"❌ Google Maps API request failed: {response.status_code}")

    except Exception as e:
        st.error(f"❌ Error testing Google Maps API: {e}")


def test_openai_api():
    """Test OpenAI API connection"""
    try:
        # Placeholder for OpenAI API test
        st.info("OpenAI API test not implemented yet")
    except Exception as e:
        st.error(f"❌ Error testing OpenAI API: {e}")


def get_database_statistics():
    """Get database statistics"""
    try:
        all_businesses = db.get_all_businesses()
        all_cells = db.get_all_grid_cells()

        businesses_with_website = sum(
            1 for b in all_businesses if b.get("has_website", False)
        )

        # Get database file size
        import os

        db_size = os.path.getsize("businesses.db") / (1024 * 1024)  # MB

        return {
            "total_businesses": len(all_businesses),
            "businesses_with_website": businesses_with_website,
            "businesses_without_website": len(all_businesses) - businesses_with_website,
            "total_cells": len(all_cells),
            "coverage_percentage": grid_manager.get_coverage_stats().get(
                "coverage_percentage", 0
            ),
            "db_size_mb": db_size,
        }

    except Exception as e:
        return {
            "total_businesses": 0,
            "businesses_with_website": 0,
            "businesses_without_website": 0,
            "total_cells": 0,
            "coverage_percentage": 0,
            "db_size_mb": 0,
        }


def run_database_migration():
    """Run database migration"""
    try:
        import sys
        from pathlib import Path

        sys.path.append(str(Path(__file__).parent.parent.parent))

        import migrate_database

        migrate_database.migrate_database("businesses.db")

        st.success("Database migration completed successfully!")

    except Exception as e:
        st.error(f"Error during migration: {e}")


def run_data_analysis():
    """Run data analysis on database"""
    task_manager.add_task("Data Analysis", data_analysis_task)


def data_analysis_task(progress_callback=None):
    """Task for comprehensive data analysis"""
    try:
        if progress_callback:
            progress_callback(20, "Loading businesses...")

        all_businesses = db.get_all_businesses()

        if progress_callback:
            progress_callback(40, "Analyzing website coverage...")

        businesses_with_website = sum(
            1 for b in all_businesses if b.get("has_website", False)
        )
        website_percentage = (
            (businesses_with_website / len(all_businesses)) * 100
            if all_businesses
            else 0
        )

        if progress_callback:
            progress_callback(60, "Analyzing ratings...")

        ratings = [b.get("rating", 0) for b in all_businesses if b.get("rating")]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0

        if progress_callback:
            progress_callback(80, "Analyzing locations...")

        # Location analysis would go here

        if progress_callback:
            progress_callback(100, "Analysis completed!")

        # Store results
        st.session_state.analysis_results = {
            "total_businesses": len(all_businesses),
            "website_percentage": website_percentage,
            "avg_rating": avg_rating,
        }

        return True

    except Exception as e:
        if progress_callback:
            progress_callback(0, f"Error: {str(e)}")
        return {"error": str(e)}


def export_database():
    """Export database to CSV"""
    try:
        all_businesses = db.get_all_businesses()

        if all_businesses:
            import pandas as pd

            df = pd.DataFrame(all_businesses)
            csv = df.to_csv(index=False)

            st.download_button(
                label="Download Database Export",
                data=csv,
                file_name="webomat_database_export.csv",
                mime="text/csv",
            )
        else:
            st.warning("No data to export")

    except Exception as e:
        st.error(f"Error exporting database: {e}")


def initialize_grid():
    """Initialize grid system"""
    try:
        if grid_manager.ensure_initialized():
            st.success("Grid system initialized successfully!")
        else:
            st.info("Grid system already initialized")

    except Exception as e:
        st.error(f"Error initializing grid: {e}")


def reset_grid():
    """Reset grid system"""
    if st.button("⚠️ Yes, Reset Grid", key="confirm_reset_grid_final"):
        try:
            db.execute_query("DELETE FROM grid_cells")
            db.execute_query("DELETE FROM grid_cell_businesses")
            st.success("Grid system reset successfully!")

        except Exception as e:
            st.error(f"Error resetting grid: {e}")


def save_system_settings(config):
    """Save system settings to session state"""
    st.session_state.system_settings = config


def clear_streamlit_cache():
    """Clear Streamlit cache"""
    try:
        st.cache_data.clear()
        st.cache_resource.clear()
    except Exception:
        pass  # Cache clearing might fail in some cases
