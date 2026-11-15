
from __future__ import annotations

from fastapi import HTTPException, status

from .. import db
from ..config import FORMULES


def formule_of(user: dict) -> dict:
    key = user.get("formule") or "decouverte"
    return FORMULES.get(key, FORMULES["decouverte"]) | {"id": key}


def compteur(user_id: int) -> dict:
    with db.get_conn() as con:
        lettres = db.fetchone(
            con,
            """
            SELECT COUNT(*) AS n
            FROM candidatures
            WHERE user_id = ?
              AND lettre IS NOT NULL
              AND lettre != ''
            """,
            (user_id,),
        )

        envois = db.fetchone(
            con,
            """
            SELECT COUNT(*) AS n
            FROM candidatures
            WHERE user_id = ?
              AND statut != 'a_envoyer'
            """,
            (user_id,),
        )

        entretien = db.fetchone(
            con,
            """
            SELECT COUNT(*) AS n
            FROM candidatures
            WHERE user_id = ?
              AND statut = 'entretien'
            """,
            (user_id,),
        )

    return {
        "lettres": int(lettres["n"] if lettres else 0),
        "envois": int(envois["n"] if envois else 0),
        "entretien_obtenu": int(entretien["n"] if entretien else 0) > 0,
    }


def agent_arrete(user_id: int) -> bool:
    return compteur(user_id)["entretien_obtenu"]


def assert_peut_matcher(user: dict, nb_offres: int) -> None:
    plan = formule_of(user)

    if nb_offres > plan["max_matchs"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"La formule {plan['nom']} affiche au plus "
                f"{plan['max_matchs']} offres. "
                "Passez à une formule supérieure."
            ),
        )


def assert_peut_generer_lettre(user: dict) -> None:
    plan = formule_of(user)
    c = compteur(user["id"])

    if c["lettres"] >= plan["max_lettres"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Quota de lettres atteint ({plan['max_lettres']}) "
                f"pour la formule {plan['nom']}."
            ),
        )


def assert_peut_envoyer(user: dict) -> None:
    if agent_arrete(user["id"]):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Règle d'arrêt : un entretien est déjà obtenu. "
                "Les candidatures sont suspendues."
            ),
        )

    plan = formule_of(user)
    c = compteur(user["id"])

    if c["envois"] >= plan["max_envois"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Quota d'envois atteint ({plan['max_envois']}) "
                f"pour la formule {plan['nom']}."
            ),
        )


def assert_bonus(user: dict, feature: str) -> None:
    plan = formule_of(user)

    if not plan.get(feature):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"La fonctionnalité n'est pas incluse "
                f"dans la formule {plan['nom']}."
            ),
        )
