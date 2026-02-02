import os
from urllib.parse import urlparse
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()  # loads .env if present
except Exception:
    pass

import psycopg2


CANDIDATE_ENV_KEYS = [
    "DATABASE_URL",
    "POSTGRES_URL",
    "SUPABASE_DB_URL",
    "SUPABASE_DATABASE_URL",
    "PG_URL",
]


def pick_db_url() -> str:
    for k in CANDIDATE_ENV_KEYS:
        v = os.getenv(k)
        if v and v.strip():
            return v.strip()
    raise SystemExit(
        "Nenalezen DB URL v env. Nastav jednu z proměnných: "
        + ", ".join(CANDIDATE_ENV_KEYS)
        + "\nNapř. (Windows CMD): set DATABASE_URL=postgresql://..."
    )


def fetch_tables(cur):
    cur.execute(
        """
        select table_schema, table_name
        from information_schema.tables
        where table_type='BASE TABLE'
          and table_schema not in ('pg_catalog','information_schema')
        order by table_schema, table_name
        """
    )
    return cur.fetchall()


def fetch_columns(cur, schema: str, table: str):
    cur.execute(
        """
        select
          ordinal_position,
          column_name,
          data_type,
          is_nullable,
          column_default
        from information_schema.columns
        where table_schema = %s
          and table_name = %s
        order by ordinal_position
        """,
        (schema, table),
    )
    return cur.fetchall()


def main():
    db_url = pick_db_url()

    # psycopg2 likes postgres:// too, but let's be safe
    if db_url.startswith("postgres://"):
        db_url = "postgresql://" + db_url[len("postgres://"):]

    conn = psycopg2.connect(db_url)
    conn.autocommit = True

    out_lines = []
    out_lines.append(f"# DB schema dump ({datetime.utcnow().isoformat()}Z)\n")

    with conn.cursor() as cur:
        tables = fetch_tables(cur)
        print(f"Nalezeno tabulek: {len(tables)}\n")

        for schema, table in tables:
            header = f"## {schema}.{table}"
            print(header)
            out_lines.append(header + "\n")

            cols = fetch_columns(cur, schema, table)
            for pos, name, dtype, nullable, default in cols:
                line = f"- {pos}. **{name}** `{dtype}`  null={nullable}  default={default}"
                print(line)
                out_lines.append(line)

            print()
            out_lines.append("")

    # write markdown file
    os.makedirs("tmp", exist_ok=True)
    path = os.path.join("tmp", "schema.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))

    print(f"✅ Uloženo do: {path}")
    conn.close()


if __name__ == "__main__":
    main()

