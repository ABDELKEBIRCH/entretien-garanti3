import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

SECRET = os.getenv("APP_SECRET", "dev-secret-entretien-garanti")
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
CORS_ORIGINS = tuple(
    origin.strip() for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",") if origin.strip()
)
TOKEN_HOURS = 48
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
DB_PATH = Path(__file__).resolve().parents[1] / "entretien.db"
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER).strip()
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "true").lower() == "true"
INTERVIEW_NOTIFICATION_EMAIL = os.getenv("INTERVIEW_NOTIFICATION_EMAIL", "").strip()
FRONTEND_DIR = ROOT / "frontend"

STATUTS = ("a_envoyer", "envoyee", "reponse", "entretien", "refus")
STATUT_LABELS = {
    "a_envoyer": "À envoyer",
    "envoyee": "Envoyée",
    "reponse": "Réponse reçue",
    "entretien": "Entretien obtenu",
    "refus": "Refus",
}

FORMULES = {
    "decouverte": {
        "nom": "Découverte",
        "prix": "Gratuit",
        "max_matchs": 8,
        "max_lettres": 2,
        "max_envois": 2,
        "sources": ["demo", "remotive"],
        "cv_adapte": False,
        "prep_entretien": False,
        "resume": "Matching limité et 2 lettres pour tester le parcours.",
    },
    "candidat": {
        "nom": "Candidat",
        "prix": "Étudiant",
        "max_matchs": 40,
        "max_lettres": 15,
        "max_envois": 15,
        "sources": ["demo", "rss", "remotive"],
        "cv_adapte": False,
        "prep_entretien": False,
        "resume": "Collecte 2 sources, lettres personnalisées, suivi des statuts.",
    },
    "garanti": {
        "nom": "Accompagnement Pro",
        "prix": "Premium",
        "max_matchs": 999,
        "max_lettres": 999,
        "max_envois": 999,
        "sources": ["demo", "rss", "remotive"],
        "cv_adapte": True,
        "prep_entretien": True,
        "resume": "CV adapté à l’offre et préparation orale pour chaque entretien.",
    },
}
