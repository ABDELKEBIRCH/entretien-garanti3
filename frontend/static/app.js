const $ = (sel, el = document) => el.querySelector(sel);
const app = $("#app");
const TOKEN_KEY = "eg_token";
const esc = (s) =>
  String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;");

function prefsLine(p = {}) {
  const bits = [p.pref_poste, p.pref_ville, p.pref_contrat].map((x) => (x || "").trim()).filter(Boolean);
  if (!bits.length) {
    return "Aucune préférence enregistrée — le classement repose surtout sur le CV. Renseignez poste, ville et contrat dans Profil.";
  }
  return "Classement selon vos préférences : " + bits.map(esc).join(" · ");
}

const api = async (path, opts = {}) => {
  const headers = { ...(opts.headers || {}) };
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) headers.Authorization = `Bearer ${token}`;
  if (opts.body && !(opts.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(opts.body);
  }
  const res = await fetch(path, { ...opts, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || JSON.stringify(data) || res.statusText);
  return data;
};

const state = { me: null, flash: "" };

function route() {
  const hash = location.hash.replace("#", "") || "/";
  return hash.startsWith("/") ? hash : "/" + hash;
}

function nav() {
  const logged = !!localStorage.getItem(TOKEN_KEY);
  const links = logged
    ? [
        ["#/dashboard", "Tableau de bord"],
        ["#/offres", "Offres"],
        ["#/candidatures", "Candidatures"],
        ["#/profil", "Profil / CV"],
        ["#/formules", "Formules"],
        ["#/journal", "Journal"],
      ]
    : [
        ["#/", "Accueil"],
        ["#/connexion", "Connexion"],
        ["#/inscription", "Inscription"],
      ];
  return `
    <header class="top">
      <div class="brand">Entretien garanti
        <small>s'arrêter au premier oui</small>
      </div>
      <nav>
        ${links.map(([h, l]) => `<a href="${h}" class="${route() === h.slice(1) || (route()===h.replace('#','')) ? "active" : ""}">${l}</a>`).join("")}
        ${logged ? `<button class="btn btn-ghost" id="logout">Sortir</button>` : `<a class="btn btn-primary" href="#/inscription">Commencer</a>`}
      </nav>
    </header>`;
}

function layout(html) {
  app.innerHTML = `${nav()}<main class="wrap">${state.flash ? `<div class="flash">${state.flash}</div>` : ""}${html}</main>
    <footer>Prototype pédagogique — pas de scraping de comptes tiers, pas de paiement réel, candidatures simulées. Loi 09-08 : consentement, minimisation, droit de suppression.</footer>`;
  state.flash = "";
  $("#logout")?.addEventListener("click", () => {
    localStorage.removeItem(TOKEN_KEY);
    location.hash = "#/";
    render();
  });
}

function landing() {
  layout(`
    <section class="hero">
      <div>
        <p class="kicker">Agent de candidature</p>
        <h1>Le second métier de la recherche d'emploi, automatisé jusqu'à l'entretien.</h1>
        <p class="muted">Déposez votre CV. L'agent trouve des offres, écrit une lettre honnête, et s'arrête dès qu'un entretien est obtenu.</p>
        <div class="row" style="margin-top:18px">
          <a class="btn btn-primary" href="#/inscription">Créer un compte</a>
          <a class="btn btn-ghost" href="#/connexion">Se connecter</a>
        </div>
      </div>
      <div class="card">
        <h3>Quatre temps</h3>
        <ol>
          <li><strong>Trouver</strong> — démo marocaine + RSS</li>
          <li><strong>Adapter</strong> — lettre (et CV en formule premium)</li>
          <li><strong>Postuler</strong> — envoi simulé après validation</li>
          <li><strong>S'arrêter</strong> — statut « entretien obtenu »</li>
        </ol>
      </div>
    </section>
    <div class="steps">
      ${[
        ["01", "Trouver", "Matching TF-IDF + compétences, score expliqué."],
        ["02", "Adapter", "Lettre factuelle : rien d'inventé hors CV."],
        ["03", "Postuler", "Vous relisez, puis un clic (simulation)."],
        ["04", "S'arrêter", "L'agent se tait au premier entretien."],
      ].map(([n,t,d]) => `<article class="card"><p class="kicker">${n}</p><h3>${t}</h3><p class="muted">${d}</p></article>`).join("")}
    </div>
  `);
}

function formAuth(mode) {
  const insc = mode === "inscription";
  layout(`
    <div class="grid grid-2">
      <form class="card" id="auth">
        <h2>${insc ? "Créer un compte" : "Connexion"}</h2>
        ${insc ? `<label>Nom</label><input name="nom" required />` : ""}
        <label>E-mail</label><input name="email" type="email" required />
        <label>Mot de passe (8 caractères min.)</label><input name="password" type="password" required minlength="8" />
        ${insc ? `
          <label>Formule</label>
          <select name="formule">
            <option value="decouverte">Découverte (gratuit)</option>
            <option value="candidat">Candidat</option>
            <option value="garanti">Entretien garanti</option>
          </select>
          <label class="row"><input type="checkbox" name="consentement_09_08" required />
            J'accepte le traitement de mes données (loi 09-08) : CV, profil, candidatures. Droit de suppression dans Profil.
          </label>` : ""}
        <p id="err" class="flash err" hidden></p>
        <button class="btn btn-primary" type="submit">${insc ? "S'inscrire" : "Entrer"}</button>
      </form>
      <div class="card">
        <h3>Transparence</h3>
        <p class="muted">Les mots de passe sont hachés (bcrypt). Les lettres sont relisables avant tout envoi. L'IA ne doit pas inventer d'expériences.</p>
      </div>
    </div>
  `);
  $("#auth").onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = Object.fromEntries(fd.entries());
    if (insc) body.consentement_09_08 = fd.has("consentement_09_08");
    try {
      const data = await api(insc ? "/api/auth/register" : "/api/auth/login", { method: "POST", body });
      localStorage.setItem(TOKEN_KEY, data.token);
      location.hash = "#/dashboard";
      render();
    } catch (err) {
      const box = $("#err");
      box.hidden = false;
      box.textContent = err.message;
    }
  };
}

async function dashboard() {
  const d = await api("/api/dashboard");
  const s = d.par_statut;
  layout(`
    ${d.agent_arrete ? `<div class="banner-stop">Règle d'arrêt active : un entretien est obtenu. Plus aucune candidature ne part.</div>` : ""}
    <p class="kicker">Bonjour ${d.user.nom}</p>
    <h1>Tableau de bord</h1>
    <p class="muted">Formule ${d.plan.nom} — ${d.plan.resume}</p>
    <div class="grid grid-3" style="margin:18px 0">
      <div class="card"><p class="muted">Offres en base</p><div class="score">${d.n_offres}</div></div>
      <div class="card"><p class="muted">Lettres / envois</p><div class="score">${d.compteurs.lettres} / ${d.compteurs.envois}</div><p class="muted">plafonds ${d.plan.max_lettres} / ${d.plan.max_envois}</p></div>
      <div class="card"><p class="muted">Entretiens</p><div class="score">${s.entretien || 0}</div><p class="muted">${s.a_envoyer || 0} à envoyer · ${s.envoyee || 0} envoyées</p></div>
    </div>
    <div class="card">
      <h3>Dernières candidatures</h3>
      ${d.recentes.length ? `<table><thead><tr><th>Offre</th><th>Score</th><th>Statut</th></tr></thead><tbody>
        ${d.recentes.map(r => `<tr><td>${r.titre}<br><span class="muted">${r.entreprise}</span></td><td>${Math.round((r.score||0)*100)}%</td><td>${d.labels[r.statut] || r.statut}</td></tr>`).join("")}
      </tbody></table>` : `<p class="muted">Aucune candidature. Importez un CV puis ouvrez les offres recommandées.</p>`}
    </div>
  `);
}

async function profil() {
  const me = await api("/api/auth/me");
  const p = me.profil || {};
  layout(`
    <h1>Profil et CV</h1>
    <div class="grid grid-2">
      <form class="card" id="cvform">
        <h3>Import PDF / DOCX</h3>
        <input type="file" name="file" accept=".pdf,.docx" required />
        <button class="btn btn-primary" style="margin-top:12px">Extraire</button>
        <p class="muted">Fichier actuel : ${p.cv_filename || "aucun"}</p>
      </form>
      <form class="card" id="prefs">
        <h3>Préférences</h3>
        <p class="muted">Ces critères classent les offres (poste, ville, CDI/CDD/stage).</p>
        <label>Poste visé</label><input name="pref_poste" value="${esc(p.pref_poste)}" placeholder="ex. data engineer" />
        <label>Ville</label><input name="pref_ville" value="${esc(p.pref_ville)}" placeholder="ex. Agadir" />
        <label>Contrat</label><input name="pref_contrat" value="${esc(p.pref_contrat)}" placeholder="ex. CDI" />
        <button class="btn btn-primary" type="submit" style="margin-top:12px">Enregistrer</button>
      </form>
    </div>
    <div class="card" style="margin-top:16px">
      <h3>Données extraites (modifiables — honnêteté du CV)</h3>
      <form id="struct">
        <label>Compétences (une par ligne)</label>
        <textarea name="competences">${(p.competences || []).join("\n")}</textarea>
        <label>Expériences</label>
        <textarea name="experiences">${(p.experiences || []).join("\n")}</textarea>
        <label>Formation</label>
        <textarea name="formation">${(p.formation || []).join("\n")}</textarea>
        <label>Langues</label>
        <textarea name="langues">${(p.langues || []).join("\n")}</textarea>
        <button class="btn btn-primary" style="margin-top:12px">Mettre à jour le profil</button>
      </form>
    </div>
    <div class="card" style="margin-top:16px">
      <h3>Droit de suppression</h3>
      <p class="muted">Efface compte, CV, candidatures et journal.</p>
      <button class="btn btn-clay" id="wipe">Supprimer mon compte</button>
    </div>
  `);
  $("#cvform").onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData();
    fd.append("file", e.target.file.files[0]);
    try {
      await api("/api/profil/cv", { method: "POST", body: fd });
      state.flash = "CV lu et structuré.";
      render();
    } catch (err) { alert(err.message); }
  };
  const saveStruct = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const lines = (k) => (fd.get(k) || "").split("\n").map(s => s.trim()).filter(Boolean);
    const body = e.target.id === "prefs"
      ? Object.fromEntries(fd.entries())
      : { competences: lines("competences"), experiences: lines("experiences"), formation: lines("formation"), langues: lines("langues") };
    try {
      await api("/api/profil", { method: "PUT", body });
      state.flash = "Profil enregistré.";
      render();
    } catch (err) { alert(err.message); }
  };
  $("#prefs").onsubmit = saveStruct;
  $("#struct").onsubmit = saveStruct;
  $("#wipe").onclick = async () => {
    if (!confirm("Supprimer définitivement le compte ?")) return;
    await api("/api/auth/compte", { method: "DELETE" });
    localStorage.removeItem(TOKEN_KEY);
    location.hash = "#/";
    render();
  };
}

async function offres() {
  layout(`<h1>Offres recommandées</h1><p class="muted">Collecte et matching en cours…</p>`);
  const data = await api("/api/offres/recommandees");
  layout(`
    ${data.agent_arrete ? `<div class="banner-stop">Agent à l'arrêt — consultation seule.</div>` : ""}
    <div class="row"><h1 style="margin:0">Offres recommandées</h1>
      <button class="btn btn-ghost" id="refresh">Relancer la collecte</button>
      <span class="pill">${data.formule.nom} · max ${data.formule.max_matchs} offres</span>
    </div>
    <p class="muted">${prefsLine(data.preferences)}</p>
    <div class="grid" style="margin-top:16px">
      ${data.offres.length ? data.offres.map(o => `
        <article class="card">
          <div class="row" style="justify-content:space-between">
            <div>
              <h3 style="margin:0">${o.titre}</h3>
              <p class="muted">${o.entreprise} · ${o.ville} · ${o.source}</p>
            </div>
            <div class="score">${Math.round((o.score||0)*100)}%</div>
          </div>
          <p>${(o.description || "").slice(0, 280)}…</p>
          <p>${(o.matching?.competences_communes || []).map(c => `<span class="tag">${c}</span>`).join("")}</p>
          <ul>${(o.matching?.raisons || []).map(r => `<li class="muted">${r}</li>`).join("")}</ul>
          <div class="row">
            ${o.url ? `<a class="btn btn-ghost" href="${o.url}" target="_blank" rel="noopener">Annonce</a>` : ""}
            <button class="btn btn-primary" data-id="${o.id}">Créer une candidature</button>
          </div>
        </article>`).join("") : `<div class="card"><p>Aucune offre pour ces préférences. Vérifiez le poste, la ville et le contrat, ou relancez la collecte.</p></div>`}
    </div>
  `);
  $("#refresh").onclick = async () => {
    await api("/api/offres/collecter", { method: "POST" });
    render();
  };
  app.querySelectorAll("button[data-id]").forEach(b => {
    b.onclick = async () => {
      try {
        const c = await api("/api/candidatures", { method: "POST", body: { offre_id: Number(b.dataset.id) } });
        location.hash = `#/candidature/${c.id}`;
        render();
      } catch (err) { alert(err.message); }
    };
  });
}

async function candidatures() {
  const data = await api("/api/candidatures");
  layout(`
    ${data.agent_arrete ? `<div class="banner-stop">Règle d'arrêt : entretien obtenu.</div>` : ""}
    <h1>Candidatures</h1>
    <p class="muted">${data.compteurs.lettres} lettres · ${data.compteurs.envois} envois</p>
    <div class="card">
      <table>
        <thead><tr><th>Offre</th><th>Score</th><th>Statut</th><th></th></tr></thead>
        <tbody>
          ${data.items.map(i => `<tr>
            <td>${i.titre}<br><span class="muted">${i.entreprise}</span></td>
            <td>${Math.round((i.score||0)*100)}%</td>
            <td>${i.statut}</td>
            <td><a href="#/candidature/${i.id}">Ouvrir</a></td>
          </tr>`).join("") || `<tr><td colspan="4">Aucune.</td></tr>`}
        </tbody>
      </table>
    </div>
  `);
}

async function candidature(id) {
  const data = await api("/api/candidatures");
  const c = data.items.find(x => String(x.id) === String(id));
  if (!c) { layout("<p>Introuvable.</p>"); return; }
  layout(`
    ${data.agent_arrete ? `<div class="banner-stop">Agent arrêté.</div>` : ""}
    <p><a href="#/candidatures">← liste</a></p>
    <h1>${c.titre}</h1>
    <p class="muted">${c.entreprise} · ${c.ville} · score ${Math.round((c.score||0)*100)}%</p>
    <div class="grid grid-2">
      <div class="card">
        <h3>Lettre (à valider)</h3>
        <textarea id="lettre">${c.lettre || ""}</textarea>
        <div class="row" style="margin-top:10px">
          <button class="btn btn-ghost" id="gen">Générer</button>
          <button class="btn btn-primary" id="save">Enregistrer la lettre</button>
          <button class="btn btn-clay" id="send">Marquer envoyée</button>
        </div>
      </div>
      <div class="card">
        <h3>Statut</h3>
        <select id="statut">${["a_envoyer","envoyee","reponse","entretien","refus"].map(s => `<option ${s===c.statut?"selected":""} value="${s}">${s}</option>`).join("")}</select>
        <button class="btn btn-primary" id="stat" style="margin-top:10px">Mettre à jour</button>
        <p class="muted">Passer à « entretien » déclenche l'arrêt de l'agent.</p>
        <h3>Bonus formule Entretien garanti</h3>
        <button class="btn btn-ghost" id="cvad">CV adapté (mots-clés)</button>
        <button class="btn btn-ghost" id="prep">Préparation entretien</button>
        <pre id="bonus" style="white-space:pre-wrap;font-family:Outfit,sans-serif">${c.cv_adapte || ""}\n\n${c.questions_entretien || ""}</pre>
      </div>
    </div>
    <div class="card" style="margin-top:16px">
      <h3>Pourquoi ce score</h3>
      <ul>${(c.explication?.raisons || []).map(r => `<li>${r}</li>`).join("")}</ul>
    </div>
  `);
  const go = async (fn) => { try { await fn(); render(); } catch (e) { alert(e.message); } };
  $("#gen").onclick = () => go(() => api(`/api/candidatures/${id}/lettre`, { method: "POST" }));
  $("#save").onclick = () => go(() => api(`/api/candidatures/${id}`, { method: "PATCH", body: { lettre: $("#lettre").value } }));
  $("#send").onclick = () => go(async () => {
    await api(`/api/candidatures/${id}`, { method: "PATCH", body: { lettre: $("#lettre").value } });
    const r = await api(`/api/candidatures/${id}/envoyer`, { method: "POST" });
    state.flash = r.message;
  });
  $("#stat").onclick = () => go(() => api(`/api/candidatures/${id}`, { method: "PATCH", body: { statut: $("#statut").value } }));
  $("#cvad").onclick = () => go(async () => {
    const r = await api(`/api/candidatures/${id}/cv-adapte`, { method: "POST" });
    state.flash = "CV adapté généré (aucun fait inventé).";
    $("#bonus").textContent = r.texte;
  });
  $("#prep").onclick = () => go(async () => {
    const r = await api(`/api/candidatures/${id}/prep-entretien`, { method: "POST" });
    $("#bonus").textContent = r.texte;
  });
}

async function formules() {
  const d = await api("/api/dashboard");
  layout(`
    <h1>Trois formules</h1>
    <p class="muted">Paiement réel hors périmètre : le changement est immédiat pour la démonstration.</p>
    <div class="grid grid-3">
      ${Object.entries(d.formules).map(([id, f]) => `
        <article class="card">
          <p class="kicker">${f.prix}</p>
          <h3>${f.nom}</h3>
          <p>${f.resume}</p>
          <ul>
            <li>${f.max_matchs} offres affichées</li>
            <li>${f.max_lettres} lettres · ${f.max_envois} envois</li>
            <li>Sources : ${f.sources.join(", ")}</li>
            <li>CV adapté : ${f.cv_adapte ? "oui" : "non"}</li>
            <li>Préparation entretien : ${f.prep_entretien ? "oui" : "non"}</li>
          </ul>
          <button class="btn ${d.user.formule===id?"btn-ghost":"btn-primary"}" data-f="${id}" ${d.user.formule===id?"disabled":""}>
            ${d.user.formule===id?"Formule actuelle":"Choisir"}
          </button>
        </article>`).join("")}
    </div>
  `);
  app.querySelectorAll("button[data-f]").forEach(b => {
    b.onclick = async () => {
      await api("/api/formule", { method: "PUT", body: { formule: b.dataset.f } });
      render();
    };
  });
}

async function journal() {
  const j = await api("/api/journal");
  layout(`
    <h1>Journal d'activité</h1>
    <div class="card"><table>
      <thead><tr><th>Date</th><th>Action</th><th>Détails</th></tr></thead>
      <tbody>
        ${j.items.map(i => `<tr><td>${i.date}</td><td>${i.action}</td><td class="muted">${i.details}</td></tr>`).join("")}
      </tbody>
    </table></div>
  `);
}

async function render() {
  const r = route();
  try {
    if (r === "/" ) return landing();
    if (r === "/connexion") return formAuth("connexion");
    if (r === "/inscription") return formAuth("inscription");
    if (!localStorage.getItem(TOKEN_KEY) && r !== "/") {
      location.hash = "#/connexion";
      return formAuth("connexion");
    }
    if (r === "/dashboard") return await dashboard();
    if (r === "/profil") return await profil();
    if (r === "/offres") return await offres();
    if (r === "/candidatures") return await candidatures();
    if (r.startsWith("/candidature/")) return await candidature(r.split("/")[2]);
    if (r === "/formules") return await formules();
    if (r === "/journal") return await journal();
    landing();
  } catch (err) {
    if (String(err.message).includes("401") || /expir/i.test(err.message) || /Authentification/i.test(err.message)) {
      localStorage.removeItem(TOKEN_KEY);
      return formAuth("connexion");
    }
    layout(`<div class="flash err">${err.message}</div>`);
  }
}

window.addEventListener("hashchange", render);
render();
