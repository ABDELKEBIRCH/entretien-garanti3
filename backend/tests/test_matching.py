from app.services.matching import classer, scorer, tokeniser


def test_tokeniser_ignore_stopwords():
    toks = tokeniser("Le développeur Python et le SQL")
    assert "python" in toks
    assert "sql" in toks
    assert "le" not in toks


def test_score_plus_haut_si_competences_communes():
    profil = {
        "cv_texte": "Développeur Python FastAPI SQL Git Docker Casablanca",
        "competences": ["Python", "FastAPI", "SQL", "Git"],
        "experiences": ["Stage API Python"],
        "pref_poste": "développeur python",
        "pref_ville": "casablanca",
    }
    bonne = {
        "titre": "Développeur Python junior",
        "entreprise": "X",
        "ville": "Casablanca",
        "description": "API FastAPI SQL Git Docker",
    }
    mauvaise = {
        "titre": "Comptable junior",
        "entreprise": "Y",
        "ville": "Agadir",
        "description": "TVA Sage lettrage comptabilité générale",
    }
    s1 = scorer(profil, bonne)
    s2 = scorer(profil, mauvaise)
    assert s1["score"] > s2["score"]
    assert "Python" in s1["competences_communes"] or "python" in [c.lower() for c in s1["competences_communes"]]
    assert s1["raisons"]


def test_preferences_data_engineer_agadir_cdi():
    profil = {
        "cv_texte": "",
        "competences": [],
        "experiences": [],
        "pref_poste": "data engenieer",
        "pref_ville": "agadir",
        "pref_contrat": "cdi",
    }
    cible = {
        "titre": "Data engineer",
        "entreprise": "Agadir Data Hub",
        "ville": "Agadir",
        "description": "CDI. Python SQL Spark Airflow pipelines.",
    }
    autre = {
        "titre": "Comptable junior",
        "entreprise": "Fiduciaire",
        "ville": "Casablanca",
        "description": "TVA Sage lettrage. CDI.",
    }
    ranked = classer(profil, [autre, cible])
    assert ranked[0]["titre"] == "Data engineer"
    assert ranked[0]["score"] > ranked[1]["score"]


def test_classer_ordre():
    profil = {
        "cv_texte": "React JavaScript CSS HTML",
        "competences": ["React", "JavaScript"],
        "experiences": [],
        "pref_poste": "frontend",
        "pref_ville": "",
    }
    offres = [
        {"id": 1, "titre": "Comptable", "description": "Sage Excel", "ville": "", "entreprise": "A"},
        {"id": 2, "titre": "Dev React", "description": "React JavaScript HTML CSS", "ville": "", "entreprise": "B"},
    ]
    ranked = classer(profil, offres)
    assert ranked[0]["titre"] == "Dev React"
