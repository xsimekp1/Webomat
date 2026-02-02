"""
Quick Website Generator page for Streamlit app
"""

import streamlit as st
import re
from components.ui_components import task_status_display
from utils.tasks import task_manager


def quick_generator_page():
    """Quick website generator page with manual inputs"""
    st.header("🌐 Quick Website Generator")

    st.info("""
    **Generate a website instantly** by providing business details and source links.
    This skips the business discovery process and creates a website directly from your inputs.
    """)

    # Form sections
    with st.form("quick_website_form"):
        st.subheader("📋 Business Information")

        # Basic information
        col1, col2 = st.columns(2)

        with col1:
            business_name = st.text_input(
                "Business Name *",
                placeholder="Enter the business name",
                help="Required: The name of the business",
            )

            business_address = st.text_input(
                "Address *",
                placeholder="Enter the business address",
                help="Required: Physical address or location description",
            )

            business_phone = st.text_input(
                "Phone Number",
                placeholder="+420 123 456 789",
                help="Optional: Contact phone number",
            )

        with col2:
            business_email = st.text_input(
                "Email",
                placeholder="contact@business.com",
                help="Optional: Contact email address",
            )

            business_type = st.selectbox(
                "Business Type",
                ["Restaurant", "Cafe", "Store", "Service", "Hotel", "Other"],
                help="Select the type of business for appropriate template",
            )

            business_rating = st.slider(
                "Rating (Optional)",
                min_value=0.0,
                max_value=5.0,
                value=4.0,
                step=0.1,
                help="Estimated customer rating (0-5 stars)",
            )

        st.subheader("🔗 Source Links")

        # Multiple links input
        st.write("Add any existing online resources or references:")

        num_links = st.number_input(
            "Number of links", min_value=1, max_value=10, value=3, step=1
        )

        link_data = []
        for i in range(num_links):
            col1, col2 = st.columns([3, 1])

            with col1:
                link_url = st.text_input(
                    f"Link {i + 1}",
                    placeholder="https://example.com/page",
                    key=f"link_{i}",
                )

            with col2:
                link_type = st.selectbox(
                    "Type",
                    ["Website", "Facebook", "Instagram", "Google Maps", "Other"],
                    key=f"link_type_{i}",
                )

            if link_url:
                link_data.append({"url": link_url, "type": link_type})

        st.subheader("📝 Business Description")

        # Description input
        business_description = st.text_area(
            "Business Description *",
            placeholder="Describe the business, its services, atmosphere, target customers, unique features, etc.",
            height=150,
            help="Required: Detailed description that will be used to generate the website content",
        )

        # Additional features
        st.subheader("✨ Additional Features")

        col1, col2, col3 = st.columns(3)

        with col1:
            has_photos = st.checkbox("Has Photos Available", value=True)

            if has_photos:
                photo_urls = st.text_area(
                    "Photo URLs (one per line)",
                    placeholder="https://example.com/photo1.jpg\nhttps://example.com/photo2.jpg",
                    height=100,
                    help="Optional: URLs to business photos",
                )
            else:
                photo_urls = ""

        with col2:
            has_menu = st.checkbox("Has Menu/Services", value=True)

            if has_menu:
                menu_text = st.text_area(
                    "Menu/Services Description",
                    placeholder="List of products, services, or menu items with prices",
                    height=100,
                )
            else:
                menu_text = ""

        with col3:
            has_hours = st.checkbox("Has Operating Hours", value=True)

            if has_hours:
                hours_text = st.text_input(
                    "Hours", placeholder="Mon-Fri 9:00-18:00, Sat-Sun 10:00-16:00"
                )
            else:
                hours_text = ""

        # Website generation options
        st.subheader("⚙️ Website Options")

        col1, col2 = st.columns(2)

        with col1:
            website_style = st.selectbox(
                "Website Style",
                ["Modern", "Classic", "Minimal", "Creative"],
                help="Choose the visual style for the generated website",
            )

            website_color = st.color_picker("Primary Color", value="#1f77b4")

        with col2:
            website_language = st.selectbox(
                "Language",
                ["Czech", "English", "Both"],
                help="Primary language for the website",
            )

            add_contact_form = st.checkbox("Add Contact Form", value=True)

        # Submit button
        submitted = st.form_submit_button(
            "🌐 Generate Website", use_container_width=True, type="primary"
        )

        if submitted:
            # Validate required fields
            if not business_name or not business_address or not business_description:
                st.error("Please fill in all required fields (*).")
                return

            # Start generation task
            business_data = {
                "name": business_name,
                "address": business_address,
                "phone": business_phone,
                "email": business_email,
                "type": business_type,
                "rating": business_rating,
                "description": business_description,
                "links": link_data,
                "has_photos": has_photos,
                "photo_urls": photo_urls if has_photos else "",
                "has_menu": has_menu,
                "menu_text": menu_text if has_menu else "",
                "has_hours": has_hours,
                "hours_text": hours_text if has_hours else "",
                "style": website_style,
                "color": website_color,
                "language": website_language,
                "add_contact_form": add_contact_form,
            }

            task_manager.add_task(
                "Quick Website Generation", quick_website_generation_task, business_data
            )

            st.success("Website generation started! Check progress below.")

    # Display running generation tasks
    display_running_tasks()


def quick_website_generation_task(business_data, progress_callback=None):
    """Task for quick website generation"""
    try:
        if progress_callback:
            progress_callback(10, "Processing business information...")

        # Validate and prepare data
        processed_data = prepare_business_data(business_data)

        if progress_callback:
            progress_callback(25, "Processing source links...")

        # Process source links
        link_content = process_source_links(processed_data["links"])

        if progress_callback:
            progress_callback(50, "Generating website content...")

        # Generate website content using OpenAI
        website_content = generate_website_content(processed_data, link_content)

        if progress_callback:
            progress_callback(75, "Creating website files...")

        # Create HTML website
        website_html = create_website_html(website_content, processed_data)

        if progress_callback:
            progress_callback(90, "Saving website...")

        # Save website
        website_path = save_quick_website(website_html, processed_data["name"])

        if progress_callback:
            progress_callback(100, "Website generation completed!")

        # Store result
        if "quick_generated_websites" not in st.session_state:
            st.session_state.quick_generated_websites = []

        st.session_state.quick_generated_websites.append(
            {
                "name": processed_data["name"],
                "path": website_path,
                "url": f"/{website_path}",
                "generated_at": pd.Timestamp.now(),
            }
        )

        return True

    except Exception as e:
        if progress_callback:
            progress_callback(0, f"Error: {str(e)}")
        return {"error": str(e)}


def prepare_business_data(business_data):
    """Validate and prepare business data"""
    # Clean and validate inputs
    processed = business_data.copy()

    # Clean phone number
    if processed.get("phone"):
        processed["phone"] = re.sub(r"[^\d+\s\-\(\)]", "", processed["phone"])

    # Validate URLs
    validated_links = []
    for link in processed.get("links", []):
        url = link.get("url", "").strip()
        if url and (url.startswith("http://") or url.startswith("https://")):
            validated_links.append(link)

    processed["links"] = validated_links

    return processed


def process_source_links(links):
    """Process and extract content from source links"""
    content_summary = []

    for link_info in links:
        url = link_info.get("url")
        link_type = link_info.get("type")

        try:
            # Simple content extraction (simplified)
            import requests

            response = requests.get(
                url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}
            )

            if response.status_code == 200:
                # Extract basic content
                content = response.text[:1000]  # First 1000 chars
                content_summary.append(
                    {"url": url, "type": link_type, "content": content}
                )
        except Exception as e:
            content_summary.append(
                {
                    "url": url,
                    "type": link_type,
                    "content": f"Error accessing link: {str(e)}",
                }
            )

    return content_summary


def generate_website_content(business_data, link_content):
    """Generate website content using OpenAI or local logic"""
    try:
        # For now, create a structured content dict
        # In real implementation, would use OpenAI API
        website_content = {
            "title": business_data["name"],
            "description": business_data["description"],
            "address": business_data["address"],
            "phone": business_data.get("phone", ""),
            "email": business_data.get("email", ""),
            "type": business_data["type"],
            "rating": business_data["rating"],
            "services": business_data.get("menu_text", ""),
            "hours": business_data.get("hours_text", ""),
            "style": business_data["style"],
            "color": business_data["color"],
            "language": business_data["language"],
            "add_contact_form": business_data["add_contact_form"],
            "photos": business_data.get("photo_urls", "").split("\n")
            if business_data.get("photo_urls")
            else [],
            "links": link_content,
        }

        return website_content

    except Exception as e:
        return {"error": str(e)}


def create_website_html(content, business_data):
    """Create HTML website from content"""
    try:
        # Simple HTML template (would use opencode in real implementation)
        html_template = f"""
<!DOCTYPE html>
<html lang="{content["language"][:2].lower()}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{content["title"]} - {content["type"]}</title>
    <style>
        :root {{ --primary-color: {content["color"]}; }}
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .title {{ color: var(--primary-color); font-size: 2.5em; margin-bottom: 10px; }}
        .subtitle {{ color: #666; font-size: 1.2em; }}
        .info-section {{ background: #f9f9f9; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        .contact-info {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; }}
        .btn {{ background: var(--primary-color); color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">{content["title"]}</h1>
            <p class="subtitle">{content["type"]} ⭐ {"★" * int(content["rating"])}</p>
        </div>
        
        <div class="info-section">
            <h3>About Us</h3>
            <p>{content["description"]}</p>
            
            <h3>Location & Hours</h3>
            <p><strong>Address:</strong> {content["address"]}</p>
            <p><strong>Hours:</strong> {content["hours"]}</p>
            
            {"<h3>Our Menu</h3><p>" + content["services"] + "</p>" if content["services"] else ""}
            
            <h3>Contact Information</h3>
            <div class="contact-info">
                <div>
                    <p><strong>Phone:</strong> {content["phone"]}</p>
                    <p><strong>Email:</strong> {content["email"]}</p>
                </div>
                <div>
                    <button class="btn">Contact Us</button>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>&copy; 2024 {content["title"]}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """

        return html_template

    except Exception as e:
        return f"Error generating HTML: {str(e)}"


def save_quick_website(html_content, business_name):
    """Save generated website to file system"""
    import os
    from datetime import datetime
    import re

    # Create safe filename
    safe_name = re.sub(r"[^a-zA-Z0-9]", "_", business_name).lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create directory if it doesn't exist
    quick_websites_dir = "quick_generated_websites"
    os.makedirs(quick_websites_dir, exist_ok=True)

    # Save HTML file
    filename = f"{safe_name}_{timestamp}.html"
    filepath = os.path.join(quick_websites_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    return filename


def display_running_tasks():
    """Display running quick generation tasks"""
    running_tasks = task_manager.get_running_tasks()
    quick_tasks = [t for t in running_tasks if "quick website" in t["name"].lower()]

    if quick_tasks:
        st.subheader("🔄 Running Website Generation")
        for task in quick_tasks:
            task_status_display(task)

    # Display completed websites
    if (
        "quick_generated_websites" in st.session_state
        and st.session_state.quick_generated_websites
    ):
        st.subheader("📋 Recently Generated Websites")

        for website in reversed(
            st.session_state.quick_generated_websites[-5:]
        ):  # Show last 5
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.write(f"**{website['name']}**")
                st.caption(
                    f"Generated: {website['generated_at'].strftime('%Y-%m-%d %H:%M')}"
                )

            with col2:
                if st.button("👁️ View", key=f"view_{website['url']}"):
                    st.info(f"Website saved as: {website['path']}")

            with col3:
                if st.button("📥 Download", key=f"download_{website['url']}"):
                    try:
                        with open(
                            f"quick_generated_websites/{website['path']}",
                            "r",
                            encoding="utf-8",
                        ) as f:
                            st.download_button(
                                label="Download Website",
                                data=f.read(),
                                file_name=website["path"],
                                mime="text/html",
                            )
                    except Exception as e:
                        st.error(f"Error downloading {website['path']}: {e}")
