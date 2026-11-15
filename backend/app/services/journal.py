from __future__ import annotations

import json

from .. import db


def log(user_id: int | None, action: str, details: dict | str | None = None) -> None:
    payload = details if isinstance(details, str) else json.dumps(details or {}, ensure_ascii=False)
    with db.get_conn() as con:
        con.execute(
            "INSERT INTO journal (user_id, action, details, date) VALUES (?, ?, ?, ?)",
            (user_id, action, payload, db.now_iso()),
        )


def lister(user_id: int, limit: int = 80) -> list[dict]:
    with db.get_conn() as con:
        return db.fetchall(
            con,
            "SELECT * FROM journal WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
