import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import db
from app.main import app
from app.services import collector


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "t.db"
    monkeypatch.setattr("app.db.DB_PATH", test_db)
    monkeypatch.setattr("app.config.DB_PATH", test_db)
    db.init_db(test_db)
    collector.charger_demo()
    with TestClient(app) as c:
        yield c


def _auth(client: TestClient, formule="garanti"):
    r = client.post(
        "/api/auth/register",
        json={
            "nom": "Sara Test",
            "email": "sara@example.com",
            "password": "motdepasse",
            "consentement_09_08": True,
            "formule": formule,
        },
    )
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_exige_consentement(client):
    r = client.post(
        "/api/auth/register",
        json={"nom": "A B", "email": "a@b.com", "password": "motdepasse", "consentement_09_08": False},
    )
    assert r.status_code == 400


def test_parcours_matching_lettre_envoi_arret(client):
    h = _auth(client)
    client.put(
        "/api/profil",
        headers=h,
        json={
            "competences": ["Python", "FastAPI", "SQL", "Git"],
            "experiences": ["Stage API Python chez Atlas"],
            "formation": ["Licence informatique 2024"],
            "langues": ["Français"],
            "pref_poste": "développeur python",
            "pref_ville": "Casablanca",
        },
    )
    me = client.get("/api/auth/me", headers=h).json()
    uid = me["user"]["id"]
    from app import db as dbmod

    with dbmod.get_conn() as con:
        con.execute(
            "UPDATE profils SET cv_texte=? WHERE user_id=?",
            ("Développeur Python FastAPI SQL Git Docker Casablanca stage Atlas", uid),
        )
    rec = client.get("/api/offres/recommandees", headers=h)
    assert rec.status_code == 200
    offres = rec.json()["offres"]
    assert offres
    assert offres[0]["score"] >= offres[-1]["score"]
    oid = offres[0]["id"]
    c = client.post("/api/candidatures", headers=h, json={"offre_id": oid})
    assert c.status_code == 200
    cid = c.json()["id"]
    lettre = client.post(f"/api/candidatures/{cid}/lettre", headers=h)
    assert lettre.status_code == 200
    assert "Madame" in lettre.json()["texte"] or "Objet" in lettre.json()["texte"]
    env = client.post(f"/api/candidatures/{cid}/envoyer", headers=h)
    assert env.status_code == 200
    patch = client.patch(f"/api/candidatures/{cid}", headers=h, json={"statut": "entretien"})
    assert patch.status_code == 200
    # règle d'arrêt
    autre = offres[1]["id"]
    c2 = client.post("/api/candidatures", headers=h, json={"offre_id": autre})
    assert c2.status_code == 409
    dash = client.get("/api/dashboard", headers=h)
    assert dash.json()["agent_arrete"] is True
