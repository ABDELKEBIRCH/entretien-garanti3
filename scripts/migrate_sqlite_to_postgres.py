"""Copy an existing Entretien garanti SQLite database to PostgreSQL."""

from __future__ import annotations

import argparse
import os
import sys
import sqlite3
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("postgres_url", help="URL PostgreSQL cible (postgresql://...) ")
    parser.add_argument("--sqlite", type=Path, default=Path("backend/entretien.db"), help="Fichier SQLite source")
    parser.add_argument("--replace", action="store_true", help="Vider les tables cible avant la migration")
    args = parser.parse_args()
    if not args.sqlite.exists():
        raise SystemExit(f"Base SQLite introuvable : {args.sqlite}")
    if not args.postgres_url.startswith(("postgres://", "postgresql://")):
        raise SystemExit("L'URL cible doit utiliser postgres:// ou postgresql://")

    os.environ["DATABASE_URL"] = args.postgres_url
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
    from app.db import init_db
    import psycopg2

    init_db()
    src = sqlite3.connect(f"file:{args.sqlite.resolve().as_posix()}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    tables = ("users", "profils", "offres", "candidatures", "journal")
    copied = {}
    try:
        with psycopg2.connect(args.postgres_url) as target:
            with target.cursor() as cursor:
                cursor.execute("SELECT EXISTS (SELECT 1 FROM users) OR EXISTS (SELECT 1 FROM profils) OR EXISTS (SELECT 1 FROM offres) OR EXISTS (SELECT 1 FROM candidatures) OR EXISTS (SELECT 1 FROM journal)")
                if cursor.fetchone()[0] and not args.replace:
                    raise SystemExit("La base PostgreSQL contient déjà des données. Utilisez --replace pour les remplacer.")
                if args.replace:
                    cursor.execute("TRUNCATE TABLE journal, candidatures, offres, profils, users CASCADE")
                for table in tables:
                    rows = [dict(row) for row in src.execute(f"SELECT * FROM {table}")]
                    if not rows:
                        copied[table] = 0
                        continue
                    columns = list(rows[0])
                    names = ", ".join(f'"{column}"' for column in columns)
                    values = ", ".join(["%s"] * len(columns))
                    query = f"INSERT INTO {table} ({names}) VALUES ({values}) ON CONFLICT DO NOTHING"
                    cursor.executemany(query, [tuple(row[column] for column in columns) for row in rows])
                    copied[table] = len(rows)
                for table in ("users", "profils", "offres", "candidatures", "journal"):
                    cursor.execute(
                        "SELECT setval(pg_get_serial_sequence(%s, 'id'), COALESCE((SELECT MAX(id) FROM " + table + "), 1), EXISTS (SELECT 1 FROM " + table + "))",
                        (table,),
                    )
    finally:
        src.close()
    print("Migration terminée : " + ", ".join(f"{table}={count}" for table, count in copied.items()))


if __name__ == "__main__":
    main()
