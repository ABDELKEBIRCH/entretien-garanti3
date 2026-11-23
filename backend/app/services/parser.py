
"""Extraction heuristique du CV (PDF / DOCX) — sans inventer de faits."""

from __future__ import annotations

import re
from pathlib import Path

from .matching import normaliser_competence


# Headings used to identify CV sections.
COMP_HEADERS = re.compile(
    r"^(compétences(?: techniques)?|competences(?: techniques)?|"
    r"technical skills?|skills|savoir[- ]faire|technologies|outils)\s*:?\s*$",
    re.I,
)

EXP_HEADERS = re.compile(
    r"^(expériences?(?: professionnelles?)?|experiences?(?: professionnelles?)?|"
    r"professional experience|work experience|employment history|"
    r"parcours professionnel|emploi)\s*:?\s*$",
    re.I,
)

FORM_HEADERS = re.compile(
    r"^(formation|éducation|education|academic background|"
    r"diplômes?|cursus|études|qualifications)\s*:?\s*$",
    re.I,
)

LANG_HEADERS = re.compile(
    r"^(langues|languages)\s*:?\s*$",
    re.I,
)

# These sections are not part of the four fields currently stored
# by the application.
OTHER_HEADERS = re.compile(
    r"^(profil|profile|à propos|about|additional information|"
    r"informations complémentaires|centres d.intérêt|interests|"
    r"loisirs|certifications?|projets|projects|contact|"
    r"references|références)\s*:?\s*$",
    re.I,
)

# These are category labels, not individual skills.
SKILL_CATEGORIES = {
    "programming",
    "programming languages",
    "machine learning",
    "bi & data engineering",
    "data engineering",
    "data analysis",
    "libraries",
    "concepts",
    "tools",
    "frameworks",
    "databases",
    "cloud",
    "development",
    "programmation",
    "langages de programmation",
    "apprentissage automatique",
    "analyse de données",
    "outils",
    "bibliothèques",
    "concepts",
}

LANGUAGE_NAMES = {
    "arabic": "Arabic",
    "arabe": "Arabic",
    "français": "French",
    "francais": "French",
    "french": "French",
    "anglais": "English",
    "english": "English",
    "espagnol": "Spanish",
    "spanish": "Spanish",
    "allemand": "German",
    "german": "German",
    "amazigh": "Amazigh",
    "italien": "Italian",
    "italian": "Italian",
}


def extraire_texte(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _pdf(path)

    if suffix == ".docx":
        return _docx(path)

    raise ValueError("Formats acceptés : PDF et DOCX.")


def _pdf(path: Path) -> str:
    import pdfplumber

    chunks = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            chunks.append(page.extract_text() or "")

    return "\n".join(chunks)


def _docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def structurer(texte: str) -> dict:
    lignes = [
        re.sub(r"\s+", " ", ln).strip()
        for ln in texte.splitlines()
    ]
    lignes = [ln for ln in lignes if ln]

    sections = _decouper(lignes)

    competences = _competences(
        sections.get("competences", "")
    )

    experiences = _puces(
        sections.get("experiences", "")
    )

    formation = _puces(
        sections.get("formation", "")
    )

    langues = _langues(
        sections.get("langues", ""),
        sections.get("autres", ""),
    )

    return {
        "competences": competences,
        "experiences": experiences,
        "formation": formation,
        "langues": langues,
        "cv_texte": texte.strip(),
    }


def _decouper(lignes: list[str]) -> dict[str, str]:
    courant = "autres"

    buckets = {
        "competences": [],
        "experiences": [],
        "formation": [],
        "langues": [],
        "autres": [],
    }

    for ln in lignes:

        if COMP_HEADERS.match(ln):
            courant = "competences"
            continue

        if EXP_HEADERS.match(ln):
            courant = "experiences"
            continue

        if FORM_HEADERS.match(ln):
            courant = "formation"
            continue

        if LANG_HEADERS.match(ln):
            courant = "langues"
            continue

        if OTHER_HEADERS.match(ln):
            courant = "autres"
            continue

        buckets[courant].append(ln)

    return {
        key: "\n".join(value)
        for key, value in buckets.items()
    }


def _competences(bloc: str) -> list[str]:
    if not bloc:
        return []

    items = []

    for ligne in bloc.splitlines():

        # Example: "Programming: Python, SQL, MATLAB"
        if ":" in ligne:
            _, contenu = ligne.split(":", 1)
            ligne = contenu

        morceaux = re.split(r"[,;•·|]", ligne)

        for raw in morceaux:
            item = raw.strip(" -–\t")

            if not item:
                continue

            if item.lower() in SKILL_CATEGORIES:
                continue

            if len(item) < 2 or len(item) > 60:
                continue

            items.append(item)

    # Remove duplicates while preserving the original order.
    seen = set()
    resultat = []

    for item in items:
        key = normaliser_competence(item)

        if not key or key in seen:
            continue

        seen.add(key)
        resultat.append(item)

    # Avoid displaying "scikit" alongside "scikit-learn".
    normalized = {
        normaliser_competence(item)
        for item in resultat
    }

    if "scikit-learn" in normalized:
        resultat = [
            item for item in resultat
            if normaliser_competence(item) != "scikit"
        ]

    return resultat[:80]


def _puces(bloc: str) -> list[str]:
    if not bloc:
        return []

    resultat = []

    for ligne in bloc.splitlines():
        ligne = ligne.strip(" -•–\t")

        if len(ligne) > 8:
            resultat.append(ligne)

    return resultat[:20]


def _langues(bloc: str, autres: str) -> list[str]:
    resultat = []

    # First, read the dedicated Languages section.
    sources = [bloc]

    # Also support lines such as:
    # Languages: Arabic (Native) · French (Professional...)
    for ligne in autres.splitlines():
        if re.match(r"^\s*(languages|langues)\s*:", ligne, re.I):
            sources.append(ligne.split(":", 1)[1])

    for source in sources:
        if not source:
            continue

        morceaux = re.split(r"[,;•·|]", source)

        for morceau in morceaux:
            morceau = morceau.strip(" -–\t")

            if not morceau:
                continue

            match = re.match(
                r"^([A-Za-zÀ-ÿ]+)(.*)$",
                morceau
            )

            if not match:
                continue

            nom = match.group(1).lower()
            niveau = match.group(2).strip()

            langue = LANGUAGE_NAMES.get(nom)

            if not langue:
                continue

            valeur = langue

            if niveau:
                valeur += f" {niveau}"

            if valeur.lower() not in {
                item.lower() for item in resultat
            }:
                resultat.append(valeur)

    return resultat[:12]
