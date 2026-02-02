"""
Businesses page for Streamlit app
"""

import streamlit as st
import pandas as pd
import os
from utils.stats import (
    get_business_dataframe,
    get_facebook_businesses,
    get_high_rated_businesses,
)
from components.ui_components import business_table, filter_controls, apply_filters
from utils.tasks import task_manager


def businesses_page():
    """Businesses page with filterable table and actions"""
    st.header("📋 Businesses")

    try:
        from utils.database import db

        all_businesses = db.get_all_businesses()

        if not all_businesses:
            st.warning("No businesses found in database.")
            st.info(
                "Use the Search or Map pages to find and add businesses to the database."
            )
            return

        # Filters
        website_filter, rating_range, review_range, search_term = filter_controls(
            all_businesses
        )

        # Apply filters
        filtered_businesses = apply_filters(
            all_businesses, website_filter, rating_range, review_range, search_term
        )

        # Filter summary
        st.info(
            f"Showing {len(filtered_businesses)} of {len(all_businesses)} businesses"
        )

        # Business table
        if filtered_businesses:
            business_df = get_business_dataframe(filtered_businesses)
            business_table(business_df, height=400)

            # Business details section
            st.subheader("🔍 Business Details")

            if business_df is not None and not business_df.empty:
                selected_business_id = st.selectbox(
                    "Select a business to view details",
                    options=business_df["ID"].tolist()
                    if "ID" in business_df.columns
                    else [],
                    format_func=lambda x: f"ID {x}",
                )

                if selected_business_id:
                    selected_business = next(
                        (
                            b
                            for b in filtered_businesses
                            if b.get("id") == selected_business_id
                        ),
                        None,
                    )

                    if selected_business:
                        display_business_details(selected_business)

                        # CRM sekce
                        st.markdown("---")
                        current_user = st.session_state.get("current_user")
                        crm_call_scheduler(selected_business, db, current_user)
                        st.markdown("---")
                        crm_notes_editor(selected_business, db)
        else:
            st.info("No businesses match the selected filters.")

        st.markdown("---")

        # Bulk Actions
        st.subheader("🛠️ Bulk Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🌐 Generate Websites (No Website)", use_container_width=True):
                businesses_without_website = [
                    b for b in filtered_businesses if not b.get("has_website", False)
                ]

                if businesses_without_website:
                    st.info(
                        f"Found {len(businesses_without_website)} businesses without websites."
                    )
                    # Would integrate with website generation task
                else:
                    st.warning("No businesses without websites in current filter.")

        with col2:
            if st.button("📥 Export Filtered Data", use_container_width=True):
                if filtered_businesses:
                    export_df = get_business_dataframe(filtered_businesses)
                    csv = export_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="businesses_export.csv",
                        mime="text/csv",
                    )
                else:
                    st.warning("No data to export.")

        with col3:
            if st.button("📊 Generate Report", use_container_width=True):
                generate_business_report(filtered_businesses)

        st.markdown("---")

        # Special Lists
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📘 Facebook Businesses")
            facebook_businesses = get_facebook_businesses()
            if facebook_businesses:
                st.info(
                    f"Found {len(facebook_businesses)} businesses with Facebook pages."
                )

                # Show first 5
                facebook_df = get_business_dataframe(facebook_businesses[:5])
                if facebook_df is not None and not facebook_df.empty:
                    business_table(facebook_df, height=200)
            else:
                st.info("No Facebook businesses found.")

        with col2:
            st.subheader("⭐ High Rated Businesses (4.5+)")
            high_rated = get_high_rated_businesses(4.5)
            if high_rated:
                st.info(f"Found {len(high_rated)} high-rated businesses.")

                # Show first 5
                high_rated_df = get_business_dataframe(high_rated[:5])
                if high_rated_df is not None and not high_rated_df.empty:
                    business_table(high_rated_df, height=200)
            else:
                st.info("No high-rated businesses found.")

    except Exception as e:
        st.error(f"Error loading businesses: {e}")
        st.exception(e)


def display_business_details(business):
    """Display detailed information about a selected business"""
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"📍 {business.get('name', 'Unknown Business')}")

        # Basic info
        st.write("**Address:**", business.get("address", "N/A"))
        st.write("**Phone:**", business.get("phone", "N/A"))
        st.write("**Website:**", business.get("website", "N/A"))
        st.write(
            "**Has Website:**", "✅ Yes" if business.get("has_website") else "❌ No"
        )

        # Doména - editovatelné
        current_domain = business.get("domain_name", "")
        new_domain = st.text_input(
            "Název domény",
            value=current_domain,
            key=f"domain_{business.get('id')}",
            placeholder="www.firma.cz nebo firma.cz",
        )

        if new_domain != current_domain:
            if st.button("💾 Uložit doménu", key=f"save_domain_{business.get('id')}"):
                try:
                    import sqlite3
                    from utils.database import db

                    with sqlite3.connect(db.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE businesses SET domain_name = ? WHERE id = ?",
                            (new_domain, business.get("id")),
                        )
                        conn.commit()
                    st.success(f"Doména uložena: {new_domain}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Chyba při ukládání domény: {e}")

        if business.get("facebook_id"):
            st.write("**Facebook ID:**", business.get("facebook_id"))

        # Rating and reviews
        col1a, col2a = st.columns(2)
        with col1a:
            st.metric("Rating", f"{business.get('rating', 0):.1f}/5.0")
        with col2a:
            st.metric("Reviews", business.get("review_count", 0))

        # Reviews preview
        reviews = business.get("reviews", [])
        if reviews:
            st.write("**Recent Reviews:**")
            for review in reviews[:3]:
                st.write(
                    f"• {review.get('author_name', 'Anonymous')}: {review.get('text', '')[:100]}..."
                )

    with col2:
        # Actions
        st.subheader("🛠️ Actions")

        if st.button("🌐 Generate Website", use_container_width=True):
            # Trigger website generation
            task_manager.add_task(
                "Generate Website",
                generate_website_for_business,
                business.get("place_id"),
            )
            st.success("Website generation started!")

        if st.button("📍 Show on Map", use_container_width=True):
            # Store selected business for map display
            st.session_state.selected_map_business = business
            st.session_state.current_page = "Map"
            st.rerun()

        if business.get("facebook_id") and not business.get("has_website"):
            if st.button("📸 Download Facebook Photo", use_container_width=True):
                task_manager.add_task(
                    "Download Facebook Photo",
                    download_facebook_photo_task,
                    business.get("facebook_id"),
                    business.get("place_id"),
                )
                st.success("Facebook photo download started!")


def generate_website_for_business(place_id, progress_callback=None):
    """Generate website for a business"""
    try:
        from webomat import Webomat

        webomat = Webomat()

        if progress_callback:
            progress_callback(0, "Initializing website generation...")

        # Generate website (simplified version)
        if progress_callback:
            progress_callback(50, "Creating website content...")

        # Actual website generation logic would go here
        # For now, simulate
        import time

        time.sleep(1)

        if progress_callback:
            progress_callback(100, "Website generation completed!")

        return True
    except Exception as e:
        return {"error": str(e)}


def download_facebook_photo_task(facebook_id, place_id, progress_callback=None):
    """Download Facebook photo for a business"""
    try:
        from webomat import Webomat

        webomat = Webomat()

        if progress_callback:
            progress_callback(0, "Starting photo download...")

        success = webomat.download_facebook_photo(
            facebook_id, f"businesses_data/{place_id}/facebook_photo.jpg"
        )

        if success:
            if progress_callback:
                progress_callback(100, "Photo downloaded successfully!")
            return True
        else:
            if progress_callback:
                progress_callback(0, "Photo download failed")
            return False
    except Exception as e:
        return {"error": str(e)}


def generate_business_report(businesses):
    """Generate a report for the filtered businesses"""
    if not businesses:
        st.warning("No businesses to report on.")
        return

    # Calculate statistics
    total = len(businesses)
    with_website = sum(1 for b in businesses if b.get("has_website", False))
    without_website = total - with_website
    avg_rating = sum(b.get("rating", 0) for b in businesses) / total if total > 0 else 0

    # Display report
    st.info(f"**Report Summary:**")
    st.write(f"• Total businesses: {total}")
    st.write(f"• With websites: {with_website} ({with_website / total * 100:.1f}%)")
    st.write(
        f"• Without websites: {without_website} ({without_website / total * 100:.1f}%)"
    )
    st.write(f"• Average rating: {avg_rating:.1f}/5.0")

    # Top rated businesses
    top_rated = sorted(businesses, key=lambda x: x.get("rating", 0), reverse=True)[:5]
    if top_rated:
        st.write("**Top 5 Rated Businesses:**")
        for i, business in enumerate(top_rated, 1):
            st.write(
                f"{i}. {business.get('name', 'Unknown')} - {business.get('rating', 0):.1f}"
            )
