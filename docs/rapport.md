# Rapport — Mini-projet Entretien garanti

**Agent IA de candidature automatique — prototype pédagogique**

## 1. Introduction

La recherche d’emploi impose de scruter plusieurs canaux, de réécrire des lettres et de suivre des réponses rarement automatisées. L’objectif de ce projet n’est pas un robot d’envoi massif : c’est un **assistant borné**, qui s’arrête au premier entretien, qui n’invente rien, et qui reste sous le contrôle du candidat.

Ce rapport décrit la conception, les choix techniques, les résultats du matching et des lettres, les limites, et le traitement des données personnelles (loi 09-08).

## 2. Problématique et objectifs

Le MVP couvre : compte et consentement, parseur de CV, deux sources d’offres, score expliqué, lettres, trois formules, tableau de bord, règle d’arrêt, journal.

Hors périmètre : paiement réel, contournement d’anti-robots, connexion aux comptes LinkedIn / Rekrute.

## 3. Conception

### 3.1 Cas d’utilisation

Le candidat est l’acteur principal. L’agent est un système qui collect, score, rédige et journalise. Les diagrammes détaillés sont dans `docs/diagrammes.md`.

### 3.2 Modèle de données

Cinq tables SQLite : `users`, `profils`, `offres`, `candidatures`, `journal`. L’unicité `(user_id, offre_id)` évite les doubles candidatures. L’empreinte `fingerprint` déduplique les offres collectées.

### 3.3 Parcours

Inscription → CV → collecte → matching → candidature → lettre validée → envoi simulé → statuts → **entretien ⇒ stop**.

## 4. Choix techniques

| Couche | Choix | Motif |
| --- | --- | --- |
| API | FastAPI | Endpoints clairs, tests `TestClient` |
| UI | SPA vanilla servie par FastAPI | Zéro Node requis, démo locale simple |
| BDD | SQLite via `db.py` | Conforme à la tâche, portable |
| Auth | bcrypt + JWT | Mot de passe non stocké en clair |
| Matching | TF-IDF maison + cosinus | Explicable, sans modèle lourd |
| Lettres | Gabarit + LLM optionnel | Coût API maîtrisé, garde-fou |
| Offres | JSON marocain + RSS | Deux sources même hors-ligne (démo) |

**TF-IDF vs embeddings.** Les embeddings (sentence-transformers) sont plus sensibles au paraphrase mais demandent un téléchargement de modèle et rendent l’explication opaque. Pour un MVP évalué sur la *pertinence expliquée*, TF-IDF + recouvrement de compétences est un meilleur compromis pédagogique. Un passage aux embeddings reste une évolution (formule premium, cache).

**LLM.** Si `OPENAI_API_KEY` est absent, un gabarit n’utilise que formation, expériences et compétences du profil. Un filtre heuristique écarte des formulations du type « expert / certifié » hors CV.

## 5. Fonctionnalités réalisées

- Authentification, consentement, suppression de compte.
- Parseur PDF/DOCX, sections FR/EN, liste d’indices de compétences.
- 20 offres de démonstration (villes marocaines, métiers variés) + RSS We Work Remotely.
- Matching scoré, raisons en français, page offres.
- Lettres éditables, quotas par formule.
- Statuts, dashboard, journal.
- Bonus formule *Entretien garanti* : CV réordonné (mots-clés déjà présents), questions d’entretien.
- Tests unitaires matching / parseur et test d’intégration du parcours d’arrêt.

## 6. Résultats

Sur un CV « Python / FastAPI / SQL / Casablanca », les offres *Développeur Python junior* et *Data analyst* remontent devant *Comptable* ou *Designer UI/UX*. Le score n’est pas une vérité métier : c’est un **indice** que le candidat doit recouper avec l’annonce.

Les lettres gabarit sont répétitives mais honnêtes. Avec un LLM, la qualité rhétorique s’améliore à condition de garder le filtre et la relecture humaine — exigence de transparence du cahier des charges.

## 7. Éthique, légal, sécurité

- **09-08 / RGPD** : consentement à l’inscription, finalité limitée à la candidature, droit d’effacement (`DELETE /api/auth/compte`).
- **Sites tiers** : pas d’automatisation de comptes ; RSS public + jeu interne.
- **Honnêteté** : pas de compétence fantôme dans le CV adapté.
- **Sécurité** : bcrypt, JWT, `.env` hors Git, pas de secrets dans le dépôt.

## 8. Limites

- Parsing fragile sur CV tabulaires / colonnes.
- RSS international, peu d’offres marocaines « live » (d’où le jeu de démo, comme le conseille la fiche).
- Envoi simulé uniquement.
- TF-IDF sensible au vocabulaire exact de l’annonce.
- Python très récent : certaines roues binaires peuvent manquer ; le matching n’utilise pas scikit-learn pour cette raison.

## 9. Organisation

Les 35 tâches ClickUp structurent six sprints (cadrage → soutenance). Git : branches à créer selon l’équipe (`main`, `feat/parser`, etc.). Definition of Done : code + test ou écran + mention dans le journal d’activité.

## 10. Conclusion et pistes

Le prototype montre qu’un agent utile n’est pas un spam de candidatures : c’est un **filtre + une rédaction contrôlée + un stop**. Extensions : embeddings, e-mail réel opt-in, détection d’offres frauduleuses, FR/AR/EN, analyse marché par ville.

## Annexes

- User stories : `docs/cahier_des_charges.md`
- UML : `docs/diagrammes.md`
- Slides : `docs/presentation.html`
- Jeu d’offres : `backend/data/offres_demo.json`
