"""
Search page for Streamlit app
"""

import streamlit as st
import pandas as pd
from components.ui_components import business_table, task_status_display
from utils.tasks import task_manager


def search_page():
    """Search page with location input and progress tracking"""
    st.header("🔍 Business Search")

    # Search mode selection
    search_mode = st.selectbox(
        "Search Mode", ["Nearby Location", "Grid Search", "Keyword Search"]
    )

    if search_mode == "Nearby Location":
        nearby_search_mode()
    elif search_mode == "Grid Search":
        grid_search_mode()
    else:
        keyword_search_mode()


def nearby_search_mode():
    """Nearby location search mode"""
    st.subheader("📍 Search Nearby Businesses")

    # Search parameters
    col1, col2 = st.columns(2)

    with col1:
        location = st.text_input(
            "Location",
            placeholder="Enter address or coordinates",
            value="Praha, Czech Republic",
        )
        radius = st.slider(
            "Search Radius (meters)",
            min_value=100,
            max_value=5000,
            value=1000,
            step=100,
        )

    with col2:
        limit = st.number_input(
            "Number of Results", min_value=1, max_value=50, value=10, step=1
        )

        # Filter options
        filter_no_website = st.checkbox("Only show businesses without websites")
        filter_high_rated = st.checkbox("Only show high-rated businesses (4.5+)")

    # Search button
    if st.button("🔍 Search Nearby", use_container_width=True, type="primary"):
        if location:
            # Start search task
            task_manager.add_task(
                "Nearby Business Search",
                nearby_search_task,
                location,
                radius,
                limit,
                filter_no_website,
                filter_high_rated,
            )
            st.success("Search started! Check progress below.")
        else:
            st.error("Please enter a location.")

    # Display running tasks
    running_tasks = task_manager.get_running_tasks()
    search_tasks = [t for t in running_tasks if "search" in t["name"].lower()]
    if search_tasks:
        st.subheader("🔄 Running Searches")
        for task in search_tasks:
            from components.ui_components import task_status_display

            task_status_display(task)

    # Display recent search results
    display_nearby_search_results()


def grid_search_mode():
    """Grid-based search mode"""
    st.subheader("🗺️ Grid Search")

    # Grid search parameters
    col1, col2 = st.columns(2)

    with col1:
        search_type = st.selectbox(
            "Search Type", ["Random Cells", "Spiral from Center", "Area Based"]
        )

        if search_type == "Random Cells":
            cell_count = st.number_input(
                "Number of Cells to Search", min_value=1, max_value=100, value=5, step=1
            )

        elif search_type == "Spiral from Center":
            center_location = st.text_input(
                "Center Location",
                value="50.0755, 14.4378",  # Prague coordinates
            )
            max_cells = st.number_input(
                "Maximum Cells", min_value=1, max_value=50, value=10, step=1
            )

        else:  # Area Based
            area_description = st.text_area(
                "Area Description",
                placeholder="Describe the area to search (e.g., 'Prague city center, 2km radius')",
            )

    with col2:
        # Filters
        business_types = st.multiselect(
            "Business Types",
            ["restaurant", "cafe", "store", "service", "other"],
            default=["restaurant", "cafe", "store"],
        )

        min_rating = st.slider(
            "Minimum Rating", min_value=0.0, max_value=5.0, value=0.0, step=0.1
        )

    # Start grid search button
    if st.button("🗺️ Start Grid Search", use_container_width=True):
        if search_type == "Random Cells":
            task_manager.add_task(
                "Random Grid Search",
                random_grid_search_task,
                cell_count,
                business_types,
                min_rating,
            )
        elif search_type == "Spiral from Center":
            task_manager.add_task(
                "Spiral Grid Search",
                spiral_grid_search_task,
                center_location,
                max_cells,
                business_types,
                min_rating,
            )
        else:
            task_manager.add_task(
                "Area Grid Search",
                area_grid_search_task,
                area_description,
                business_types,
                min_rating,
            )

        st.success("Grid search started!")

    # Display running grid search tasks
    running_tasks = task_manager.get_running_tasks()
    grid_tasks = [t for t in running_tasks if "grid search" in t["name"].lower()]

    if grid_tasks:
        st.subheader("🔄 Running Grid Searches")
        for task in grid_tasks:
            task_status_display(task)


def keyword_search_mode():
    """Keyword-based search mode"""
    st.subheader("🔤 Keyword Search")

    # Search parameters
    keyword = st.text_input(
        "Search Keyword",
        placeholder="Enter business name, type, or keyword",
        value="restaurant",
    )

    col1, col2 = st.columns(2)

    with col1:
        search_in = st.selectbox("Search In", ["Business Names", "Addresses", "Both"])

        limit = st.number_input(
            "Result Limit", min_value=1, max_value=100, value=20, step=1
        )

    with col2:
        sort_by = st.selectbox(
            "Sort By", ["Relevance", "Rating", "Review Count", "Newest"]
        )

        order = st.selectbox("Order", ["Descending", "Ascending"])

    # Search button
    if st.button("🔤 Search Keyword", use_container_width=True, type="primary"):
        if keyword:
            task_manager.add_task(
                "Keyword Business Search",
                keyword_search_task,
                keyword,
                search_in,
                limit,
                sort_by,
                order,
            )
            st.success("Keyword search started!")
        else:
            st.error("Please enter a search keyword.")

    # Display recent keyword searches
    display_keyword_search_results()


def nearby_search_task(
    location,
    radius,
    limit,
    filter_no_website,
    filter_high_rated,
    progress_callback=None,
):
    """Task for nearby business search"""
    try:
        from webomat import Webomat

        if progress_callback:
            progress_callback(10, "Initializing search...")

        webomat = Webomat()

        if progress_callback:
            progress_callback(30, "Geocoding location...")

        # Geocode location to coordinates
        geocode_result = webomat.geocode_address(location)
        if not geocode_result:
            return {"error": "Location not found"}

        lat, lng = geocode_result

        if progress_callback:
            progress_callback(50, "Searching for nearby businesses...")

        # Search nearby places
        places = webomat.search_nearby_places(lat, lng, radius)

        if progress_callback:
            progress_callback(70, "Filtering results...")

        # Filter and process results
        filtered_places = webomat.filter_places(places)

        # Apply additional filters
        if filter_no_website:
            filtered_places = [p for p in filtered_places if not p.get("website")]

        if filter_high_rated:
            filtered_places = [p for p in filtered_places if p.get("rating", 0) >= 4.5]

        # Limit results
        filtered_places = filtered_places[:limit]

        if progress_callback:
            progress_callback(90, "Processing results...")

        # Save to database
        webomat.process_businesses(filtered_places)

        # Store results in session state
        st.session_state.nearby_search_results = [
            {
                "name": p.get("name"),
                "address": p.get("vicinity"),
                "rating": p.get("rating"),
                "website": p.get("website", ""),
                "phone": p.get("formatted_phone_number", ""),
                "has_website": bool(p.get("website")),
                "place_id": p.get("place_id"),
                "lat": p.get("geometry", {}).get("location", {}).get("lat"),
                "lng": p.get("geometry", {}).get("location", {}).get("lng"),
            }
            for p in filtered_places
        ]

        if progress_callback:
            progress_callback(100, f"Found {len(filtered_places)} businesses!")

        return len(filtered_places)

    except Exception as e:
        if progress_callback:
            progress_callback(0, f"Error: {str(e)}")
        return {"error": str(e)}


def random_grid_search_task(
    cell_count, business_types, min_rating, progress_callback=None
):
    """Task for random grid cell search"""
    try:
        from utils.database import grid_manager

        if progress_callback:
            progress_callback(10, "Getting random cells...")

        # Get random unsearched cells
        cells = grid_manager.get_random_unsearched_cells(cell_count)

        if not cells:
            return {"error": "No unsearched cells available"}

        if progress_callback:
            progress_callback(30, f"Searching {len(cells)} grid cells...")

        total_businesses = 0
        for i, cell in enumerate(cells):
            if progress_callback:
                progress_callback(
                    30 + (50 * (i + 1) / len(cells)),
                    f"Searching cell {i + 1}/{len(cells)}...",
                )

            # Search this cell (simplified)
            # In real implementation, would call webomat.search_grid_cell
            # For now, simulate
            import time

            time.sleep(0.1)
            total_businesses += 1

        if progress_callback:
            progress_callback(
                100, f"Found {total_businesses} businesses in {len(cells)} cells!"
            )

        return total_businesses

    except Exception as e:
        if progress_callback:
            progress_callback(0, f"Error: {str(e)}")
        return {"error": str(e)}


def keyword_search_task(
    keyword, search_in, limit, sort_by, order, progress_callback=None
):
    """Task for keyword business search"""
    try:
        from utils.database import db

        if progress_callback:
            progress_callback(10, "Searching database...")

        # Get all businesses from database
        all_businesses = db.get_all_businesses()

        if progress_callback:
            progress_callback(30, "Applying keyword filter...")

        # Filter by keyword
        keyword_lower = keyword.lower()
        filtered_businesses = []

        for business in all_businesses:
            if search_in in ["Business Names", "Both"]:
                name_match = keyword_lower in business.get("name", "").lower()
            else:
                name_match = False

            if search_in in ["Addresses", "Both"]:
                address_match = keyword_lower in business.get("address", "").lower()
            else:
                address_match = False

            if name_match or address_match:
                filtered_businesses.append(business)

        if progress_callback:
            progress_callback(70, "Sorting results...")

        # Sort results
        reverse = order == "Descending"

        if sort_by == "Rating":
            filtered_businesses.sort(key=lambda x: x.get("rating", 0), reverse=reverse)
        elif sort_by == "Review Count":
            filtered_businesses.sort(
                key=lambda x: x.get("review_count", 0), reverse=reverse
            )
        elif sort_by == "Newest":
            filtered_businesses.sort(
                key=lambda x: x.get("created_at", ""), reverse=reverse
            )
        # Relevance (name match priority)
        else:
            filtered_businesses.sort(
                key=lambda x: (
                    keyword_lower not in x.get("name", "").lower(),
                    x.get("name", ""),
                )
            )

        # Limit results
        filtered_businesses = filtered_businesses[:limit]

        if progress_callback:
            progress_callback(
                100, f"Found {len(filtered_businesses)} matching businesses!"
            )

        # Store results
        st.session_state.keyword_search_results = filtered_businesses

        return len(filtered_businesses)

    except Exception as e:
        if progress_callback:
            progress_callback(0, f"Error: {str(e)}")
        return {"error": str(e)}


def display_nearby_search_results():
    """Display recent nearby search results"""
    if (
        "nearby_search_results" in st.session_state
        and st.session_state.nearby_search_results
    ):
        results = st.session_state.nearby_search_results

        st.subheader(f"📍 Recent Nearby Search Results ({len(results)} businesses)")

        # Results summary
        with_website = sum(1 for b in results if b.get("has_website", False))
        without_website = len(results) - with_website

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", len(results))
        with col2:
            st.metric("With Website", with_website)
        with col3:
            st.metric("Without Website", without_website)

        # Results table
        if results:
            df = pd.DataFrame(results)

            # Select columns to display
            display_columns = ["name", "address", "rating", "has_website", "phone"]
            available_columns = [col for col in display_columns if col in df.columns]

            if available_columns:
                df_display = df[available_columns]
                df_display.columns = [
                    col.replace("_", " ").title() for col in available_columns
                ]
                business_table(df_display, height=300)

                # Action buttons
                st.subheader("🛠️ Actions")
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button(
                        "🌐 Generate Websites (No Website)", use_container_width=True
                    ):
                        no_website_businesses = [
                            b for b in results if not b.get("has_website", False)
                        ]
                        if no_website_businesses:
                            st.info(
                                f"Would generate websites for {len(no_website_businesses)} businesses."
                            )

                with col2:
                    if st.button("🗺️ Show on Map", use_container_width=True):
                        st.session_state.map_search_results = results
                        st.session_state.current_page = "Map"
                        st.rerun()

                with col3:
                    if st.button("📥 Export Results", use_container_width=True):
                        if available_columns:
                            csv = df[available_columns].to_csv(index=False)
                            st.download_button(
                                label="Download Search Results",
                                data=csv,
                                file_name="nearby_search_results.csv",
                                mime="text/csv",
                            )


def display_keyword_search_results():
    """Display recent keyword search results"""
    if (
        "keyword_search_results" in st.session_state
        and st.session_state.keyword_search_results
    ):
        results = st.session_state.keyword_search_results

        st.subheader(f"🔤 Recent Keyword Search Results ({len(results)} businesses)")

        if results:
            df = pd.DataFrame(results)

            # Select columns to display
            display_columns = ["name", "address", "rating", "has_website", "phone"]
            available_columns = [col for col in display_columns if col in df.columns]

            if available_columns:
                df_display = df[available_columns]
                df_display.columns = [
                    col.replace("_", " ").title() for col in available_columns
                ]
                business_table(df_display, height=300)
