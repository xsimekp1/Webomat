#!/usr/bin/env python3
"""
Database Inspection Script

Connects to Supabase PostgreSQL database and displays table structure.
Loads connection details from environment variables.

Usage:
    python scripts/inspect_db.py
    python scripts/inspect_db.py --table sellers
    python scripts/inspect_db.py --all
"""

import os
import sys
import argparse
from pathlib import Path

# Try to load dotenv from multiple locations
def load_env():
    """Load environment variables from .env files."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("Warning: python-dotenv not installed. Using system environment variables.")
        return

    # Check multiple locations for .env files
    locations = [
        Path(__file__).parent.parent / "backend" / ".env",
        Path(__file__).parent.parent / ".env",
        Path.cwd() / "backend" / ".env",
        Path.cwd() / ".env",
    ]

    for loc in locations:
        if loc.exists():
            load_dotenv(loc)
            print(f"Loaded environment from: {loc}")
            return

    print("Warning: No .env file found. Using system environment variables.")


def get_connection():
    """Get database connection from Supabase URL."""
    import psycopg2

    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url:
        print("Error: SUPABASE_URL environment variable not set")
        sys.exit(1)

    # Extract database host from Supabase URL
    # Format: https://PROJECT_REF.supabase.co
    import re
    match = re.match(r"https://([^.]+)\.supabase\.co", supabase_url)
    if not match:
        print(f"Error: Could not parse Supabase URL: {supabase_url}")
        sys.exit(1)

    project_ref = match.group(1)

    # Construct PostgreSQL connection string
    # Supabase PostgreSQL is at db.PROJECT_REF.supabase.co
    db_host = f"db.{project_ref}.supabase.co"
    db_port = 5432
    db_name = "postgres"
    db_user = "postgres"

    # For Supabase, we need the database password (not service_role_key)
    db_password = os.getenv("SUPABASE_DB_PASSWORD")

    if not db_password:
        print("Warning: SUPABASE_DB_PASSWORD not set. Trying service role key...")
        db_password = service_key

    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
            sslmode="require",
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print("\nTip: Set SUPABASE_DB_PASSWORD environment variable with your database password.")
        print("You can find it in Supabase Dashboard > Settings > Database > Connection string")
        sys.exit(1)


def list_tables(conn):
    """List all tables in the public schema."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)

    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables


def get_table_columns(conn, table_name):
    """Get column information for a table."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))

    columns = cursor.fetchall()
    cursor.close()
    return columns


def get_table_indexes(conn, table_name):
    """Get indexes for a table."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename = %s
    """, (table_name,))

    indexes = cursor.fetchall()
    cursor.close()
    return indexes


def get_foreign_keys(conn, table_name):
    """Get foreign keys for a table."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table,
            ccu.column_name AS foreign_column
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.table_schema = 'public'
        AND tc.table_name = %s
        AND tc.constraint_type = 'FOREIGN KEY'
    """, (table_name,))

    fks = cursor.fetchall()
    cursor.close()
    return fks


def print_table_info(conn, table_name, show_indexes=False, show_fks=False):
    """Print detailed information about a table."""
    print(f"\n{'=' * 60}")
    print(f"TABLE: {table_name}")
    print('=' * 60)

    columns = get_table_columns(conn, table_name)

    print("\nColumns:")
    print("-" * 60)
    print(f"{'Name':<25} {'Type':<20} {'Nullable':<10} {'Default'}")
    print("-" * 60)

    for col in columns:
        name, dtype, nullable, default, max_len = col
        if max_len:
            dtype = f"{dtype}({max_len})"
        nullable_str = "YES" if nullable == "YES" else "NO"
        default_str = str(default)[:30] if default else ""
        print(f"{name:<25} {dtype:<20} {nullable_str:<10} {default_str}")

    if show_indexes:
        indexes = get_table_indexes(conn, table_name)
        if indexes:
            print("\nIndexes:")
            print("-" * 60)
            for idx_name, idx_def in indexes:
                print(f"  {idx_name}")

    if show_fks:
        fks = get_foreign_keys(conn, table_name)
        if fks:
            print("\nForeign Keys:")
            print("-" * 60)
            for constraint, column, ref_table, ref_column in fks:
                print(f"  {column} -> {ref_table}.{ref_column}")


def main():
    parser = argparse.ArgumentParser(description="Inspect Supabase database structure")
    parser.add_argument("--table", "-t", help="Show specific table")
    parser.add_argument("--all", "-a", action="store_true", help="Show all tables with details")
    parser.add_argument("--indexes", "-i", action="store_true", help="Show indexes")
    parser.add_argument("--fks", "-f", action="store_true", help="Show foreign keys")

    args = parser.parse_args()

    load_env()

    try:
        import psycopg2
    except ImportError:
        print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)

    conn = get_connection()
    print(f"Connected to database successfully\n")

    tables = list_tables(conn)

    if args.table:
        if args.table not in tables:
            print(f"Error: Table '{args.table}' not found")
            print(f"Available tables: {', '.join(tables)}")
            sys.exit(1)
        print_table_info(conn, args.table, args.indexes, args.fks)

    elif args.all:
        print(f"Found {len(tables)} tables in public schema")
        for table in tables:
            print_table_info(conn, table, args.indexes, args.fks)

    else:
        print("Tables in public schema:")
        print("-" * 40)
        for table in tables:
            cursor = conn.cursor()
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            count = cursor.fetchone()[0]
            cursor.close()
            print(f"  {table:<35} ({count} rows)")

        print(f"\nTotal: {len(tables)} tables")
        print("\nTip: Use --table TABLE_NAME for details, or --all for all tables")

    conn.close()


if __name__ == "__main__":
    main()
