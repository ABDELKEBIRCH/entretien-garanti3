from __future__ import annotations

import json
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from .. import db
from ..auth import current_user
from ..services import collector, journal, matching, plans

router = APIRouter(prefix="/api/offres", tags=["offres"])


class OffreImport(BaseModel):
    titre: str = Field(min_length=3, max_length=180)
    entreprise: str = Field(default="", max_length=120)
    ville: str = Field(default="", max_length=160)
    description: str = Field(default="", max_length=12000)
    url: HttpUrl


@router.post("/importer")

def importer_offre(body: OffreImport, user: dict = Depends(current_user)):
    """Enregistre une annonce copiée par le candidat depuis une source externe."""
    url = str(body.url)
    if not url.startswith("https://"):
        raise HTTPException(status_code=422, detail="Utilisez le lien sécurisé HTTPS de l’annonce.")
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    source = "linkedin" if host == "linkedin.com" or host.endswith(".linkedin.com") else (
        "indeed" if host == "indeed.com" or host.endswith(".indeed.com") or host == "indeed.co.uk" or host.endswith(".indeed.co.uk") else "import_manuel"
    )
    offre = {
        "source": source,
        "titre": body.titre.strip(),
        "entreprise": body.entreprise.strip(),
        "ville": body.ville.strip(),
        "description": body.description.strip(),
        "url": url,
    }
    created = collector.ajouter_offre_importee(offre)
    with db.get_conn() as con:
        row = db.fetchone(con, "SELECT * FROM offres WHERE fingerprint = ?", (collector.fingerprint(source, offre["titre"], offre["entreprise"], url),))
    journal.log(user["id"], "offre_importee", {"source": source, "titre": offre["titre"], "deja_existante": not created})
    return {"offre": dict(row) if row else None, "deja_existante": not created}


def _profil(user_id: int) -> dict:
    with db.get_conn() as con:
        user = db.fetchone(con, "SELECT * FROM users WHERE id = ?", (user_id,))
        row = db.fetchone(con, "SELECT * FROM profils WHERE user_id = ?", (user_id,))
    has_cv = bool(row and (row.get("cv_texte") or "").strip())
    has_pref = bool(
        row
        and (
            (row.get("pref_poste") or "").strip()
            or (row.get("pref_ville") or "").strip()
            or (row.get("pref_contrat") or "").strip()
        )
    )
    if not row or (not has_cv and not has_pref):
        raise HTTPException(
            status_code=400,
            detail="Importez un CV ou enregistrez vos préférences (poste, ville, contrat) pour lancer le matching.",
        )
    out = dict(row)
    for key in ("competences", "experiences", "formation", "langues"):
        out[key] = db.parse_json(out.get(key), [])
    out["nom"] = user["nom"]
    return out


@router.post("/collecter")
def collecter(user: dict = Depends(current_user)):
    plan = plans.formule_of(user)
    result = collector.collecter(plan["sources"], user_id=user["id"])
    return result


@router.get("/recommandees")
def recommandees(user: dict = Depends(current_user)):
    plan = plans.formule_of(user)
    profil = _profil(user["id"])
    collector.charger_demo()
    if "rss" in plan["sources"]:
        collector.charger_rss()
    if "remotive" in plan["sources"]:
        collector.charger_remotive()
    offres = collector.lister(plan["sources"])
    ranked = matching.classer(profil, offres)[: plan["max_matchs"]]
    journal.log(user["id"], "matching", {"n": len(ranked)})
    return {
        "formule": plan,
        "offres": ranked,
        "agent_arrete": plans.agent_arrete(user["id"]),
        "preferences": {
            "pref_poste": profil.get("pref_poste") or "",
            "pref_ville": profil.get("pref_ville") or "",
            "pref_contrat": profil.get("pref_contrat") or "",
            "competences": profil.get("competences") or [],
        },
    }
