"""Génère une dizaine de CV DOCX pour tester le parseur."""

from pathlib import Path

from docx import Document

OUT = Path(__file__).resolve().parents[1] / "data" / "sample_cvs"

PEOPLE = [
    ("Sara El Amrani", "Licence informatique 2024", "Stage FastAPI SQL Git", "Python FastAPI SQL Git Docker Excel", "Casablanca"),
    ("Youssef Benali", "Master data 2025", "Projet Power BI pandas SQL", "Python pandas SQL Power BI Excel", "Rabat"),
    ("Imane Kadiri", "Licence MIAGE", "Stage React Node Git", "JavaScript React Node HTML CSS Git", "Tanger"),
    ("Omar Tazi", "DUT réseaux", "Support Windows Linux", "Linux Windows réseaux Git", "Casablanca"),
    ("Nadia Senhaji", "Licence marketing", "Stage SEO Canva", "SEO Canva Excel communication", "Marrakech"),
    ("Mehdi Lahlou", "Cycle ingénieur logiciel", "Java Spring SQL", "Java Spring SQL Git", "Rabat"),
    ("Fatima Zahra Ouazzani", "Licence design", "Stage Figma Photoshop", "Figma Photoshop UI UX", "Fès"),
    ("Anas Chraibi", "Master cybersécurité", "Projet Linux Python logs", "Linux Python réseaux Git", "Rabat"),
    ("Salma Berrada", "Licence LEA", "Rédaction WordPress SEO", "SEO WordPress français rédaction", "Télétravail"),
    ("Karim El Fassi", "Licence gestion", "Stage Excel Sage", "Excel Sage comptabilité", "Casablanca"),
    ("Hajar Mouline", "Licence informatique", "App Flutter API REST", "Flutter Dart Git API", "Casablanca"),
    ("Reda Amrani", "Master SI", "Assistant projet Agile Scrum", "Agile Scrum Excel communication SQL", "Rabat"),
]


def build(nom, form, exp, skills, ville):
    d = Document()
    d.add_paragraph(nom)
    d.add_paragraph(ville)
    d.add_paragraph("FORMATION")
    d.add_paragraph(form)
    d.add_paragraph("EXPÉRIENCES")
    d.add_paragraph(exp)
    d.add_paragraph("COMPÉTENCES")
    d.add_paragraph(skills)
    d.add_paragraph("LANGUES")
    d.add_paragraph("Français, Arabe, Anglais")
    slug = nom.lower().replace(" ", "_")
    path = OUT / f"cv_{slug}.docx"
    d.save(path)
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for p in PEOPLE:
        print(build(*p))
    # sara canonique
    build("Sara El Amrani", "Licence sciences et techniques informatique, Université Hassan II, 2024",
          "Stage 6 mois Atlas Data Labs : APIs Python FastAPI, SQL, Git",
          "Python, FastAPI, SQL, Git, Docker, Excel, HTML, CSS", "Casablanca")
    (OUT / "cv_sara.docx").unlink(missing_ok=True)
    src = OUT / "cv_sara_el_amrani.docx"
    if src.exists():
        src.replace(OUT / "cv_sara.docx")


if __name__ == "__main__":
    main()
