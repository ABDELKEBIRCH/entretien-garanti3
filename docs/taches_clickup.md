# Suivi des 35 tâches ClickUp — Entretien garanti

Ce document présente la répartition des tâches du projet, les livrables attendus et l'état réel de leur avancement.

**Responsable du suivi GitHub : Abdelkebir Chouiter**

## 1. Légende des statuts

- **Terminé** : tâche réalisée et vérifiée.
- **En cours** : travail commencé, mais non terminé.
- **À faire** : tâche non encore réalisée.
- **Partiel** : une partie de la tâche a été réalisée.

## 2. Tableau de suivi des tâches

| # | Tâche | Responsable | Livrable | Statut |
|---|---|---|---|---|
| 1 | Cahier des charges et User Stories | Abdelkebir | `docs/cahier_des_charges.md` | En cours de vérification |
| 2 | Dépôt GitHub, branches, README et gitignore | Abdelkebir | Dépôt GitHub, `README.md`, `.gitignore` | **Terminé** |
| 3 | Organisation et suivi ClickUp | Abdelkebir | Fichier de suivi ClickUp | À faire |
| 4 | Maquettes et conception de l'interface | Abdelkebir | `frontend/` | À faire |
| 5 | MCD et conception SQL | Abdelkebir | Modèle de données | À faire |
| 6 | Étude du matching et du LLM | Abdelkebir | `docs/rapport.md` | À faire |
| 7 | Diagramme de cas d'utilisation | Camarade 2 | `docs/diagrammes.md` | À faire |
| 8 | Développement de la base SQLite (`db.py`) | Abdelkebir | `backend/app/db.py` | À faire |
| 9 | Authentification bcrypt et consentement 09-08 | Camarade 1 | Modules d'authentification | À faire |
| 10 | Développement du parseur PDF/DOCX | Abdelkebir | `backend/app/cv_parser.py` | À faire |
| 11 | Conception des prompts pour les lettres | Camarade 2 | `backend/app/services/llm.py` | À faire |
| 12 | Pages d'inscription et d'importation du CV | Camarade 3 | `frontend/` | Partiel |
| 13 | Diagramme de classes | Camarade 2 | `docs/diagrammes.md` | À faire |
| 14 | Tests du parseur sur 10 à 15 CV | Abdelkebir | `backend/tests/` | À faire |
| 15 | Collecteur d'offres : démo et RSS | Abdelkebir | `backend/app/collector.py` | À faire |
| 16 | Moteur de matching expliqué | Abdelkebir | `backend/app/matching.py` | À faire |
| 17 | Développement des endpoints FastAPI | Camarade 1 | `backend/app/routers/` | À faire |
| 18 | Page des offres recommandées | Camarade 3 | Interface frontend | À faire |
| 19 | Tests du moteur de matching | Abdelkebir | `backend/tests/` | À faire |
| 20 | Génération des lettres et garde-fous | Camarade 2 | Module de génération des lettres | À faire |
| 21 | Gestion des trois formules et des quotas | Camarade 1 | `backend/app/plans.py` | À faire |
| 22 | Validation et modification des lettres | Camarade 3 | Interface frontend | À faire |
| 23 | Diagramme de séquence | Camarade 2 | `docs/diagrammes.md` | À faire |
| 24 | Cache et normalisation des offres | Abdelkebir | Matching et base de données | À faire |
| 25 | Règle d'arrêt au premier entretien et journal | Camarade 1 | `plans.py`, journal et candidatures | Partiel : correction transactionnelle dans le routeur des candidatures |
| 26 | Tableau de bord | Camarade 3 | Interface dashboard | À faire |
| 27 | Évaluation de la qualité | Abdelkebir | Tests et rapport | À faire |
| 28 | Adaptation du CV et préparation à l'entretien | Camarade 2 | Services et endpoints concernés | À faire |
| 29 | Tests d'intégration | Camarade 1 | `backend/tests/` | À faire |
| 30 | Rapport sur l'éthique et la sécurité | Camarade 2 | `docs/rapport.md` | À faire |
| 31 | Rapport final | Camarade 3 | `docs/rapport.md` | À faire |
| 32 | Présentation orale de 15 minutes | Camarade 3 | `docs/presentation.html` | À faire |
| 33 | Nettoyage et préparation de la version 1.0 | Camarade 1 | Projet final | À faire |
| 34 | Script de démonstration | Camarade 1 | `scripts/demo.md` | À faire |
| 35 | Relecture finale du projet | Toute l'équipe | Projet complet | À faire |

## 3. Réalisations vérifiées d'Abdelkebir

### Tâche 2 — Dépôt GitHub et organisation

**Travaux réalisés :**

- Création du dépôt Git local.
- Création du dépôt GitHub `entretien-garanti3`.
- Configuration de l'identité Git.
- Création de la branche principale `main`.
- Création de la branche d'intégration `develop`.
- Préparation du fichier `.gitignore`.
- Rédaction et mise à jour du fichier `README.md`.
- Ajout du frontend au dépôt GitHub.
- Publication des modifications sur GitHub.

**Historique des commits :**

| Commit | Description |
|---|---|
| `ef63a4a` | Add frontend |
| `c1ec929` | Add project documentation and gitignore |

**Dépôt GitHub :**

https://github.com/ABDELKEBIRCH/entretien-garanti3

### Contribution complémentaire — Routeur des candidatures

- Analyse du fonctionnement du routeur des candidatures.
- Correction du problème lié aux écritures imbriquées dans la transaction.
- Déplacement des opérations de journalisation afin de résoudre le problème de verrouillage SQLite.

Cette correction a été vérifiée par le fonctionnement de l'opération concernée.

## 4. Organisation Git

Les branches principales du projet sont :

- `main` : version stable.
- `develop` : branche d'intégration.
- `feature/*` : branches dédiées aux fonctionnalités.

Les nouvelles fonctionnalités seront développées progressivement et intégrées dans `develop` après vérification.

## 5. Règles de suivi

- Une tâche ne passe au statut « Terminé » qu'après réalisation et vérification.
- Chaque contribution doit être enregistrée avec un commit correspondant au travail réellement effectué.
- Les fichiers des autres membres ne sont pas attribués à Abdelkebir sans contribution effective.
- Les modifications sont ajoutées progressivement au dépôt GitHub.
- Les informations sensibles, fichiers `.env`, bases de données locales et fichiers temporaires ne doivent pas être publiés.

**Dernière mise à jour : 04/11/2026**