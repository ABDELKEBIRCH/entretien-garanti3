# Cahier des charges — Entretien garanti

## 1. Objet

Prototype d’agent de candidature : à partir d’un CV, l’application propose des offres, génère une lettre de motivation honnête, suit les statuts et **s’arrête au premier entretien**.

## 2. Acteurs

| Acteur | Rôle |
| --- | --- |
| Candidat | Compte, CV, validation des lettres, suivi |
| Agent (système) | Collecte, matching, génération, journal, règle d’arrêt |
| Recruteur | Hors système (annonces via démo / RSS) |

## 3. User stories (MVP)

1. En tant que candidat, je crée un compte avec consentement 09-08.
2. J’importe un CV PDF/DOCX et je corrige les compétences extraites.
3. Je vois des offres scorées, avec une explication du score.
4. Je génère une lettre, je la relis, je l’envoie (simulation).
5. Je change le statut (réponse, entretien, refus).
6. Dès « entretien obtenu », plus aucun envoi.
7. Je choisis une des 3 formules (quotas).
8. Je consulte le journal et je peux supprimer mon compte.

## 4. Formules

- **Découverte** : 8 offres, 2 lettres, 2 envois, source démo.
- **Candidat** : 40 offres, 15 lettres / envois, démo + RSS.
- **Entretien garanti** : jusqu’à l’entretien, CV adapté, préparation orale.

Paiement en ligne : hors périmètre (bascule manuelle).

## 5. Règles métier

- Matching = TF-IDF + recouvrement de compétences + bonus ville/titre.
- Lettres : faits du CV uniquement (gabarit ou LLM + filtre).
- Envoi réel d’e-mail : hors MVP (simulation tracée).
- Pas de contournement de jobboards ni de comptes tiers.

## 6. Interfaces

SPA (HTML/JS) servie par FastAPI. API REST JSON, JWT.

## 7. Exigences non fonctionnelles

- SQLite locale, mots de passe bcrypt, secret JWT dans `.env`.
- Temps de matching < 2 s sur le jeu de démo.
- Tests pytest : matching, parseur, parcours API.

## 8. Planning (repris des 35 tâches ClickUp)

Semaines 1–6 : cadrage, BDD/auth/CV, collecte/matching, lettres/formules, dashboard/arrêt/tests, documentation/soutenance.
