# Diagrammes UML

## Cas d'utilisation

```mermaid
usecaseDiagram
    actor Candidat
    actor Agent
    Candidat --> (Créer un compte et consentir 09-08)
    Candidat --> (Importer un CV)
    Candidat --> (Consulter les offres scorées)
    Candidat --> (Valider une lettre)
    Candidat --> (Suivre les statuts)
    Candidat --> (Choisir une formule)
    Candidat --> (Supprimer ses données)
    Agent --> (Collecter les offres)
    Agent --> (Calculer le matching)
    Agent --> (Générer une lettre honnête)
    Agent --> (Journaliser)
    Agent --> (Arrêter après un entretien)
    (Valider une lettre) ..> (Générer une lettre honnête) : include
    (Suivre les statuts) ..> (Arrêter après un entretien) : extend
```

## Classes (simplifié)

```mermaid
classDiagram
    class User {
      +id
      +nom
      +email
      +password_hash
      +formule
      +consentement_09_08
    }
    class Profil {
      +competences
      +experiences
      +formation
      +langues
      +preferences
      +cv_texte
    }
    class Offre {
      +source
      +titre
      +entreprise
      +ville
      +description
      +fingerprint
    }
    class Candidature {
      +score
      +explication
      +lettre
      +statut
    }
    class Journal {
      +action
      +details
      +date
    }
    User "1" --> "1" Profil
    User "1" --> "*" Candidature
    Offre "1" --> "*" Candidature
    User "1" --> "*" Journal
```

## Séquence — du CV à l'entretien

```mermaid
sequenceDiagram
    participant C as Candidat
    participant UI as Frontend
    participant API as FastAPI
    participant M as Matching
    participant L as Module lettres
    C->>UI: Upload CV
    UI->>API: POST /api/profil/cv
    API-->>UI: Profil structuré
    C->>UI: Voir offres
    UI->>API: GET /api/offres/recommandees
    API->>M: classer(profil, offres)
    M-->>API: scores + raisons
    API-->>UI: liste
    C->>UI: Générer lettre
    UI->>API: POST /candidatures/{id}/lettre
    API->>L: faits du CV uniquement
    L-->>API: texte
    C->>UI: Valider puis envoyer
    UI->>API: POST .../envoyer
    C->>UI: Statut entretien
    API-->>API: agent_arrete = true
```
