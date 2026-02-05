#!/usr/bin/env python3
"""
Seed testovací data pro vsechny obchodniky - vytvoří ledger entries pro otestování dashboardu
"""

import os
import sys
from supabase import create_client, Client


def get_supabase():
    """Získá Supabase client z environment proměnných"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print(
            "CHYBA: Chybí SUPABASE_URL nebo SUPABASE_SERVICE_ROLE_KEY environment proměnné"
        )
        return None

    return create_client(supabase_url, supabase_key)


def get_seller_ids():
    """Ziska vsechny seller IDs pro seedovani"""
    supabase = create_client()

    # Najdi vsechny aktivni sellers
    result = (
        supabase.table("sellers")
        .select("id, email, first_name")
        .eq("is_active", True)
        .execute()
    )

    if result.data:
        seller_ids = [(seller["id"], seller["first_name"]) for seller in result.data]
        print(f"OK Nalezeno {len(seller_ids)} aktivnich sellers:")
        for seller_id, name in seller_ids:
            print(f"   - {name} (ID: {seller_id})")
        return seller_ids, supabase
    else:
        print("CHYBA Zadne aktivni sellers v tabulce")
        return [], supabase


def seed_ledger_entries(supabase: Client, seller_id: str):
    """Vytvoří testovací ledger entries pro Andreyho"""

    # Smazat existující testovací data
    supabase.table("ledger_entries").delete().eq("is_test", True).execute()
    print("Smazany existujici testovaci ledger entries")

    # Vytvořit testovací pohyby
    entries = [
        {
            "seller_id": seller_id,
            "entry_type": "commission_earned",
            "amount": 12000.0,  # NÁROKY: 12,250 CZK
            "description": "Test provize z Webomat projektu",
            "related_business_id": None,
            "related_project_id": None,
            "is_test": True,
            "created_at": "2025-01-15T10:00:00Z",
            "created_by": seller_id,
        },
        {
            "seller_id": seller_id,
            "entry_type": "admin_adjustment",
            "amount": 250.0,  # Malý admin adjustment (narůstá)
            "description": "Korekce výpočtu provize",
            "is_test": True,
            "created_at": "2025-01-16T14:00:00Z",
            "created_by": seller_id,
        },
        {
            "seller_id": seller_id,
            "entry_type": "payout_paid",
            "amount": -5000.0,  # VÝPLATY: 5,000 CZK (záporné = výdej)
            "description": "Výplata za leden 2025",
            "is_test": True,
            "created_at": "2025-01-31T16:00:00Z",
            "created_by": seller_id,
        },
    ]

    # Vložit všechny entries
    for i, entry in enumerate(entries, 1):
        try:
            result = supabase.table("ledger_entries").insert(entry).execute()
            print(
                f"✅ Vytvořen ledger entry #{i}: {entry['entry_type']} = {entry['amount']} CZK"
            )
        except Exception as e:
            print(f"❌ Chyba při vytváření ledger entry #{i}: {e}")
            return False

    print(f"📊 Vytvořeno {len(entries)} ledger entries pro Andreyho")
    return True


def verify_balance(supabase: Client, seller_id: str):
    """Ověří správnost balance výpočtu"""

    # Načti všechny entries pro Andreyho
    result = (
        supabase.table("ledger_entries")
        .select("*")
        .eq("seller_id", seller_id)
        .eq("is_test", True)
        .execute()
    )

    if not result.data:
        print("❌ Žádná data k ověření")
        return

    # Vypočít balance
    total_earned = sum(
        e["amount"] for e in result.data if e["entry_type"] == "commission_earned"
    )
    admin_adjustments = sum(
        e["amount"] for e in result.data if e["entry_type"] == "admin_adjustment"
    )
    total_paid_out = abs(
        sum(e["amount"] for e in result.data if e["entry_type"] == "payout_paid")
    )

    available_balance = total_earned + admin_adjustments - total_paid_out

    print(f"\n📊 Souhrn pro Andreyho:")
    print(f"   NÁROKY: {total_earned} CZK")
    print(f"   Admin úpravy: {admin_adjustments} CZK")
    print(f"   VÝPLATY: {total_paid_out} CZK")
    print(f"   nárok na vyplacení: {available_balance} CZK")
    print(f"   Očekávaný výsledek: 8,250 CZK")
    print(f"   Aktuální výsledek: {available_balance} CZK")

    if abs(available_balance - 8250) < 0.01:  # tolerance 1 haléř
        print("✅ Balance výpočet je správný!")
    else:
        print("❌ Balance výpočet je špatný!")


def main():
    print("Seedovani testovacich dat pro vsechny obchodniky...")

    # Ziskat Supabase client a vsechny seller IDs
    seller_ids, supabase = get_seller_ids()

    if not seller_ids:
        print("CHYBA Nelze pokracovat bez seller IDs")
        return 1

    # Vytvořit ledger entries pro všechny sellers
    success_count = 0
    for seller_id, seller_name in seller_ids:
        print(f"\n📊 Zpracovávám {seller_name}...")
        if seed_ledger_entries(supabase, seller_id):
            success_count += 1
            verify_balance(supabase, seller_id)

    print(f"\n✅ Hotovo! Zpracováno {success_count} ze {len(seller_ids)} sellers")
    print(f"🌐 Dashboard URL: https://webomat.vercel.app/en/dashboard")
    print("📱 Všichni sellers by se se měli přihlásit a vidět data v dashboardu")

    return 0


if __name__ == "__main__":
    exit(main())
