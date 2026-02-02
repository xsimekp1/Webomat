"""
Reusable Streamlit components
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
import sqlite3

try:
    import plotly.express as px
    import plotly.graph_objects as go

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


def stat_card(title: str, value: Any, delta: Any = None, color: str = "blue"):
    """Create a statistics card"""
    if delta is not None:
        try:
            delta_num = (
                int(delta) if isinstance(delta, str) and delta.isdigit() else delta
            )
            delta_color = "green" if delta_num >= 0 else "red"
        except (ValueError, TypeError):
            delta_color = "blue"
        delta_html = f'<span style="color: {delta_color};">{delta}</span>'
    else:
        delta_html = ""

    st.markdown(
        f"""
    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin: 10px 0;">
        <h3 style="color: {color}; margin: 0;">{title}</h3>
        <p style="font-size: 24px; font-weight: bold; margin: 10px 0;">{value}</p>
        {delta_html}
    </div>
    """,
        unsafe_allow_html=True,
    )


def business_table(dataframe: pd.DataFrame, height: int = 400):
    """Display business data with custom styling"""
    if dataframe.empty:
        st.info("No businesses found.")
        return

    # Display with better formatting
    st.dataframe(
        dataframe,
        height=height,
        use_container_width=True,
        column_config={
            "Has Website": st.column_config.CheckboxColumn(
                "Has Website",
                help="Whether the business has a website",
                default=False,
            ),
        },
    )


def progress_bar_with_message(progress: float, message: str):
    """Display progress bar with custom message"""
    st.progress(progress)
    st.caption(message)


def task_status_display(task_info: Dict):
    """Display task status"""
    status = task_info["status"]
    if status == "running":
        st.info(f"🔄 **{task_info['name']}** - {task_info['message']}")
        progress_bar_with_message(task_info["progress"], task_info["message"])
    elif status == "completed":
        st.success(f"✅ **{task_info['name']}** - Completed")
    elif status == "failed":
        st.error(f"❌ **{task_info['name']}** - {task_info['error']}")


def website_status_chart(stats: Dict):
    """Create a pie chart for website status"""
    if not stats or not PLOTLY_AVAILABLE:
        return None

    if not stats.get("businesses_with_website"):
        return None

    data = {
        "Status": ["Has Website", "No Website"],
        "Count": [
            stats["businesses_with_website"],
            stats["businesses_without_website"],
        ],
    }

    fig = px.pie(
        values=data["Count"],
        names=data["Status"],
        title="Website Status Distribution",
        color_discrete_map={"Has Website": "#1f77b4", "No Website": "#ff7f0e"},
    )

    return fig


def coverage_progress_chart(coverage_percentage: float):
    """Create a progress chart for grid coverage"""
    if not PLOTLY_AVAILABLE:
        return None

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=coverage_percentage,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Grid Coverage (%)"},
            delta={"reference": 100},
            gauge={
                "axis": {"range": [None, 100]},
                "bar": {"color": "#1f77b4"},
                "steps": [
                    {"range": [0, 25], "color": "lightgray"},
                    {"range": [25, 50], "color": "gray"},
                    {"range": [50, 75], "color": "lightblue"},
                    {"range": [75, 100], "color": "blue"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": 90,
                },
            },
        )
    )

    fig.update_layout(height=300)
    return fig


def rating_histogram(businesses: List[Dict]):
    """Create a histogram of business ratings"""
    if not businesses or not PLOTLY_AVAILABLE:
        return None

    ratings = [b.get("rating", 0) for b in businesses if b.get("rating")]

    if not ratings:
        return None

    fig = px.histogram(
        x=ratings,
        nbins=20,
        title="Rating Distribution",
        labels={"x": "Rating", "y": "Count"},
        color_discrete_sequence=["#1f77b4"],
    )

    return fig


def filter_controls(businesses: List[Dict]):
    """Create filter controls for businesses"""
    if not businesses:
        return None, None, None, None

    st.sidebar.subheader("🔍 Filters")

    # Website status filter
    website_filter = st.sidebar.selectbox(
        "Website Status", ["All", "Has Website", "No Website"]
    )

    # Rating filter
    ratings = sorted(set([b.get("rating", 0) for b in businesses if b.get("rating")]))
    if ratings:
        min_rating, max_rating = st.sidebar.slider(
            "Rating Range", min_value=0.0, max_value=5.0, value=(0.0, 5.0), step=0.1
        )

    # Review count filter
    review_counts = [
        b.get("review_count", 0) for b in businesses if b.get("review_count")
    ]
    if review_counts:
        min_reviews, max_reviews = st.sidebar.slider(
            "Review Count Range",
            min_value=0,
            max_value=max(review_counts),
            value=(0, max(review_counts)),
            step=1,
        )

    # Search filter
    search_term = st.sidebar.text_input("Search by Name or Address")

    return (
        website_filter,
        (min_rating, max_rating),
        (min_reviews, max_reviews),
        search_term,
    )


def apply_filters(
    businesses: List[Dict],
    website_filter: str,
    rating_range: tuple,
    review_range: tuple,
    search_term: str,
):
    """Apply filters to business list"""
    filtered = businesses.copy()

    # Website status filter
    if website_filter != "All":
        has_website = website_filter == "Has Website"
        filtered = [b for b in filtered if b.get("has_website", False) == has_website]

    # Rating filter
    min_rating, max_rating = rating_range
    filtered = [b for b in filtered if min_rating <= b.get("rating", 0) <= max_rating]

    # Review count filter
    min_reviews, max_reviews = review_range
    filtered = [
        b for b in filtered if min_reviews <= b.get("review_count", 0) <= max_reviews
    ]

    # Search filter
    if search_term:
        search_lower = search_term.lower()
        filtered = [
            b
            for b in filtered
            if search_lower in b.get("name", "").lower()
            or search_lower in b.get("address", "").lower()
        ]

    return filtered


# CRM komponenty
def crm_call_scheduler(business: Dict, db_manager, current_user: str = None) -> None:
    """CRM plánovač hovorů"""
    st.subheader("📞 Plánovač hovorů")

    business_id = business.get("id")
    if not business_id:
        st.error("Business ID nenalezeno")
        return

    # Aktuální stav
    current_next_call = business.get("next_call_date", "")
    current_notes = business.get("call_notes", "")
    current_last_contact = business.get("last_contact", "")
    current_assigned = business.get("assigned_user", "")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Aktuální stav:**")
        if current_next_call:
            st.write(f"📅 Další hovor: {current_next_call}")
        else:
            st.write("📅 Další hovor: Nenaplánováno")

        if current_last_contact:
            st.write(f"📞 Poslední kontakt: {current_last_contact}")
        else:
            st.write("📞 Poslední kontakt: Nikdy")

        if current_assigned:
            st.write(f"👤 Přiřazený uživatel: {current_assigned}")
        else:
            st.write("👤 Přiřazený uživatel: Nikdo")

    with col2:
        # Rychlé akce
        st.write("**Rychlé akce:**")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("📞 Volat dnes", key=f"call_today_{business_id}"):
                today = datetime.now().strftime("%Y-%m-%d")
                if db_manager.update_call_info(business_id, next_call_date=today):
                    st.success("Hovor naplánován na dnešní den!")
                    st.rerun()
                else:
                    st.error("Chyba při plánování hovoru")

        with col_b:
            if st.button("⏰ Za týden", key=f"call_week_{business_id}"):
                week_later = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                if db_manager.update_call_info(business_id, next_call_date=week_later):
                    st.success("Hovor naplánován za týden!")
                    st.rerun()
                else:
                    st.error("Chyba při plánování hovoru")

        with col_c:
            if st.button("✅ Dokončit", key=f"call_done_{business_id}"):
                if db_manager.mark_call_completed(business_id, "Hovor dokončen"):
                    st.success("Hovor označen jako dokončený!")
                    st.rerun()
                else:
                    st.error("Chyba při dokončování hovoru")

    # Vlastní datum
    st.write("---")
    custom_date = st.date_input(
        "Vybrat vlastní datum hovoru",
        value=None
        if not current_next_call
        else datetime.strptime(current_next_call, "%Y-%m-%d").date(),
        key=f"custom_date_{business_id}",
    )

    if custom_date:
        selected_date = custom_date.strftime("%Y-%m-%d")
        if selected_date != current_next_call:
            if st.button("💾 Uložit datum", key=f"save_date_{business_id}"):
                if db_manager.update_call_info(
                    business_id, next_call_date=selected_date
                ):
                    st.success(f"Datum hovoru nastaveno na {selected_date}")
                    st.rerun()
                else:
                    st.error("Chyba při ukládání data")

    # Přiřazení uživatele
    st.write("---")
    st.write("**👤 Přiřazení uživatele:**")
    new_assigned = st.text_input(
        "Uživatel zodpovědný za tohoto klienta",
        value=current_assigned or current_user or "",
        key=f"assigned_{business_id}",
        placeholder="Zadejte jméno uživatele...",
    )

    if new_assigned != current_assigned:
        if st.button("👤 Uložit uživatele", key=f"save_user_{business_id}"):
            # Potřebujem přidat metodu pro aktualizaci assigned_user
            try:
                with sqlite3.connect(db_manager.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE businesses SET assigned_user = ? WHERE id = ?",
                        (new_assigned, business_id),
                    )
                    conn.commit()
                st.success(f"Klient přiřazen uživateli: {new_assigned}")
                st.rerun()
            except Exception as e:
                st.error(f"Chyba při ukládání uživatele: {e}")


def crm_data_sync(db_manager, current_user: str = None) -> None:
    """Komponenta pro synchronizaci CRM dat"""
    st.subheader("🔄 Synchronizace CRM dat")

    tab1, tab2 = st.tabs(["📤 Export", "📥 Import"])

    with tab1:
        st.write("**Exportovat CRM data pro sdílení:**")
        export_user = st.text_input(
            "Exportovat jen pro uživatele (prázdné = vše)",
            value=current_user or "",
            key="export_user",
        )

        if st.button("📤 Exportovat CRM data", key="export_crm"):
            crm_data = db_manager.export_crm_data(export_user if export_user else None)
            json_data = json.dumps(crm_data, indent=2, ensure_ascii=False)

            st.download_button(
                label="💾 Stáhnout JSON soubor",
                data=json_data,
                file_name=f"crm_data_{export_user or 'all'}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                key="download_crm",
            )

            st.success(f"✅ Připraveno {crm_data['total_clients']} klientů k exportu")

    with tab2:
        st.write("**Importovat CRM data ze sdíleného souboru:**")

        uploaded_file = st.file_uploader(
            "Vyberte CRM JSON soubor", type=["json"], key="crm_import"
        )

        if uploaded_file:
            try:
                crm_data = json.load(uploaded_file)

                col1, col2 = st.columns(2)
                with col1:
                    merge_strategy = st.selectbox(
                        "Strategie sloučení",
                        ["update", "skip"],
                        format_func=lambda x: "Aktualizovat existující"
                        if x == "update"
                        else "Přeskočit existující",
                        key="merge_strategy",
                    )

                with col2:
                    assign_to_user = st.text_input(
                        "Přiřadit klienty uživateli",
                        value=current_user or "",
                        key="assign_user",
                    )

                if st.button("📥 Importovat data", key="import_crm"):
                    result = db_manager.import_crm_data(
                        crm_data,
                        assign_to_user if assign_to_user else None,
                        merge_strategy,
                    )

                    st.success(f"✅ Import dokončen:")
                    st.write(f"• Importováno: {result['imported']}")
                    st.write(f"• Aktualizováno: {result['updated']}")
                    st.write(f"• Přeskočeno: {result['skipped']}")

                    if result["imported"] > 0 or result["updated"] > 0:
                        st.rerun()

            except json.JSONDecodeError:
                st.error("❌ Neplatný JSON soubor")
            except Exception as e:
                st.error(f"❌ Chyba při importu: {e}")


def crm_notes_editor(business: Dict, db_manager) -> None:
    """CRM editor poznámek"""
    st.subheader("📝 Poznámky z hovorů")

    business_id = business.get("id")
    if not business_id:
        st.error("Business ID nenalezeno")
        return

    current_notes = business.get("call_notes", "")

    # Editor poznámek
    new_notes = st.text_area(
        "Poznámky z komunikace",
        value=current_notes,
        height=150,
        key=f"notes_{business_id}",
        placeholder="Zde zapište poznámky z hovoru, dohody, připomínky...",
    )

    # Tlačítko pro uložení
    if new_notes != current_notes:
        if st.button("💾 Uložit poznámky", key=f"save_notes_{business_id}"):
            if db_manager.update_call_info(business_id, call_notes=new_notes):
                st.success("Poznámky uloženy!")
                st.rerun()
            else:
                st.error("Chyba při ukládání poznámek")

    # Historie poznámek (pokud máme více záznamů)
    if current_notes:
        with st.expander("📋 Aktuální poznámky"):
            st.write(current_notes)


def crm_today_calls(db_manager) -> None:
    """Zobrazí dnešní hovory"""
    st.subheader("📞 Dnešní hovory")

    today_calls = db_manager.get_businesses_for_calls()

    if not today_calls:
        st.info("Žádné hovory nenaplánované na dnešní den")
        return

    st.write(f"📋 **Celkem k zavolání:** {len(today_calls)} podniků")

    # Zobrazit jako karty
    for business in today_calls[:10]:  # Zobrazit jen prvních 10
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.write(f"🏢 **{business.get('name', 'Neznámý')}**")
                st.write(f"📍 {business.get('address', 'Neznámá adresa')[:50]}...")
                if business.get("phone"):
                    st.write(f"📞 {business.get('phone')}")

            with col2:
                rating = business.get("rating", 0)
                if rating > 0:
                    st.metric(
                        "Hodnocení",
                        f"{rating} ⭐",
                        f"{business.get('review_count', 0)} recenzí",
                    )
                else:
                    st.metric("Hodnocení", "N/A")

                if business.get("call_notes"):
                    with st.expander("📝 Poznámky"):
                        st.write(
                            business["call_notes"][:200] + "..."
                            if len(business["call_notes"]) > 200
                            else business["call_notes"]
                        )

            with col3:
                if st.button("✅ Dokončit", key=f"done_today_{business.get('id')}"):
                    if db_manager.mark_call_completed(
                        business["id"], "Hovor dokončen z dashboardu"
                    ):
                        st.success(f"Hovor s {business['name']} dokončen!")
                        st.rerun()
                    else:
                        st.error("Chyba při dokončování hovoru")

            st.divider()

    if len(today_calls) > 10:
        st.info(f"... a dalších {len(today_calls) - 10} podniků")


def crm_stats_cards(db_manager) -> None:
    """Zobrazí CRM statistiky"""
    crm_stats = db_manager.get_crm_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        stat_card(
            "📞 Dnes", str(crm_stats.get("today_calls", 0)), "hovorů k zavolání", "📱"
        )

    with col2:
        stat_card(
            "📅 Zítra",
            str(crm_stats.get("tomorrow_calls", 0)),
            "hovorů naplánováno",
            "📅",
        )

    with col3:
        stat_card(
            "📝 Poznámky",
            str(crm_stats.get("with_notes", 0)),
            "podniků s poznámkami",
            "📝",
        )

    with col4:
        stat_card(
            "🔄 Kontakty",
            str(crm_stats.get("recent_contacts", 0)),
            "posledních 7 dní",
            "🔄",
        )


def crm_business_table(businesses: List[Dict], show_crm: bool = True) -> None:
    """Rozšířená tabulka podniků s CRM sloupci"""
    if not businesses:
        st.warning("Žádné podniky k zobrazení")
        return

    # Připravit data pro tabulku
    df_data = []
    for business in businesses:
        row = {
            "Název": business.get("name", "Neznámý"),
            "Adresa": business.get("address", "Neznámá"),
            "Telefon": business.get("phone", "Neznámý"),
            "Hodnocení": f"{business.get('rating', 0)} ⭐"
            if business.get("rating", 0) > 0
            else "N/A",
            "Web": "✅" if business.get("has_website") else "❌",
            "Status": business.get("status", "new"),
        }

        if show_crm:
            next_call = business.get("next_call_date", "")
            row["Další hovor"] = next_call if next_call else "Nenaplánováno"
            row["Poznámky"] = "📝" if business.get("call_notes") else ""
            row["Doména"] = business.get("domain_name", "")

        df_data.append(row)

    df = pd.DataFrame(df_data)

    # Konfigurace sloupců
    column_config = {
        "Název": st.column_config.TextColumn("Název", width="large"),
        "Adresa": st.column_config.TextColumn("Adresa", width="large"),
        "Telefon": st.column_config.TextColumn("Telefon", width="medium"),
        "Hodnocení": st.column_config.TextColumn("Hodnocení", width="small"),
        "Web": st.column_config.TextColumn("Web", width="small"),
        "Status": st.column_config.TextColumn("Status", width="small"),
    }

    if show_crm:
        column_config["Další hovor"] = st.column_config.TextColumn(
            "Další hovor", width="medium"
        )
        column_config["Poznámky"] = st.column_config.TextColumn(
            "Poznámky", width="small"
        )
        column_config["Doména"] = st.column_config.TextColumn("Doména", width="medium")

    # Zobrazit tabulku
    event = st.dataframe(
        df,
        use_container_width=True,
        column_config=column_config,
        hide_index=True,
    )

    return event
