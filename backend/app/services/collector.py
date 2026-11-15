"""Collecte d'offres : données de démonstration et sources d'offres réelles."""

from __future__ import annotations

import hashlib
import html
import json
import re
import time
from datetime import datetime, timezone

import feedparser
import httpx
from .. import db
from ..config import DATA_DIR
from . import journal
from .matching import extraire_competences_requises

RSS_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-product-jobs.rss",
]
REMOTIVE_API = "https://remotive.com/api/remote-jobs"
# Remotive recommande au plus quatre appels par jour. Six heures entre deux
# appels au niveau du processus respecte cette limite dans le cas normal.
_remotive_last_fetch: float | None = None
_rss_last_fetch: float | None = None


def fingerprint(source: str, titre: str, entreprise: str, url: str) -> str:
    raw = "|".join([source, titre.lower().strip(), (entreprise or "").lower().strip(), url or ""])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _upsert(offre: dict) -> bool:
    fp = fingerprint(
        offre["source"],
        offre.get("titre") or "",
        offre.get("entreprise") or "",
        offre.get("url") or "",
    )
    offre = {**offre, "fingerprint": fp}
    skills = extraire_competences_requises(
        f"{offre.get('titre') or ''}\n{offre.get('description') or ''}",
        list(offre.get("competences_requises") or []),
    )
    with db.get_conn() as con:
        existing = db.fetchone(con, "SELECT id FROM offres WHERE fingerprint = ?", (fp,))
        if existing:
            con.execute(
                """UPDATE offres SET titre = ?, entreprise = ?, ville = ?, description = ?,
                   date_pub = ?, url = ?, competences_requises = ?, last_seen_at = ? WHERE fingerprint = ?""",
                (offre.get("titre") or "Offre", offre.get("entreprise") or "", offre.get("ville") or "",
                 offre.get("description") or "", offre.get("date_pub") or "", offre.get("url") or "",
                 json.dumps(skills, ensure_ascii=False), db.now_iso(), fp),
            )
            return False
        con.execute(
            """
            INSERT INTO offres (source, titre, entreprise, ville, description, date_pub, url, fingerprint, competences_requises, last_seen_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                offre["source"],
                offre.get("titre") or "Offre",
                offre.get("entreprise") or "",
                offre.get("ville") or "",
                offre.get("description") or "",
                offre.get("date_pub") or "",
                offre.get("url") or "",
                fp,
                json.dumps(skills, ensure_ascii=False),
                db.now_iso(),
            ),
        )
    return True


def ajouter_offre_importee(offre: dict) -> bool:
    """Ajoute une annonce que l'utilisateur a copiée depuis sa source."""
    return _upsert(offre)


def charger_demo() -> int:
    path = DATA_DIR / "offres_demo.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    n = 0
    for item in data:
        if _upsert({**item, "source": "demo"}):
            n += 1
    return n


def charger_rss(timeout: float = 6.0) -> int:
    global _rss_last_fetch
    now = time.monotonic()
    if _rss_last_fetch is not None and now - _rss_last_fetch < 6 * 60 * 60:
        return 0
    _rss_last_fetch = now
    n = 0
    for url in RSS_FEEDS:
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                r = client.get(url, headers={"User-Agent": "EntretienGaranti/2.0 (job-search application)"})
                r.raise_for_status()
                parsed = feedparser.parse(r.text)
        except Exception:
            continue
        for entry in parsed.entries[:25]:
            titre = entry.get("title") or "Offre distante"
            lien = entry.get("link") or url
            resume = entry.get("summary") or entry.get("description") or ""
            # résumé HTML naïf
            texte = _strip_html(resume)[:2500]
            if _upsert(
                {
                    "source": "rss",
                    "titre": titre[:180],
                    "entreprise": _entreprise(entry, titre),
                    "ville": "Télétravail / international",
                    "description": texte,
                    "date_pub": entry.get("published") or datetime.now(timezone.utc).date().isoformat(),
                    "url": lien,
                }
            ):
                n += 1
    return n


def charger_remotive(timeout: float = 8.0, limit: int = 100) -> int:
    """Charge les offres distantes de Remotive, avec attribution vers la source."""
    global _remotive_last_fetch
    now = time.monotonic()
    if _remotive_last_fetch is not None and now - _remotive_last_fetch < 6 * 60 * 60:
        return 0
    # Mémoriser aussi les échecs évite de marteler le service lorsqu'il est indisponible.
    _remotive_last_fetch = now
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(
                REMOTIVE_API,
                params={"limit": min(max(int(limit), 1), 100)},
                headers={"User-Agent": "EntretienGaranti/1.0 (personal job search)"},
            )
            response.raise_for_status()
            jobs = response.json().get("jobs", [])
    except (httpx.HTTPError, ValueError, TypeError):
        return 0

    added = 0
    for job in jobs:
        title = str(job.get("title") or "Offre à distance")[:180]
        description = _strip_html(str(job.get("description") or ""))[:4000]
        tags = job.get("tags") or []
        skills = [str(tag)[:80] for tag in tags if tag]
        created = str(job.get("publication_date") or "")[:40]
        if _upsert({
            "source": "remotive",
            "titre": title,
            "entreprise": str(job.get("company_name") or "")[:120],
            "ville": str(job.get("candidate_required_location") or "Télétravail")[:160],
            "description": description,
            "date_pub": created,
            "url": str(job.get("url") or ""),
            "competences_requises": skills,
        }):
            added += 1
    return added


def collecter(sources: list[str], user_id: int | None = None) -> dict:
    added = {"demo": 0, "rss": 0, "remotive": 0}
    if "demo" in sources:
        added["demo"] = charger_demo()
    if "rss" in sources:
        added["rss"] = charger_rss()
    if "remotive" in sources:
        added["remotive"] = charger_remotive()
    journal.log(user_id, "collecte_offres", added)
    with db.get_conn() as con:
        total = db.fetchone(con, "SELECT COUNT(*) AS n FROM offres")["n"]
    return {"ajoutees": added, "total": total}


def lister(sources: list[str] | None = None) -> list[dict]:
    cutoff = datetime.now(timezone.utc).timestamp() - 30 * 24 * 60 * 60
    recent_after = datetime.fromtimestamp(cutoff, timezone.utc).isoformat()
    with db.get_conn() as con:
        if sources:
            placeholders = ",".join("?" * len(sources))
            return db.fetchall(con, f"SELECT * FROM offres WHERE source IN ({placeholders}) AND (source NOT IN ('rss', 'remotive') OR last_seen_at >= ?) ORDER BY id DESC", (*sources, recent_after))
        return db.fetchall(con, "SELECT * FROM offres WHERE source NOT IN ('rss', 'remotive') OR last_seen_at >= ? ORDER BY id DESC", (recent_after,))


def _strip_html(markup: str) -> str:
    text = re.sub(r"(?is)<(script|style)\b[^>]*>.*?</\1\s*>", " ", markup or "")
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _entreprise(entry: dict, titre: str) -> str:
    if entry.get("author"):
        return str(entry["author"])[:80]
    if ":" in titre:
        return titre.split(":", 1)[0].strip()[:80]
    return "Entreprise (RSS)"
