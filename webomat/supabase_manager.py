#!/usr/bin/env python3
"""
Supabase Database Manager pro Webomat
CLI nástroj pro správu PostgreSQL databáze na Supabase
"""

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import click
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

# Načtení proměnných z .env
# Najít .env soubor v aktuálním adresáři nebo nadřazených
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Zkusit načíst z nadřazeného adresáře
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()  # Fallback na výchozí chování

# Supabase konfigurační proměnné
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # Přidat timeout parametry k DATABASE_URL
    if "?" in DATABASE_URL:
        SUPABASE_CONFIG = {"dsn": f"{DATABASE_URL}&connect_timeout=30"}
    else:
        SUPABASE_CONFIG = {"dsn": f"{DATABASE_URL}?connect_timeout=30"}
else:
    SUPABASE_CONFIG = {
        "host": os.getenv("SUPABASE_HOST"),
        "port": os.getenv("SUPABASE_PORT"),
        "dbname": os.getenv("SUPABASE_DBNAME"),
        "user": os.getenv("SUPABASE_USER"),
        "password": os.getenv("SUPABASE_PASSWORD"),
        "sslmode": os.getenv("SUPABASE_SSLMODE", "require"),
        "connect_timeout": 30,  # 30 sekund timeout
    }


class SupabaseManager:
    """Správce PostgreSQL databáze na Supabase"""

    def __init__(self):
        self.connection_pool = None
        self._init_connection_pool()

    def _init_connection_pool(self):
        """Inicializace connection poolu"""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1, maxconn=10, **SUPABASE_CONFIG
            )
            print("[OK] Connection pool inicializovan")
        except Exception as e:
            print(f"[ERROR] Chyba pri inicializaci connection poolu: {e}")
            sys.exit(1)

    def get_connection(self):
        """Získání připojení z poolu"""
        try:
            return self.connection_pool.getconn()
        except Exception as e:
            print(f"❌ Chyba při získávání připojení: {e}")
            return None

    def release_connection(self, conn):
        """Vrácení připojení do poolu"""
        if conn and self.connection_pool:
            self.connection_pool.putconn(conn)

    def test_connection(self) -> bool:
        """Test připojení k databázi"""
        conn = None
        try:
            conn = self.get_connection()
            if not conn:
                return False

            cursor = conn.cursor()
            cursor.execute("SELECT NOW();")
            result = cursor.fetchone()
            cursor.close()

            print(f"[OK] Pripojeni uspesne! Aktualni cas: {result[0]}")
            return True

        except Exception as e:
            print(f"[ERROR] Chyba pripojeni: {e}")
            return False
        finally:
            if conn:
                self.release_connection(conn)

    def create_tables(self):
        """Vytvoření všech tabulek podle navrhované struktury"""
        conn = None
        try:
            conn = self.get_connection()
            if not conn:
                return False

            cursor = conn.cursor()

            # 1. Prodejci (sellers)
            cursor.execute("""
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
            """)

            # 2. Firmy/Leady (businesses)
            cursor.execute("""
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
            """)

            # 3. Kontaktní osoby (business_contacts)
            cursor.execute("""
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
            """)

            # 4. CRM aktivity (crm_activities)
            cursor.execute("""
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
            """)

            # 5. Úkoly (tasks)
            cursor.execute("""
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
            """)

            # 6. Web projekty (website_projects)
            cursor.execute("""
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
            """)

            # 7. Projektové přílohy (project_assets)
            cursor.execute("""
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
            """)

            # 8. Faktury klientům (client_invoices)
            cursor.execute("""
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
            """)

            # 9. Položky faktur (client_invoice_items)
            cursor.execute("""
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
            """)

            # 10. Provize (commissions)
            cursor.execute("""
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
            """)

            # 11. Výplaty (payouts)
            cursor.execute("""
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
            """)

            # 12. Položky výplat (payout_items)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payout_items (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    payout_id UUID NOT NULL REFERENCES payouts(id) ON DELETE CASCADE,
                    commission_id UUID NOT NULL REFERENCES commissions(id),
                    amount DECIMAL(10,2) NOT NULL
                );
            """)

            # Indexy pro výkon
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_businesses_owner_seller ON businesses(owner_seller_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_businesses_status_crm ON businesses(status_crm);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_businesses_next_follow_up ON businesses(next_follow_up_at);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_contacts_business ON business_contacts(business_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_crm_activities_business ON crm_activities(business_id, occurred_at DESC);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_crm_activities_seller ON crm_activities(seller_id, occurred_at DESC);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_business ON tasks(business_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_projects_business ON website_projects(business_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_invoices_business ON client_invoices(business_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_commissions_seller ON commissions(seller_id);"
            )

            conn.commit()
            print("[OK] Vsechny tabulky uspesne vytvoreny!")
            return True

        except Exception as e:
            print(f"[ERROR] Chyba pri vytvareni tabulek: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.release_connection(conn)

    def get_table_stats(self) -> Dict[str, int]:
        """Získání počtu záznamů v každé tabulce"""
        tables = [
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

        stats = {}
        conn = None

        try:
            conn = self.get_connection()
            if not conn:
                return {}

            cursor = conn.cursor()

            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cursor.fetchone()[0]
                    stats[table] = count
                except Exception as e:
                    print(f"[WARN] Chyba pri cteni tabulky {table}: {e}")
                    stats[table] = -1  # Indikuje chybu

            return stats

        except Exception as e:
            print(f"[ERROR] Chyba pri ziskavani statistik: {e}")
            return {}
        finally:
            if conn:
                self.release_connection(conn)

    def reset_database(self) -> bool:
        """Reset databáze - smazání všech tabulek a znovu vytvoření"""
        conn = None
        try:
            conn = self.get_connection()
            if not conn:
                return False

            cursor = conn.cursor()

            # Seznam tabulek v pořadí kvůli cizím klíčům
            tables = [
                "payout_items",
                "payouts",
                "commissions",
                "client_invoice_items",
                "client_invoices",
                "project_assets",
                "website_projects",
                "tasks",
                "crm_activities",
                "business_contacts",
                "businesses",
                "sellers",
            ]

            # DROP tabulky
            for table in tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                    print(f"[OK] Tabulka {table} smazana")
                except Exception as e:
                    print(f"[WARN] Chyba pri mazani {table}: {e}")

            conn.commit()

            # Znovu vytvoření tabulek
            return self.create_tables()

        except Exception as e:
            print(f"[ERROR] Chyba pri resetu databaze: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.release_connection(conn)

    def show_table_records(self, table_name: str, limit: int = 10) -> bool:
        """Zobrazení záznamů z tabulky (omezeno limitem)"""
        conn = None
        try:
            conn = self.get_connection()
            if not conn:
                return False

            cursor = conn.cursor()

            # Získání sloupců tabulky
            cursor.execute(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """,
                (table_name,),
            )

            columns = cursor.fetchall()
            if not columns:
                print(f"[ERROR] Tabulka '{table_name}' neexistuje!")
                return False

            # Zobrazení struktury tabulky
            print(f"\n📋 Záznamy z tabulky '{table_name}' (limit: {limit}):")
            print("=" * 80)

            # Header
            header = " | ".join(
                [f"{col[0]:<20}" for col in columns[:5]]
            )  # Max 5 sloupců pro čitelnost
            if len(columns) > 5:
                header += " | ..."
            print(header)
            print("-" * len(header))

            # Získání dat
            cursor.execute(f"SELECT * FROM {table_name} LIMIT %s;", (limit,))
            rows = cursor.fetchall()

            if not rows:
                print("(žádné záznamy)")
                return True

            # Zobrazení dat
            for row in rows:
                row_str = ""
                for i, value in enumerate(row[:5]):  # Max 5 sloupců
                    if value is None:
                        display_value = "NULL"
                    elif isinstance(value, (int, float)):
                        display_value = str(value)
                    elif isinstance(value, str) and len(value) > 20:
                        display_value = value[:17] + "..."
                    else:
                        display_value = str(value)
                    row_str += f"{display_value:<20} | "
                if len(row) > 5:
                    row_str += "..."
                print(row_str.rstrip(" | "))

            if len(rows) == limit:
                print(f"\n(Zobrazeno prvních {limit} záznamů, může jich být více)")

            return True

        except Exception as e:
            print(f"[ERROR] Chyba pri cteni tabulky {table_name}: {e}")
            return False
        finally:
            if conn:
                self.release_connection(conn)

    def insert_test_record(self, table_name: str) -> bool:
        """Vložení testovacího záznamu do tabulky s generováním dat podle datových typů"""
        conn = None
        try:
            conn = self.get_connection()
            if not conn:
                return False

            cursor = conn.cursor()

            # Získání sloupců tabulky
            cursor.execute(
                """
                SELECT column_name, data_type, is_nullable, column_default, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position;
            """,
                (table_name,),
            )

            columns = cursor.fetchall()
            if not columns:
                print(f"[ERROR] Tabulka '{table_name}' neexistuje!")
                return False

            # Příprava dat pro insert
            insert_columns = []
            insert_values = []
            placeholders = []

            for col_name, data_type, is_nullable, default_value, max_length in columns:
                # Přeskočit sloupce s default hodnotou nebo auto-generované
                if col_name == "id" and (
                    default_value and "gen_random_uuid" in default_value
                ):
                    continue
                if default_value and "NOW()" in default_value.upper():
                    continue
                if "created_at" in col_name or "updated_at" in col_name:
                    continue

                insert_columns.append(col_name)

                # Generování testovacích dat podle datového typu
                if data_type == "uuid":
                    value = str(uuid.uuid4())
                elif data_type in ("varchar", "character varying", "text"):
                    max_len = max_length or 100
                    value = f"Test {col_name}"[:max_len]
                elif data_type == "integer":
                    value = 1
                elif data_type == "bigint":
                    value = 1000
                elif data_type in ("numeric", "decimal"):
                    value = 99.99
                elif data_type == "boolean":
                    value = True
                elif data_type == "date":
                    value = datetime.now().date()
                elif data_type == "timestamp without time zone":
                    value = datetime.now()
                elif data_type == "timestamp with time zone":
                    value = datetime.now()
                elif data_type == "jsonb":
                    value = '{"test": "data"}'
                else:
                    # Pro neznámé typy použít NULL pokud je nullable
                    if is_nullable == "YES":
                        value = None
                    else:
                        value = f"test_{data_type}"

                insert_values.append(value)
                placeholders.append("%s")

            if not insert_columns:
                print(f"[WARN] Žádné sloupce pro insert v tabulce '{table_name}'")
                return True

            # Sestavení a spuštění INSERT dotazu
            columns_str = ", ".join(insert_columns)
            placeholders_str = ", ".join(placeholders)
            query = (
                f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders_str})"
            )

            cursor.execute(query, insert_values)
            conn.commit()

            print(f"[OK] Testovací záznam vložen do tabulky '{table_name}'")
            print(f"   Vložené sloupce: {', '.join(insert_columns)}")
            return True

        except Exception as e:
            print(
                f"[ERROR] Chyba pri vkladani testovacího záznamu do {table_name}: {e}"
            )
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.release_connection(conn)


# CLI Interface pomocí Click
@click.group()
def cli():
    """Supabase Database Manager pro Webomat"""
    pass


@cli.command()
def connect():
    """Test připojení k Supabase databázi"""
    manager = SupabaseManager()
    success = manager.test_connection()
    if success:
        click.echo("[OK] Pripojeni funguje!")
    else:
        click.echo("[ERROR] Pripojeni selhalo!")
        sys.exit(1)


@cli.command()
def init():
    """Inicializace databáze - vytvoření všech tabulek"""
    manager = SupabaseManager()

    # Nejprve test připojení
    if not manager.test_connection():
        click.echo("❌ Nelze se připojit k databázi!")
        sys.exit(1)

    # Vytvoření tabulek
    click.echo("[INFO] Vytvareni databazove struktury...")
    success = manager.create_tables()

    if success:
        click.echo("[OK] Databaze uspesne inicializovana!")
    else:
        click.echo("[ERROR] Chyba pri inicializaci databaze!")
        sys.exit(1)


@cli.command()
def status():
    """Zobrazení stavu databáze a počtu záznamů v tabulkách"""
    manager = SupabaseManager()

    # Test připojení
    if not manager.test_connection():
        click.echo("[ERROR] Nelze se pripojit k databazi!")
        sys.exit(1)

    # Získání statistik
    click.echo("[INFO] Nacitani statistik tabulek...")
    stats = manager.get_table_stats()

    if not stats:
        click.echo("[ERROR] Nelze ziskat statistiky!")
        return

    click.echo("\n[INFO] Statistiky databaze:")
    click.echo("=" * 50)

    for table, count in stats.items():
        if count == -1:
            click.echo(f"{table:<30}: CHYBA")
        else:
            click.echo(f"{table:<30}: {count}")

    total_records = sum(count for count in stats.values() if count >= 0)
    click.echo("-" * 50)
    click.echo(f"{'Celkem záznamů':<30}: {total_records}")


@cli.command()
@click.confirmation_option(
    prompt="Opravdu chcete resetovat celou databázi? Všechna data budou ztracena!"
)
def reset():
    """Reset databáze - smazání všech tabulek a znovu vytvoření"""
    manager = SupabaseManager()

    # Test připojení
    if not manager.test_connection():
        click.echo("[ERROR] Nelze se pripojit k databazi!")
        sys.exit(1)

    click.echo("[INFO] Resetovani databaze...")
    success = manager.reset_database()

    if success:
        click.echo("[OK] Databaze uspesne resetovana a znovu vytvorena!")
    else:
        click.echo("[ERROR] Chyba pri resetu databaze!")
        sys.exit(1)


@cli.command()
@click.argument("table_name")
@click.option("--limit", default=10, help="Maximální počet zobrazených záznamů")
def show(table_name, limit):
    """Zobrazení záznamů z tabulky"""
    manager = SupabaseManager()

    # Test připojení
    if not manager.test_connection():
        click.echo("[ERROR] Nelze se pripojit k databazi!")
        sys.exit(1)

    success = manager.show_table_records(table_name, limit)

    if not success:
        sys.exit(1)


@cli.command()
@click.argument("table_name")
def insert_test(table_name):
    """Vložení testovacího záznamu do tabulky"""
    manager = SupabaseManager()

    # Test připojení
    if not manager.test_connection():
        click.echo("[ERROR] Nelze se pripojit k databazi!")
        sys.exit(1)

    success = manager.insert_test_record(table_name)

    if not success:
        sys.exit(1)

    success = manager.show_table_records(table_name, limit)

    if not success:
        sys.exit(1)


def run_default():
    """Výchozí akce - připojení k databázi a zobrazení statistik"""
    manager = SupabaseManager()

    print("🔌 Testování připojení k databázi...")
    if not manager.test_connection():
        print("❌ Nelze se připojit k databázi!")
        sys.exit(1)

    print("\n📊 Načítání statistik tabulek...")
    stats = manager.get_table_stats()

    if not stats:
        print("❌ Nelze získat statistiky!")
        return

    print("\n📈 Statistiky databáze:")
    print("=" * 50)

    for table, count in stats.items():
        if count == -1:
            print(f"{table:<30}: CHYBA")
        else:
            print(f"{table:<30}: {count}")

    total_records = sum(count for count in stats.values() if count >= 0)
    print("-" * 50)
    print(f"{'Celkem záznamů':<30}: {total_records}")


if __name__ == "__main__":
    # Pokud nejsou zadány žádné argumenty, spusť výchozí akci
    if len(sys.argv) == 1:
        run_default()
    else:
        cli()
