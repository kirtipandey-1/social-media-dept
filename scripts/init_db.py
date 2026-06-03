#!/usr/bin/env python3
"""One-shot DB initializer. Run once during install or to reset databases."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_settings
from db.sqlite_db import get_connection as sq_conn, init_schema as sq_init
from db.sqlite_db import seed_competitors, seed_employees
from db.duckdb_db import get_connection as dq_conn, init_schema as dq_init
from db.chroma_db import get_collection


def main():
    print("🎵 Social Media Dept — Database Initializer")
    print("=" * 45)

    s = load_settings()

    print("\nInitialising SQLite (social.db)...")
    conn = sq_conn()
    sq_init(conn)
    ig_handles = s.get("competitors", {}).get("instagram", [])
    seed_competitors(conn, ig_handles, "instagram")
    seed_employees(conn, s.get("employees", {}))
    print(f"  ✓ 11 tables created")
    print(f"  ✓ {len(ig_handles)} competitors seeded")
    print(f"  ✓ {len(s.get('employees', {}))} employees registered")

    print("\nInitialising DuckDB (analytics.duckdb)...")
    dq_init(dq_conn())
    print("  ✓ post_performance + daily_kpis tables created")

    print("\nInitialising ChromaDB (hooks/)...")
    col = get_collection()
    print(f"  ✓ hooks collection ready ({col.count()} existing hooks)")

    print("\n✅ All databases initialised.")


if __name__ == "__main__":
    main()
