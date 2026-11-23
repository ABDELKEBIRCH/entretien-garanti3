"""Génération de textes : LLM si clé présente, sinon gabarit factuel. Jamais d'invention."""

from __future__ import annotations

import json
import re

import httpx

from ..config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL


GARDE_FOU = """
Tu es un rédacteur professionnel spécialisé dans les candidatures.

RÈGLES STRICTES :
- N'invente aucune compétence, expérience, formation, date ou réalisation.
- Utilise uniquement les informations fournies dans le profil et le CV.
- Ne présente jamais une compétence demandée par l'offre comme acquise si elle est absente du CV.
- Distingue toujours les compétences techniques des langues.
- Relie naturellement les expériences et compétences réelles du candidat aux besoins de l'offre.
- Évite les répétitions, les phrases génériques et les formulations artificielles.
- Adopte un français professionnel, naturel, fluide et convaincant.
- Ne mentionne jamais que tu es une IA.

STRUCTURE :
1. Introduction : poste visé et motivation.
2. Adéquation : compétences réelles pertinentes pour l'offre.
3. Parcours : expériences et formation pertinentes.
4. Conclusion : intérêt pour un échange professionnel.

Rédige une lettre concise de 250 à 350 mots.
N'utilise aucun placeholder comme (e), (se) ou [Nom].
Ne répète pas inutilement les informations du CV.
"""



LANGUES_CONNues = (
    "français", "french",
    "anglais", "english",
    "arabe", "arabic",
    "espagnol", "spanish",
    "allemand", "german",
    "amazigh",
    "italien", "italian",
)



#To seperate the languages from the technical skills 

def est_langue(value: str) -> bool:
    """Détecte si une compétence correspond à une langue."""
    texte = str(value).lower()

    # Retirer les niveaux et les indications de maîtrise
    texte = re.sub(
        r"\b(natif|native|courant|courante|fluent|bilingue|"
        r"débutant|débutante|intermédiaire|avancé|avancée|"
        r"a1|a2|b1|b2|c1|c2)\b",
        " ",
        texte,
    )

    texte = re.sub(r"\([^)]*\)", " ", texte)
    texte = re.sub(r"[^a-zà-ÿ]+", " ", texte).strip()

    return any(
        re.search(rf"\b{re.escape(langue)}\b", texte)
        for langue in LANGUES_CONNues
    )





def faits_autorises(profil: dict) -> dict:
    return {
        "competences": profil.get("competences") or [],
        "experiences": profil.get("experiences") or [],
        "formation": profil.get("formation") or [],
        "langues": profil.get("langues") or [],
        "extrait_cv": (profil.get("cv_texte") or "")[:4000],
    }




def filtrer_invention(texte: str, profil: dict) -> str:
    """Filtre les affirmations non vérifiables à partir du CV."""

    cv = (profil.get("cv_texte") or "").lower()

    faits = []
    for cle in ("competences", "experiences", "formation", "langues"):
        valeurs = profil.get(cle) or []
        if isinstance(valeurs, str):
            valeurs = [valeurs]
        faits.extend(str(v).lower() for v in valeurs)

    source = cv + " " + " ".join(faits)

    expressions_sensibles = (
        r"\bexpert(?:e)? en\b",
        r"\bmaîtrise parfaite\b",
        r"\bcertifi(?:é|ée|és|ées)\b",
        r"\b\d+\s+ans? d'expérience\b",
        r"\bj'ai dirigé\b",
        r"\bj'ai supervisé\b",
        r"\bj'ai développé\b",
        r"\bj'ai réalisé\b",
        r"\bj'ai piloté\b",
    )

    # Repérer les compétences explicitement revendiquées.
    expressions_competences = (
        r"\b(?:je\s+)?(?:maîtrise|maitrise|connais)\s+(.+)",
        r"\bcompétences?\s+en\s+(.+)",
        r"\bconnaissances?\s+en\s+(.+)",
        r"\bexpérience\s+en\s+(.+)",
    )

    lignes = []
    interdites = []

    for phrase in re.split(r"(?<=[.!?])\s+", texte):
        low = phrase.lower()
        suspect = False

        # Vérifier les affirmations sensibles.
        if any(
            re.search(expression, low)
            and not re.search(expression, source)
            for expression in expressions_sensibles
        ):
            suspect = True

        # Vérifier les compétences revendiquées.
        for expression in expressions_competences:
            match = re.search(expression, low)

            if match:
                competences = re.split(
                    r",|\bet\b|\bou\b|/|;",
                    match.group(1),
                )

                for competence in competences:
                    competence = competence.strip(" .,:;")

                    if len(competence) >= 2 and competence not in source:
                        suspect = True
                        break

            if suspect:
                break

        if suspect:
            interdites.append(phrase)
        else:
            lignes.append(phrase)

    clean = " ".join(lignes).strip()

    if interdites:
        clean += (
            "\n\n[Contrôle d'honnêteté] Certaines affirmations "
            "n'ont pas pu être vérifiées à partir du CV et ont été écartées."
        )

    return clean




def nettoyer_element(value: str) -> str:
    """Nettoie la ponctuation et les espaces des éléments du CV."""
    texte = str(value).strip()
    texte = re.sub(r"\s*;\s*", "; ", texte)
    texte = re.sub(r"\s*,\s*", ", ", texte)
    texte = re.sub(r"[.;,\s]+$", "", texte)
    return texte



def lettre_gabarit(profil: dict, offre: dict, matching: dict | None = None) -> str:
    nom = profil.get("nom") or "Candidat"

    titre = offre.get("titre") or "poste proposé"
    entreprise = offre.get("entreprise") or "votre entreprise"
    ville = offre.get("ville")

    # Compétences techniques uniquement
    competences = [
        c for c in (profil.get("competences") or [])
        if not est_langue(c)
    ]

    communs = [
        c for c in (matching or {}).get("competences_communes", [])
        if not est_langue(c)
    ]

    pertinentes = communs or competences
    pertinentes = pertinentes[:6]

    # Informations du parcours
    experiences = profil.get("experiences") or []
    formations = profil.get("formation") or []
    langues = profil.get("langues") or []

    if isinstance(langues, str):
        langues = [langues]

    lieu = f" à {ville}" if ville else ""
    entreprise_formatee = entreprise

    if entreprise.lower().startswith(("agadir ", "atlas ")):
        pass

    # Formation
    paragraphe_formation = ""
    if formations:
        paragraphe_formation = (
            "Mon parcours académique comprend notamment "
            + " ; ".join(nettoyer_element(f) for f in formations[:2]) + "."
        )

    # Expérience
    paragraphe_experience = ""
    if experiences:
        paragraphe_experience = (
            "Mon parcours professionnel comprend "
            + " ; ".join(nettoyer_element(e) for e in experiences[:2]) + "."
        )

    # Compétences et adéquation avec l'offre
    paragraphe_competences = ""
    if pertinentes:
        paragraphe_competences = (
            "Les compétences que j'ai développées, notamment "
            + ", ".join(pertinentes)
            + ", constituent une base pertinente pour contribuer aux missions de ce poste."
        )

    # Langues
    paragraphe_langues = ""
    if langues:
        paragraphe_langues = (
            "Je dispose également des connaissances linguistiques suivantes : "
            + ", ".join(langues) + "."
        )

    # Description de l'offre : uniquement pour contextualiser
    description = (offre.get("description") or "").lower()

    domaines = [
        mot for mot in (
            "analyse de données", "data analysis",
            "traitement des données", "data processing",
            "visualisation", "reporting",
            "data warehouse", "entrepôt de données",
            "etl", "data pipeline", "data pipelines",
            "intégration des données", "data integration",
            "qualité des données", "data quality"
        )
        if mot in description
    ]

    if domaines and pertinentes:
        phrase_motivation = (
            "L'orientation du poste vers "
            + ", ".join(domaines[:2])
            + " correspond à mon intérêt professionnel et aux compétences que j'ai développées."
        )
    else:
        phrase_motivation = (
            "Cette opportunité représente pour moi l'occasion de mobiliser "
            "mes connaissances et de poursuivre mon développement professionnel."
        )

    paragraphes = [
        f"Objet : Candidature au poste de {titre}",
        "",
        "Madame, Monsieur,",
        "",
        f"Je vous adresse ma candidature pour le poste de {titre} {entreprise}{lieu}. "
        + phrase_motivation,
    ]

    if paragraphe_formation:
        paragraphes += ["", paragraphe_formation]

    if paragraphe_experience:
        paragraphes += ["", paragraphe_experience]

    if paragraphe_competences:
        paragraphes += ["", paragraphe_competences]

    if paragraphe_langues:
        paragraphes += ["", paragraphe_langues]

    paragraphes += [
        "",
        "Je serais ravi de pouvoir échanger avec vous afin de vous présenter "
        "plus en détail mon parcours et ma motivation pour rejoindre votre équipe.",
        "",
        "Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.",
        "",
        nom,
    ]

    return "\n".join(paragraphes)


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
    except Exception as e:
        print("Erreur API LLM :", type(e).__name__, str(e))
        return None


def generer_lettre(profil: dict, offre: dict, matching: dict | None = None) -> dict:
    faits = faits_autorises(profil)


    matching_filtre = dict(matching or {})

    for cle in (
        "competences_communes",
        "competences_requises",
        "competences_profil",
        "competences_manquantes",
    ):
        if cle in matching_filtre:
            matching_filtre[cle] = [
                c for c in matching_filtre[cle]
                if not est_langue(c)
            ]


    prompt_user = (
        "Rédige une lettre de motivation.\nOffre :\n"
        + json.dumps(
            {k: offre.get(k) for k in ("titre", "entreprise", "ville", "description")},
            ensure_ascii=False,
        )
        + "\nProfil (seules sources autorisées) :\n"
        + json.dumps(faits, ensure_ascii=False)
        + "\nPoints de matching :\n"
        + json.dumps(matching_filtre, ensure_ascii=False)
    )
    llm = _chat(
        [
            {"role": "system", "content": GARDE_FOU},
            {"role": "user", "content": prompt_user},
        ]
    )
    source = "llm" if llm else "gabarit"
    texte = filtrer_invention(llm, profil) if llm else lettre_gabarit(profil, offre, matching_filtre)
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
