"""Matching TF-IDF + recouvrement de compétences, avec explication."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

STOP = {
    "le", "la", "les", "un", "une", "des", "de", "du", "et", "ou", "en", "au", "aux",
    "pour", "par", "avec", "sans", "sur", "dans", "que", "qui", "dont", "est", "sont",
    "plus", "moins", "très", "the", "and", "or", "to", "of", "in", "for", "a", "an",
    "nous", "vous", "leur", "cette", "ces", "ce", "son", "sa", "ses", "votre", "notre",
}

CORRECTIONS = {
    "engenieer": "engineer",
    "engenier": "engineer",
    "ingeneer": "engineer",
    "ingeneur": "ingenieur",
    "ingeneure": "ingenieur",
    "developper": "developer",
    "developpeur": "developpeur",
    "analist": "analyste",
    "analyst": "analyste",
}

SYNONYMES = {
    "engineer": {"engineer", "ingenieur", "ingenieure"},
    "ingenieur": {"engineer", "ingenieur", "ingenieure"},
    "ingenieure": {"engineer", "ingenieur", "ingenieure"},
    "developer": {"developer", "developpeur", "dev"},
    "developpeur": {"developer", "developpeur", "dev"},
    "analyste": {"analyste", "analyst"},
    "data": {"data", "donnee", "donnees"},
    "frontend": {"frontend", "front"},
    "backend": {"backend", "back"},
}

CONTRAT_ALIAS = {
    "cdi": "cdi",
    "cdd": "cdd",
    "stage": "stage",
    "stagiaire": "stage",
    "internship": "stage",
    "alternance": "alternance",
    "freelance": "freelance",
    "independant": "freelance",
    "independante": "freelance",
}

# Catalogue étendu de compétences. L'extraction combine ce vocabulaire avec les
# compétences explicitement fournies par l'annonce ou le profil.
COMPETENCES_CATALOGUE = (
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", ".NET", "PHP", "Ruby", "Go", "Golang", "Rust", "Kotlin", "Swift", "Dart", "R", "MATLAB", "VBA", "Bash", "PowerShell", "Scala", "Perl", "Objective-C", "Elixir", "Haskell", "Clojure", "Lua", "Groovy", "Fortran", "COBOL",
    "HTML", "CSS", "Sass", "Less", "Tailwind CSS", "Bootstrap", "React", "Next.js", "Vue.js", "Nuxt.js", "Angular", "Svelte", "Node.js", "Express.js", "NestJS", "Fastify", "FastAPI", "Django", "Flask", "Spring Boot", "Spring", "ASP.NET", "Laravel", "Symfony", "Ruby on Rails", "Phoenix", "Gin", "Fiber", "Flutter", "React Native", "Ionic", "jQuery",
    "SQL", "NoSQL", "PostgreSQL", "Postgres", "MySQL", "MariaDB", "SQLite", "Microsoft SQL Server", "Oracle Database", "MongoDB", "Redis", "Elasticsearch", "OpenSearch", "Cassandra", "DynamoDB", "Firestore", "Neo4j", "BigQuery", "Snowflake", "Redshift", "Databricks", "Data Warehouse", "Data Lake", "ETL", "ELT", "dbt", "Apache Spark", "PySpark", "Apache Kafka", "Apache Airflow", "Pandas", "NumPy", "Polars", "Dask", "Hadoop", "Hive", "Flink", "Data Modeling", "Data Modelling", "Data Engineering", "Data Analysis", "Data Analytics", "Business Intelligence", "Data Visualization", "Data Quality", "Data Governance", "Data Mining", "Statistics", "Statistiques", "Analyse de données", "Analyse de données", "Informatique décisionnelle",
    "Machine Learning", "Deep Learning", "Artificial Intelligence", "Intelligence artificielle", "IA générative", "Generative AI", "Natural Language Processing", "Traitement du langage naturel", "Computer Vision", "Vision par ordinateur", "Large Language Models", "Prompt Engineering", "MLOps", "TensorFlow", "PyTorch", "scikit-learn", "Keras", "Hugging Face", "LangChain", "LlamaIndex", "OpenAI API", "RAG", "OCR", "NLP", "LLM", "IA", "Power BI", "Tableau", "Looker", "Qlik Sense", "Excel", "Google Sheets", "SPSS", "SAS", "Jupyter", "Matplotlib", "Seaborn",
    "AWS", "Amazon Web Services", "Azure", "Microsoft Azure", "GCP", "Google Cloud", "Google Cloud Platform", "Oracle Cloud", "OCI", "Cloud Computing", "Cloud Architecture", "Serverless", "Microservices", "Docker", "Kubernetes", "K8s", "Helm", "Terraform", "Ansible", "Puppet", "Chef", "Jenkins", "GitHub Actions", "GitLab CI", "CI/CD", "DevOps", "DevSecOps", "SRE", "Linux", "Unix", "Windows Server", "Nginx", "Apache HTTP Server", "Prometheus", "Grafana", "Datadog", "OpenTelemetry", "Argo CD", "Pulumi", "Vagrant", "Packer",
    "Git", "GitHub", "GitLab", "Bitbucket", "REST API", "RESTful API", "GraphQL", "gRPC", "SOAP", "WebSocket", "JSON", "XML", "YAML", "OAuth", "OAuth 2.0", "OpenID Connect", "JWT", "API Design", "API Integration", "Cybersecurity", "Cybersécurité", "Application Security", "Network Security", "Penetration Testing", "OWASP", "IAM", "Active Directory", "SIEM", "Incident Response", "Information Security", "ISO 27001", "NIST",
    "Unit Testing", "Integration Testing", "End-to-End Testing", "Test Automation", "Quality Assurance", "Software Testing", "TDD", "BDD", "Selenium", "Playwright", "Cypress", "pytest", "Jest", "Vitest", "JUnit", "Postman", "JMeter", "Appium", "Robot Framework", "SonarQube",
    "Figma", "Adobe XD", "Adobe Photoshop", "Adobe Illustrator", "Adobe InDesign", "Sketch", "Canva", "UI Design", "UX Design", "UX Research", "User Research", "Interaction Design", "Prototyping", "Wireframing", "Design System", "Accessibility", "WCAG", "Premiere Pro", "After Effects", "Blender", "AutoCAD", "SolidWorks", "Revit", "CATIA", "GIS", "ArcGIS", "QGIS",
    "Project Management", "Gestion de projet", "Product Management", "Product Ownership", "Agile", "Scrum", "Kanban", "SAFe", "Jira", "Confluence", "Trello", "Asana", "Notion", "Leadership", "Team Leadership", "People Management", "Communication", "Communication écrite", "Communication orale", "Travail d'équipe", "Travail en équipe", "Collaboration", "Problem Solving", "Résolution de problèmes", "Critical Thinking", "Esprit critique", "Autonomie", "Adaptabilité", "Organisation", "Gestion du temps", "Négociation", "Customer Service", "Service client", "Relation client", "Customer Success", "CRM", "Salesforce", "HubSpot", "SAP", "ERP", "Sales", "Vente", "Account Management", "Business Development", "Prospection commerciale", "Négociation commerciale", "Marketing", "Digital Marketing", "Marketing digital", "SEO", "SEA", "SEM", "Google Analytics", "Google Ads", "Meta Ads", "Social Media Marketing", "Content Marketing", "Content Creation", "Copywriting", "Email Marketing", "Growth Marketing", "Market Research", "Étude de marché", "Brand Management", "Public Relations", "Relations presse",
    "Accounting", "Comptabilité", "Bookkeeping", "Finance", "Financial Analysis", "Analyse financière", "Financial Modeling", "Financial Reporting", "Budgeting", "Forecasting", "Audit", "Auditing", "Tax", "Fiscalité", "Payroll", "Paie", "Excel avancé", "QuickBooks", "Sage", "Cegid", "SAP FI", "Financial Accounting",
    "Human Resources", "Ressources humaines", "Recruitment", "Recrutement", "Talent Acquisition", "HRIS", "Workday", "Employee Relations", "Formation professionnelle", "Training", "Performance Management", "Change Management", "Gestion du changement", "Supply Chain", "Logistics", "Logistique", "Procurement", "Achats", "Inventory Management", "Gestion de stock", "Operations Management", "Gestion des opérations", "Lean", "Six Sigma", "Lean Six Sigma", "Process Improvement", "Amélioration continue", "Quality Management", "Gestion de la qualité", "ISO 9001", "Project Planning", "Risk Management", "Gestion des risques", "Compliance", "Conformité", "Contract Management", "Gestion des contrats", "Research", "Recherche scientifique", "Laboratory Skills", "Laboratory Techniques", "Laboratoire", "First Aid", "Premiers secours", "Patient Care", "Soins aux patients", "Public Speaking", "Prise de parole en public", "Enseignement", "Teaching", "Pédagogie", "Rédaction", "Technical Writing", "Documentation technique", "Français", "French", "Anglais", "English", "Arabe", "Arabic", "Espagnol", "Spanish", "Allemand", "German", "Amazigh", "Italien", "Italian",
)

COMPETENCE_ALIAS = {
    "js": "javascript", "ecmascript": "javascript", "ts": "typescript",
    "node": "node.js", "nodejs": "node.js", "vue": "vue.js", "vuejs": "vue.js",
    "nextjs": "next.js", "nuxtjs": "nuxt.js", "reactjs": "react",
    "postgres": "postgresql", "postgresql": "postgresql", "mssql": "microsoft sql server",
    "sql server": "microsoft sql server", "mongo": "mongodb", "k8s": "kubernetes",
    "amazon web services": "aws", "microsoft azure": "azure", "google cloud platform": "google cloud",
    "gcp": "google cloud", "restful api": "rest api", "apis rest": "rest api",
    "api rest": "rest api", "ml": "machine learning", "deep-learning": "deep learning",
    "ai": "artificial intelligence", "genai": "generative ai", "nlp": "natural language processing",
    "traitement automatique du langage naturel": "natural language processing",
    "llm": "large language models", "large language model": "large language models",
    "pytorch": "pytorch", "powerbi": "power bi", "power-bi": "power bi",
    "ci cd": "ci/cd", "continuous integration": "ci/cd", "continuous deployment": "ci/cd",
    "ux": "ux design", "ui": "ui design", "user experience": "ux design", "user interface": "ui design",
    "gestion de projets": "gestion de projet", "project management": "project management",
    "teamwork": "travail en equipe", "team work": "travail en equipe",
    "problem-solving": "resolution de problemes", "problem solving": "resolution de problemes",
    "customer support": "service client", "customer care": "service client",
    "human resources": "ressources humaines", "hr": "ressources humaines",
    "talent acquisition": "recrutement", "supply-chain": "supply chain",
    "french": "francais", "english": "anglais", "arabic": "arabe",
    "spanish": "espagnol", "german": "allemand", "italian": "italien",
}


def normaliser_competence(value: str) -> str:
    key = sans_accents(str(value or "").lower()).strip()
    key = re.sub(r"\([^)]*\)|\[[^]]*\]", " ", key)
    key = re.sub(r"\b(avancee?|intermediaire|debutant|debutante|expert|experte|advanced|intermediate|beginner|proficient)\b", " ", key)
    key = re.sub(r"\s+", " ", key).strip(" .,:;-/")
    key = re.sub(r"\s+", " ", key)
    return COMPETENCE_ALIAS.get(key, key)


def extraire_competences(texte: str) -> list[str]:
    normalized = sans_accents((texte or "").lower())
    found: list[str] = []
    seen: set[str] = set()
    for skill in sorted(COMPETENCES_CATALOGUE, key=len, reverse=True):
        key = sans_accents(skill.lower())
        if skill == "Go":
            continue
        if len(key) == 1:
            continue
        if re.search(rf"(?<![a-z0-9]){re.escape(key)}(?![a-z0-9])", normalized):
            canonical = normaliser_competence(skill)
            if canonical not in seen:
                found.append(skill)
                seen.add(canonical)
    # Les annonces fournissent parfois des mots-clés sous forme de tags courts.
    for alias, canonical in COMPETENCE_ALIAS.items():
        if len(alias) < 3:
            continue
        if re.search(rf"(?<![a-z0-9]){re.escape(sans_accents(alias))}(?![a-z0-9])", normalized):
            key = normaliser_competence(canonical)
            display = next((item for item in COMPETENCES_CATALOGUE if normaliser_competence(item) == key), canonical)
            if key not in seen:
                found.append(display)
                seen.add(key)
    # R et Go sont ambigus seuls ; ne les compter que dans un contexte de langage.
    if re.search(r"\b(?:r\s*(?:programming|language|langage|studio)|rstudio)\b", normalized):
        if "r" not in seen:
            found.append("R")
            seen.add("r")
    if re.search(r"\b(?:go\s*(?:lang|language|langage|developer|programming)|golang)\b", normalized):
        if "go" not in seen:
            found.append("Go")
            seen.add("go")
    return found


SKILL_SECTION = re.compile(
    r"^(?:competences?(?:\s+(?:techniques?|requises?|demandees?|souhaitees?|cles?))?|"
    r"skills?(?:\s+(?:required|needed|preferred))?|qualifications?|requirements?|"
    r"profil recherche|what you(?:'|’)ll need|what you bring|must[- ]have skills?)\b",
    re.I,
)
SECTION_END = re.compile(
    r"^(?:missions?|responsabilites?|responsibilities|description|about us|a propos|"
    r"avantages|benefits|nous offrons|what you will do|your role)\b",
    re.I,
)


def _dedupe_skills(skills: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in skills:
        value = re.sub(r"\s+", " ", str(item or "").strip(" \t\r\n-–•·,;:/"))
        key = normaliser_competence(value)
        if value and key and key not in seen:
            result.append(value)
            seen.add(key)
    return result


def extraire_competences_requises(texte: str, tags: list[str] | None = None) -> list[str]:
    """Réunit les tags source, le catalogue et les listes explicites de prérequis."""
    found = list(tags or [])
    found.extend(extraire_competences(texte))
    in_skill_section = False
    for raw_line in re.split(r"[\r\n]+", texte or ""):
        line = re.sub(r"<[^>]+>", " ", raw_line)
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            continue
        normalized_line = sans_accents(line.lower()).strip(" :-")
        if SKILL_SECTION.search(normalized_line):
            in_skill_section = True
            tail = re.split(r"[:：]", line, maxsplit=1)
            line = tail[1].strip() if len(tail) > 1 else ""
        elif SECTION_END.search(normalized_line):
            in_skill_section = False
            continue
        if in_skill_section and line:
            # On conserve les éléments d'une liste de prérequis, sans prendre
            # une phrase entière de l'annonce pour une compétence.
            for item in re.split(r"[,;|•·\u2022]|\s+[+]\s+|\s+et\s+|\s+and\s+", line, flags=re.I):
                item = item.strip(" \t-–:*.")
                words = item.split()
                if 1 <= len(words) <= 5 and len(item) <= 64:
                    if not re.search(r"\b(?:nous recherchons|vous etes|vous serez|you will|we are looking)\b", item, re.I):
                        found.append(item)
    return _dedupe_skills(found)


def sans_accents(texte: str) -> str:
    t = unicodedata.normalize("NFD", texte or "")
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def tokeniser(texte: str) -> list[str]:
    mots = re.findall(r"[a-zA-ZàâäéèêëïîôùûüçÀÂÄÉÈÊËÏÎÔÙÛÜÇ+#.]{2,}", (texte or "").lower())
    out = []
    for m in mots:
        m = m.strip(".")
        if m in STOP or len(m) <= 1:
            continue
        canon = CORRECTIONS.get(sans_accents(m), m)
        out.append(canon)
    return out


def etendre(tokens: list[str] | set[str]) -> set[str]:
    out: set[str] = set()
    for t in tokens:
        n = sans_accents(t)
        n = CORRECTIONS.get(n, n)
        out.add(n)
        out.add(t)
        out |= SYNONYMES.get(n, set())
    return {sans_accents(x) for x in out}


def detecter_contrat(offre: dict) -> str:
    blob = sans_accents(f"{offre.get('titre') or ''} {offre.get('description') or ''}".lower())
    for alias, canon in CONTRAT_ALIAS.items():
        if re.search(rf"\b{re.escape(alias)}\b", blob):
            return canon
    return ""


def normaliser_contrat(pref: str) -> str:
    t = sans_accents((pref or "").lower().strip())
    t = re.sub(r"[^a-z]", "", t)
    return CONTRAT_ALIAS.get(t, t)


def _tf(tokens: list[str]) -> Counter:
    return Counter(tokens)


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) | set(b)
    num = sum(a[k] * b[k] for k in keys)
    da = math.sqrt(sum(v * v for v in a.values()))
    db = math.sqrt(sum(v * v for v in b.values()))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def _idf_weight(docs: list[list[str]]) -> dict[str, float]:
    n = max(len(docs), 1)
    df: Counter = Counter()
    for d in docs:
        df.update(set(d))
    return {t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}


def scorer(profil: dict, offre: dict, corpus_tokens: list[list[str]] | None = None) -> dict:
    cv = profil.get("cv_texte") or ""
    comps = [str(c) for c in profil.get("competences") or []]
    pref_poste = profil.get("pref_poste") or ""
    pref_ville = sans_accents((profil.get("pref_ville") or "").lower().strip())
    pref_contrat = normaliser_contrat(profil.get("pref_contrat") or "")
    texte_profil = " ".join(
        [cv, " ".join(comps), pref_poste, " ".join(profil.get("experiences") or [])]
    )
    texte_offre = " ".join(
        [
            offre.get("titre") or "",
            offre.get("entreprise") or "",
            offre.get("ville") or "",
            offre.get("description") or "",
        ]
    )
    tok_p = tokeniser(texte_profil)
    tok_o = tokeniser(texte_offre)
    docs = corpus_tokens or [tok_p, tok_o]
    idf = _idf_weight(docs)
    vec_p = Counter({t: _tf(tok_p)[t] * idf.get(t, 1.0) for t in set(tok_p)})
    vec_o = Counter({t: _tf(tok_o)[t] * idf.get(t, 1.0) for t in set(tok_o)})
    sim = _cosine(vec_p, vec_o)

    offre_low = texte_offre.lower()
    # Le candidat est évalué avec les champs structurés ET tout le texte du CV,
    # des expériences, de la formation et des langues.
    profil_competences = _dedupe_skills(
        comps + extraire_competences(texte_profil)
    )
    profil_skills = {normaliser_competence(skill) for skill in profil_competences}

    requis_source = offre.get("competences_requises") or []
    if isinstance(requis_source, str):
        try:
            import json
            parsed = json.loads(requis_source)
            requis_source = parsed if isinstance(parsed, list) else [parsed]
        except (ValueError, TypeError):
            requis_source = re.split(r"[,;|\n]", requis_source)
    elif not isinstance(requis_source, (list, tuple, set)):
        requis_source = []
    requis = extraire_competences_requises(texte_offre, [str(item) for item in requis_source])
    texte_profil_normalise = sans_accents(texte_profil.lower())

    def est_maitrisee(skill: str) -> bool:
        key = normaliser_competence(skill)
        if key in profil_skills:
            return True
        # Permet aussi de comparer une compétence écrite en toutes lettres dans
        # le CV à un tag différent mais équivalent de l'annonce.
        return bool(key and re.search(rf"(?<![a-z0-9]){re.escape(key)}(?![a-z0-9])", texte_profil_normalise))

    communs = [skill for skill in requis if est_maitrisee(skill)]
    if not requis:
        offre_skills = {normaliser_competence(skill) for skill in extraire_competences(texte_offre)}
        communs = [skill for skill in profil_competences if normaliser_competence(skill) in offre_skills]
    # La couverture des exigences mesure les compétences demandées que le
    # candidat possède. Le recouvrement inverse (part des compétences du CV
    # visibles dans l'offre) est conservé comme indicateur, mais ne gonfle pas
    # le score : un CV très long ne doit pas être favorisé artificiellement.
    recouvrement = len(communs) / max(len(profil_skills), 1)
    couverture_requise = len(communs) / max(len(requis), 1) if requis else 0.0
    manquantes = [skill for skill in requis if not est_maitrisee(skill)]

    ville_offre = sans_accents((offre.get("ville") or "").lower())
    remote = any(k in ville_offre for k in ("remote", "distanciel", "teletravail"))
    score_ville: float | None = None
    ville_ok = False
    if pref_ville and ville_offre:
        if pref_ville in ville_offre or ville_offre in pref_ville:
            score_ville = 1.0
            ville_ok = True
        elif remote:
            score_ville = 0.7
            ville_ok = True
        else:
            score_ville = 0.0

    score_titre: float | None = None
    titre = offre.get("titre") or ""
    tok_pref = etendre(tokeniser(pref_poste))
    tok_titre = etendre(tokeniser(titre))
    inter_titre = tok_pref & tok_titre
    if pref_poste and tok_pref:
        # F1 entre les mots du poste recherché et ceux du titre : pénalise
        # autant les mots attendus absents que les mots sans rapport.
        precision_titre = len(inter_titre) / max(len(tok_titre), 1)
        rappel_titre = len(inter_titre) / max(len(tok_pref), 1)
        score_titre = (
            2 * precision_titre * rappel_titre / (precision_titre + rappel_titre)
            if precision_titre + rappel_titre
            else 0.0
        )

    contrat_offre = detecter_contrat(offre)
    score_contrat: float | None = None
    contrat_ok = False
    if pref_contrat and contrat_offre:
        score_contrat = 1.0 if contrat_offre == pref_contrat else 0.0
        contrat_ok = contrat_offre == pref_contrat

    # Moyenne pondérée des critères disponibles, avec des poids explicites.
    # Les préférences absentes et les données d'annonce inconnues sont omises,
    # puis les poids restants sont normalisés pour toujours produire un score
    # de 0 à 100 %.
    criteres: list[tuple[str, float, float]] = []
    if requis:
        criteres.append(("competences", couverture_requise, 0.60))
    if texte_profil.strip():
        criteres.append(("similarite", sim, 0.20))
    if score_titre is not None:
        criteres.append(("poste", score_titre, 0.10))
    if score_ville is not None:
        criteres.append(("localisation", score_ville, 0.05))
    if score_contrat is not None:
        criteres.append(("contrat", score_contrat, 0.05))
    poids_actifs = sum(poids for _, _, poids in criteres)
    poids_effectifs = {
        nom: round(poids / poids_actifs, 4)
        for nom, _, poids in criteres
    } if poids_actifs else {}
    score = (
        sum(valeur * poids for _, valeur, poids in criteres) / poids_actifs
        if poids_actifs
        else 0.0
    )
    score = round(max(0.0, min(1.0, score)), 4)

    raisons = []
    if communs:
        raisons.append("Compétences demandées maîtrisées : " + ", ".join(communs[:8]))
    elif comps:
        raisons.append("Peu de compétences explicites du CV apparaissent dans l'annonce.")
    raisons.append(f"Similarité textuelle TF-IDF : {sim:.0%}.")
    if ville_ok and pref_ville:
        raisons.append("La localisation correspond aux préférences (ou offre en télétravail).")
    elif pref_ville:
        raisons.append("La ville de l'annonce ne correspond pas à la préférence.")
    if score_titre is not None and score_titre >= 0.5:
        raisons.append("Le titre se rapproche du poste recherché.")
    elif score_titre is not None:
        raisons.append("Le titre correspond peu au poste recherché.")
    elif pref_poste:
        raisons.append("Le titre s'éloigne du poste visé dans les préférences.")
    if pref_contrat and contrat_offre and contrat_ok:
        raisons.append(f"Type de contrat aligné ({pref_contrat.upper()}).")
    elif pref_contrat and contrat_offre and not contrat_ok:
        raisons.append("Le contrat de l'annonce ne correspond pas à la préférence.")
    if requis:
        raisons.append(f"Couverture des compétences requises : {couverture_requise:.0%} ({len(communs)}/{len(requis)}).")
    if criteres:
        labels_criteres = {
            "competences": "compétences", "similarite": "texte",
            "poste": "poste", "localisation": "localisation", "contrat": "contrat",
        }
        raisons.append("Critères du score : " + ", ".join(
            f"{labels_criteres[nom]} {valeur:.0%} (poids {poids_effectifs[nom]:.0%})"
            for nom, valeur, _ in criteres
        ) + ".")
    if manquantes:
        raisons.append("Compétences demandées à renforcer : " + ", ".join(manquantes[:8]) + ".")
    mots_profil = set(tokeniser(texte_profil))
    mots_manquants = [mot for mot in tokeniser(titre)[:8] if mot not in mots_profil and len(mot) > 3]
    if mots_manquants:
        raisons.append("Éléments de l'offre peu couverts par le CV : " + ", ".join(mots_manquants[:5]) + ".")

    return {
        "score": score,
        "similarite_tfidf": round(sim, 4),
        "recouvrement_competences": round(recouvrement, 4),
        "competences_communes": communs,
        "competences_requises": requis,
        "competences_profil": profil_competences,
        "competences_manquantes": manquantes,
        "couverture_competences": round(couverture_requise, 4),
        "details_score": {nom: round(valeur, 4) for nom, valeur, _ in criteres},
        "poids_score": poids_effectifs,
        "methode_score": "Moyenne pondérée normalisée : compétences requises 60 %, similarité textuelle 20 %, poste 10 %, localisation 5 %, contrat 5 % (critères indisponibles omis).",
        "raisons": raisons,
        "contrat_detecte": contrat_offre,
    }


def classer(profil: dict, offres: list[dict]) -> list[dict]:
    corpus = [tokeniser(profil.get("cv_texte") or "") + tokeniser(profil.get("pref_poste") or "")]
    for o in offres:
        corpus.append(tokeniser((o.get("titre") or "") + " " + (o.get("description") or "")))
    ranked = []
    for offre in offres:
        expl = scorer(profil, offre, corpus)
        ranked.append({**offre, "matching": expl, "score": expl["score"]})
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked
