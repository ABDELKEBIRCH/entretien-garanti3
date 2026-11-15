# Entretien garanti

Application web de recherche d'emploi permettant de comparer les offres à un profil, préparer les candidatures et suivre leur progression jusqu'aux entretiens.

## Présentation du projet

**Entretien garanti** est une application web basée sur l'intelligence artificielle. Elle permet de :

- Importer et analyser un CV.
- Extraire les compétences et les informations du candidat.
- Collecter des offres réelles depuis l'API publique Remotive et les flux RSS We Work Remotely, en complément des annonces de démonstration.
- Ajouter manuellement les annonces ouvertes sur LinkedIn, Indeed ou un site carrière pour les classer avec les autres offres.
- Rechercher et trier les annonces par intitulé, entreprise, ville, compétences, score et source.
- Recommander les offres les plus pertinentes selon le profil du candidat.
- Expliquer les scores de correspondance entre le CV et les offres.
- Générer des lettres de motivation adaptées au profil.
- Gérer les candidatures et suivre leur évolution.
- Enregistrer les détails d'un entretien et envoyer sa confirmation par e-mail via SMTP.
- Télécharger, pour chaque candidature, un CV ciblé au format Word et un guide de préparation d'entretien au format PDF.
- Afficher les compétences requises par offre et les écarts de compétences du profil.
- Proposer trois formules d'utilisation.
- Arrêter automatiquement les nouvelles candidatures dès l'obtention d'un entretien.

**Limites du prototype :**

- Les offres LinkedIn et Indeed ne sont pas aspirées : leur accès automatisé exige une autorisation ou une intégration partenaire.
- Aucun paiement réel.
- L'envoi réel d'e-mail nécessite une configuration SMTP.

## Technologies utilisées

- **Backend :** Python, FastAPI.
- **Frontend :** React, Vite, JavaScript.
- **Base de données :** SQLite par défaut en local, PostgreSQL pour un déploiement évolutif.
- **Traitement du langage :** TF-IDF et outils d'analyse de texte.
- **Analyse des CV :** pdfplumber et python-docx.
- **Collecte des offres :** API publique Remotive, flux RSS We Work Remotely, import manuel depuis les plateformes et données JSON de démonstration. La fraîcheur des offres distantes est suivie ; les annonces non revues depuis 30 jours ne sont plus recommandées.
- **Intelligence artificielle :** intégration LLM optionnelle.

## Prérequis

- Python 3.12 recommandé.
- pip.
- Git.
- Node.js 20.19+ et pnpm pour construire l'interface React.
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
│   ├── src/
│   │   ├── App.jsx
│   │   └── styles.css
│   ├── package.json
│   └── vite.config.js
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

Installer et construire le frontend React depuis le dossier `frontend` :

```bash
pnpm install --frozen-lockfile
pnpm run build
```

Le script `run.ps1` réalise ces étapes avant de lancer FastAPI. En développement frontend, lancez aussi `pnpm dev` dans `frontend` ; Vite transmet les appels `/api` au serveur local FastAPI.

Pour PostgreSQL, renseigner `DATABASE_URL` (ex. `postgresql://utilisateur:motdepasse@hote:5432/entretien`). Pour envoyer les confirmations d'entretien, renseigner `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` et `SMTP_FROM`. `INTERVIEW_NOTIFICATION_EMAIL` permet de choisir une adresse de réception fixe ; si elle est vide, la confirmation part à l'adresse du compte candidat.

Pour transférer les données d'une base SQLite existante, après installation des dépendances :

```bash
python scripts/migrate_sqlite_to_postgres.py "postgresql://utilisateur:motdepasse@hote:5432/entretien" --sqlite backend/entretien.db
```

La migration copie les comptes, profils, offres, candidatures et journal dans une base cible vide. Avec `--replace`, elle remplace les données existantes de la cible. Faire une sauvegarde des deux bases avant une migration de production.

La clé LLM est optionnelle : `OPENAI_API_KEY`.

Sans cette clé, l'application peut utiliser un modèle de lettre basé sur un gabarit factuel, selon la configuration du projet.

## Lancer l'application

Depuis la racine du projet, avec l'environnement virtuel et Node.js/pnpm installés :

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm run build
cd ..
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
Frontend (React / Vite)
                 |
                 v
          Backend FastAPI
                 |
       +---------+---------+
       |         |         |
       v         v         v
   SQLite ou PostgreSQL   Analyse CV   Collecte
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
