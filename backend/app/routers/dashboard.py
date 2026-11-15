from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import db
from ..auth import current_user
from ..config import FORMULES, STATUT_LABELS
from ..services import journal, plans

router = APIRouter(prefix="/api", tags=["dashboard"])


class FormuleIn(BaseModel):
    formule: str


@router.get("/dashboard")
def dashboard(user: dict = Depends(current_user)):
    c = plans.compteur(user["id"])
    with db.get_conn() as con:
        by_status = db.fetchall(
            con,
            "SELECT statut, COUNT(*) AS n FROM candidatures WHERE user_id = ? GROUP BY statut",
            (user["id"],),
        )
        recent = db.fetchall(
            con,
            """
            SELECT c.id, c.statut, c.score, c.date_maj, o.titre, o.entreprise
            FROM candidatures c JOIN offres o ON o.id = c.offre_id
            WHERE c.user_id = ? ORDER BY c.date_maj DESC LIMIT 8
            """,
            (user["id"],),
        )
        n_offres = db.fetchone(con, "SELECT COUNT(*) AS n FROM offres")["n"]
    stats = {s: 0 for s in STATUT_LABELS}
    for row in by_status:
        stats[row["statut"]] = row["n"]
    return {
        "user": {k: user[k] for k in ("id", "nom", "email", "formule") if k in user},
        "plan": plans.formule_of(user),
        "compteurs": c,
        "par_statut": stats,
        "labels": STATUT_LABELS,
        "recentes": recent,
        "n_offres": n_offres,
        "agent_arrete": c["entretien_obtenu"],
        "formules": FORMULES,
    }


@router.put("/formule")
def changer_formule(body: FormuleIn, user: dict = Depends(current_user)):
    if body.formule not in FORMULES:
        raise HTTPException(status_code=400, detail="Formule inconnue.")
    with db.get_conn() as con:
        con.execute("UPDATE users SET formule = ? WHERE id = ?", (body.formule, user["id"]))
    journal.log(user["id"], "changement_formule", {"formule": body.formule})
    return {"ok": True, "formule": FORMULES[body.formule] | {"id": body.formule}}


@router.get("/journal")
def get_journal(user: dict = Depends(current_user)):
    return {"items": journal.lister(user["id"])}


@router.get("/formules")
def list_formules():
    return FORMULES
