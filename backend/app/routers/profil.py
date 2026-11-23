
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from .. import db
from ..auth import current_user
from ..config import UPLOAD_DIR
from ..services import journal
from ..services.parser import extraire_texte, structurer

router = APIRouter(prefix="/api/profil", tags=["profil"])


class ProfilIn(BaseModel):
    competences: list[str] | None = None
    experiences: list[str] | None = None
    formation: list[str] | None = None
    langues: list[str] | None = None
    pref_poste: str | None = None
    pref_ville: str | None = None
    pref_contrat: str | None = None


def _dump_profil(row: dict) -> dict:
    out = dict(row)

    for key in ("competences", "experiences", "formation", "langues"):
        out[key] = db.parse_json(out.get(key), [])

    return out


@router.get("")
def get_profil(user: dict = Depends(current_user)):
    with db.get_conn() as con:
        row = db.fetchone(
            con,
            "SELECT * FROM profils WHERE user_id = ?",
            (user["id"],),
        )

    return _dump_profil(row) if row else {}


@router.put("")
def put_profil(body: ProfilIn, user: dict = Depends(current_user)):
    with db.get_conn() as con:
        row = db.fetchone(
            con,
            "SELECT * FROM profils WHERE user_id = ?",
            (user["id"],),
        )

        # Create the profile if it does not exist.
        if not row:
            con.execute(
                "INSERT INTO profils (user_id) VALUES (?)",
                (user["id"],),
            )

            row = db.fetchone(
                con,
                "SELECT * FROM profils WHERE user_id = ?",
                (user["id"],),
            )

        data = _dump_profil(row)
        updates = body.model_dump(exclude_none=True)

        # Apply only the fields provided by the user.
        for key, value in updates.items():
            data[key] = value

        con.execute(
            """
            UPDATE profils SET
                competences=?,
                experiences=?,
                formation=?,
                langues=?,
                pref_poste=?,
                pref_ville=?,
                pref_contrat=?
            WHERE user_id=?
            """,
            (
                json.dumps(data["competences"], ensure_ascii=False),
                json.dumps(data["experiences"], ensure_ascii=False),
                json.dumps(data["formation"], ensure_ascii=False),
                json.dumps(data["langues"], ensure_ascii=False),
                data.get("pref_poste") or "",
                data.get("pref_ville") or "",
                data.get("pref_contrat") or "",
                user["id"],
            ),
        )

        row = db.fetchone(
            con,
            "SELECT * FROM profils WHERE user_id = ?",
            (user["id"],),
        )

    journal.log(user["id"], "maj_profil", {})

    return _dump_profil(row)


@router.post("/cv")
async def upload_cv(
    file: UploadFile = File(...),
    user: dict = Depends(current_user),
):
    # Check the uploaded file format.
    name = file.filename or "cv.pdf"
    suffix = Path(name).suffix.lower()

    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=400,
            detail="CV au format PDF ou DOCX uniquement.",
        )

    # Save the CV file.
    dest = UPLOAD_DIR / f"user_{user['id']}{suffix}"
    content = await file.read()

    if len(content) > 8_000_000:
        raise HTTPException(
            status_code=400,
            detail="Fichier trop volumineux (8 Mo max).",
        )

    dest.write_bytes(content)

    # Extract and structure the CV information.
    try:
        texte = extraire_texte(dest)
        struct = structurer(texte)

    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Lecture du CV impossible : {exc}",
        ) from exc

    # Save the extracted information in the user's profile.
    with db.get_conn() as con:

        # Create a profile if the user does not have one yet.
        con.execute(
            """
            INSERT INTO profils (user_id)
            VALUES (?)
            ON CONFLICT(user_id) DO NOTHING
            """,
            (user["id"],),
        )

        # Update the profile with the extracted CV information.
        con.execute(
            """
            UPDATE profils SET
                competences=?,
                experiences=?,
                formation=?,
                langues=?,
                cv_texte=?,
                cv_filename=?
            WHERE user_id=?
            """,
            (
                json.dumps(struct["competences"], ensure_ascii=False),
                json.dumps(struct["experiences"], ensure_ascii=False),
                json.dumps(struct["formation"], ensure_ascii=False),
                json.dumps(struct["langues"], ensure_ascii=False),
                struct["cv_texte"],
                name,
                user["id"],
            ),
        )

        row = db.fetchone(
            con,
            "SELECT * FROM profils WHERE user_id = ?",
            (user["id"],),
        )

    # Record the CV import in the activity journal.
    journal.log(
        user["id"],
        "import_cv",
        {
            "fichier": name,
            "competences": len(struct["competences"]),
        },
    )

    return _dump_profil(row)
