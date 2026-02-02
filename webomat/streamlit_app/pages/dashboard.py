"""
Dashboard page for Streamlit app
"""

import streamlit as st
from utils.stats import get_dashboard_stats, get_business_dataframe
from components.ui_components import (
    stat_card,
    website_status_chart,
    coverage_progress_chart,
    rating_histogram,
    task_status_display,
    crm_stats_cards,
    crm_today_calls,
)
from utils.tasks import task_manager


def dashboard_page():
    """Dashboard page with statistics and quick actions"""
    st.header("📊 Dashboard")

    # Handle navigation from buttons using st.switch_page
    if st.session_state.get("nav_to_businesses"):
        del st.session_state["nav_to_businesses"]
        st.switch_page("pages/businesses.py")
    elif st.session_state.get("nav_to_map"):
        del st.session_state["nav_to_map"]
        st.switch_page("pages/map.py")
    elif st.session_state.get("nav_to_search"):
        del st.session_state["nav_to_search"]
        st.switch_page("pages/search.py")
    elif st.session_state.get("nav_to_settings"):
        del st.session_state["nav_to_settings"]
        st.switch_page("pages/settings.py")

    # Get statistics
    try:
        stats = get_dashboard_stats()

        # Top statistics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            stat_card("Total Businesses", stats["total_businesses"])

        with col2:
            website_percentage = (
                (stats["businesses_with_website"] / stats["total_businesses"] * 100)
                if stats["total_businesses"] > 0
                else 0
            )
            stat_card(
                "Have Website",
                f"{stats['businesses_with_website']} ({website_percentage:.1f}%)",
            )

        with col3:
            stat_card("No Website", stats["businesses_without_website"], color="orange")

        with col4:
            stat_card("Avg Rating", f"{stats['avg_rating']:.1f}/5.0", color="green")

        st.markdown("---")

        # Charts section
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Website Status")
            website_chart = website_status_chart(stats)
            if website_chart:
                st.plotly_chart(website_chart, width="stretch")
            else:
                st.info("No data available for website status chart.")

        with col2:
            st.subheader("🗺️ Grid Coverage")
            coverage_chart = coverage_progress_chart(stats["coverage_percentage"])
            if coverage_chart:
                st.plotly_chart(coverage_chart, width="stretch")
            else:
                st.info("No data available for coverage chart.")

        st.markdown("---")

        # Rating distribution
        try:
            from utils.database import db

            all_businesses = db.get_all_businesses()
            if all_businesses:
                st.subheader("⭐ Rating Distribution")
                rating_chart = rating_histogram(all_businesses)
                if rating_chart:
                    st.plotly_chart(rating_chart, width="stretch")
        except Exception as e:
            st.error(f"Error creating rating chart: {e}")

        st.markdown("---")

        # CRM Section
        st.header("📞 CRM - Správa hovorů")

        try:
            from utils.database import db

            # CRM statistiky
            crm_stats_cards(db)

            st.markdown("---")

            # Dnešní hovory
            crm_today_calls(db)

        except Exception as e:
            st.error(f"Chyba při načítání CRM dat: {e}")
            st.code(f"Debug info: {str(e)}")
            import traceback

            st.code(traceback.format_exc())

        st.markdown("---")

        # Quick Actions
        st.subheader("🚀 Quick Actions")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📋 Show All Businesses", use_container_width=True):
                st.session_state["nav_to_businesses"] = True
                st.rerun()

        with col2:
            if st.button("🗺️ Show Map", use_container_width=True):
                st.session_state["nav_to_map"] = True
                st.rerun()

        with col3:
            if st.button("🔍 Start Search", use_container_width=True):
                st.session_state["nav_to_search"] = True
                st.rerun()

        with col4:
            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state["nav_to_settings"] = True
                st.rerun()

        st.markdown("---")

        # Running Tasks
        running_tasks = task_manager.get_running_tasks()
        if running_tasks:
            st.subheader("🔄 Running Tasks")
            for task in running_tasks:
                task_status_display(task)

        # Recent Activity
        st.subheader("📋 Recent Activity")

        try:
            from utils.database import db

            recent_businesses = db.get_all_businesses()[:5]  # Get 5 most recent

            if recent_businesses:
                recent_df = get_business_dataframe(recent_businesses)
                if "ID" in recent_df.columns and "Name" in recent_df.columns:
                    display_df = recent_df[["ID", "Name", "Rating", "Has Website"]]
                    st.dataframe(display_df, use_container_width=True)
                else:
                    st.info("Recent businesses data format issue.")
            else:
                st.info("No businesses found in database.")
        except Exception as e:
            st.error(f"Error loading recent activity: {e}")

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        st.exception(e)
