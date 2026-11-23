
from __future__ import annotations

import json
import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from .. import db
from ..auth import current_user
from ..config import INTERVIEW_NOTIFICATION_EMAIL, STATUTS
from ..services import documents, email, journal, llm, matching, plans

router = APIRouter(prefix="/api/candidatures", tags=["candidatures"])


class CreateIn(BaseModel):
    offre_id: int


class PatchIn(BaseModel):
    statut: str | None = None
    lettre: str | None = None
    entretien_date: str | None = None
    entretien_lieu: str | None = None
    entretien_notes: str | None = None


def _profil(user: dict) -> dict:
    with db.get_conn() as con:
        row = db.fetchone(
            con,
            "SELECT * FROM profils WHERE user_id = ?",
            (user["id"],),
        )

    if not row:
        raise HTTPException(
            status_code=400,
            detail="Profil incomplet.",
        )

    out = dict(row)

    for key in ("competences", "experiences", "formation", "langues"):
        out[key] = db.parse_json(out.get(key), [])

    out["nom"] = user["nom"]

    return out


def _enrich(row: dict) -> dict:
    out = dict(row)
    out["explication"] = db.parse_json(
        out.get("explication"),
        {},
    )
    return out


@router.get("")
def lister(user: dict = Depends(current_user)):
    with db.get_conn() as con:
        rows = db.fetchall(
            con,
            """
            SELECT c.*, o.titre, o.entreprise, o.ville, o.source, o.url,
                   o.description, o.competences_requises
            FROM candidatures c
            JOIN offres o ON o.id = c.offre_id
            WHERE c.user_id = ?
            ORDER BY c.id DESC
            """,
            (user["id"],),
        )

    profil = _profil(user) if rows else None
    items = []
    for row in rows:
        item = _enrich(row)
        if profil:
            explication = matching.scorer(profil, item)
            item["score"] = explication["score"]
            item["explication"] = explication
        items.append(item)

    return {
        "agent_arrete": plans.agent_arrete(user["id"]),
        "compteurs": plans.compteur(user["id"]),
        "items": items,
    }


@router.post("")
def creer(body: CreateIn, user: dict = Depends(current_user)):
    if plans.agent_arrete(user["id"]):
        raise HTTPException(
            status_code=409,
            detail="Agent arrêté : entretien déjà obtenu.",
        )

    with db.get_conn() as con:
        offre = db.fetchone(
            con,
            "SELECT * FROM offres WHERE id = ?",
            (body.offre_id,),
        )

        if not offre:
            raise HTTPException(
                status_code=404,
                detail="Offre inconnue.",
            )

        exist = db.fetchone(
            con,
            """
            SELECT * FROM candidatures
            WHERE user_id = ? AND offre_id = ?
            """,
            (user["id"], body.offre_id),
        )

        if exist:
            return _enrich(exist)

    profil = _profil(user)
    expl = matching.scorer(profil, offre)
    now = db.now_iso()

    with db.get_conn() as con:
        cur = con.execute(
            """
            INSERT INTO candidatures (
                user_id,
                offre_id,
                score,
                explication,
                statut,
                date_creation,
                date_maj
            )
            VALUES (?, ?, ?, ?, 'a_envoyer', ?, ?)
            """,
            (
                user["id"],
                body.offre_id,
                expl["score"],
                json.dumps(expl, ensure_ascii=False),
                now,
                now,
            ),
        )

        cid = cur.lastrowid

        row = db.fetchone(
            con,
            """
            SELECT c.*, o.titre, o.entreprise, o.ville, o.source, o.url
            FROM candidatures c
            JOIN offres o ON o.id = c.offre_id
            WHERE c.id = ?
            """,
            (cid,),
        )

    journal.log(
        user["id"],
        "candidature_creee",
        {
            "id": cid,
            "offre_id": body.offre_id,
        },
    )

    return _enrich(row)


@router.patch("/{cid}")
def patch(cid: int, body: PatchIn, user: dict = Depends(current_user)):
    entretien_obtenu = False
    nouvel_entretien = False
    confirmer_email = False

    with db.get_conn() as con:
        row = db.fetchone(
            con,
            """
            SELECT * FROM candidatures
            WHERE id = ? AND user_id = ?
            """,
            (cid, user["id"]),
        )

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Candidature introuvable.",
            )

        statut = row["statut"]
        lettre = row["lettre"]
        rendezvous = {key: row.get(key) or "" for key in ("entretien_date", "entretien_lieu", "entretien_notes")}

        if body.lettre is not None:
            lettre = body.lettre
        for key in rendezvous:
            value = getattr(body, key)
            if value is not None:
                rendezvous[key] = value.strip()

        if body.statut is not None:
            if body.statut not in STATUTS:
                raise HTTPException(
                    status_code=400,
                    detail="Statut invalide.",
                )

            statut = body.statut

        con.execute(
            """
            UPDATE candidatures
            SET statut = ?, lettre = ?, entretien_date = ?, entretien_lieu = ?, entretien_notes = ?, date_maj = ?
            WHERE id = ?
            """,
            (
                statut,
                lettre,
                rendezvous["entretien_date"],
                rendezvous["entretien_lieu"],
                rendezvous["entretien_notes"],
                db.now_iso(),
                cid,
            ),
        )

        entretien_obtenu = statut == "entretien"
        nouvel_entretien = entretien_obtenu and row["statut"] != "entretien"
        confirmer_email = entretien_obtenu and not bool(row.get("entretien_email_envoye"))

        row = db.fetchone(
            con,
            """
            SELECT c.*, o.titre, o.entreprise, o.ville, o.source, o.url, u.email, u.nom
            FROM candidatures c
            JOIN offres o ON o.id = c.offre_id
            JOIN users u ON u.id = c.user_id
            WHERE c.id = ?
            """,
            (cid,),
        )

    email_status = "deja_envoye" if row.get("entretien_email_envoye") else "non_configure"
    if confirmer_email:
        try:
            sent = email.envoyer_confirmation_entretien(
                INTERVIEW_NOTIFICATION_EMAIL or row["email"], row["nom"], row["titre"], row["entreprise"],
                rendezvous["entretien_date"], rendezvous["entretien_lieu"], rendezvous["entretien_notes"],
            )
            if sent:
                with db.get_conn() as con:
                    con.execute("UPDATE candidatures SET entretien_email_envoye = 1 WHERE id = ?", (cid,))
                row["entretien_email_envoye"] = 1
                email_status = "envoye"
        except Exception:
            email_status = "echec"

    # Enregistrer les événements après la fermeture
    # du premier accès à la base de données.
    if nouvel_entretien:
        journal.log(
            user["id"],
            "entretien_obtenu",
            {"id": cid},
        )

        journal.log(
            user["id"],
            "agent_arrete",
            {"raison": "entretien obtenu"},
        )

    result = _enrich(row)
    result["confirmation_email"] = email_status
    return result


@router.post("/{cid}/lettre")
def generer_lettre(cid: int, user: dict = Depends(current_user)):
    plans.assert_peut_generer_lettre(user)

    with db.get_conn() as con:
        row = db.fetchone(
            con,
            """
            SELECT * FROM candidatures
            WHERE id = ? AND user_id = ?
            """,
            (cid, user["id"]),
        )

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Candidature introuvable.",
            )

        offre = db.fetchone(
            con,
            "SELECT * FROM offres WHERE id = ?",
            (row["offre_id"],),
        )

    profil = _profil(user)
    expl = db.parse_json(row.get("explication"), {})
    gen = llm.generer_lettre(profil, offre, expl)

    with db.get_conn() as con:
        con.execute(
            """
            UPDATE candidatures
            SET lettre = ?, date_maj = ?
            WHERE id = ?
            """,
            (
                gen["texte"],
                db.now_iso(),
                cid,
            ),
        )

    journal.log(
        user["id"],
        "lettre_generee",
        {
            "id": cid,
            "source": gen["source"],
        },
    )

    return gen


@router.post("/{cid}/envoyer")
def envoyer(cid: int, user: dict = Depends(current_user)):
    plans.assert_peut_envoyer(user)

    with db.get_conn() as con:
        row = db.fetchone(
            con,
            """
            SELECT * FROM candidatures
            WHERE id = ? AND user_id = ?
            """,
            (cid, user["id"]),
        )

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Candidature introuvable.",
            )

        if not (row.get("lettre") or "").strip():
            raise HTTPException(
                status_code=400,
                detail="Validez ou générez une lettre avant l'envoi.",
            )

        con.execute(
            """
            UPDATE candidatures
            SET statut = 'envoyee', date_maj = ?
            WHERE id = ?
            """,
            (db.now_iso(), cid),
        )

        offre = db.fetchone(
            con,
            """
            SELECT titre, entreprise
            FROM offres
            WHERE id = ?
            """,
            (row["offre_id"],),
        )

    journal.log(
        user["id"],
        "candidature_envoyee",
        {
            "id": cid,
            "mode": "simule",
        },
    )

    return {
        "ok": True,
        "message": (
            f"Candidature marquée comme envoyée "
            f"(simulation pédagogique — aucun e-mail réel) "
            f"pour {offre['titre']} / {offre['entreprise']}."
        ),
    }







@router.post("/{cid}/confirmer-envoi")
def confirmer_envoi(cid: int, user: dict = Depends(current_user)):
    # Vérifier que la candidature appartient au candidat connecté
    with db.get_conn() as con:
        candidature = db.fetchone(
            con,
            """
            SELECT id, statut
            FROM candidatures
            WHERE id = ? AND user_id = ?
            """,
            (cid, user["id"]),
        )

        if not candidature:
            raise HTTPException(
                status_code=404,
                detail="Candidature introuvable.",
            )

        # Éviter de confirmer plusieurs fois la même candidature
        if candidature["statut"] != "a_envoyer":
            raise HTTPException(
                status_code=409,
                detail="Cette candidature n'est plus en attente d'envoi.",
            )

        # Enregistrer la confirmation du candidat
        con.execute(
            """
            UPDATE candidatures
            SET statut = 'envoyee',
                date_maj = ?
            WHERE id = ? AND user_id = ?
            """,
            (db.now_iso(), cid, user["id"]),
        )

    # Enregistrer l'événement dans le journal
    journal.log(
        user["id"],
        "candidature_envoyee",
        {"id": cid, "mode": "confirme_par_candidat"},
    )

    return {
        "ok": True,
        "statut": "envoyee",
        "message": "Votre candidature est maintenant marquée comme envoyée.",
    }











@router.post("/{cid}/cv-adapte")
def cv_adapte(cid: int, user: dict = Depends(current_user)):
    plans.assert_bonus(user, "cv_adapte")

    with db.get_conn() as con:
        row = db.fetchone(
            con,
            """
            SELECT * FROM candidatures
            WHERE id = ? AND user_id = ?
            """,
            (cid, user["id"]),
        )

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Candidature introuvable.",
            )

        offre = db.fetchone(
            con,
            "SELECT * FROM offres WHERE id = ?",
            (row["offre_id"],),
        )

    texte = llm.adapter_cv(_profil(user), offre)

    with db.get_conn() as con:
        con.execute(
            """
            UPDATE candidatures
            SET cv_adapte = ?, date_maj = ?
            WHERE id = ?
            """,
            (
                texte,
                db.now_iso(),
                cid,
            ),
        )

    journal.log(
        user["id"],
        "cv_adapte",
        {"id": cid},
    )

    return {"texte": texte}


@router.post("/{cid}/prep-entretien")
def prep(cid: int, user: dict = Depends(current_user)):
    plans.assert_bonus(user, "prep_entretien")

    with db.get_conn() as con:
        row = db.fetchone(
            con,
            """
            SELECT * FROM candidatures
            WHERE id = ? AND user_id = ?
            """,
            (cid, user["id"]),
        )

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Candidature introuvable.",
            )

        offre = db.fetchone(
            con,
            "SELECT * FROM offres WHERE id = ?",
            (row["offre_id"],),
        )

    texte = llm.prep_entretien(_profil(user), offre)

    with db.get_conn() as con:
        con.execute(
            """
            UPDATE candidatures
            SET questions_entretien = ?, date_maj = ?
            WHERE id = ?
            """,
            (
                texte,
                db.now_iso(),
                cid,
            ),
        )

    journal.log(
        user["id"],
        "prep_entretien",
        {"id": cid},
    )

    return {"texte": texte}


def _document_context(cid: int, user: dict):
    with db.get_conn() as con:
        row = db.fetchone(
            con,
            "SELECT * FROM candidatures WHERE id = ? AND user_id = ?",
            (cid, user["id"]),
        )
        if not row:
            raise HTTPException(status_code=404, detail="Candidature introuvable.")
        offre = db.fetchone(con, "SELECT * FROM offres WHERE id = ?", (row["offre_id"],))
    return row, offre, _profil(user)


def _safe_filename(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value or "candidature").strip("-")[:48]
    return slug or "candidature"


@router.get("/{cid}/documents/cv-adapte.docx")
def telecharger_cv_adapte(cid: int, user: dict = Depends(current_user)):

    plans.assert_bonus(user, "cv_adapte")

    """Create a tailored Word CV using only facts already present in the profile."""
    row, offre, profil = _document_context(cid, user)
    profil["nom"] = user["nom"]
    content = documents.creer_cv_word(profil, offre, user.get("email", ""))
    journal.log(user["id"], "cv_adapte_telecharge", {"id": cid, "format": "docx"})
    filename = _safe_filename(offre.get("titre") or "cv-adapte")
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="CV-{filename}.docx"'},
    )


@router.get("/{cid}/documents/guide-entretien.pdf")
def telecharger_guide_entretien(cid: int, user: dict = Depends(current_user)):

    plans.assert_bonus(user, "prep_entretien")

    """Create a personal PDF guide from the selected job and candidate profile."""
    row, offre, profil = _document_context(cid, user)
    profil["nom"] = user["nom"]
    guide = (row.get("questions_entretien") or "").strip() or llm.prep_entretien(profil, offre)
    if not (row.get("questions_entretien") or "").strip():
        with db.get_conn() as con:
            con.execute(
                "UPDATE candidatures SET questions_entretien = ?, date_maj = ? WHERE id = ?",
                (guide, db.now_iso(), cid),
            )
    content = documents.creer_guide_pdf(
        profil, offre, guide, matching.scorer(profil, offre),
        {key: row.get(key) for key in ("entretien_date", "entretien_lieu", "entretien_notes")},
    )
    journal.log(user["id"], "guide_entretien_telecharge", {"id": cid, "format": "pdf"})
    filename = _safe_filename(offre.get("titre") or "guide-entretien")
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Guide-entretien-{filename}.pdf"'},
    )
