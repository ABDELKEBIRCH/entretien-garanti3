
"""SQLite/PostgreSQL access: schema, connections and basic queries."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import DATABASE_URL, DB_PATH, UPLOAD_DIR


# Maximum time to wait when the database is locked.
DB_TIMEOUT = 30


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    formule TEXT NOT NULL DEFAULT 'decouverte',
    date_inscription TEXT NOT NULL,
    consentement_09_08 INTEGER NOT NULL DEFAULT 0,
    consentement_date TEXT
);

CREATE TABLE IF NOT EXISTS profils (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    competences TEXT NOT NULL DEFAULT '[]',
    experiences TEXT NOT NULL DEFAULT '[]',
    formation TEXT NOT NULL DEFAULT '[]',
    langues TEXT NOT NULL DEFAULT '[]',
    pref_poste TEXT DEFAULT '',
    pref_ville TEXT DEFAULT '',
    pref_contrat TEXT DEFAULT '',
    cv_texte TEXT DEFAULT '',
    cv_filename TEXT DEFAULT '',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS offres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    titre TEXT NOT NULL,
    entreprise TEXT DEFAULT '',
    ville TEXT DEFAULT '',
    description TEXT DEFAULT '',
    date_pub TEXT DEFAULT '',
    url TEXT DEFAULT '',
    fingerprint TEXT NOT NULL UNIQUE,
    competences_requises TEXT NOT NULL DEFAULT '[]',
    last_seen_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS candidatures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    offre_id INTEGER NOT NULL,
    score REAL DEFAULT 0,
    explication TEXT NOT NULL DEFAULT '{}',
    lettre TEXT DEFAULT '',
    cv_adapte TEXT DEFAULT '',
    questions_entretien TEXT DEFAULT '',
    statut TEXT NOT NULL DEFAULT 'a_envoyer',
    entretien_date TEXT DEFAULT '',
    entretien_lieu TEXT DEFAULT '',
    entretien_notes TEXT DEFAULT '',
    entretien_email_envoye INTEGER NOT NULL DEFAULT 0,
    date_creation TEXT NOT NULL,
    date_maj TEXT NOT NULL,
    UNIQUE (user_id, offre_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (offre_id) REFERENCES offres(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    details TEXT DEFAULT '',
    date TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_offres_source ON offres(source);
CREATE INDEX IF NOT EXISTS idx_cand_user ON candidatures(user_id);
CREATE INDEX IF NOT EXISTS idx_journal_user ON journal(user_id);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def init_db(path: Path | None = None) -> None:
    db_path = path or DB_PATH

    db_path.parent.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    if DATABASE_URL and DATABASE_URL.startswith(("postgres://", "postgresql://")):
        import psycopg2
        from psycopg2.extras import RealDictCursor

        pg_schema = SCHEMA.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY")
        pg_schema = pg_schema.replace("INTEGER PRIMARY KEY", "BIGSERIAL PRIMARY KEY")
        pg_schema = pg_schema.replace("INTEGER NOT NULL", "BIGINT NOT NULL")
        pg_schema = pg_schema.replace("INTEGER,", "BIGINT,")
        con = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        try:
            with con.cursor() as cur:
                for statement in pg_schema.split(";"):
                    if statement.strip():
                        cur.execute(statement)
                _migrate_columns(con, postgres=True)
            con.commit()
        finally:
            con.close()
        return

    with sqlite3.connect(db_path, timeout=DB_TIMEOUT) as con:
        con.execute("PRAGMA busy_timeout = 30000")
        con.execute("PRAGMA journal_mode = WAL")
        con.execute("PRAGMA foreign_keys = ON")

        con.executescript(SCHEMA)
        _migrate_columns(con)
        con.commit()


def _migrate_columns(con, postgres: bool = False) -> None:
    migrations = {
        "offres": {
            "competences_requises": "TEXT NOT NULL DEFAULT '[]'",
            "last_seen_at": "TEXT NOT NULL DEFAULT ''",
        },
        "candidatures": {
            "entretien_date": "TEXT DEFAULT ''",
            "entretien_lieu": "TEXT DEFAULT ''",
            "entretien_notes": "TEXT DEFAULT ''",
            "entretien_email_envoye": "INTEGER NOT NULL DEFAULT 0",
        },
    }
    for table, columns in migrations.items():
        if postgres:
            for name, declaration in columns.items():
                con.cursor().execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {name} {declaration}")
        else:
            existing = {row[1] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}
            for name, declaration in columns.items():
                if name not in existing:
                    con.execute(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}")
    if postgres:
        con.cursor().execute("CREATE INDEX IF NOT EXISTS idx_offres_seen ON offres(last_seen_at)")
    else:
        con.execute("CREATE INDEX IF NOT EXISTS idx_offres_seen ON offres(last_seen_at)")


@contextmanager
def get_conn(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    if DATABASE_URL and DATABASE_URL.startswith(("postgres://", "postgresql://")):
        import psycopg2
        from psycopg2.extras import RealDictCursor

        class CursorAdapter:
            def __init__(self, cursor, connection):
                self._cursor, self._connection = cursor, connection
            def __getattr__(self, key):
                return getattr(self._cursor, key)
            @property
            def lastrowid(self):
                with self._connection.cursor() as cur:
                    cur.execute("SELECT LASTVAL() AS id")
                    return cur.fetchone()["id"]

        class ConnectionAdapter:
            def __init__(self, connection): self._connection = connection
            def execute(self, sql, params=()):
                cur = self._connection.cursor()
                cur.execute(sql.replace("?", "%s"), params)
                return CursorAdapter(cur, self._connection)
            def __getattr__(self, key): return getattr(self._connection, key)

        raw = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        con = ConnectionAdapter(raw)
        try:
            yield con
            raw.commit()
        except Exception:
            raw.rollback()
            raise
        finally:
            raw.close()
        return

    con = sqlite3.connect(
        path or DB_PATH,
        timeout=DB_TIMEOUT,
    )

    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout = 30000")
    con.execute("PRAGMA foreign_keys = ON")

    try:
        yield con
        con.commit()

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None

    return dict(row)


def parse_json(value: str | None, default: Any) -> Any:
    if not value:
        return default

    try:
        return json.loads(value)

    except json.JSONDecodeError:
        return default


def fetchone(
    con: sqlite3.Connection,
    sql: str,
    params: tuple = (),
) -> dict[str, Any] | None:

    return row_to_dict(
        con.execute(sql, params).fetchone()
    )


def fetchall(
    con: sqlite3.Connection,
    sql: str,
    params: tuple = (),
) -> list[dict[str, Any]]:

    return [
        dict(row)
        for row in con.execute(sql, params).fetchall()
    ]
