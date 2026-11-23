
from __future__ import annotations

import re
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse  # permet de renvoyer le navigateur vers une autre adresse
from pydantic import BaseModel, Field

from .. import db
from ..auth import create_token, current_user, hash_password, verify_password
from ..config import APP_BASE_URL
from ..services import journal
from ..services.email import envoyer_verification_email

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Email format validation
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterIn(BaseModel):
    nom: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=180)
    password: str = Field(min_length=8, max_length=128)
    password_confirm: str = Field(min_length=8, max_length=128)
    consentement_09_08: bool
    formule: str = "decouverte"


class LoginIn(BaseModel):
    email: str
    password: str


class ResendVerificationIn(BaseModel):
    email: str


def _public_user(user: dict) -> dict:
    user = dict(user)
    user.pop("password_hash", None)
    return user


# --------------------------------------------------
# Registration
# --------------------------------------------------

@router.post("/register")
def register(body: RegisterIn):
    if not body.consentement_09_08:
        raise HTTPException(
            status_code=400,
            detail="Le consentement à la loi 09-08 (données personnelles) est obligatoire.",
        )

    if body.password != body.password_confirm:
        raise HTTPException(
            status_code=400,
            detail="Les deux mots de passe ne correspondent pas.",
        )

    if not EMAIL_RE.match(body.email.strip().lower()):
        raise HTTPException(status_code=400, detail="E-mail invalide.")

    email = body.email.strip().lower()

    formule = (
        body.formule
        if body.formule in {"decouverte", "candidat", "garanti"}
        else "decouverte"
    )

    # Generate a secure verification token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    expires_at = (
        datetime.now(timezone.utc) + timedelta(hours=24)
    ).isoformat()

    with db.get_conn() as con:
        if db.fetchone(con, "SELECT id FROM users WHERE email = ?", (email,)):
            raise HTTPException(
                status_code=409,
                detail="Un compte existe déjà avec cet e-mail.",
            )

        cur = con.execute(
            """
            INSERT INTO users (
                nom, email, password_hash, formule,
                date_inscription, consentement_09_08, consentement_date,
                email_verified, verification_token, verification_expires_at
            )
            VALUES (?, ?, ?, ?, ?, 1, ?, 0, ?, ?)
            """,
            (
                body.nom.strip(),
                email,
                hash_password(body.password),
                formule,
                db.now_iso(),
                db.now_iso(),
                token_hash,
                expires_at,
            ),
        )

        uid = cur.lastrowid
        con.execute(
            "INSERT INTO profils (user_id) VALUES (?)",
            (uid,),
        )

    journal.log(uid, "inscription", {"formule": formule})

    lien = f"{APP_BASE_URL}/api/auth/verifier?token={raw_token}"

    try:
        envoyer_verification_email(email, body.nom.strip(), lien)
    except Exception:
        print(f"Lien de vérification pour {email}: {lien}")

    return {
        "message": (
            "Inscription réussie. Veuillez vérifier votre adresse e-mail "
            "pour activer votre compte."
        )
    }


# --------------------------------------------------
# Email verification
# --------------------------------------------------

@router.get("/verifier")
def verifier_email(token: str):
    # On ne stocke que le hash du token : on hache celui reçu dans le lien pour pouvoir le comparer.
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    now = db.now_iso()  # heure actuelle, pour vérifier que le lien n'a pas dépassé 24 h

    with db.get_conn() as con:
        user = db.fetchone(
            con,
            """
            SELECT id, email FROM users
            WHERE verification_token = ?
              AND verification_expires_at > ?
              AND email_verified = 0
            """,
            (token_hash, now),
        )

        if not user:
            # Lien faux, expiré ou déjà utilisé : on renvoie vers la page de connexion avec verifie=0.
            # 303 = "va voir cette autre adresse", le navigateur suit automatiquement.
            return RedirectResponse(url="/?verifie=0#/connexion", status_code=303)

        # Compte vérifié : on efface le token pour qu'il ne puisse plus être réutilisé.
        con.execute(
            """
            UPDATE users
            SET email_verified = 1,
                verification_token = NULL,
                verification_expires_at = NULL
            WHERE id = ?
            """,
            (user["id"],),
        )

    journal.log(user["id"], "verification_email", {})

    # Succès : page de connexion avec verifie=1 (la page affichera le message vert).
    # Le "?verifie=1" est placé AVANT le "#" car le routage de l'app lit uniquement ce qui suit le "#".
    return RedirectResponse(url="/?verifie=1#/connexion", status_code=303)






# --------------------------------------------------
# Resend verification email
# --------------------------------------------------

@router.post("/renvoyer-verification")
def renvoyer_verification(body: ResendVerificationIn):
    email = body.email.strip().lower()

    with db.get_conn() as con:
        user = db.fetchone(
            con,
            "SELECT id, nom, email_verified FROM users WHERE email = ?",
            (email,),
        )

        if user and not user["email_verified"]:
            raw_token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

            expires_at = (
                datetime.now(timezone.utc) + timedelta(hours=24)
            ).isoformat()

            con.execute(
                """
                UPDATE users
                SET verification_token = ?, verification_expires_at = ?
                WHERE id = ?
                """,
                (token_hash, expires_at, user["id"]),
            )

    if user and not user["email_verified"]:
        lien = f"{APP_BASE_URL}/api/auth/verifier?token={raw_token}"

        try:
            envoyer_verification_email(email, user["nom"], lien)
        except Exception:
            print(f"Lien de vérification pour {email}: {lien}")

    return {
        "message": (
            "Si un compte non vérifié existe avec cette adresse, "
            "un nouveau lien sera envoyé."
        )
    }


# --------------------------------------------------
# Login
# --------------------------------------------------

@router.post("/login")
def login(body: LoginIn):
    email = body.email.strip().lower()

    with db.get_conn() as con:
        user = db.fetchone(
            con,
            "SELECT * FROM users WHERE email = ?",
            (email,),
        )

    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects.",
        )

    if not user.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Veuillez vérifier votre adresse e-mail avant de vous connecter.",
        )

    journal.log(user["id"], "connexion", {})

    return {
        "token": create_token(user["id"], email),
        "user": _public_user(user),
    }


# --------------------------------------------------
# Current user
# --------------------------------------------------

@router.get("/me")
def me(user: dict = Depends(current_user)):
    with db.get_conn() as con:
        profil = db.fetchone(
            con,
            "SELECT * FROM profils WHERE user_id = ?",
            (user["id"],),
        )

    if profil:
        for key in ("competences", "experiences", "formation", "langues"):
            profil[key] = db.parse_json(profil.get(key), [])

    return {"user": user, "profil": profil}


# --------------------------------------------------
# Account deletion
# --------------------------------------------------

@router.delete("/compte")
def supprimer_compte(user: dict = Depends(current_user)):
    """Droit de suppression (loi 09-08 / minimisation)."""

    with db.get_conn() as con:
        con.execute(
            "DELETE FROM candidatures WHERE user_id = ?",
            (user["id"],),
        )
        con.execute(
            "DELETE FROM profils WHERE user_id = ?",
            (user["id"],),
        )
        con.execute(
            "DELETE FROM journal WHERE user_id = ?",
            (user["id"],),
        )
        con.execute(
            "DELETE FROM users WHERE id = ?",
            (user["id"],),
        )

    return {
        "ok": True,
        "message": "Compte et données personnelles supprimés.",
    }
