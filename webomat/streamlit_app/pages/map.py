"""
Map page for Streamlit app
"""

import streamlit as st
from components.ui_components import task_status_display
from utils.tasks import task_manager


def map_page():
    """Map page with embedded Folium map and controls"""
    st.header("🗺️ Interactive Map")

    # Show current businesses from database
    try:
        from utils.database import db

        all_businesses = db.get_all_businesses()

        if all_businesses:
            st.info(f"📊 Database contains {len(all_businesses)} businesses")

            # Quick stats
            with_website = sum(1 for b in all_businesses if b.get("has_website", False))
            without_website = len(all_businesses) - with_website

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Businesses", len(all_businesses))
            with col2:
                st.metric("With Website", with_website)
            with col3:
                st.metric("Without Website", without_website)

        else:
            st.warning("No businesses in database. Use Search page to add businesses.")
            return

    except Exception as e:
        st.error(f"Error loading business data: {e}")
        return

    # Map controls
    st.subheader("🗺️ Map Controls")

    col1, col2 = st.columns([1, 2])

    with col1:
        # Business filters
        business_filter = st.selectbox(
            "Show Businesses",
            ["All", "With Website", "Without Website"],
            help="Filter which businesses to show on map",
        )

        # Map refresh button
        if st.button("🔄 Generate Map", use_container_width=True):
            generate_map_with_progress()

    with col2:
        st.markdown("**Color Legend:**")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("🟦 **Blue:** Has Website")
        with col_b:
            st.markdown("🟠 **Orange:** No Website")
        with col_c:
            st.markdown("🔴 **Red:** Search Areas")

    # Generate and display map
    if all_businesses:
        display_business_map(all_businesses, business_filter)

    st.markdown("---")

    # Nearby search section
    st.subheader("🔍 Find More Businesses")

    # Search parameters
    nearby_col1, nearby_col2 = st.columns(2)

    with nearby_col1:
        search_location = st.text_input(
            "Location",
            placeholder="Enter address (e.g., Prague, Czech Republic)",
            value="Praha, Czech Republic",
        )

        search_radius = st.slider(
            "Search Radius (meters)",
            min_value=100,
            max_value=3000,
            value=1000,
            step=100,
        )

    with nearby_col2:
        result_limit = st.number_input(
            "Max Results", min_value=5, max_value=50, value=10, step=1
        )

        filter_by_website = st.selectbox(
            "Filter New Businesses",
            ["All", "Only Without Website", "Only With Website"],
        )

    # Search button
    if st.button("🔍 Search & Add to Map", type="primary", use_container_width=True):
        if search_location:
            # Start search task
            task_manager.add_task(
                "Nearby Map Search",
                nearby_map_search_task,
                search_location,
                search_radius,
                result_limit,
                filter_by_website,
            )
            st.success(
                "Search started! New businesses will be added to database and map."
            )
        else:
            st.error("Please enter a location.")

    # Display running tasks
    running_tasks = task_manager.get_running_tasks()
    map_tasks = [t for t in running_tasks if "map" in t["name"].lower()]
    if map_tasks:
        st.subheader("🔄 Search Progress")
        for task in map_tasks:
            from components.ui_components import task_status_display

            task_status_display(task)

    # Show current map if exists
    import os

    map_file = "grid_coverage.html"

    if os.path.exists(map_file):
        st.info("Current coverage map:")

        # Read and display the HTML file
        with open(map_file, "r", encoding="utf-8") as f:
            map_html = f.read()

        st.components.v1.html(map_html, height=600)

        # Map statistics
        display_map_statistics()
    else:
        st.warning("No map available. Click 'Generate New Map' to create one.")

        if st.button("🗺️ Generate New Map", type="primary"):
            generate_map_with_progress()

    st.markdown("---")

    # Map Actions
    st.subheader("🛠️ Map Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Grid Statistics", use_container_width=True):
            show_detailed_grid_stats()

    with col2:
        if st.button("📍 Selected Business", use_container_width=True):
            if "selected_map_business" in st.session_state:
                show_selected_business_details()
            else:
                st.info(
                    "No business selected. Select a business from the Businesses page first."
                )

    with col3:
        if st.button("📥 Download Map", use_container_width=True):
            if os.path.exists(map_file):
                with open(map_file, "r", encoding="utf-8") as f:
                    map_data = f.read()
                st.download_button(
                    label="Download Map HTML",
                    data=map_data,
                    file_name="webomap_coverage.html",
                    mime="text/html",
                )
            else:
                st.error("No map file available to download.")

    st.markdown("---")

    # Running tasks
    running_tasks = task_manager.get_running_tasks()
    map_tasks = [t for t in running_tasks if "map" in t["name"].lower()]

    if map_tasks:
        st.subheader("🔄 Map Generation Tasks")
        for task in map_tasks:
            task_status_display(task)


def generate_map_with_progress():
    """Generate map with progress tracking"""
    task_manager.add_task("Generate Coverage Map", generate_map_task)


def generate_map_task(progress_callback=None):
    """Generate the coverage map"""
    try:
        from utils.database import grid_manager
        from webomat import Webomat

        if progress_callback:
            progress_callback(0, "Initializing map generation...")

        webomat = Webomat()

        if progress_callback:
            progress_callback(25, "Getting grid statistics...")

        # Get grid statistics
        stats = grid_manager.get_coverage_stats()

        if progress_callback:
            progress_callback(50, "Creating map...")

        # Generate map
        webomat.handle_show_coverage()

        if progress_callback:
            progress_callback(75, "Saving map...")

        if progress_callback:
            progress_callback(100, "Map generation completed!")

        return True
    except Exception as e:
        if progress_callback:
            progress_callback(0, f"Error: {str(e)}")
        return {"error": str(e)}


def nearby_map_search_task(
    location, radius, limit, filter_by_website, progress_callback=None
):
    """Task for nearby business search from map page"""
    try:
        from webomat import Webomat

        if progress_callback:
            progress_callback(10, "Initializing search...")

        webomat = Webomat()

        if progress_callback:
            progress_callback(30, "Searching for businesses...")

        # Try to parse location as coordinates first
        try:
            lat, lng = map(float, location.split(","))
        except:
            # Geocode address
            geocode_result = webomat.geocode_address(location)
            if not geocode_result:
                return {"error": "Location not found"}
            lat, lng = geocode_result

        # Search nearby places
        places = webomat.search_nearby_places(lat, lng, radius)

        if progress_callback:
            progress_callback(50, "Processing results...")

        # Filter places
        filtered_places = webomat.filter_places(places)

        # Apply website filter
        if filter_by_website == "Only Without Website":
            filtered_places = [p for p in filtered_places if not p.get("website")]
        elif filter_by_website == "Only With Website":
            filtered_places = [p for p in filtered_places if p.get("website")]

        # Limit results
        filtered_places = filtered_places[:limit]

        if progress_callback:
            progress_callback(80, "Preparing results...")

        # Store results for map display
        st.session_state.map_search_results = [
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


def display_business_map(businesses, filter_type):
    """Display businesses on an interactive map"""
    try:
        import folium
        from streamlit_folium import st_folium

        # Filter businesses
        if filter_type == "With Website":
            filtered_businesses = [b for b in businesses if b.get("has_website", False)]
        elif filter_type == "Without Website":
            filtered_businesses = [
                b for b in businesses if not b.get("has_website", False)
            ]
        else:
            filtered_businesses = businesses

        if not filtered_businesses:
            st.info(f"No businesses found with filter: {filter_type}")
            return

        # Create map centered on Czech Republic
        m = folium.Map(location=[49.8, 15.5], zoom_start=7)

        # Add business markers
        for business in filtered_businesses:
            lat = business.get("lat")
            lng = business.get("lng")

            if lat and lng:
                # Choose color based on website status
                color = "blue" if business.get("has_website", False) else "orange"

                # Create popup content
                popup_content = f"""
                <b>{business.get("name", "Unknown")}</b><br>
                📍 {business.get("address", "N/A")}<br>
                ⭐ {business.get("rating", 0):.1f}/5.0<br>
                🌐 {business.get("website", "No website")}<br>
                📞 {business.get("phone", "N/A")}
                """

                folium.CircleMarker(
                    location=[lat, lng],
                    radius=6,
                    popup=popup_content,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                ).add_to(m)

        # Display map
        st_folium(m, width=700, height=500)

        # Summary
        st.info(f"📍 Showing {len(filtered_businesses)} businesses on map")

    except ImportError:
        st.error(
            "Map display requires folium. Install with: pip install folium streamlit-folium"
        )
    except Exception as e:
        st.error(f"Error displaying map: {e}")


def display_nearby_search_results():
    """Display results from nearby search"""
    if "map_search_results" in st.session_state:
        results = st.session_state.map_search_results

        if results:
            st.subheader("📍 Search Results")
            st.info(f"Found {len(results)} new businesses")

            # Add to main map display
            display_business_map(results, "All")

            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ Add All to Database", use_container_width=True):
                    # Add results to database
                    from utils.database import db

                    for business in results:
                        # Convert to database format
                        db_business = {
                            "name": business.get("name"),
                            "address": business.get("address"),
                            "phone": business.get("phone"),
                            "rating": business.get("rating"),
                            "website": business.get("website"),
                            "lat": business.get("lat"),
                            "lng": business.get("lng"),
                            "place_id": business.get("place_id"),
                        }
                        db.save_business(db_business)

                    st.success(f"Added {len(results)} businesses to database!")
                    st.rerun()

            with col2:
                if st.button("🗺️ Show on Main Map", use_container_width=True):
                    st.session_state.current_page = "Map"
                    st.rerun()


def quick_generate_for_business(business_data):
    """Quickly generate website for a business from search results"""
    try:
        # Prepare business data for quick generation
        quick_data = {
            "name": business_data.get("name", ""),
            "address": business_data.get("address", ""),
            "phone": business_data.get("phone", ""),
            "type": "Business",  # Default type
            "rating": business_data.get("rating", 4.0),
            "description": f"Business located at {business_data.get('address', '')}",
            "links": [],  # No additional links
            "has_photos": False,
            "photo_urls": "",
            "has_menu": False,
            "menu_text": "",
            "has_hours": False,
            "hours_text": "",
            "style": "Modern",
            "color": "#1f77b4",
            "language": "Czech",
            "add_contact_form": True,
        }

        task_manager.add_task(
            f"Quick Gen: {business_data.get('name', 'Unknown')}",
            quick_website_generation_task,
            quick_data,
        )

        st.success(f"Website generation started for {business_data.get('name')}!")

    except Exception as e:
        st.error(f"Error starting website generation: {e}")


def display_map_statistics():
    """Display detailed map statistics"""
    try:
        from utils.database import grid_manager, db

        # Grid statistics
        grid_stats = grid_manager.get_coverage_stats()

        st.subheader("📊 Grid Coverage Statistics")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Cells", grid_stats["total_cells"])
            st.metric("Searched Cells", grid_stats["searched_cells"])
            st.metric(
                "Coverage Percentage", f"{grid_stats['coverage_percentage']:.1f}%"
            )

        with col2:
            unsearched = grid_stats["total_cells"] - grid_stats["searched_cells"]
            st.metric("Unsearched Cells", unsearched)

            # Businesses per cell average
            avg_businesses = (
                grid_stats["total_businesses"] / grid_stats["searched_cells"]
                if grid_stats["searched_cells"] > 0
                else 0
            )
            st.metric("Avg Businesses/Cell", f"{avg_businesses:.1f}")

        # Business statistics
        all_businesses = db.get_all_businesses()
        if all_businesses:
            st.subheader("📋 Business Distribution")

            # Location distribution by region
            regions = {}
            for business in all_businesses:
                # Simple region classification by coordinates
                lat = business.get("lat", 0)
                lng = business.get("lng", 0)

                if 50.0 <= lat <= 51.5:  # Northern CZ
                    region = "North"
                elif 48.5 <= lat < 50.0:  # Southern CZ
                    region = "South"
                else:
                    region = "Other"

                regions[region] = regions.get(region, 0) + 1

            if regions:
                st.write("**Businesses by Region:**")
                for region, count in regions.items():
                    st.write(f"• {region}: {count}")

            # Website coverage
            with_website = sum(1 for b in all_businesses if b.get("has_website", False))
            without_website = len(all_businesses) - with_website

            col1a, col2a = st.columns(2)
            with col1a:
                st.metric("Businesses with Website", with_website)
            with col2a:
                st.metric("Businesses without Website", without_website)

    except Exception as e:
        st.error(f"Error loading map statistics: {e}")


def show_selected_business_details():
    """Show details of the selected business on map"""
    if "selected_map_business" in st.session_state:
        business = st.session_state.selected_map_business

        st.subheader(f"📍 {business.get('name', 'Unknown Business')}")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Address:**", business.get("address", "N/A"))
            st.write("**Phone:**", business.get("phone", "N/A"))
            st.write("**Website:**", business.get("website", "N/A"))

        with col2:
            st.metric("Rating", f"{business.get('rating', 0):.1f}/5.0")
            st.metric("Reviews", business.get("review_count", 0))
            st.write("**Has Website:**", "✅" if business.get("has_website") else "❌")

        # Coordinates
        if business.get("lat") and business.get("lng"):
            st.write(
                f"**Coordinates:** {business.get('lat'):.4f}, {business.get('lng'):.4f}"
            )


def show_detailed_grid_stats():
    """Show detailed grid statistics"""
    try:
        from utils.database import grid_manager, db

        # Get all grid cells for detailed analysis
        all_cells = grid_manager.db.get_all_grid_cells()
        all_businesses = db.get_all_businesses()

        st.subheader("📈 Detailed Grid Analysis")

        if all_cells:
            # Search status distribution
            searched_cells = sum(1 for cell in all_cells if cell.get("searched", False))
            unsearched_cells = len(all_cells) - searched_cells

            # Business distribution in searched cells
            businesses_in_searched = sum(
                1 for b in all_businesses if b.get("lat") and b.get("lng")
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Searched Cells", searched_cells)
                st.metric("Unsearched Cells", unsearched_cells)

            with col2:
                search_percentage = (
                    (searched_cells / len(all_cells)) * 100 if all_cells else 0
                )
                st.metric("Search Percentage", f"{search_percentage:.2f}%")
                st.metric("Businesses in Searched Areas", businesses_in_searched)

            with col3:
                businesses_per_searched = (
                    businesses_in_searched / searched_cells if searched_cells > 0 else 0
                )
                st.metric(
                    "Avg Businesses/Searched Cell", f"{businesses_per_searched:.1f}"
                )

                total_coverage_area = searched_cells * 4  # Assuming 2km x 2km cells
                st.metric("Coverage Area (km²)", total_coverage_area)

            # Coverage by density
            if all_cells:
                st.subheader("🗺️ Coverage Density Map")

                # Create density information
                cell_densities = []
                for cell in all_cells[:100]:  # Limit to first 100 for performance
                    if cell.get("searched", False):
                        # Count businesses near this cell
                        cell_lat = cell.get("lat_center", 0)
                        cell_lng = cell.get("lng_center", 0)

                        nearby_businesses = sum(
                            1
                            for b in all_businesses
                            if (
                                abs(b.get("lat", 0) - cell_lat) < 0.01
                                and abs(b.get("lng", 0) - cell_lng) < 0.01
                            )
                        )

                        cell_densities.append(
                            {
                                "lat": cell_lat,
                                "lng": cell_lng,
                                "density": nearby_businesses,
                            }
                        )

                if cell_densities:
                    st.write(
                        f"Analyzed {len(cell_densities)} searched cells for business density."
                    )

                    # Create density chart
                    density_data = [c["density"] for c in cell_densities]
                    if density_data:
                        st.write(
                            f"**Business Density Range:** {min(density_data)} - {max(density_data)} businesses per cell"
                        )
                        st.write(
                            f"**Average Density:** {sum(density_data) / len(density_data):.1f} businesses per cell"
                        )

    except Exception as e:
        st.error(f"Error loading detailed grid statistics: {e}")
