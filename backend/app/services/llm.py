"""Génération de textes : LLM si clé présente, sinon gabarit factuel. Jamais d'invention."""

from __future__ import annotations

import json
import re

import httpx

from ..config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL


GARDE_FOU = """
Tu es un assistant de candidature honnête.
Règles STRICTES :
- N'invente AUCUNE compétence, diplôme, entreprise, date ou réalisation absente du CV.
- Si l'offre demande quelque chose d'absent, ne le prétends pas : tu peux mentionner une motivation d'apprentissage sans mentir.
- Utilise uniquement les faits fournis (profil JSON + extraits de CV).
- Français soutenu, 280 à 420 mots, structure : accroche, adéquation, 2 faits du parcours, conclusion.
- Ne mentionne pas que tu es une IA.
"""


def faits_autorises(profil: dict) -> dict:
    return {
        "competences": profil.get("competences") or [],
        "experiences": profil.get("experiences") or [],
        "formation": profil.get("formation") or [],
        "langues": profil.get("langues") or [],
        "extrait_cv": (profil.get("cv_texte") or "")[:4000],
    }


def filtrer_invention(texte: str, profil: dict) -> str:
    """Retire les phrases qui affirment des compétences hors CV (heuristique)."""
    autorise = {c.lower() for c in (profil.get("competences") or [])}
    cv = (profil.get("cv_texte") or "").lower()
    lignes = []
    interdites = []
    for phrase in re.split(r"(?<=[.!?])\s+", texte):
        low = phrase.lower()
        suspect = False
        for mot in ("expert en", "maîtrise parfaite", "certifié", "10 ans d'expérience"):
            if mot in low and mot not in cv:
                suspect = True
        if suspect:
            interdites.append(phrase)
            continue
        lignes.append(phrase)
    clean = " ".join(lignes).strip()
    if interdites:
        clean += (
            "\n\n[Contrôle d'honnêteté] Des formulations trop affirmatives hors CV ont été écartées. "
            "Compétences autorisées : " + ", ".join(sorted(autorise)[:20]) + "."
        )
    return clean


def lettre_gabarit(profil: dict, offre: dict, matching: dict | None = None) -> str:
    nom = profil.get("nom") or "le/la candidat(e)"
    comps = ", ".join((profil.get("competences") or [])[:8]) or "les compétences décrites dans mon CV"
    exp = (profil.get("experiences") or ["un parcours détaillé dans le CV joint"])[0]
    form = (profil.get("formation") or ["ma formation"])[0]
    communs = ""
    if matching and matching.get("competences_communes"):
        communs = " En particulier : " + ", ".join(matching["competences_communes"][:6]) + "."
    ville = offre.get("ville") or "votre localisation"
    return (
        f"Objet : Candidature — {offre.get('titre')}\n\n"
        f"Madame, Monsieur,\n\n"
        f"Je vous adresse ma candidature pour le poste de {offre.get('titre')} au sein de "
        f"{offre.get('entreprise') or 'votre entreprise'} ({ville}). "
        f"Mon profil s'appuie sur {form}, et sur l'expérience suivante : {exp}.\n\n"
        f"Les éléments de mon CV en lien avec votre annonce sont : {comps}.{communs} "
        f"Je n'attribue à mon parcours que ce qui y figure réellement ; si l'annonce exige "
        f"d'autres outils, je suis prêt(e) à les apprendre sans les présenter comme déjà acquis.\n\n"
        f"Je serais heureux(se) d'échanger lors d'un entretien pour préciser ma motivation "
        f"et la façon dont je pourrais contribuer à vos équipes.\n\n"
        f"Veuillez agréer, Madame, Monsieur, l'expression de mes salutations distinguées.\n\n"
        f"{nom}"
    )


def _chat(messages: list[dict]) -> str | None:
    if not OPENAI_API_KEY:
        return None
    try:
        with httpx.Client(timeout=45.0) as client:
            r = client.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={"model": OPENAI_MODEL, "temperature": 0.3, "messages": messages},
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def generer_lettre(profil: dict, offre: dict, matching: dict | None = None) -> dict:
    faits = faits_autorises(profil)
    prompt_user = (
        "Rédige une lettre de motivation.\nOffre :\n"
        + json.dumps(
            {k: offre.get(k) for k in ("titre", "entreprise", "ville", "description")},
            ensure_ascii=False,
        )
        + "\nProfil (seules sources autorisées) :\n"
        + json.dumps(faits, ensure_ascii=False)
        + "\nPoints de matching :\n"
        + json.dumps(matching or {}, ensure_ascii=False)
    )
    llm = _chat(
        [
            {"role": "system", "content": GARDE_FOU},
            {"role": "user", "content": prompt_user},
        ]
    )
    source = "llm" if llm else "gabarit"
    texte = filtrer_invention(llm, profil) if llm else lettre_gabarit(profil, offre, matching)
    return {"texte": texte, "source": source, "honnetete": "faits_cv_uniquement"}


def adapter_cv(profil: dict, offre: dict) -> str:
    comps = profil.get("competences") or []
    desc = (offre.get("description") or "").lower()
    mises = [c for c in comps if c.lower() in desc]
    autres = [c for c in comps if c not in mises]
    lignes = [
        f"CV adapté pour : {offre.get('titre')} — {offre.get('entreprise')}",
        "",
        "Mots-clés de l'offre présents dans le CV (mis en avant, jamais inventés) :",
        "- " + ", ".join(mises or ["aucun mot-clé commun — le CV original reste la référence"]),
        "",
        "Autres compétences du CV :",
        "- " + ", ".join(autres or ["—"]),
        "",
        "Expériences (inchangées) :",
    ]
    for e in profil.get("experiences") or []:
        lignes.append(f"- {e}")
    lignes += ["", "Formation :"]
    for f in profil.get("formation") or []:
        lignes.append(f"- {f}")
    lignes += [
        "",
        "Note éthique : aucune expérience absente du CV n'a été ajoutée. Seul l'ordre / la mise en avant change.",
    ]
    return "\n".join(lignes)


def prep_entretien(profil: dict, offre: dict) -> str:
    titre = offre.get("titre") or "ce poste"
    faits = faits_autorises(profil)
    llm = _chat(
        [
            {
                "role": "system",
                "content": "Coach d'entretien honnête. Questions + pistes de réponses UNIQUEMENT à partir du CV. 8 questions.",
            },
            {
                "role": "user",
                "content": json.dumps({"offre": offre.get("titre"), "profil": faits}, ensure_ascii=False),
            },
        ]
    )
    if llm:
        return llm
    comps = ", ".join((profil.get("competences") or [])[:6]) or "votre parcours"
    return (
        f"Préparation — {titre} chez {offre.get('entreprise')}\n\n"
        f"1. Présentez-vous en 2 minutes en vous appuyant uniquement sur votre formation et vos expériences listées.\n"
        f"2. Pourquoi {offre.get('entreprise')} et ce poste ? Reliez la description de l'annonce à {comps}.\n"
        f"3. Décrivez une réalisation concrète déjà écrite dans votre CV.\n"
        f"4. Quel outil de l'annonce maîtrisez-vous vraiment ? Ne citez que des compétences du CV.\n"
        f"5. Quelle limite reconnaissez-vous (compétence demandée absente du CV) et comment l'apprendrez-vous ?\n"
        f"6. Question sur le travail en équipe / communication.\n"
        f"7. Pretentions et disponibilité.\n"
        f"8. Avez-vous des questions ? (équipe, stack réelle, critères des 90 premiers jours)\n\n"
        f"Rappel : ne jamais inventer un projet ou un diplôme pendant l'oral."
    )
