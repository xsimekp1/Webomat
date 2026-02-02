"""
Seed script pro přidání mock ledger entries pro Andy a Iru.

Spuštění: python scripts/seed_ledger_entries.py
"""
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load .env from backend directory
load_dotenv('backend/.env')

sys.path.insert(0, 'backend')

from app.database import get_supabase

# User IDs
ANDY_ID = "ad2bcf07-9f96-43f4-abb6-fbb0fbf700f6"
IRA_ID = "cc480355-6bb4-40da-82d5-c95238536f53"

def create_ledger_entries():
    """Create mock ledger entries for Andy and Ira."""
    s = get_supabase()

    now = datetime.utcnow()

    entries = [
        # ===== ANDY =====
        # Provize za projekty
        {
            "seller_id": ANDY_ID,
            "entry_type": "commission_earned",
            "amount": 3000.0,
            "description": "Provize za projekt Restaurace U Pepíka - balíček Profi",
            "notes": "Klient zaplatil jednorázovou platbu",
            "is_test": False,
            "created_at": (now - timedelta(days=45)).isoformat(),
        },
        {
            "seller_id": ANDY_ID,
            "entry_type": "commission_earned",
            "amount": 1500.0,
            "description": "Provize za projekt Kadeřnictví Styl - balíček Start",
            "notes": None,
            "is_test": False,
            "created_at": (now - timedelta(days=30)).isoformat(),
        },
        {
            "seller_id": ANDY_ID,
            "entry_type": "commission_earned",
            "amount": 5000.0,
            "description": "Provize za projekt AutoServis Novák - balíček Premium",
            "notes": "Velký projekt s rozšířenou funkcionalitou",
            "is_test": False,
            "created_at": (now - timedelta(days=14)).isoformat(),
        },
        {
            "seller_id": ANDY_ID,
            "entry_type": "commission_earned",
            "amount": 500.0,
            "description": "Měsíční provize - Restaurace U Pepíka",
            "notes": "Opakovaná měsíční platba",
            "is_test": False,
            "created_at": (now - timedelta(days=7)).isoformat(),
        },
        # Admin úprava
        {
            "seller_id": ANDY_ID,
            "entry_type": "admin_adjustment",
            "amount": 500.0,
            "description": "Bonus za získání 3 klientů v měsíci",
            "notes": "Schváleno vedením",
            "is_test": False,
            "created_at": (now - timedelta(days=20)).isoformat(),
        },
        # Výplata
        {
            "seller_id": ANDY_ID,
            "entry_type": "payout_paid",
            "amount": -4000.0,
            "description": "Výplata provizí - leden 2025",
            "notes": "Převod na účet",
            "is_test": False,
            "created_at": (now - timedelta(days=25)).isoformat(),
        },

        # ===== IRA =====
        # Provize za projekty
        {
            "seller_id": IRA_ID,
            "entry_type": "commission_earned",
            "amount": 2500.0,
            "description": "Provize za projekt Pekárna Sladká - balíček Profi",
            "notes": None,
            "is_test": False,
            "created_at": (now - timedelta(days=60)).isoformat(),
        },
        {
            "seller_id": IRA_ID,
            "entry_type": "commission_earned",
            "amount": 4500.0,
            "description": "Provize za projekt Fitness Centrum Power - balíček Premium",
            "notes": "Klient přešel z konkurence",
            "is_test": False,
            "created_at": (now - timedelta(days=35)).isoformat(),
        },
        {
            "seller_id": IRA_ID,
            "entry_type": "commission_earned",
            "amount": 1000.0,
            "description": "Provize za projekt Květinářství Rosa - balíček Start",
            "notes": None,
            "is_test": False,
            "created_at": (now - timedelta(days=21)).isoformat(),
        },
        {
            "seller_id": IRA_ID,
            "entry_type": "commission_earned",
            "amount": 750.0,
            "description": "Měsíční provize - Fitness Centrum Power",
            "notes": None,
            "is_test": False,
            "created_at": (now - timedelta(days=5)).isoformat(),
        },
        {
            "seller_id": IRA_ID,
            "entry_type": "commission_earned",
            "amount": 3500.0,
            "description": "Provize za projekt IT Solutions s.r.o. - balíček Custom",
            "notes": "Speciální požadavky klienta",
            "is_test": False,
            "created_at": (now - timedelta(days=3)).isoformat(),
        },
        # Admin úpravy
        {
            "seller_id": IRA_ID,
            "entry_type": "admin_adjustment",
            "amount": 1000.0,
            "description": "Bonus za nejlepší obchodník měsíce",
            "notes": "Prosinec 2024",
            "is_test": False,
            "created_at": (now - timedelta(days=40)).isoformat(),
        },
        {
            "seller_id": IRA_ID,
            "entry_type": "admin_adjustment",
            "amount": -200.0,
            "description": "Korekce provize - chybný výpočet",
            "notes": "Oprava z minulého měsíce",
            "is_test": False,
            "created_at": (now - timedelta(days=15)).isoformat(),
        },
        # Výplaty
        {
            "seller_id": IRA_ID,
            "entry_type": "payout_reserved",
            "amount": -3000.0,
            "description": "Rezervace pro výplatu - prosinec",
            "notes": "Čeká na schválení",
            "is_test": False,
            "created_at": (now - timedelta(days=50)).isoformat(),
        },
        {
            "seller_id": IRA_ID,
            "entry_type": "payout_paid",
            "amount": -3000.0,
            "description": "Výplata provizí - prosinec 2024",
            "notes": "Převod na účet",
            "is_test": False,
            "created_at": (now - timedelta(days=45)).isoformat(),
        },
        {
            "seller_id": IRA_ID,
            "entry_type": "payout_paid",
            "amount": -2000.0,
            "description": "Výplata provizí - leden 2025",
            "notes": "Převod na účet",
            "is_test": False,
            "created_at": (now - timedelta(days=10)).isoformat(),
        },
    ]

    print(f"Vkladam {len(entries)} zaznamu do ledger_entries...")

    for entry in entries:
        try:
            result = s.table("ledger_entries").insert(entry).execute()
            if result.data:
                print(f"  [OK] {entry['entry_type']}: {entry['amount']} - {entry['description'][:50]}...")
            else:
                print(f"  [ERR] Chyba pri vkladani: {entry['description'][:50]}...")
        except Exception as e:
            print(f"  [ERR] Chyba: {e}")

    print("\nHotovo!")

    # Zobraz souhrn
    print("\n=== SOUHRN ===")

    for seller_id, name in [(ANDY_ID, "Andy"), (IRA_ID, "Ira")]:
        result = s.table("ledger_entries").select("amount, entry_type").eq("seller_id", seller_id).execute()

        total = sum(e["amount"] for e in result.data)
        earned = sum(e["amount"] for e in result.data if e["entry_type"] == "commission_earned")
        adjustments = sum(e["amount"] for e in result.data if e["entry_type"] == "admin_adjustment")
        payouts = sum(e["amount"] for e in result.data if e["entry_type"] in ["payout_paid", "payout_reserved"])

        print(f"\n{name}:")
        print(f"  Provize:     {earned:,.0f} CZK")
        print(f"  Upravy:      {adjustments:+,.0f} CZK")
        print(f"  Vyplaty:     {payouts:,.0f} CZK")
        print(f"  ---------------------")
        print(f"  Zustatek:    {total:,.0f} CZK")


if __name__ == "__main__":
    create_ledger_entries()
