"""
Help page for Streamlit app
"""

import streamlit as st


def help_page():
    """Help page with platform overview and guides"""
    st.header("❓ Nápověda")

    # Tabs for different help sections
    tab1, tab2, tab3 = st.tabs(
        ["Přehled platformy", "Workflow", "Často kladené otázky"]
    )

    with tab1:
        overview_section()

    with tab2:
        workflow_section()

    with tab3:
        faq_section()


def overview_section():
    """Platform overview section"""
    st.markdown("""
    ## Co je Webomat

    Webomat je platforma pro:
    - **sběr leadů / kontaktů** (firmy, které typicky nemají web, ale mají dobré hodnocení)
    - **řízení obchodního procesu** (CRM: kontakt → deal/projekt → follow-up)
    - **automatizovanou tvorbu webu** (generování webové stránky pomocí AI)
    - **správu verzí webu** pod jedním projektem
    - a do budoucna **fakturaci a provize** (pro klienty i obchodníky)
    """)


def workflow_section():
    """Workflow explanation"""
    st.markdown("""
    ## Jak vypadá tok práce

    ### A) Získání kontaktu
    Kontakt může přijít z více zdrojů:
    - **automaticky** (Webomat skript hledá podniky z Google Places a filtruje dle ratingu / recenzí)
    - **ručně** (někdo zadá kontakt v UI)

    ### B) CRM kvalifikace
    Na kontaktu držíme identifikační info, stav v CRM, plánování, vlastníka, poznámky.

    ### C) Deal / Projekt
    Z kontaktu vznikne Deal (obchodní případ) a klient může mít více projektů.

    ### D) Zadání webu a generování
    Zadání obsahuje text, inspirace, assety. Generování vytvoří verzi webu.
    """)


def faq_section():
    """FAQ section"""
    st.markdown("""
    ## Často kladené otázky

    ### Proč některé kontakty nevidím?
    - můžeš mít filtr (status, owner)
    - nebo kontakt patří jinému obchodníkovi

    ### Jak poznám, že je něco testovací?
    - test záznamy označit štítkem "TEST"

    ### Proč mi nejde vygenerovat web?
    - můžeš být reviewer → generování zablokované
    - nebo není vyplněné zadání
    """)
