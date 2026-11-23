import React, { useEffect, useState } from "react";
import {
  ArrowDownToLine, ArrowLeft, ArrowRight, ArrowUpRight, Bell, BriefcaseBusiness,
  Building2, CalendarDays, Check, CheckCircle2, ChevronDown, CircleHelp, Clock3,
  FileCheck2, FileText, Filter, LayoutDashboard, LogOut, MapPin,
  Menu, MessageSquareText, Plus, Search, Settings2, ShieldCheck, Sparkles,
  Target, TrendingUp, UserRound, X,
} from "lucide-react";

const TOKEN_KEY = "eg_token";
const $ = (selector, root = document) => root.querySelector(selector);
const STATUSES = ["a_envoyer", "envoyee", "reponse", "entretien", "refus"];
const STATUS_NAMES = { a_envoyer: "À préparer", envoyee: "Envoyée", reponse: "Réponse reçue", entretien: "Entretien", refus: "Refus" };
const STATUS_TONES = { a_envoyer: "slate", envoyee: "blue", reponse: "violet", entretien: "green", refus: "rose" };

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    options = { ...options, body: JSON.stringify(options.body) };
  }
  const response = await fetch(path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Erreur ${response.status}`);
  return data;
}

async function download(path, fallback) {
  const token = localStorage.getItem(TOKEN_KEY);
  const response = await fetch(path, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Le téléchargement a échoué.");
  }
  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") || "";
  const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] || fallback;
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
}

function useRoute() {
  const [route, setRoute] = useState(() => location.hash.slice(1) || "/");
  useEffect(() => {
    const onChange = () => setRoute(location.hash.slice(1) || "/");
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}

function useData(path, refreshKey = 0) {
  const [state, setState] = useState({ data: null, error: "", loading: true });
  useEffect(() => {
    let active = true;
    setState((current) => ({ ...current, loading: true, error: "" }));
    api(path).then((data) => active && setState({ data, error: "", loading: false }))
      .catch((error) => active && setState({ data: null, error: error.message, loading: false }));
    return () => { active = false; };
  }, [path, refreshKey]);
  return state;
}

function Button({ children, variant = "secondary", className = "", ...props }) {
  return <button className={`button button-${variant} ${className}`} {...props}>{children}</button>;
}

function PageTitle({ eyebrow, title, description, action }) {
  return <div className="page-title-row"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{description && <p className="page-description">{description}</p>}</div>{action}</div>;
}

function Badge({ children, tone = "slate", dot = false }) {
  return <span className={`badge badge-${tone}`}>{dot && <i />}{children}</span>;
}

function Score({ value = 0 }) {
  const percent = Math.round((value || 0) * 100);
  return <div className="score-wrap"><div className="score-ring" style={{ "--score": `${percent * 3.6}deg` }}><span>{percent}<small>%</small></span></div><span className="score-caption">compatibilité</span></div>;
}

function EmptyState({ icon: Icon = FileText, title, text, action }) {
  return <div className="empty-state"><span className="empty-icon"><Icon size={22} /></span><h3>{title}</h3><p>{text}</p>{action}</div>;
}

function Loading({ label = "Chargement…" }) {
  return <div className="loading"><span className="spinner" />{label}</div>;
}

function AuthPage({ mode, onAuth, onNotice }) {
  const signup = mode === "inscription";
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const verifie = new URLSearchParams(location.search).get("verifie");
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");

    const form = new FormData(event.currentTarget);
    const body = Object.fromEntries(form.entries());

    if (signup) body.consentement_09_08 = form.has("consentement_09_08");

    if (signup && body.password !== body.password_confirm) {
      setError("Les deux mots de passe ne correspondent pas.");
      setBusy(false);
      return;
    }

    try {
      const result = await api(
        signup ? "/api/auth/register" : "/api/auth/login",
        { method: "POST", body }
      );

      if (signup) {
        setError("");
        setMessage(
          "Inscription réussie. Consultez votre boîte e-mail pour vérifier votre adresse."
        );
        location.hash = "#/connexion";
      } else {
        onAuth(result);
        onNotice("Content de vous revoir.");
        history.replaceState(null, "", location.pathname);
        location.hash = "#/dashboard";
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-layout">
      <a className="wordmark auth-wordmark" href="#/">
        <span className="brand-mark">
          <BriefcaseBusiness size={19} />
        </span>
        <span>
          Entretien<span className="brand-light"> garanti</span>
        </span>
      </a>

      <section className="auth-panel">
        <div className="auth-art">
          <div className="auth-art-copy">
            <Badge tone="light">
              <Sparkles size={13} /> Votre prochain chapitre
            </Badge>
            <h1>Une recherche d’emploi qui avance avec vous.</h1>
            <p>
              Des offres pertinentes, un suivi simple et une préparation claire
              à chaque étape.
            </p>
            <div className="auth-proof">
              <span><Check size={14} /> Profil valorisé</span>
              <span><Check size={14} /> Parcours suivi</span>
            </div>
          </div>

          <div className="auth-orbit orbit-one" />
          <div className="auth-orbit orbit-two" />

          <div className="auth-art-card">
            <span className="mini-icon"><Target size={16} /></span>
            <div>
              <strong>Une candidature à la fois</strong>
              <small>Du profil à l’entretien</small>
            </div>
            <ArrowUpRight size={17} />
          </div>
        </div>

        <div className="auth-form-wrap">
          <div className="auth-form-head">
            <span className="eyebrow">
              {signup ? "Commencer gratuitement" : "Votre espace personnel"}
            </span>
            <h2>{signup ? "Créer votre compte" : "Bon retour parmi nous"}</h2>
            <p>
              {signup
                ? "Configurez votre espace candidat en quelques instants."
                : "Connectez-vous pour reprendre votre recherche."}
            </p>
          </div>

          <form className="form-stack" onSubmit={submit}>
            {signup && (
              <Field label="Nom complet">
                <input name="nom" placeholder="Votre nom" required minLength="2" />
              </Field>
            )}

            <Field label="Adresse e-mail">
              <input
                name="email"
                type="email"
                placeholder="vous@exemple.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </Field>

            <Field label="Mot de passe">
              <input
                name="password"
                type="password"
                placeholder="8 caractères minimum"
                minLength="8"
                required
              />
            </Field>

            {signup && (
              <Field label="Confirmer le mot de passe">
                <input
                  name="password_confirm"
                  type="password"
                  placeholder="Retapez le mot de passe"
                  minLength="8"
                  required
                />
              </Field>
            )}

            {signup && (
              <>
                <Field label="Formule">
                  <select name="formule" defaultValue="decouverte">
                    <option value="decouverte">Découverte · gratuit</option>
                    <option value="candidat">Candidat</option>
                    <option value="garanti">Entretien garanti</option>
                  </select>
                </Field>

                <label className="check-row">
                  <input
                    name="consentement_09_08"
                    type="checkbox"
                    required
                  />
                  <span>
                    J’accepte le traitement de mes données pour utiliser le
                    service. Je peux supprimer mon compte depuis mon profil.
                  </span>
                </label>
              </>
            )}

            {!signup && verifie === "1" && <div className="notice notice-info"><CheckCircle2 size={17} />Votre adresse e-mail est vérifiée. Vous pouvez maintenant vous connecter.</div>}
            {!signup && verifie === "0" && <div className="notice notice-error"><X size={17} />Lien invalide, expiré ou déjà utilisé. Si votre compte n’est pas encore vérifié, demandez un nouveau lien.</div>}
            {error && <div className="notice notice-error">{error}</div>}

            {message && (
              <div className="notice notice-success">{message}</div>
            )}

            <Button
              type="submit"
              variant="primary"
              className="button-wide"
              disabled={busy}
            >
              {busy
                ? "Un instant…"
                : signup
                  ? "Créer mon espace"
                  : "Se connecter"}
              <ArrowRight size={16} />
            </Button>
          </form>

          {!signup && (
            <button
              type="button"
              className="auth-resend"
              onClick={async () => {
                if (!email.trim()) {
                  setError("Saisissez votre adresse e-mail.");
                  return;
                }

                try {
                  const result = await api(
                    "/api/auth/renvoyer-verification",
                    {
                      method: "POST",
                      body: { email },
                    }
                  );

                  setError("");
                  setMessage(result.message);
                } catch (err) {
                  setError(err.message);
                }
              }}
            >
              Renvoyer le lien de vérification
            </button>
          )}

          <p className="auth-switch">
            {signup
              ? "Vous avez déjà un compte ?"
              : "Vous découvrez le service?"}{" "}
            <a href={signup ? "#/connexion" : "#/inscription"}>
              {signup ? "Se connecter" : "Créer un compte"}
            </a>
          </p>

          <div className="auth-secure">
            <ShieldCheck size={15} /> Vos informations restent confidentielles
          </div>
        </div>
      </section>

      <footer className="auth-footer">
        © 2026 Entretien garanti <span>·</span> Conçu pour accompagner votre
        recherche
      </footer>
    </div>
  );
}

function Field({ label, hint, children, className = "" }) {
  return <label className={`field ${className}`}><span className="field-label">{label}</span>{children}{hint && <small className="field-hint">{hint}</small>}</label>;
}

const navigation = [
  { heading: "ESPACE CANDIDAT", items: [
    ["/dashboard", "Vue d’ensemble", LayoutDashboard], ["/offres", "Offres recommandées", Search], ["/candidatures", "Mes candidatures", BriefcaseBusiness],
  ] },
  { heading: "MON PROFIL", items: [["/profil", "Profil & CV", UserRound], ["/formules", "Mon abonnement", Sparkles], ["/journal", "Activité récente", Clock3]] },
];

function Shell({ route, user, onLogout, notice, onDismiss, children }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const activePath = route.startsWith("/candidature/") ? "/candidatures" : route;
  const initials = (user?.nom || "C").split(/\s+/).slice(0, 2).map((word) => word[0]).join("").toUpperCase();
  return <div className="app-frame">
    {mobileOpen && <button className="mobile-scrim" aria-label="Fermer le menu" onClick={() => setMobileOpen(false)} />}
    <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}><a className="wordmark" href="#/dashboard"><span className="brand-mark"><BriefcaseBusiness size={19} /></span><span>Entretien<span className="brand-light"> garanti</span></span></a><div className="workspace-switch"><span className="workspace-avatar">{initials || "C"}</span><span><strong>Espace candidat</strong><small>Recherche d’emploi</small></span><ChevronDown size={15} /></div>
      {navigation.map((group) => <div className="nav-group" key={group.heading}><div className="nav-heading">{group.heading}</div>{group.items.map(([path, label, Icon]) => <a key={path} className={`nav-link ${activePath === path ? "nav-active" : ""}`} href={`#${path}`} onClick={() => setMobileOpen(false)}><Icon size={18} strokeWidth={1.8} /><span>{label}</span>{path === "/candidatures" && <span className="nav-indicator" />}</a>)}</div>)}
      <div className="sidebar-spacer"/><div className="sidebar-help"><span className="help-icon"><CircleHelp size={17} /></span><strong>Besoin d’un coup de main ?</strong><p>Votre profil complet améliore la pertinence des offres.</p><a href="#/profil">Compléter mon profil <ArrowRight size={13} /></a></div><button className="account-button" onClick={onLogout}><span className="avatar">{initials}</span><span className="account-copy"><strong>{user?.nom || "Mon compte"}</strong><small>{user?.email || "Candidat"}</small></span><LogOut size={16} /></button>
    </aside>
    <div className="main-column"><header className="topbar"><button className="icon-button mobile-menu" aria-label="Ouvrir le menu" onClick={() => setMobileOpen(true)}><Menu size={20} /></button><div className="breadcrumbs"><span>Mon espace</span><span className="crumb-slash">/</span><strong>{route.startsWith("/candidature/") ? "Détail de candidature" : (navigation.flatMap((g) => g.items).find(([path]) => path === route)?.[1] || "Accueil")}</strong></div><div className="topbar-actions"><span className="topbar-status"><i /> Espace candidat</span><a className="icon-button" href="#/journal" title="Activité récente" aria-label="Activité récente"><Bell size={18} /></a><a
    className="topbar-avatar"
    href="#/profil"
    title="Mon profil"
    aria-label="Accéder à mon profil">
  {initials}
</a></div></header>
      {notice && <div className="toast"><CheckCircle2 size={17} />{notice}<button aria-label="Fermer" onClick={onDismiss}><X size={15} /></button></div>}
      <main className="content-area">{children}</main><footer className="app-footer"><span>Entretien garanti</span><span>Un accompagnement clair, à chaque étape.</span><a href="#/journal">Confidentialité & activité</a></footer>
    </div>
  </div>;
}

function Dashboard({ onNotice }) {
  const { data, error, loading } = useData("/api/dashboard");
  const profileState = useData("/api/profil");
  if (loading) return <Loading label="Préparation de votre espace…" />;
  if (error) return <NoticeError message={error} />;
  const count = Object.values(data.par_statut || {}).reduce((sum, value) => sum + value, 0);
  const profile = profileState.data || {};
  const hasProfile = Boolean(profile.cv_filename && profile.competences?.length && profile.pref_poste);
  return <><PageTitle eyebrow="VOTRE RECHERCHE, EN UN SEUL ENDROIT" title={`Bonjour ${(data.user.nom || "").split(" ")[0]} 👋`} description="Voici où vous en êtes dans votre recherche d’emploi." action={<a className="button button-primary" href="#/offres"><Search size={16} />Explorer les offres</a>} />
    {data.agent_arrete && <div className="stop-banner"><span className="stop-icon"><CheckCircle2 size={19} /></span><div><strong>Félicitations pour votre entretien !</strong><p>Votre agent a suspendu les nouvelles candidatures. Vous pouvez préparer la suite sereinement.</p></div><a href="#/candidatures">Voir le suivi <ArrowRight size={14} /></a></div>}
    <section className="stat-grid"><StatCard icon={BriefcaseBusiness} label="Candidatures suivies" value={count} detail={`${data.compteurs.envois} envoyée${data.compteurs.envois > 1 ? "s" : ""}`} tint="green" /><StatCard icon={CalendarDays} label="Entretiens obtenus" value={data.par_statut.entretien || 0} detail="Chaque échange compte" tint="violet" /><StatCard icon={FileCheck2} label="Lettres préparées" value={data.compteurs.lettres} detail={`Sur ${data.plan.max_lettres} disponibles`} tint="amber" /><StatCard icon={Target} label="Offres dans la base" value={data.n_offres} detail="À explorer selon votre profil" tint="blue" /></section>
    <div className="dashboard-grid"><section className="panel recent-panel"><div className="panel-heading"><div><h2>Activité récente</h2><p>Le suivi de vos dernières candidatures</p></div><a className="text-link" href="#/candidatures">Tout afficher <ArrowRight size={14} /></a></div>{data.recentes.length ? <div className="table-scroll"><table className="data-table"><thead><tr><th>Poste</th><th>Correspondance</th><th>Statut</th><th>Dernière activité</th><th /></tr></thead><tbody>{data.recentes.map((item) => <tr key={item.id}><td><strong>{item.titre}</strong><small>{item.entreprise}</small></td><td><div className="table-score"><span className="tiny-bar"><i style={{ width: `${Math.round(item.score * 100)}%` }} /></span>{Math.round(item.score * 100)}%</div></td><td><Badge tone={STATUS_TONES[item.statut]} dot>{STATUS_NAMES[item.statut] || item.statut}</Badge></td><td>{dateShort(item.date_maj)}</td><td><a className="row-open" href={`#/candidature/${item.id}`} aria-label={`Ouvrir ${item.titre}`}><ArrowUpRight size={16} /></a></td></tr>)}</tbody></table></div> : <EmptyState icon={BriefcaseBusiness} title="Votre suivi commence ici" text="Enregistrez une offre qui vous intéresse pour suivre votre candidature." action={<a className="button button-primary" href="#/offres">Voir les offres <ArrowRight size={15} /></a>} />}</section>
      <aside className="panel side-panel"><div className="panel-heading"><div><h2>Prochaines étapes</h2><p>De petits pas, un profil plus fort</p></div><Sparkles className="heading-spark" size={18} /></div><div className="step-list"><Step icon={UserRound} title="Compléter votre profil" text="Ajoutez compétences et préférences." href="/profil" done={hasProfile} /><Step icon={Search} title="Explorer les offres" text="Repérez les postes qui vous correspondent." href="/offres" /><Step icon={FileText} title="Préparer une candidature" text="Créez une candidature et générez vos documents." href="/candidatures" /></div><div className="plan-mini"><span className="plan-mini-icon"><Sparkles size={15} /></span><div><small>VOTRE FORMULE</small><strong>{data.plan.nom}</strong></div><a href="#/formules" aria-label="Voir ma formule"><ArrowRight size={15} /></a></div></aside></div>
  </>;
}

function StatCard({ icon: Icon, label, value, detail, tint }) {
  return <article className="stat-card"><div className={`stat-icon stat-${tint}`}><Icon size={19} /></div><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-detail">{detail}</div></article>;
}

function Step({ icon: Icon, title, text, href, done }) {
  return <a className="step-item" href={`#${href}`}><span className={`step-icon ${done ? "step-done" : ""}`}>{done ? <Check size={16} /> : <Icon size={16} />}</span><span><strong>{title}</strong><small>{done ? "Votre profil est prêt." : text}</small></span><ArrowRight size={15} /></a>;
}

function OffersPage({ onNotice }) {
  const [refresh, setRefresh] = useState(0);
  const [filter, setFilter] = useState("Toutes");
  const [search, setSearch] = useState("");
  const [sourceFilter, setSourceFilter] = useState("Toutes les sources");
  const [sortBy, setSortBy] = useState("score");
  const { data, error, loading } = useData("/api/offres/recommandees", refresh);
  const [busyId, setBusyId] = useState(null);
  const [importBusy, setImportBusy] = useState(false);
  if (loading) return <Loading label="Analyse des offres et de votre profil…" />;
  if (error) return <><PageTitle eyebrow="OPPORTUNITÉS" title="Offres recommandées" description="Des postes classés selon votre expérience, vos compétences et vos préférences." /><NoticeError message={error} action={<a className="button button-primary" href="#/profil">Compléter mon profil</a>} /></>;
  const options = ["Toutes", "Très bon match", "Télétravail"];
  const sourceOptions = ["Toutes les sources", ...new Set(data.offres.map((offer) => offer.source))];
  const query = [data.preferences?.pref_poste].filter(Boolean).join(" ") || "emploi";
  const where = data.preferences?.pref_ville || "";
  const linkedinSearch = `https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(query)}&location=${encodeURIComponent(where)}`;
  const indeedSearch = `https://www.indeed.com/jobs?q=${encodeURIComponent(query)}&l=${encodeURIComponent(where)}`;
  const needle = search.trim().toLocaleLowerCase("fr");
  const filtered = data.offres.filter((offer) => {
    const matchesPill = filter === "Toutes" || (filter === "Très bon match" ? offer.score >= 0.65 : /remote|distance|télétravail/i.test(offer.ville || ""));
    const text = [offer.titre, offer.entreprise, offer.ville, offer.description, ...(offer.matching?.competences_requises || [])].join(" ").toLocaleLowerCase("fr");
    return matchesPill && (sourceFilter === "Toutes les sources" || offer.source === sourceFilter) && (!needle || text.includes(needle));
  }).sort((a, b) => sortBy === "recent" ? String(b.date_pub || "").localeCompare(String(a.date_pub || "")) : (b.score || 0) - (a.score || 0));
  async function create(offer) {
    setBusyId(offer.id);
    try {
      const application = await api("/api/candidatures", { method: "POST", body: { offre_id: offer.id } });
      location.hash = `#/candidature/${application.id}`;
    } catch (err) { onNotice(err.message); }
    finally { setBusyId(null); }
  }
  async function collect() {
    setBusyId("collect");
    try { const result = await api("/api/offres/collecter", { method: "POST" }); setRefresh((n) => n + 1); onNotice(`Collecte terminée : ${Object.values(result.ajoutees || {}).reduce((a, b) => a + b, 0)} nouvelle(s) offre(s).`); }
    catch (err) { onNotice(err.message); }
    finally { setBusyId(null); }
  }
  async function importOffer(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form).entries());
    setImportBusy(true);
    try {
      const result = await api("/api/offres/importer", { method: "POST", body: values });
      form.reset(); setRefresh((n) => n + 1);
      onNotice(result.deja_existante ? "Cette annonce est déjà dans votre espace." : "Annonce ajoutée et classée dans vos offres.");
    } catch (err) { onNotice(err.message); }
    finally { setImportBusy(false); }
  }
  return <><PageTitle eyebrow="TROUVEZ VOTRE PROCHAINE OPPORTUNITÉ" title="Offres recommandées" description="Chaque score est expliqué : voyez ce qui correspond à votre profil et ce que vous pourrez renforcer." action={<Button disabled={busyId === "collect"} onClick={collect}><TrendingUp size={16} />Actualiser</Button>} />
    <div className="live-source-note"><div><strong>Offres réelles actualisées</strong><span>Remotive et We Work Remotely · chaque annonce conserve son attribution.</span></div><div className="portal-search-links"><span>Recherche externe :</span><a href={linkedinSearch} target="_blank" rel="noreferrer">LinkedIn</a><a href={indeedSearch} target="_blank" rel="noreferrer">Indeed</a></div></div>
    <details className="import-job"><summary><Plus size={16} />Ajouter une offre trouvée sur LinkedIn, Indeed ou un autre site</summary><form className="import-job-form" onSubmit={importOffer}><div className="import-job-grid"><Field label="Intitulé du poste"><input name="titre" required minLength="3" maxLength="180" placeholder="Ex. Développeur Python" /></Field><Field label="Entreprise"><input name="entreprise" maxLength="120" placeholder="Nom de l’entreprise" /></Field><Field label="Ville ou mode de travail"><input name="ville" maxLength="160" placeholder="Casablanca, hybride, télétravail…" /></Field><Field label="Lien de l’annonce"><input name="url" type="url" required placeholder="https://…" /></Field><Field label="Description et compétences demandées" className="import-description"><textarea name="description" maxLength="12000" rows="4" placeholder="Collez ici les principales missions et compétences demandées." /></Field></div><div className="import-job-footer"><span>Le lien est conservé. L’annonce n’est pas aspirée automatiquement.</span><Button type="submit" variant="primary" disabled={importBusy}>{importBusy ? "Ajout…" : "Ajouter à mes offres"}<ArrowRight size={15} /></Button></div></form></details>
    <div className="offer-controls"><label className="offer-search"><Search size={16} /><input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Poste, entreprise, ville ou compétence" /></label><label className="filter-select"><span>Source</span><select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)}>{sourceOptions.map((source) => <option key={source}>{source}</option>)}</select><ChevronDown size={14} /></label><label className="filter-select"><span>Trier</span><select value={sortBy} onChange={(e) => setSortBy(e.target.value)}><option value="score">Meilleure correspondance</option><option value="recent">Plus récentes</option></select><ChevronDown size={14} /></label></div>
    <div className="offers-toolbar"><div className="filter-pills"><Filter size={15} />{options.map((option) => <button key={option} type="button" aria-pressed={filter === option} className={filter === option ? "filter-active" : ""} onClick={() => setFilter(option)}>{option}</button>)}</div><span className="result-count">{filtered.length} offre{filtered.length > 1 ? "s" : ""} · {data.formule.nom}</span></div>
    {data.agent_arrete && <div className="notice notice-info"><CheckCircle2 size={18} />Votre entretien est obtenu. Les offres restent consultables, mais les nouvelles candidatures sont suspendues.</div>}
    {filtered.length ? <div className="offer-grid">{filtered.map((offer) => <article className="offer-card" key={offer.id}><div className="offer-card-top"><span className="company-avatar">{(offer.entreprise || "E").slice(0, 1).toUpperCase()}</span><span className="source-label">{offer.source === "demo" ? "DÉMONSTRATION" : `SOURCE · ${offer.source.toUpperCase()}`}</span><span className="offer-type-icon"><FileCheck2 size={16} /></span></div><div className="offer-title-line"><div><h2>{offer.titre}</h2><div className="company-name">{offer.entreprise || "Entreprise"}</div></div><Score value={offer.score} /></div><div className="offer-meta"><span><MapPin size={14} />{offer.ville || "Lieu non précisé"}</span><span><Clock3 size={14} />{offer.matching?.contrat_detecte || "Contrat à confirmer"}</span></div><p className="offer-description">{(offer.description || "Découvrez les détails de cette opportunité.").slice(0, 185)}{(offer.description || "").length > 185 ? "…" : ""}</p><div className="skill-label">{offer.matching?.competences_requises?.length || 0} COMPÉTENCES DEMANDÉES</div><div className="skill-list">{(offer.matching?.competences_requises || []).slice(0, 8).map((skill) => <span className={`skill-chip ${(offer.matching?.competences_communes || []).some((x) => x.toLowerCase() === skill.toLowerCase()) ? "skill-good" : ""}`} key={skill}>{skill}</span>)}{(offer.matching?.competences_requises || []).length > 8 && <span className="skill-more">+{offer.matching.competences_requises.length - 8} autres compétences</span>}{!offer.matching?.competences_requises?.length && <span className="skill-chip">Aucune compétence détectée</span>}</div><div className="offer-card-bottom">{offer.url ? <a className="subtle-link" href={offer.url} target="_blank" rel="noreferrer">Voir l’annonce <ArrowUpRight size={14} /></a> : <span className="subtle-link">Score expliqué</span>}<Button variant="primary" disabled={busyId === offer.id || data.agent_arrete} onClick={() => create(offer)}>{busyId === offer.id ? "Création…" : "Suivre cette offre"}<ArrowRight size={15} /></Button></div></article>)}</div> : <EmptyState icon={Search} title="Aucune offre dans ce filtre" text="Essayez une autre sélection ou actualisez les offres disponibles." action={<Button onClick={() => setFilter("Toutes")}>Afficher toutes les offres</Button>} />}
  </>;
}

function ApplicationsPage() {
  const [refresh, setRefresh] = useState(0);
  const [status, setStatus] = useState("toutes");
  const { data, error, loading } = useData("/api/candidatures", refresh);
  if (loading) return <Loading label="Chargement de vos candidatures…" />;
  if (error) return <NoticeError message={error} />;
  const items = data.items.filter((item) => status === "toutes" || item.statut === status);
  return <><PageTitle eyebrow="VOTRE PARCOURS" title="Mes candidatures" description="Gardez une vue claire sur chaque opportunité, de la préparation au retour de l’entreprise." action={<a href="#/offres" className="button button-primary"><Plus size={16} />Nouvelle candidature</a>} />
    {data.agent_arrete && <div className="stop-banner"><span className="stop-icon"><CheckCircle2 size={19} /></span><div><strong>Un entretien est confirmé</strong><p>Les nouvelles candidatures sont en pause. Consultez votre guide de préparation depuis le détail de la candidature.</p></div></div>}
    <div className="application-summary"><div><span>EN SUIVI</span><strong>{data.items.length}</strong></div><div><span>LETTRES</span><strong>{data.compteurs.lettres}</strong></div><div><span>ENVOYÉES</span><strong>{data.compteurs.envois}</strong></div><div><span>ENTRETIENS</span><strong>{data.items.filter((x) => x.statut === "entretien").length}</strong></div></div>
    <section className="panel applications-panel"><div className="panel-heading"><div><h2>Votre pipeline</h2><p>Un historique à jour pour avancer en confiance</p></div><label className="filter-select"><Filter size={15} /><select value={status} onChange={(e) => setStatus(e.target.value)}><option value="toutes">Tous les statuts</option>{STATUSES.map((x) => <option key={x} value={x}>{STATUS_NAMES[x]}</option>)}</select><ChevronDown size={14} /></label></div>{items.length ? <div className="table-scroll"><table className="data-table application-table"><thead><tr><th>Poste / entreprise</th><th>Match</th><th>État</th><th>Mis à jour</th><th /></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td><a className="job-cell-link" href={`#/candidature/${item.id}`}><span className="company-avatar company-avatar-small">{(item.entreprise || "E").slice(0, 1).toUpperCase()}</span><span><strong>{item.titre}</strong><small>{item.entreprise} · {item.ville}</small></span></a></td><td><div className="table-score"><span className="tiny-bar"><i style={{ width: `${Math.round(item.score * 100)}%` }} /></span>{Math.round(item.score * 100)}%</div></td><td><Badge tone={STATUS_TONES[item.statut]} dot>{STATUS_NAMES[item.statut] || item.statut}</Badge></td><td>{dateShort(item.date_maj)}</td><td><a className="row-open" href={`#/candidature/${item.id}`}><ArrowRight size={16} /></a></td></tr>)}</tbody></table></div> : <EmptyState icon={BriefcaseBusiness} title={status === "toutes" ? "Pas encore de candidature" : "Aucun résultat pour ce statut"} text={status === "toutes" ? "Parcourez les offres adaptées à votre profil et enregistrez celles qui vous intéressent." : "Choisissez un autre statut pour voir vos candidatures."} action={status === "toutes" ? <a href="#/offres" className="button button-primary">Explorer les offres <ArrowRight size={15} /></a> : <Button onClick={() => setStatus("toutes")}>Voir tout</Button>} />}</section>
  </>;
}


function ApplicationDetail({ id, user, onNotice }) {
  const { data, error, loading } = useData("/api/candidatures");
  const [application, setApplication] = useState(null);
  const [confirmSend, setConfirmSend] = useState(false);
  const [busy, setBusy] = useState("");

  useEffect(() => {
    const found = data?.items.find(
      (item) => String(item.id) === String(id)
    );
    if (found) setApplication(found);
  }, [data, id]);

  if (loading) return <Loading />;
  if (error) return <NoticeError message={error} />;

  if (!application) {
    return (
      <EmptyState
        icon={FileText}
        title="Candidature introuvable"
        text="Cette candidature n’est plus disponible."
        action={
          <a href="#/candidatures" className="button">
            Retour au suivi
          </a>
        }
      />
    );
  }

  const c = application;
  const requiredSkills = c.explication?.competences_requises || [];
  const matchedSkillKeys = new Set(
    (c.explication?.competences_communes || []).map((skill) =>
      skill.toLocaleLowerCase("fr")
    )
  );

  const progressStages = ["a_envoyer", "envoyee", "reponse", "entretien"];
  const currentStage = progressStages.indexOf(c.statut);

  async function run(name, action) {
    setBusy(name);
    try {
      const result = await action();
      if (result) {
        setApplication((old) => ({ ...old, ...result }));
      }
      return result;
    } catch (err) {
      onNotice(err.message);
    } finally {
      setBusy("");
    }
  }

    // Appelée quand la candidate clique sur "Oui" dans la notification.
  function confirmerEnvoi() {
    setConfirmSend(false); // on ferme la notification tout de suite
    run("confirm-send", async () => {
      // Appel au backend : il passe le statut de "a_envoyer" à "envoyee" (aucun envoi réel)
      const result = await api(`/api/candidatures/${id}/confirmer-envoi`, { method: "POST" });
      onNotice(result.message); // affiche la notification verte de succès, comme "Lettre enregistrée"
      return result;
    });
  }


  async function makeDownload(type) {
    const isCv = type === "cv";
    setBusy(type);

    try {
      await download(
        `/api/candidatures/${id}/documents/${
          isCv ? "cv-adapte.docx" : "guide-entretien.pdf"
        }`,
        isCv ? "CV-adapte.docx" : "Guide-entretien.pdf"
      );

      onNotice(
        isCv
          ? "Votre CV adapté est prêt."
          : "Votre guide d’entretien est prêt."
      );
    } catch (err) {
      onNotice(err.message);
    } finally {
      setBusy("");
    }
  }

  return (
    <>
        {confirmSend && (
        <div className="toast toast-confirm" role="alertdialog">
          <CircleHelp size={17} />
          <span>Avez-vous bien envoyé votre candidature à cette entreprise ?</span>
          <span className="toast-confirm-actions">
            <button type="button" className="toast-yes" onClick={confirmerEnvoi}>Oui</button>
            <button type="button" className="toast-no" onClick={() => setConfirmSend(false)}>Non</button>
          </span>
        </div>
      )}
      <a className="back-link" href="#/candidatures">
        <ArrowLeft size={15} />
        Retour à mes candidatures
      </a>

      <div className="detail-heading">
        <div>
          <div className="eyebrow">DÉTAIL DE LA CANDIDATURE</div>
          <h1>{c.titre}</h1>
          <div className="detail-company">
            <Building2 size={16} />
            {c.entreprise}
            <span>·</span>
            <MapPin size={15} />
            {c.ville}
          </div>
        </div>
        <div className="detail-score">
          <Score value={c.score} />
        </div>
      </div>

      <section
        className={`application-progress ${
          c.statut === "refus" ? "progress-refused" : ""
        }`}
        aria-label="Progression de la candidature"
      >
        {progressStages.map((stage, index) => (
          <div
            key={stage}
            className={`progress-step ${
              c.statut !== "refus" && index <= currentStage
                ? "progress-step-done"
                : ""
            }`}
          >
            <span className="progress-dot">
              {c.statut !== "refus" && index < currentStage ? (
                <Check size={12} />
              ) : (
                index + 1
              )}
            </span>
            <span>{STATUS_NAMES[stage]}</span>
          </div>
        ))}

        {c.statut === "refus" && (
          <strong className="refusal-label">
            Candidature clôturée
          </strong>
        )}
      </section>

      <div className="detail-layout">
        <div className="detail-main">
          <section className="panel detail-panel">
            <div className="panel-heading">
              <div>
                <h2>Votre lettre de motivation</h2>
                <p>
                  Relisez et ajustez le texte avant de l’utiliser.
                </p>
              </div>
              <Badge tone={c.lettre ? "green" : "amber"} dot>
                {c.lettre ? "Brouillon disponible" : "À rédiger"}
              </Badge>
            </div>

            <textarea
              className="letter-editor"
              value={c.lettre || ""}
              onChange={(event) =>
                setApplication({ ...c, lettre: event.target.value })
              }
              placeholder="Générez une première version puis adaptez-la à votre voix…"
            />

            <div className="action-row">
              <Button
                disabled={busy === "generate-letter"}
                onClick={() =>
                  run("generate-letter", async () => {
                    const result = await api(
                      `/api/candidatures/${id}/lettre`,
                      { method: "POST" }
                    );
                    setApplication((old) => ({
                      ...old,
                      lettre: result.texte,
                    }));
                    onNotice("Votre lettre a été préparée.");
                  })
                }
              >
                <Sparkles size={15} />
                {busy === "generate-letter"
                  ? "Génération…"
                  : "Générer une lettre"}
              </Button>

              <Button
                variant="primary"
                disabled={busy === "save-letter"}
                onClick={() =>
                  run("save-letter", async () => {
                    await api(`/api/candidatures/${id}`, {
                      method: "PATCH",
                      body: { lettre: c.lettre || "" },
                    });
                    onNotice("Lettre enregistrée.");
                  })
                }
              >
                <Check size={15} />
              </Button>

              {c.statut === "a_envoyer" && (
                <Button
                  variant="primary"
                  disabled={busy === "confirm-send"}
                  onClick={() => setConfirmSend(true)}
                >
                  <Check size={15} />
                  {busy === "confirm-send"
                    ? "Confirmation…"
                    : "Marquer comme envoyée"}
                </Button>
              )}
            </div>
          </section>

          <section className="panel document-panel">
            <div className="document-panel-icon">
              <FileCheck2 size={20} />
            </div>
            <div className="document-panel-copy">
              <div className="eyebrow">VOS DOCUMENTS</div>
              <h2>Prêts pour cette opportunité</h2>
              <p>
                Un CV ciblé et un guide d’entretien construits à partir de
                votre profil.
              </p>
            </div>
            <div className="document-actions">
              <Button
                variant="primary"
                disabled={busy === "cv"}
                onClick={() => makeDownload("cv")}
              >
                <ArrowDownToLine size={15} />
                CV adapté · Word
              </Button>
              <Button
                disabled={busy === "guide"}
                onClick={() => makeDownload("guide")}
              >
                <ArrowDownToLine size={15} />
                Guide · PDF
              </Button>
            </div>
          </section>

          <section className="panel detail-panel">
            <div className="panel-heading">
              <div>
                <h2>Compétences demandées dans l’annonce</h2>
                <p>
                  {requiredSkills.length} compétence
                  {requiredSkills.length === 1 ? "" : "s"} détectée
                  {requiredSkills.length === 1 ? "" : "s"} ·{" "}
                  {matchedSkillKeys.size} retrouvée
                  {matchedSkillKeys.size === 1 ? "" : "s"} dans votre profil
                  et votre CV
                </p>
              </div>
              <span className="match-score-text">
                {Math.round((c.score || 0) * 100)}%
              </span>
            </div>

            {requiredSkills.length ? (
              <div
                className="skill-list skill-list-all"
                aria-label="Liste complète des compétences requises"
              >
                {requiredSkills.map((skill) => {
                  const matched = matchedSkillKeys.has(
                    skill.toLocaleLowerCase("fr")
                  );

                  return (
                    <span
                      className={`skill-chip ${
                        matched ? "skill-good" : "skill-missing"
                      }`}
                      key={skill}
                      title={
                        matched
                          ? "Présente dans votre profil ou votre CV"
                          : "Non détectée dans votre profil ou votre CV"
                      }
                    >
                      {matched ? (
                        <Check size={12} />
                      ) : (
                        <X size={12} />
                      )}
                      {skill}
                    </span>
                  );
                })}
              </div>
            ) : (
              <p className="no-skills-message">
                Aucune compétence explicite détectée dans le texte de cette
                annonce.
              </p>
            )}

            <div className="reason-list">
              {(c.explication?.raisons || []).map((reason, index) => (
                <div className="reason-item" key={index}>
                  <span>
                    <Check size={14} />
                  </span>
                  {reason}
                </div>
              ))}
            </div>
          </section>
        </div>

        <aside className="detail-aside">
          <section className="panel status-panel">
            <div className="panel-heading">
              <div>
                <h2>Suivi du processus</h2>
                <p>Consultez l’état de votre candidature.</p>
              </div>
              <ShieldCheck size={17} />
            </div>

            <div className="application-status-display">
              <span className="field-label">Statut actuel</span>
              <Badge tone={STATUS_TONES[c.statut] || "slate"} dot>
                {STATUS_NAMES[c.statut] || c.statut}
              </Badge>
            </div>

<div className="interview-info">
  <div className="form-divider">
    <CalendarDays size={15} />
    INFORMATIONS D’ENTRETIEN
  </div>

  <div className="interview-info-item">
    <span className="field-label">Date et heure</span>
    <div className="interview-value">
      {c.entretien_date
        ? `${dateShort(c.entretien_date)} · ${timeShort(c.entretien_date)}`
        : "\u00A0"}
    </div>
  </div>

  <div className="interview-info-item">
    <span className="field-label">Lieu ou lien</span>
    <div className="interview-value">
      {c.entretien_lieu || "\u00A0"}
    </div>
  </div>

  <div className="interview-info-item">
    <span className="field-label">Notes et consignes</span>
    <div className="interview-value">
      {c.entretien_notes || "\u00A0"}
    </div>
  </div>
</div>

            {c.entretien_email_envoye && (
              <div className="email-sent">
                <CheckCircle2 size={15} />
                E-mail de confirmation envoyé
              </div>
            )}

            {!c.entretien_email_envoye && (
              <div className="aside-footnote">
                <ShieldCheck size={14} />
                Le statut et les informations d’entretien sont communiqués
                par l’entreprise.
              </div>
            )}
          </section>

          <section className="panel prep-panel">
            <span className="prep-icon">
              <MessageSquareText size={17} />
            </span>
            <h3>Préparer votre échange</h3>
            <p>
              Le guide PDF propose des questions et des pistes de réponse
              basées sur votre profil.
            </p>
            <Button
              className="button-wide"
              onClick={() => makeDownload("guide")}
            >
              <ArrowDownToLine size={15} />
              Télécharger le guide
            </Button>
          </section>
        </aside>
      </div>
    </>
  );
}


function ProfilePage({ onNotice }) {
  const [refresh, setRefresh] = useState(0);
  const { data, error, loading } = useData("/api/auth/me", refresh);
  const [busy, setBusy] = useState(false);
  const [cvBusy, setCvBusy] = useState(false);
  const [errorText, setErrorText] = useState("");
  if (loading) return <Loading label="Chargement de votre profil…" />;
  if (error) return <NoticeError message={error} />;
  const profile = data.profil || {};
  async function save(event) {
    event.preventDefault(); setBusy(true); setErrorText("");
    const form = new FormData(event.currentTarget);
    const lines = (key) => String(form.get(key) || "").split("\n").map((line) => line.trim()).filter(Boolean);
    const body = { pref_poste: form.get("pref_poste"), pref_ville: form.get("pref_ville"), pref_contrat: form.get("pref_contrat"), competences: lines("competences"), experiences: lines("experiences"), formation: lines("formation"), langues: lines("langues") };
    try { await api("/api/profil", { method: "PUT", body }); onNotice("Votre profil a été enregistré."); setRefresh((current) => current + 1); }
    catch (err) { setErrorText(err.message); }
    finally { setBusy(false); }
  }
  async function upload(event) {
    event.preventDefault(); const file = event.currentTarget.file.files[0]; if (!file) return;
    setCvBusy(true); setErrorText(""); const form = new FormData(); form.append("file", file);
    try { await api("/api/profil/cv", { method: "POST", body: form }); onNotice("CV importé et profil mis à jour."); setRefresh((current) => current + 1); }
    catch (err) { setErrorText(err.message); }
    finally { setCvBusy(false); }
  }
  async function erase() {
    if (!window.confirm("Supprimer définitivement votre compte et vos données ?")) return;
    try { await api("/api/auth/compte", { method: "DELETE" }); localStorage.removeItem(TOKEN_KEY); location.hash = "#/"; }
    catch (err) { setErrorText(err.message); }
  }
  return <><PageTitle eyebrow="VOTRE PRÉSENTATION PROFESSIONNELLE" title="Profil & CV" description="Un profil précis permet de trouver des offres plus pertinentes et d’améliorer vos documents." /><div className="profile-layout"><div className="profile-main"><section className="panel profile-panel"><div className="panel-heading"><div><h2>Vos préférences de recherche</h2><p>Les critères utilisés pour classer les offres.</p></div><Target size={18} /></div><form id="profile-form" className="form-stack" onSubmit={save}><div className="field-grid"><Field label="Poste recherché"><input name="pref_poste" defaultValue={profile.pref_poste || ""} placeholder="Ex. développeuse web" /></Field><Field label="Ville ou région"><input name="pref_ville" defaultValue={profile.pref_ville || ""} placeholder="Ex. Casablanca" /></Field><Field label="Type de contrat"><select name="pref_contrat" defaultValue={profile.pref_contrat || ""}><option value="">Tous les contrats</option><option>CDI</option><option>CDD</option><option>Stage</option><option>Alternance</option><option>Freelance</option></select></Field></div><div className="form-divider"><UserRound size={15} />VOTRE PARCOURS</div><div className="field-grid"><Field label="Compétences" hint="Une compétence par ligne"><textarea name="competences" defaultValue={(profile.competences || []).join("\n")} placeholder={"Gestion de projet\nExcel\nCommunication"} /></Field><Field label="Expériences" hint="Postes, entreprises ou réalisations"><textarea name="experiences" defaultValue={(profile.experiences || []).join("\n")} placeholder="Décrivez vos expériences principales" /></Field><Field label="Formation"><textarea name="formation" defaultValue={(profile.formation || []).join("\n")} placeholder="Diplômes et formations" /></Field><Field label="Langues"><textarea name="langues" defaultValue={(profile.langues || []).join("\n")} placeholder="Français, arabe…" /></Field></div>{errorText && <div className="notice notice-error">{errorText}</div>}<div className="form-actions"><Button variant="primary" type="submit" disabled={busy}>{busy ? "Enregistrement…" : "Enregistrer mon profil"}<Check size={15} /></Button></div></form></section><section className="panel profile-panel"><div className="panel-heading"><div><h2>Importer un CV</h2><p>Le PDF ou Word sert à préremplir les éléments de votre parcours.</p></div><FileText size={18} /></div><form className="upload-zone" onSubmit={upload}><input name="file" type="file" accept=".pdf,.docx" required /><div><strong>{profile.cv_filename || "Choisir votre CV"}</strong><small>PDF ou DOCX · 8 Mo maximum</small></div><Button variant="primary" type="submit" disabled={cvBusy}>{cvBusy ? "Lecture…" : "Importer le CV"}<ArrowUpRight size={15} /></Button></form></section></div><aside className="profile-aside"><section className="panel profile-strength"><span className="profile-strength-icon"><ShieldCheck size={20} /></span><div className="eyebrow">VOTRE PROFIL</div><h3>La précision fait la différence.</h3><p>Ajoutez vos compétences et vos expériences pour obtenir un matching plus utile.</p><div className="strength-bar"><i style={{ width: `${profile.cv_filename ? 85 : Math.min(70, 20 + (profile.competences || []).length * 8)}%` }} /></div><small>{profile.cv_filename ? "Profil enrichi avec votre CV" : `${(profile.competences || []).length} compétence(s) renseignée(s)`}</small></section><section className="panel privacy-panel"><ShieldCheck size={17} /><h3>Vos données vous appartiennent</h3><p>Vous pouvez demander leur suppression à tout moment.</p><button className="text-danger" onClick={erase}>Supprimer mon compte</button></section></aside></div></>;
}

function PlansPage({ onNotice }) {
  const { data, error, loading } = useData("/api/dashboard"); const [busy, setBusy] = useState(""); const [selected, setSelected] = useState("");
  if (loading) return <Loading />; if (error) return <NoticeError message={error} />;
  const highlights = [["Offres analysées", (plan) => `${plan.max_matchs} offres`], ["Lettres", (plan) => `${plan.max_lettres} par période`], ["Suivi", () => "Candidatures & statuts"], ["Préparation", (plan) => plan.prep_entretien ? "Documents & entretien" : "Outils essentiels"]];
  async function choose(id) { setBusy(id); try { await api("/api/formule", { method: "PUT", body: { formule: id } }); setSelected(id); onNotice("Votre formule a été mise à jour."); } catch (err) { onNotice(err.message); } finally { setBusy(""); } }
  return <><PageTitle eyebrow="UNE FORMULE À VOTRE RYTHME" title="Mon abonnement" description="Choisissez les outils qui accompagnent le mieux votre recherche." /><div className="plan-grid">{Object.entries(data.formules).map(([id, plan], index) => { const current = selected || data.user.formule; return <article className={`plan-card ${index === 2 ? "plan-featured" : ""}`} key={id}>{index === 2 && <div className="plan-ribbon"><Sparkles size={13} />ACCOMPAGNEMENT COMPLET</div>}<div className={`plan-icon plan-icon-${index}`}><Sparkles size={19} /></div><div className="plan-price">{plan.prix}</div><h2>{plan.nom}</h2><p>{plan.resume}</p><div className="plan-divider"/><div className="plan-feature-list">{highlights.map(([label, value]) => <div key={label}><Check size={15} /><span><small>{label}</small><strong>{value(plan)}</strong></span></div>)}</div><Button variant={current === id ? "quiet" : index === 2 ? "primary" : "secondary"} className="button-wide" disabled={busy === id || current === id} onClick={() => choose(id)}>{current === id ? "Formule actuelle" : busy === id ? "Mise à jour…" : "Choisir cette formule"}</Button></article>;})}</div><p className="fine-print">La sélection est immédiate pour cette démonstration. Aucun paiement réel n’est effectué.</p></>;
}

function JournalPage() {
  const { data, error, loading } = useData("/api/journal"); if (loading) return <Loading />; if (error) return <NoticeError message={error} />;
  return <><PageTitle eyebrow="TRANSPARENCE" title="Activité récente" description="Retrouvez les principales actions effectuées dans votre espace." />{data.items.length ? <section className="panel journal-panel"><div className="journal-list">{data.items.map((item, index) => <div className="journal-row" key={`${item.id || index}-${item.date}`}><span className="journal-dot"><Clock3 size={14}/></span><span className="journal-action"><strong>{item.action.replaceAll("_", " ")}</strong><small>{item.details || "Activité de votre espace"}</small></span><time>{dateShort(item.date)} · {timeShort(item.date)}</time></div>)}</div></section> : <EmptyState icon={Clock3} title="Aucune activité pour le moment" text="Vos actions récentes apparaîtront ici." />}</>;
}

function NoticeError({ message, action }) { return <div className="notice notice-error"><X size={17} /><span>{message}</span>{action}</div>; }

function dateShort(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value.slice(0, 10) : new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "short", year: "numeric" }).format(date);
}
function timeShort(value) {
  if (!value) return "";
  const date = new Date(value); return Number.isNaN(date.getTime()) ? "" : new Intl.DateTimeFormat("fr-FR", { hour: "2-digit", minute: "2-digit" }).format(date);
}

export default function App() {
  const route = useRoute();
  const [user, setUser] = useState(null);
  const [notice, setNotice] = useState("");
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!localStorage.getItem(TOKEN_KEY)) { setReady(true); return; }
    api("/api/auth/me").then((data) => setUser(data.user)).catch(() => { localStorage.removeItem(TOKEN_KEY); setUser(null); }).finally(() => setReady(true));
  }, []);
  useEffect(() => { if (notice) { const timer = window.setTimeout(() => setNotice(""), 4800); return () => clearTimeout(timer); } }, [notice]);
  function onAuth(result) { localStorage.setItem(TOKEN_KEY, result.token); setUser(result.user); }
  function logout() { localStorage.removeItem(TOKEN_KEY); setUser(null); location.hash = "#/"; }
  if (!ready) return <div className="boot-screen"><div className="brand-mark"><BriefcaseBusiness size={20}/></div><span className="spinner"/></div>;
  if (!user && route !== "/" && route !== "/connexion" && route !== "/inscription") { location.hash = "#/connexion"; return <AuthPage mode="connexion" onAuth={onAuth} onNotice={setNotice}/>; }
  if (route === "/connexion" || route === "/inscription") return <AuthPage mode={route.slice(1)} onAuth={onAuth} onNotice={setNotice}/>;
  if (!user && route === "/") return <Landing />;
  let page;
  if (route === "/dashboard" || route === "/") page = <Dashboard onNotice={setNotice}/>;
  else if (route === "/offres") page = <OffersPage onNotice={setNotice}/>;
  else if (route === "/candidatures") page = <ApplicationsPage/>;
  else if (route.startsWith("/candidature/")) page = <ApplicationDetail id={route.split("/")[2]} user={user} onNotice={setNotice}/>;
  else if (route === "/profil") page = <ProfilePage onNotice={setNotice}/>;
  else if (route === "/formules") page = <PlansPage onNotice={setNotice}/>;
  else if (route === "/journal") page = <JournalPage/>;
  else page = <Dashboard onNotice={setNotice}/>;
  return <Shell route={route} user={user} onLogout={logout} notice={notice} onDismiss={() => setNotice("")}>{page}</Shell>;
}

function Landing() {
  return <div className="landing"><header className="landing-header"><a className="wordmark" href="#/"><span className="brand-mark"><BriefcaseBusiness size={19}/></span><span>Entretien<span className="brand-light"> garanti</span></span></a><nav><a href="#/connexion">Se connecter</a><a className="button button-primary" href="#/inscription">Créer mon espace <ArrowRight size={15}/></a></nav></header><main><section className="landing-hero"><div className="landing-copy"><Badge tone="soft"><Sparkles size={13}/>Votre recherche, mieux accompagnée</Badge><h1>Du profil à l’entretien, gardez le fil de votre recherche.</h1><p>Découvrez des offres réelles, comparez leurs compétences avec votre profil, suivez chaque candidature et préparez vos échanges.</p><div className="landing-actions"><a href="#/inscription" className="button button-primary">Créer mon espace <ArrowRight size={16}/></a><a href="#/connexion" className="button button-quiet">J’ai déjà un compte</a></div><div className="landing-trust"><span><CheckCircle2 size={15}/> Vos candidatures, suivies</span><span><ShieldCheck size={15}/> Votre profil reste le vôtre</span></div></div><div className="landing-visual"><div className="visual-orbit orbit-one"/><div className="visual-orbit orbit-two"/><div className="preview-window"><div className="preview-top"><span/><span/><span/><small>APERÇU ILLUSTRATIF</small></div><div className="preview-body"><div className="preview-greeting"><div><small>TABLEAU DE BORD</small><strong>Votre recherche avance</strong></div><span className="preview-avatar"><TrendingUp size={17}/></span></div><div className="preview-stats"><div><small>CANDIDATURES</small><strong>08</strong><i/></div><div><small>ENTRETIENS</small><strong>02</strong><i/></div></div><div className="preview-offer"><span className="preview-logo">N</span><div><strong>Product Designer</strong><small>Nova Studio · Casablanca</small></div><span className="preview-match">92%</span></div><div className="preview-offer"><span className="preview-logo logo-blue">A</span><div><strong>Cheffe de projet</strong><small>Atlas Digital · Hybride</small></div><span className="preview-match">86%</span></div></div></div><div className="float-note"><span><Check size={15}/></span><div><strong>Votre profil valorisé</strong><small>Compétences mises en avant</small></div></div><div className="float-score"><span>94%</span><small>DE MATCH</small></div></div></section><section className="landing-features"><div className="landing-feature"><span className="feature-icon feature-green"><Target size={19}/></span><div><strong>Des offres pertinentes</strong><p>Un classement expliqué selon votre profil et vos préférences.</p></div></div><div className="landing-feature"><span className="feature-icon feature-violet"><FileCheck2 size={19}/></span><div><strong>Des candidatures préparées</strong><p>CV adapté, lettre et guide d’entretien au même endroit.</p></div></div><div className="landing-feature"><span className="feature-icon feature-amber"><TrendingUp size={19}/></span><div><strong>Un suivi lisible</strong><p>Visualisez les étapes et gardez le fil de votre recherche.</p></div></div></section><section className="landing-bottom"><div><span className="eyebrow">LE PROCHAIN PAS EST SIMPLE</span><h2>Construisez votre recherche à votre rythme.</h2></div><a href="#/inscription" className="button button-primary">Commencer maintenant <ArrowRight size={16}/></a></section></main><footer className="landing-footer"><span>© 2026 Entretien garanti</span><span>Vos données restent sous votre contrôle.</span></footer></div>;
}