# Entretien garanti

Prototype d'un agent intelligent de candidature permettant d'accompagner les candidats dans leur recherche d'emploi, depuis l'importation du CV jusqu'au suivi des candidatures.

## Présentation du projet

**Entretien garanti** est une application web basée sur l'intelligence artificielle. Elle permet de :

- Importer et analyser un CV.
- Extraire les compétences et les informations du candidat.
- Collecter des offres d'emploi à partir de données de démonstration et de flux RSS publics.
- Recommander les offres les plus pertinentes selon le profil du candidat.
- Expliquer les scores de correspondance entre le CV et les offres.
- Générer des lettres de motivation adaptées au profil.
- Gérer les candidatures et suivre leur évolution.
- Proposer trois formules d'utilisation.
- Arrêter automatiquement les nouvelles candidatures dès l'obtention d'un entretien.

**Limites du prototype :**

- Aucune connexion à un compte de plateforme d'emploi.
- Aucun paiement réel.
- Aucun envoi réel d'e-mail.

## Technologies utilisées

- **Backend :** Python, FastAPI.
- **Frontend :** HTML, CSS, JavaScript.
- **Base de données :** SQLite.
- **Traitement du langage :** TF-IDF et outils d'analyse de texte.
- **Analyse des CV :** pdfplumber et python-docx.
- **Collecte des offres :** données JSON de démonstration et flux RSS.
- **Intelligence artificielle :** intégration LLM optionnelle.

## Prérequis

- Python 3.12 recommandé.
- pip.
- Git.
- Windows, Linux ou macOS.

## Structure du projet

```text
entretien-garanti3/
│
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── matching.py
│   │   ├── cv_parser.py
│   │   ├── collector.py
│   │   ├── plans.py
│   │   └── ...
│   │
│   ├── data/
│   │   └── sample_cvs/
│   ├── scripts/
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   └── static/
│       ├── app.css
│       └── app.js
│
├── docs/
├── scripts/
├── .env.example
├── .gitignore
└── README.md
```

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/ABDELKEBIRCH/entretien-garanti3.git
cd entretien-garanti3
```

### 2. Créer l'environnement virtuel

```bash
py -3.12 -m venv .venv
```

### 3. Activer l'environnement virtuel

Sous Windows CMD :

```cmd
.venv\Scripts\activate
```

Sous PowerShell :

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Installer les dépendances

```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 5. Configurer les variables d'environnement

Sous Windows CMD :

```cmd
copy .env.example .env
```

Sous Linux/macOS :

```bash
cp .env.example .env
```

Configurer les variables nécessaires dans le fichier `.env`.

La clé LLM est optionnelle : `OPENAI_API_KEY`.

Sans cette clé, l'application peut utiliser un modèle de lettre basé sur un gabarit factuel, selon la configuration du projet.

## Lancer l'application

Depuis la racine du projet, avec l'environnement virtuel activé :

```bash
python -m uvicorn app.main:app --reload --app-dir backend
```

L'application sera accessible à l'adresse :

http://127.0.0.1:8000

Documentation interactive de l'API :

http://127.0.0.1:8000/docs

## Tests

Pour exécuter les tests :

```bash
python -m pytest backend/tests -q
```

## Parcours de démonstration

1. Créer un compte et accepter le consentement relatif aux données personnelles.
2. Sélectionner une formule.
3. Compléter le profil du candidat.
4. Importer un CV.
5. Consulter les offres recommandées.
6. Examiner les scores et les raisons de correspondance.
7. Créer une candidature.
8. Générer et vérifier une lettre de motivation.
9. Suivre le statut de la candidature.
10. Vérifier l'arrêt des nouvelles candidatures après l'obtention d'un entretien.

## Architecture générale

```text
Frontend (HTML / CSS / JavaScript)
                 |
                 v
          Backend FastAPI
                 |
       +---------+---------+
       |         |         |
       v         v         v
   SQLite    Analyse CV   Collecte
                         des offres
       |
       v
  Matching et recommandations
       |
       v
  Génération des lettres
       |
       v
  Gestion des candidatures
```

## Éthique et protection des données

Le projet respecte les principes suivants :

- Consentement de l'utilisateur.
- Minimisation des données personnelles.
- Possibilité de suppression des données.
- Absence d'invention de compétences non présentes dans le CV.
- Utilisation de données de démonstration et de flux RSS publics.
- Absence de connexion automatisée aux comptes personnels des plateformes d'emploi.

Le projet prend notamment en considération les principes de la loi marocaine 09-08 relative à la protection des personnes physiques à l'égard du traitement des données à caractère personnel.

## Contribution

Les contributions sont organisées à travers Git et GitHub.

Branches principales :

- `main` : version stable du projet.
- `develop` : branche d'intégration.
- `feature/*` : développement des différentes fonctionnalités.

Les modifications sont proposées à travers des Pull Requests vers `develop`.

## Licence

Projet universitaire réalisé dans un cadre pédagogique et expérimental.