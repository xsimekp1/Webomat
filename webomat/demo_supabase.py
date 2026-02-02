#!/usr/bin/env python3
"""
Inspect Postgres/Supabase schema from env files (monorepo-friendly).

- Loads .env files from current dir upward + common subdirs (frontend/backend/webomat)
- Reads DATABASE_URL (preferred) or SUPABASE_* parts
- If host looks like "<ref>.supabase.co" (Cloudflare), automatically tries "db.<ref>.supabase.co"
- Connects via psycopg2 and prints table + column structure
- Writes markdown to tmp/schema.md

Usage:
  python scripts/inspect_db.py
  python scripts/inspect_db.py --schema public
  python scripts/inspect_db.py --counts
  python scripts/inspect_db.py --out tmp/schema.md
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import psycopg2
from psycopg2 import OperationalError

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


CANDIDATE_ENV_KEYS = [
    "DATABASE_URL",
    "POSTGRES_URL",
    "SUPABASE_DB_URL",
    "SUPABASE_DATABASE_URL",
    "PG_URL",
]

# common env locations in a monorepo
COMMON_ENV_PATHS = [
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    "frontend/.env",
    "frontend/.env.local",
    "frontend/.env.development",
    "frontend/.env.production",
    "backend/.env",
    "backend/.env.local",
    "backend/.env.development",
    "backend/.env.production",
    "webomat/.env",
    "webomat/.env.local",
    "webomat/.env.development",
    "webomat/.env.production",
]


def _redact_url(u: str) -> str:
    """Redact password part for safe logging."""
    try:
        p = urlparse(u)
        netloc = p.netloc
        if "@" in netloc:
            creds, hostpart = netloc.split("@", 1)
            if ":" in creds:
                user = creds.split(":", 1)[0]
                netloc = f"{user}:***@{hostpart}"
        return urlunparse((p.scheme, netloc, p.path, p.params, p.query, p.fragment))
    except Exception:
        return "<unparseable>"


def _with_sslmode(u: str, sslmode: Optional[str]) -> str:
    """Ensure sslmode is present in query string."""
    if not sslmode:
        return u
    p = urlparse(u)
    q = dict(parse_qsl(p.query, keep_blank_values=True))
    q.setdefault("sslmode", sslmode)
    return urlunparse((p.scheme, p.netloc, p.path, p.params, urlencode(q), p.fragment))


def _supabase_db_host(host: str) -> str:
    """
    If host is "<ref>.supabase.co", return "db.<ref>.supabase.co".
    If already starts with "db." or doesn't match, return original.
    """
    host = (host or "").strip()
    if not host:
        return host
    if host.startswith("db."):
        return host
    if host.endswith(".supabase.co"):
        ref = host.split(".", 1)[0]
        return f"db.{ref}.supabase.co"
    return host


def normalize_supabase_database_url(u: str, default_sslmode: str = "require") -> Optional[str]:
    """
    If URL host looks like "<ref>.supabase.co" (Cloudflare), produce alt URL with db.<ref>.supabase.co.
    Otherwise return None.
    """
    try:
        p = urlparse(u)
        host = p.hostname or ""
        new_host = _supabase_db_host(host)
        if new_host == host:
            return None

        # rebuild netloc (user:pass@host:port)
        userinfo = ""
        if p.username:
            userinfo = p.username
            if p.password:
                userinfo += f":{p.password}"
            userinfo += "@"

        port = f":{p.port}" if p.port else ""
        netloc = f"{userinfo}{new_host}{port}"

        alt = urlunparse((p.scheme, netloc, p.path, p.params, p.query, p.fragment))
        alt = _with_sslmode(alt, os.getenv("SUPABASE_SSLMODE") or default_sslmode)
        return alt
    except Exception:
        return None


def load_env_from_monorepo(start_dir: Path) -> List[Path]:
    """
    Load .env files by scanning upwards and common subpaths at each level.
    Returns list of loaded files (existing ones).
    """
    loaded: List[Path] = []
    if load_dotenv is None:
        return loaded

    start_dir = start_dir.resolve()
    parents = [start_dir] + list(start_dir.parents)

    for parent in parents:
        for rel in COMMON_ENV_PATHS:
            p = (parent / rel).resolve()
            if p.exists() and p.is_file():
                # override=True so the *closest* / most recent .env wins (practical for monorepos)
                load_dotenv(dotenv_path=str(p), override=True)
                loaded.append(p)

    return loaded


def pick_first_env_key() -> Optional[str]:
    for k in CANDIDATE_ENV_KEYS:
        v = os.getenv(k)
        if v and v.strip():
            return k
    return None


def pick_db_url() -> str:
    k = pick_first_env_key()
    if not k:
        raise SystemExit(
            "Nenalezen DB URL v env.\n"
            f"Hledal jsem klíče: {', '.join(CANDIDATE_ENV_KEYS)}\n"
            "Tip: nastav DATABASE_URL nebo dej connection string do některého .env souboru."
        )
    return os.getenv(k, "").strip()


def build_url_from_supabase_parts() -> List[str]:
    """
    Build DSN candidates from SUPABASE_* parts:
      SUPABASE_HOST, SUPABASE_PORT, SUPABASE_DBNAME, SUPABASE_USER, SUPABASE_PASSWORD, SUPABASE_SSLMODE
    Returns [base, alt_db_host_if_applicable]
    """
    host = os.getenv("SUPABASE_HOST")
    user = os.getenv("SUPABASE_USER")
    password = os.getenv("SUPABASE_PASSWORD")
    dbname = os.getenv("SUPABASE_DBNAME") or "postgres"
    port = os.getenv("SUPABASE_PORT") or "5432"
    sslmode = os.getenv("SUPABASE_SSLMODE") or "require"

    if not (host and user and password):
        return []

    base = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    base = _with_sslmode(base, sslmode)

    alt_host = _supabase_db_host(host)
    if alt_host != host:
        alt = f"postgresql://{user}:{password}@{alt_host}:{port}/{dbname}"
        alt = _with_sslmode(alt, sslmode)
        return [base, alt]

    return [base]


def connection_candidates() -> List[str]:
    """
    Create a deduplicated list of candidate DSNs:
    - from DATABASE_URL (with sslmode)
    - normalized alt "db.<ref>..." if applicable
    - from SUPABASE_* parts
    """
    sslmode = os.getenv("SUPABASE_SSLMODE") or "require"

    candidates: List[str] = []

    # 1) from DB URL env
    db_url = pick_db_url()
    if db_url.startswith("postgres://"):
        db_url = "postgresql://" + db_url[len("postgres://") :]
    db_url = _with_sslmode(db_url, sslmode)
    candidates.append(db_url)

    alt = normalize_supabase_database_url(db_url, default_sslmode=sslmode)
    if alt:
        candidates.append(alt)

    # 2) from SUPABASE_* parts
    candidates.extend(build_url_from_supabase_parts())

    # dedupe while preserving order
    uniq: List[str] = []
    seen = set()
    for c in candidates:
        if c not in seen:
            uniq.append(c)
            seen.add(c)
    return uniq


def connect_any(candidates: List[str], timeout_s: int) -> psycopg2.extensions.connection:
    last_err: Optional[Exception] = None
    for i, dsn in enumerate(candidates, start=1):
        print(f"[{i}/{len(candidates)}] Zkouším připojení: {_redact_url(dsn)}")
        try:
            conn = psycopg2.connect(dsn, connect_timeout=timeout_s)
            conn.autocommit = True
            print("  ✓ OK\n")
            return conn
        except OperationalError as e:
            last_err = e
            print(f"  ✗ Selhalo: {e}\n")

    raise SystemExit(f"Nepodařilo se připojit k DB žádným kandidátem.\nPoslední chyba: {last_err}")


def fetch_tables(cur, schema_filter: Optional[str] = None) -> List[Tuple[str, str]]:
    q = """
        select table_schema, table_name
        from information_schema.tables
        where table_type='BASE TABLE'
          and table_schema not in ('pg_catalog','information_schema')
    """
    params: List[str] = []
    if schema_filter:
        q += " and table_schema = %s"
        params.append(schema_filter)
    q += " order by table_schema, table_name"

    cur.execute(q, params or None)
    return cur.fetchall()


def fetch_columns(cur, schema: str, table: str):
    cur.execute(
        """
        select
          ordinal_position,
          column_name,
          data_type,
          udt_name,
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


def table_row_count(cur, schema: str, table: str) -> Optional[int]:
    try:
        cur.execute(f'select count(*) from "{schema}"."{table}"')
        return int(cur.fetchone()[0])
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", help="Filter schema (e.g. public)", default=None)
    ap.add_argument("--counts", help="Also count rows per table (can be slow)", action="store_true")
    ap.add_argument("--timeout", type=int, default=7, help="Connect timeout seconds (default 7)")
    ap.add_argument("--out", default="tmp/schema.md", help="Markdown output path (default tmp/schema.md)")
    args = ap.parse_args()

    loaded = load_env_from_monorepo(Path.cwd())
    if loaded:
        print("Načetl jsem .env soubory:")
        for p in loaded:
            print(f" - {p}")
        print()

    env_key = pick_first_env_key()
    if env_key:
        print(f"DB URL klíč v env: {env_key}")
    else:
        print("DB URL klíč v env: (nenalezen)")
    print()

    cands = connection_candidates()
    conn = connect_any(cands, timeout_s=args.timeout)

    out_lines: List[str] = []
    out_lines.append(f"# DB schema dump ({datetime.utcnow().isoformat()}Z)")
    out_lines.append("")
    out_lines.append(f"- Schema filter: `{args.schema or 'ALL'}`")
    out_lines.append(f"- Counts: `{args.counts}`")
    out_lines.append("")

    with conn.cursor() as cur:
        # sanity check
        cur.execute("select now()")
        now = cur.fetchone()[0]
        print(f"[OK] Připojeno. DB čas: {now}\n")
        out_lines.append(f"**Connected OK. DB time:** `{now}`")
        out_lines.append("")

        tables = fetch_tables(cur, schema_filter=args.schema)
        print(f"Nalezeno tabulek: {len(tables)}\n")
        out_lines.append(f"## Tables ({len(tables)})")
        out_lines.append("")

        for schema, table in tables:
            title = f"### {schema}.{table}"
            print(title)
            out_lines.append(title)

            if args.counts:
                cnt = table_row_count(cur, schema, table)
                if cnt is None:
                    print("  rows: (nelze zjistit)")
                    out_lines.append("- rows: (nelze zjistit)")
                else:
                    print(f"  rows: {cnt}")
                    out_lines.append(f"- rows: {cnt}")

            cols = fetch_columns(cur, schema, table)
            for pos, name, data_type, udt_name, nullable, default in cols:
                # for enums, data_type may be 'USER-DEFINED', udt_name contains enum name
                dtype = data_type
                if data_type == "USER-DEFINED" and udt_name:
                    dtype = f"enum:{udt_name}"

                line = f"  - {pos}. {name} ({dtype}) null={nullable} default={default}"
                print(line)
                out_lines.append(f"- {pos}. **{name}** `{dtype}`  null={nullable}  default={default}")

            print()
            out_lines.append("")

    # write markdown output
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"✅ Uloženo do: {out_path.resolve()}")

    conn.close()


if __name__ == "__main__":
    main()
