from pathlib import Path

from docx import Document

from app.services.parser import structurer, extraire_texte


CV = """
Sara El Amrani
Développeuse junior

FORMATION
Licence informatique, Université Hassan II, 2024

EXPÉRIENCES
Stage de 6 mois : APIs Python FastAPI et SQL chez Atlas Data Labs

COMPÉTENCES
Python, FastAPI, SQL, Git, Docker, Excel

LANGUES
Français, Arabe, Anglais
"""


def test_structurer_sections():
    p = structurer(CV)
    assert any("python" == c.lower() for c in p["competences"])
    assert p["experiences"]
    assert p["formation"]
    assert any("français" == x.lower() for x in p["langues"])
    assert "Atlas" in p["cv_texte"]


def test_docx_roundtrip(tmp_path: Path):
    path = tmp_path / "cv.docx"
    doc = Document()
    for line in CV.strip().splitlines():
        doc.add_paragraph(line)
    doc.save(path)
    texte = extraire_texte(path)
    p = structurer(texte)
    assert "FastAPI" in p["cv_texte"] or "fastapi" in p["cv_texte"].lower()
