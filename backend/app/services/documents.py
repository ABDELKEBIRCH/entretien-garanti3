"""Create downloadable, application-specific CV and interview guide documents."""

from __future__ import annotations

import html
import io
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from . import matching


def _register_pdf_fonts() -> tuple[str, str]:
    regular_candidates = (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    )
    bold_candidates = (
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
    )
    regular = next((path for path in regular_candidates if path.is_file()), None)
    bold = next((path for path in bold_candidates if path.is_file()), None)
    if regular:
        try:
            try:
                pdfmetrics.getFont("EntretienSans")
            except KeyError:
                pdfmetrics.registerFont(TTFont("EntretienSans", str(regular)))
                if bold:
                    pdfmetrics.registerFont(TTFont("EntretienSans-Bold", str(bold)))
                pdfmetrics.registerFontFamily(
                    "EntretienSans", normal="EntretienSans",
                    bold="EntretienSans-Bold" if bold else "EntretienSans",
                    italic="EntretienSans", boldItalic="EntretienSans-Bold" if bold else "EntretienSans",
                )
            return "EntretienSans", "EntretienSans-Bold" if bold else "EntretienSans"
        except Exception:
            pass
    return "Helvetica", "Helvetica-Bold"


def _clean_text(value) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value or ""))


def _list(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [_clean_text(line.strip(" •\t-")) for line in value.splitlines() if line.strip(" •\t-")]
    return [_clean_text(item).strip() for item in value if str(item).strip()]


def _cv_sections(profil: dict, offre: dict) -> dict:
    skills = _list(profil.get("competences"))
    result = matching.scorer(profil, offre)
    common = result.get("competences_communes", [])
    common_keys = {skill.casefold() for skill in common}
    prioritized = [skill for skill in skills if skill.casefold() in common_keys]
    remaining = [skill for skill in skills if skill.casefold() not in common_keys]
    return {
        "common": prioritized,
        "remaining": remaining,
        "experiences": _list(profil.get("experiences")),
        "formation": _list(profil.get("formation")),
        "langues": _list(profil.get("langues")),
    }


def creer_cv_word(profil: dict, offre: dict, email: str = "") -> bytes:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.62)
    section.bottom_margin = Inches(0.62)
    section.left_margin = Inches(0.72)
    section.right_margin = Inches(0.72)

    normal = doc.styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(10)
    normal.font.color.rgb = RGBColor(40, 52, 47)
    normal.paragraph_format.space_after = Pt(3)
    for style_name in ("Heading 1", "Heading 2"):
        style = doc.styles[style_name]
        style.font.name = "Aptos Display"
        style.font.color.rgb = RGBColor(30, 91, 68)
        style.font.bold = True
        style.font.size = Pt(12 if style_name == "Heading 1" else 10.5)
        style.paragraph_format.space_before = Pt(10)
        style.paragraph_format.space_after = Pt(4)

    name = _clean_text(profil.get("nom") or "Candidat(e)")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(str(name))
    run.bold = True
    run.font.name = "Aptos Display"
    run.font.size = Pt(23)
    run.font.color.rgb = RGBColor(22, 62, 48)

    contact = " · ".join(_clean_text(value) for value in (email, profil.get("pref_ville")) if value)
    if contact:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(8)
        run = p.add_run(contact)
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(92, 100, 94)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(3)
    run = p.add_run(f"CV ciblé · {_clean_text(offre.get('titre') or 'Offre')}")
    run.bold = True
    run.font.size = Pt(12)
    doc.add_paragraph(f"{_clean_text(offre.get('entreprise'))} · {_clean_text(offre.get('ville'))}".strip(" ·"))

    data = _cv_sections(profil, offre)

    def add_section(title: str, values: list[str]) -> None:
        if not values:
            return
        doc.add_heading(title, level=1)
        for value in values:
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(2)
            p.add_run(_clean_text(value))

    add_section("Compétences correspondant à l’offre", data["common"])
    add_section("Autres compétences du profil", data["remaining"])
    add_section("Expériences", data["experiences"])
    add_section("Formation", data["formation"])
    add_section("Langues", data["langues"])

    if not any(data[key] for key in ("common", "remaining", "experiences", "formation", "langues")):
        source_text = str(profil.get("cv_texte") or "").strip()
        if source_text:
            doc.add_heading("Informations extraites du CV source", level=1)
            for line in source_text.splitlines():
                line = line.strip()
                if line:
                    doc.add_paragraph(_clean_text(line))
        else:
            doc.add_paragraph("Complétez votre profil pour enrichir ce CV avec vos expériences et votre formation.")

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    note = footer.add_run("Document réorganisé à partir des informations du profil · aucune compétence ni expérience ajoutée")
    note.font.size = Pt(8)
    note.font.color.rgb = RGBColor(92, 100, 94)

    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()


def creer_guide_pdf(profil: dict, offre: dict, guide: str, matching_data: dict | None = None,
                    entretien: dict | None = None) -> bytes:
    out = io.BytesIO()
    doc = SimpleDocTemplate(
        out, pagesize=A4,
        rightMargin=19 * mm, leftMargin=19 * mm,
        topMargin=20 * mm, bottomMargin=18 * mm,
        title=f"Guide d'entretien — {offre.get('titre') or 'Candidature'}",
        author="Entretien garanti",
    )
    base = getSampleStyleSheet()
    regular_font, bold_font = _register_pdf_fonts()
    title_style = ParagraphStyle(
        "GuideTitle", parent=base["Title"], fontName=bold_font,
        fontSize=23, leading=28, textColor=colors.HexColor("#163e30"),
        alignment=TA_LEFT, spaceAfter=5 * mm,
    )
    subtitle_style = ParagraphStyle(
        "GuideSubtitle", parent=base["Normal"], fontName=regular_font,
        fontSize=10, leading=15, textColor=colors.HexColor("#5c645e"),
        spaceAfter=4 * mm,
    )
    heading_style = ParagraphStyle(
        "GuideHeading", parent=base["Heading2"], fontName=bold_font,
        fontSize=13, leading=17, textColor=colors.HexColor("#1f5c45"),
        spaceBefore=5 * mm, spaceAfter=2 * mm,
    )
    body_style = ParagraphStyle(
        "GuideBody", parent=base["BodyText"], fontName=regular_font,
        fontSize=9.5, leading=14, textColor=colors.HexColor("#28342f"),
        spaceAfter=2.2 * mm,
    )
    small_style = ParagraphStyle(
        "GuideSmall", parent=body_style, fontSize=8.5,
        textColor=colors.HexColor("#5c645e"),
    )

    esc = lambda value: html.escape(_clean_text(value), quote=False)
    story = [
        Paragraph("Guide de préparation", title_style),
        Paragraph(f"{esc(offre.get('titre'))} · {esc(offre.get('entreprise'))} · Préparé pour {esc(profil.get('nom') or 'le candidat')}", subtitle_style),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d7cebb"), spaceAfter=4 * mm),
    ]

    if entretien:
        details = []
        if entretien.get("entretien_date"):
            details.append(("Date et heure", entretien["entretien_date"]))
        if entretien.get("entretien_lieu"):
            details.append(("Lieu ou lien", entretien["entretien_lieu"]))
        if entretien.get("entretien_notes"):
            details.append(("Consignes", entretien["entretien_notes"]))
        if details:
            story.append(Paragraph("Informations du rendez-vous", heading_style))
            rows = [[Paragraph(f"<b>{esc(label)}</b>", body_style), Paragraph(esc(value), body_style)] for label, value in details]
            table = Table(rows, colWidths=[37 * mm, 125 * mm], hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e7efe9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d7cebb")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d7cebb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.extend([table, Spacer(1, 3 * mm)])

    matching_data = matching_data or matching.scorer(profil, offre)
    required = matching_data.get("competences_requises", [])
    missing = matching_data.get("competences_manquantes", [])
    common = matching_data.get("competences_communes", [])
    if required:
        story.append(Paragraph("Compétences de l’offre à préparer", heading_style))
        story.append(Paragraph("Maîtrisées dans votre profil : " + (", ".join(map(esc, common)) or "aucune identifiée") + ".", body_style))
        if missing:
            story.append(Paragraph("À revoir ou à présenter honnêtement comme un axe de progression : " + ", ".join(map(esc, missing)) + ".", body_style))
        else:
            story.append(Paragraph("Votre profil couvre les compétences détectées dans cette annonce. Préparez un exemple concret pour chacune.", body_style))

    story.append(Paragraph("Questions et pistes de préparation", heading_style))
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", guide or "")
    for line in cleaned.splitlines():
        line = _clean_text(line).strip()
        if not line:
            story.append(Spacer(1, 1.2 * mm))
            continue
        if re.match(r"^\d+[.)]\s*", line):
            line = re.sub(r"^(\d+[.)])\s*", r"<b>\1</b> ", esc(line))
        else:
            line = esc(line)
        story.append(Paragraph(line, body_style))

    story.extend([
        Spacer(1, 3 * mm),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#d7cebb"), spaceBefore=2 * mm, spaceAfter=2 * mm),
        Paragraph("Avant l’entretien : relisez l’offre, préparez des exemples réels tirés de votre parcours et vérifiez le lien ou l’adresse du rendez-vous. Ce guide s’appuie sur les éléments disponibles dans votre profil ; n’ajoutez aucun fait que vous ne pouvez justifier.", small_style),
    ])

    def draw_page(canvas, document):
        canvas.saveState()
        canvas.setFont(regular_font, 8)
        canvas.setFillColor(colors.HexColor("#5c645e"))
        canvas.drawString(19 * mm, 10 * mm, "Entretien garanti · Guide personnel")
        canvas.drawRightString(A4[0] - 19 * mm, 10 * mm, f"Page {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    return out.getvalue()
