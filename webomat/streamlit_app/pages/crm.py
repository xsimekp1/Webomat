"""
CRM page for Streamlit app - Simple client overview
"""

import streamlit as st
from datetime import datetime
from components.ui_components import crm_business_table
from utils.database import db


def crm_page():
    """CRM page - simple client overview table"""
    st.header("📞 CRM - Přehled klientů")

    try:
        # Načíst všechny klienty
        all_clients = db.get_all_businesses()

        if not all_clients:
            st.info("Žádní klienti v databázi")
            return

        st.write(f"📊 **Celkem klientů:** {len(all_clients)}")

        # Filtrovat podle uživatele (pokud je nastavený)
        current_user = st.session_state.get("current_user")

        if current_user:
            # Zobrazit jen klienty přiřazené tomuto uživateli
            user_clients = [
                c for c in all_clients if c.get("assigned_user") == current_user
            ]
            other_clients = [
                c for c in all_clients if c.get("assigned_user") != current_user
            ]

            if user_clients:
                st.subheader(f"👤 Vaši klienti ({len(user_clients)})")
                crm_business_table(user_clients, show_crm=True)

                if other_clients:
                    st.markdown("---")
                    with st.expander(f"👥 Ostatní klienti ({len(other_clients)})"):
                        crm_business_table(other_clients, show_crm=True)
            else:
                st.warning(
                    f"Nemáte přiřazené žádné klienty. Zadejte své jméno: **{current_user}**"
                )
                crm_business_table(all_clients, show_crm=True)
        else:
            # Zobrazit všechny klienty
            crm_business_table(all_clients, show_crm=True)

        # Rychlá akce - označit klienta jako dokončeného
        st.markdown("---")
        st.subheader("⚡ Rychlé akce")

        # Výběr klienta
        client_names = [
            f"{c.get('name', 'Neznámý')} - {c.get('address', '')[:30]}"
            for c in all_clients
        ]
        selected_client_idx = st.selectbox(
            "Vyberte klienta pro akci:",
            range(len(client_names)),
            format_func=lambda i: client_names[i],
            key="crm_client_select",
        )

        if selected_client_idx is not None:
            selected_client = all_clients[selected_client_idx]

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button(
                    "✅ Označit jako dokončený", key=f"complete_{selected_client['id']}"
                ):
                    if db.mark_call_completed(
                        selected_client["id"], "Označeno jako dokončené z CRM"
                    ):
                        st.success(
                            f"✅ Klient {selected_client['name']} označen jako dokončený!"
                        )
                        st.rerun()
                    else:
                        st.error("Chyba při označování klienta")

            with col2:
                if st.button(
                    "📞 Naplánovat hovor dnes",
                    key=f"call_today_{selected_client['id']}",
                ):
                    today = datetime.now().strftime("%Y-%m-%d")
                    if db.update_call_info(selected_client["id"], next_call_date=today):
                        st.success(
                            f"📞 Hovor s {selected_client['name']} naplánován na dnešní den!"
                        )
                        st.rerun()
                    else:
                        st.error("Chyba při plánování hovoru")

            with col3:
                if st.button(
                    "👤 Přiřadit mě", key=f"assign_me_{selected_client['id']}"
                ):
                    if current_user:
                        try:
                            import sqlite3

                            with sqlite3.connect(db.db_path) as conn:
                                cursor = conn.cursor()
                                cursor.execute(
                                    "UPDATE businesses SET assigned_user = ? WHERE id = ?",
                                    (current_user, selected_client["id"]),
                                )
                                conn.commit()
                            st.success(
                                f"👤 Klient {selected_client['name']} přiřazen vám ({current_user})!"
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"Chyba při přiřazování: {e}")
                    else:
                        st.warning("Nejdříve zadejte své jméno nahoře")

    except Exception as e:
        st.error(f"Chyba při načítání CRM dat: {e}")
        import traceback

        st.code(traceback.format_exc())
