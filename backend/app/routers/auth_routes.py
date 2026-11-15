from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .. import db
from ..auth import create_token, current_user, hash_password, verify_password
from ..services import journal

router = APIRouter(prefix="/api/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterIn(BaseModel):
    nom: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=180)
    password: str = Field(min_length=8, max_length=128)
    consentement_09_08: bool
    formule: str = "decouverte"


class LoginIn(BaseModel):
    email: str
    password: str


def _public_user(user: dict) -> dict:
    user = dict(user)
    user.pop("password_hash", None)
    return user


@router.post("/register")
def register(body: RegisterIn):
    if not body.consentement_09_08:
        raise HTTPException(
            status_code=400,
            detail="Le consentement à la loi 09-08 (données personnelles) est obligatoire.",
        )
    if not EMAIL_RE.match(body.email.strip().lower()):
        raise HTTPException(status_code=400, detail="E-mail invalide.")
    email = body.email.strip().lower()
    formule = body.formule if body.formule in {"decouverte", "candidat", "garanti"} else "decouverte"
    with db.get_conn() as con:
        if db.fetchone(con, "SELECT id FROM users WHERE email = ?", (email,)):
            raise HTTPException(status_code=409, detail="Un compte existe déjà avec cet e-mail.")
        cur = con.execute(
            """
            INSERT INTO users (nom, email, password_hash, formule, date_inscription, consentement_09_08, consentement_date)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """,
            (body.nom.strip(), email, hash_password(body.password), formule, db.now_iso(), db.now_iso()),
        )
        uid = cur.lastrowid
        con.execute("INSERT INTO profils (user_id) VALUES (?)", (uid,))
        user = db.fetchone(con, "SELECT * FROM users WHERE id = ?", (uid,))
    journal.log(uid, "inscription", {"formule": formule})
    token = create_token(uid, email)
    return {"token": token, "user": _public_user(user)}


@router.post("/login")
def login(body: LoginIn):
    email = body.email.strip().lower()
    with db.get_conn() as con:
        user = db.fetchone(con, "SELECT * FROM users WHERE email = ?", (email,))
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects.")
    journal.log(user["id"], "connexion", {})
    return {"token": create_token(user["id"], email), "user": _public_user(user)}


@router.get("/me")
def me(user: dict = Depends(current_user)):
    with db.get_conn() as con:
        profil = db.fetchone(con, "SELECT * FROM profils WHERE user_id = ?", (user["id"],))
    if profil:
        for key in ("competences", "experiences", "formation", "langues"):
            profil[key] = db.parse_json(profil.get(key), [])
    return {"user": user, "profil": profil}


@router.delete("/compte")
def supprimer_compte(user: dict = Depends(current_user)):
    """Droit de suppression (loi 09-08 / minimisation)."""
    with db.get_conn() as con:
        con.execute("DELETE FROM candidatures WHERE user_id = ?", (user["id"],))
        con.execute("DELETE FROM profils WHERE user_id = ?", (user["id"],))
        con.execute("DELETE FROM journal WHERE user_id = ?", (user["id"],))
        con.execute("DELETE FROM users WHERE id = ?", (user["id"],))
    return {"ok": True, "message": "Compte et données personnelles supprimés."}
