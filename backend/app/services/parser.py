"""Extraction heuristique du CV (PDF / DOCX) — sans inventer de faits."""

from __future__ import annotations

import re
from pathlib import Path

COMP_HEADERS = re.compile(
    r"^(compétences|competences|skills|savoir[- ]faire|technologies|outils)\b",
    re.I,
)
EXP_HEADERS = re.compile(
    r"^(expériences?|experience|parcours professionnel|emploi)\b",
    re.I,
)
FORM_HEADERS = re.compile(
    r"^(formation|éducation|education|diplômes?|cursus|études)\b",
    re.I,
)
LANG_HEADERS = re.compile(
    r"^(langues|languages)\b",
    re.I,
)
OTHER_HEADERS = re.compile(
    r"^(profil|à propos|about|centres d.intérêt|loisirs|certifications?|projets|contact)\b",
    re.I,
)

SKILL_HINTS = [
    "python", "java", "javascript", "typescript", "react", "vue", "angular", "node",
    "django", "flask", "fastapi", "sql", "mysql", "postgresql", "sqlite", "mongodb",
    "excel", "power bi", "tableau", "pandas", "numpy", "scikit", "tensorflow",
    "docker", "git", "linux", "html", "css", "php", "laravel", "spring", "c++",
    "c#", ".net", "kotlin", "swift", "figma", "photoshop", "word", "powerpoint",
    "communication", "gestion de projet", "agile", "scrum", "marketing", "seo",
    "canva", "sap", "salesforce", "r", "matlab", "autocad", "solidworks",
]


def extraire_texte(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _pdf(path)
    if suffix in {".docx", ".doc"}:
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
    lignes = [re.sub(r"\s+", " ", ln).strip() for ln in texte.splitlines()]
    lignes = [ln for ln in lignes if ln]
    sections = _decouper(lignes)
    competences = _competences(sections.get("competences", ""), texte)
    experiences = _puces(sections.get("experiences", ""))
    formation = _puces(sections.get("formation", ""))
    langues = _langues(sections.get("langues", ""), texte)
    return {
        "competences": competences,
        "experiences": experiences,
        "formation": formation,
        "langues": langues,
        "cv_texte": texte.strip(),
    }


def _decouper(lignes: list[str]) -> dict[str, str]:
    courant = "profil"
    buckets: dict[str, list[str]] = {
        "profil": [],
        "competences": [],
        "experiences": [],
        "formation": [],
        "langues": [],
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
            courant = "profil"
            continue
        buckets.setdefault(courant, []).append(ln)
    return {k: "\n".join(v) for k, v in buckets.items()}


def _competences(bloc: str, texte: str) -> list[str]:
    from .matching import extraire_competences, normaliser_competence

    items = []
    if bloc:
        for raw in re.split(r"[,;•·\n|/]", bloc):
            s = raw.strip(" -–")
            if 1 < len(s) < 48:
                items.append(s)
    found = {s.lower() for s in items}
    # Les anciens tests par sous-chaîne produisaient des faux positifs
    # (par exemple « r » dans presque chaque mot). Les termes courts sont
    # maintenant vérifiés comme des mots entiers ; le catalogue partagé couvre
    # les compétences plus longues et leurs variantes.
    for hint in SKILL_HINTS:
        if hint == "r":
            present = bool(re.search(r"(?<!\w)R(?!\w)|\bRStudio\b", texte))
        else:
            present = bool(re.search(rf"(?<![\w]){re.escape(hint)}(?![\w])", texte, re.I))
        if present and hint not in found:
            items.append(hint)
            found.add(hint)
    items.extend(extraire_competences(texte))
    # déduplication en conservant l'ordre
    seen = set()
    out = []
    for it in items:
        key = normaliser_competence(it)
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out


def _puces(bloc: str) -> list[str]:
    if not bloc:
        return []
    lignes = []
    for ln in bloc.splitlines():
        ln = ln.strip(" -•–\t")
        if len(ln) > 8:
            lignes.append(ln)
    return lignes[:20]


def _langues(bloc: str, texte: str) -> list[str]:
    cibles = ["français", "arabe", "anglais", "espagnol", "allemand", "amazigh", "italien"]
    source = (bloc + "\n" + texte).lower()
    out = []
    for lang in cibles:
        if lang in source:
            out.append(lang.capitalize())
    if bloc:
        for raw in re.split(r"[,;•\n|/]", bloc):
            s = raw.strip()
            if s and s.lower() not in {x.lower() for x in out} and len(s) < 40:
                out.append(s)
    return out[:12]
