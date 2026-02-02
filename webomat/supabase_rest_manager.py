#!/usr/bin/env python3
"""
Supabase REST API Manager pro Webomat
Vytváření tabulek přes HTTPS místo přímého PostgreSQL připojení
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

# Zkusíme importovat supabase klienta, pokud není dostupný, použijeme fallback
try:
    from supabase import create_client, Client

    SUPABASE_CLIENT_AVAILABLE = True
except ImportError:
    SUPABASE_CLIENT_AVAILABLE = False
    print("[WARNING] Supabase Python client neni dostupny, pouzivam fallback REST API")

# Načtení proměnných z .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

# Supabase REST API konfigurační proměnné
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", SUPABASE_SERVICE_ROLE_KEY)


class SupabaseRestManager:
    """Správce Supabase databáze přes REST API"""

    def __init__(self):
        if not SUPABASE_URL:
            raise ValueError("SUPABASE_URL nenalezen v .env souboru!")
        if not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY nenalezen v .env souboru!")

        self.base_url = SUPABASE_URL.rstrip("/")
        self.service_role_key = SUPABASE_SERVICE_ROLE_KEY
        self.anon_key = SUPABASE_ANON_KEY

        if SUPABASE_CLIENT_AVAILABLE:
            self.supabase: Client = create_client(
                supabase_url=self.base_url, supabase_key=self.service_role_key
            )
            print("[OK] Supabase client inicializovan")
        else:
            self.supabase = None

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.service_role_key}",
                "apikey": self.service_role_key,
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            }
        )

    def execute_sql(self, sql: str) -> dict:
        """Execute SQL přes Supabase REST API"""
        url = f"{self.base_url}/rest/v1/rpc/exec_sql"

        # Nejprve zkusíme, jestli endpoint existuje
        try:
            response = self.session.post(url, json={"sql": sql}, timeout=30)
            return {"success": response.status_code == 200, "response": response}
        except Exception as e:
            # Pokud RPC nefunguje, zkusíme přímý SQL endpoint
            return self._execute_sql_direct(sql)

    def _execute_sql_direct(self, sql: str) -> dict:
        """Execute SQL přes přímý endpoint (fallback)"""
        # Supabase má několik způsobů jak spustit SQL
        # Zkusíme GraphQL endpoint nebo jiné REST API

        # Pro DDL (CREATE TABLE, etc.) použijeme management API
        url = f"{self.base_url}/rest/v1/"

        # Rozdělíme SQL na jednotlivé příkazy
        statements = [s.strip() for s in sql.split(";") if s.strip()]

        results = []
        for statement in statements:
            if not statement:
                continue

            try:
                # Zkusíme použít GraphQL endpoint pro DDL
                gql_url = f"{self.base_url}/graphql/v1"
                gql_query = f"""
                mutation {{
                    execute(sql: "{statement.replace('"', '\\"').replace("\n", " ")}") {{
                        success
                        message
                    }}
                }}
                """

                response = self.session.post(
                    gql_url, json={"query": gql_query}, timeout=30
                )

                if response.status_code == 200:
                    results.append(
                        {
                            "statement": statement,
                            "success": True,
                            "response": response.json(),
                        }
                    )
                else:
                    results.append(
                        {
                            "statement": statement,
                            "success": False,
                            "error": response.text,
                        }
                    )

            except Exception as e:
                results.append(
                    {"statement": statement, "success": False, "error": str(e)}
                )

        return {"results": results}

    def test_connection(self) -> bool:
        """Test připojení k Supabase"""
        try:
            # Test přes REST API - zkusíme získat seznam tabulek
            response = self.session.get(f"{self.base_url}/rest/v1/", timeout=10)
            if response.status_code in [
                200,
                401,
                403,
                404,
            ]:  # 404 je normální pro prázdný endpoint
                print(
                    f"[OK] REST API pripojeni uspesne! Status: {response.status_code}"
                )
                return True
            else:
                print(
                    f"[ERROR] REST API chyba: {response.status_code} - {response.text}"
                )
                return False
        except Exception as e:
            print(f"[ERROR] Chyba pripojeni: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Chyba pripojeni: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Chyba pripojeni k REST API: {e}")
            return False

    def get_create_tables_sql(self) -> str:
        """Vrátí SQL pro vytvoření všech tabulek"""
        return """
-- Webomat Database Schema
-- Vytvoření všech tabulek pro CRM systém

-- 1. Prodejci (sellers)
CREATE TABLE IF NOT EXISTS sellers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_code VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    address TEXT,
    country VARCHAR(100) DEFAULT 'Czech Republic',
    date_of_birth DATE,
    onboarded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    contract_signed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'terminated')),
    terminated_at TIMESTAMP WITH TIME ZONE,
    commission_plan_id UUID,
    default_commission_rate DECIMAL(5,4) DEFAULT 0.15,
    payout_method VARCHAR(50) DEFAULT 'bank_transfer',
    bank_account_iban VARCHAR(50),
    last_payout_at TIMESTAMP WITH TIME ZONE,
    payout_balance_due DECIMAL(10,2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Firmy/Leady (businesses)
CREATE TABLE IF NOT EXISTS businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) DEFAULT 'manual',
    place_id VARCHAR(255) UNIQUE,
    name VARCHAR(255) NOT NULL,
    ico VARCHAR(50),
    vat_id VARCHAR(50),
    address_full TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'Czech Republic',
    lat DECIMAL(10,8),
    lng DECIMAL(11,8),
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(500),
    has_website BOOLEAN DEFAULT FALSE,
    rating DECIMAL(3,2),
    review_count INTEGER DEFAULT 0,
    price_level INTEGER,
    types JSONB DEFAULT '[]'::jsonb,
    editorial_summary TEXT,
    status_crm VARCHAR(50) DEFAULT 'new' CHECK (status_crm IN ('new', 'contacted', 'follow_up', 'interested', 'won', 'lost', 'do_not_contact')),
    status_reason TEXT,
    owner_seller_id UUID REFERENCES sellers(id),
    first_contact_at TIMESTAMP WITH TIME ZONE,
    last_contact_at TIMESTAMP WITH TIME ZONE,
    next_follow_up_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Kontaktní osoby (business_contacts)
CREATE TABLE IF NOT EXISTS business_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'other' CHECK (role IN ('owner', 'manager', 'receptionist', 'marketing', 'other')),
    email VARCHAR(255),
    phone VARCHAR(50),
    is_primary BOOLEAN DEFAULT FALSE,
    consent_status VARCHAR(20) DEFAULT 'unknown' CHECK (consent_status IN ('unknown', 'ok', 'do_not_contact')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. CRM aktivity (crm_activities)
CREATE TABLE IF NOT EXISTS crm_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    seller_id UUID REFERENCES sellers(id),
    contact_id UUID REFERENCES business_contacts(id),
    type VARCHAR(50) NOT NULL CHECK (type IN ('call', 'email', 'sms', 'whatsapp', 'meeting', 'note', 'other')),
    direction VARCHAR(20) CHECK (direction IN ('outbound', 'inbound')),
    subject VARCHAR(255),
    content TEXT,
    outcome VARCHAR(100),
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Úkoly (tasks)
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    assigned_to_seller_id UUID REFERENCES sellers(id),
    title VARCHAR(255) NOT NULL,
    due_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'done', 'cancelled')),
    priority VARCHAR(10) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 6. Web projekty (website_projects)
CREATE TABLE IF NOT EXISTS website_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    seller_id UUID REFERENCES sellers(id),
    status_web VARCHAR(50) DEFAULT 'brief' CHECK (status_web IN ('brief', 'in_progress', 'waiting_client', 'review', 'done', 'cancelled')),
    brief TEXT,
    domain VARCHAR(255),
    hosting VARCHAR(50) DEFAULT 'internal',
    tech_stack VARCHAR(100),
    started_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Projektové přílohy (project_assets)
CREATE TABLE IF NOT EXISTS project_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES website_projects(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('logo', 'photos', 'contract', 'brief', 'invoice', 'other')),
    file_path TEXT,
    filename VARCHAR(255),
    mime_type VARCHAR(100),
    size_bytes INTEGER,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    uploaded_by UUID REFERENCES sellers(id)
);

-- 8. Faktury klientům (client_invoices)
CREATE TABLE IF NOT EXISTS client_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    business_id UUID NOT NULL REFERENCES businesses(id),
    project_id UUID REFERENCES website_projects(id),
    issued_at DATE NOT NULL,
    due_at DATE NOT NULL,
    currency VARCHAR(3) DEFAULT 'CZK',
    subtotal DECIMAL(10,2) NOT NULL,
    vat DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'paid', 'overdue', 'cancelled')),
    paid_at TIMESTAMP WITH TIME ZONE,
    payment_method VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. Položky faktur (client_invoice_items)
CREATE TABLE IF NOT EXISTS client_invoice_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES client_invoices(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    qty DECIMAL(10,2) NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    vat_rate DECIMAL(5,4) DEFAULT 0.21,
    total DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. Provize (commissions)
CREATE TABLE IF NOT EXISTS commissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID NOT NULL REFERENCES sellers(id),
    business_id UUID REFERENCES businesses(id),
    project_id UUID REFERENCES website_projects(id),
    invoice_id UUID REFERENCES client_invoices(id),
    plan_id UUID,
    base_amount DECIMAL(10,2) NOT NULL,
    commission_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CZK',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'eligible', 'paid', 'void')),
    eligible_at TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 11. Výplaty (payouts)
CREATE TABLE IF NOT EXISTS payouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID NOT NULL REFERENCES sellers(id),
    period_from DATE NOT NULL,
    period_to DATE NOT NULL,
    currency VARCHAR(3) DEFAULT 'CZK',
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'sent', 'paid', 'cancelled')),
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 12. Položky výplat (payout_items)
CREATE TABLE IF NOT EXISTS payout_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payout_id UUID NOT NULL REFERENCES payouts(id) ON DELETE CASCADE,
    commission_id UUID NOT NULL REFERENCES commissions(id),
    amount DECIMAL(10,2) NOT NULL
);

-- Indexy pro výkon
CREATE INDEX IF NOT EXISTS idx_businesses_owner_seller ON businesses(owner_seller_id);
CREATE INDEX IF NOT EXISTS idx_businesses_status_crm ON businesses(status_crm);
CREATE INDEX IF NOT EXISTS idx_businesses_next_follow_up ON businesses(next_follow_up_at);
CREATE INDEX IF NOT EXISTS idx_contacts_business ON business_contacts(business_id);
CREATE INDEX IF NOT EXISTS idx_crm_activities_business ON crm_activities(business_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_crm_activities_seller ON crm_activities(seller_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_business ON tasks(business_id);
CREATE INDEX IF NOT EXISTS idx_projects_business ON website_projects(business_id);
CREATE INDEX IF NOT EXISTS idx_invoices_business ON client_invoices(business_id);
CREATE INDEX IF NOT EXISTS idx_commissions_seller ON commissions(seller_id);
"""

    def create_tables(self) -> bool:
        """Vytvoření všech tabulek - zobrazí SQL pro ruční spuštění v Supabase Dashboard"""
        print("[INFO] Pripravuji SQL pro vytvoreni databazovych tabulek...")
        print(
            "[INFO] Zkopiruj nasledujici SQL do Supabase Dashboard -> SQL Editor a spust ho:"
        )
        print()
        print("=" * 80)

        sql = self.get_create_tables_sql()
        print(sql)

        print("=" * 80)
        print()
        print("[INFO] Postup:")
        print(
            "1. Otevri https://supabase.com/dashboard/project/cmtvixayfbqhdlftsgqg/sql"
        )
        print("2. Vloz vyse uvedeny SQL kod")
        print("3. Klikni 'Run' nebo stiskni Ctrl+Enter")
        print("4. Po dokonceni zavolej: python supabase_rest_manager.py verify")
        print()
        return True

    def verify_tables(self) -> bool:
        """Ověří, že všechny tabulky byly vytvořeny"""
        expected_tables = [
            "sellers",
            "businesses",
            "business_contacts",
            "crm_activities",
            "tasks",
            "website_projects",
            "project_assets",
            "client_invoices",
            "client_invoice_items",
            "commissions",
            "payouts",
            "payout_items",
        ]

        print("[INFO] Overuji vytvoreni tabulek...")

        try:
            if self.supabase:
                # Zkusíme select z každé tabulky
                for table in expected_tables:
                    try:
                        result = (
                            self.supabase.table(table).select("id").limit(1).execute()
                        )
                        print(f"[OK] Tabulka '{table}' existuje")
                    except Exception as e:
                        print(f"[ERROR] Tabulka '{table}' chyba: {e}")
                        return False
            else:
                # Fallback - zkusíme REST API
                for table in expected_tables:
                    try:
                        response = self.session.get(
                            f"{self.base_url}/rest/v1/{table}?select=id&limit=1"
                        )
                        if response.status_code == 200:
                            print(f"[OK] Tabulka '{table}' existuje")
                        else:
                            print(
                                f"[ERROR] Tabulka '{table}' chyba: {response.status_code}"
                            )
                            return False
                    except Exception as e:
                        print(f"[ERROR] Tabulka '{table}' chyba: {e}")
                        return False

            print("[OK] Vsechny tabulky uspesne overeny!")
            return True

        except Exception as e:
            print(f"[ERROR] Chyba pri overovani tabulek: {e}")
            return False


def test_rest_connection():
    """Test připojení přes REST API"""
    try:
        manager = SupabaseRestManager()
        success = manager.test_connection()
        if success:
            print("[OK] REST API pripojeni funguje!")
        else:
            print("[ERROR] REST API pripojeni selhalo!")
        return success
    except Exception as e:
        print(f"[ERROR] Chyba pri testovani REST API: {e}")
        return False


def create_tables_rest():
    """Vytvoření tabulek přes REST API"""
    try:
        manager = SupabaseRestManager()
        success = manager.create_tables()
        return success
    except Exception as e:
        print(f"[ERROR] Chyba pri vytvareni tabulek pres REST API: {e}")
        return False


def verify_tables_rest():
    """Ověření tabulek"""
    try:
        manager = SupabaseRestManager()
        if not manager.test_connection():
            return False
        success = manager.verify_tables()
        return success
    except Exception as e:
        print(f"[ERROR] Chyba pri overovani tabulek: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_rest_connection()
    elif len(sys.argv) > 1 and sys.argv[1] == "create":
        if test_rest_connection():
            create_tables_rest()
    elif len(sys.argv) > 1 and sys.argv[1] == "verify":
        verify_tables_rest()
    else:
        print("Pouziti:")
        print("  python supabase_rest_manager.py test    - test pripojeni")
        print(
            "  python supabase_rest_manager.py create  - zobraz SQL pro vytvoreni tabulek"
        )
        print("  python supabase_rest_manager.py verify  - over vytvoreni tabulek")
