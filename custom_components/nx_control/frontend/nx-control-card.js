/*
 * NX Control card for Home Assistant
 * Shows every profile of your Nintendo Switch (time played, time left, current game)
 * and lets you give extra time, block a profile, lock the console and answer time requests.
 *
 * Loaded automatically by the NX Control integration. Everything can be set from the
 * visual editor; in YAML:
 *   type: custom:nx-control-card
 *   title: Nintendo Switch       # empty: console name
 *   show_header: true
 *   show_lock: true              # "Lock console" button
 *   console_id: a1b2c3d4         # only with several consoles
 *   profiles: [Lucas, Daniel]    # which profiles and in which order (names or ids); empty: all
 *   names: { Lucas: "Lucas 🦖" } # display name per profile (key: name or id)
 *   show_all: false              # also show users without rules ("Not managed")
 *   layout: full                 # full | compact (one line per player)
 *   time_display: both           # both | remaining | used
 *   show_avatar: true
 *   show_mode: true
 *   show_status: true
 *   show_progress: true
 *   show_today_games: true
 *   max_games: 6
 *   week_report: collapsed       # collapsed | expanded | hidden
 *   show_grant: true
 *   grant_minutes: [15, 30, 60]
 *   show_block: true
 *   show_requests: true
 */

// Must match "version" in manifest.json (checked by the build).
const CARD_VERSION = "0.2.5";

const STRINGS = {
  en: {
    title: "NX Control",
    limitLater: "today's limit when the console turns on",
    updated: "NX Control {v} is installed: reload to use it",
    reload: "Reload",
    lock: "Lock console",
    locked: "Console locked",
    unlock: "Unlock",
    noProfiles: "No profiles found. Set them up in NX Control on the console.",
    played: "Played today",
    left: "left",
    unlimited: "No limit today",
    noPlay: "No play today",
    block: "Block today",
    unblock: "Unblock",
    requests: "Time requests",
    asks: "asks for",
    approve: "Approve",
    deny: "Deny",
    offline: "Console off",
    lastSeen: "last data",
    today: "Today",
    week: "Last 7 days",
    showWeek: "Last 7 days ▾",
    hideWeek: "Hide ▴",
    nothingToday: "No games today",
    nothingWeek: "No games in the last 7 days",
    days: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    gameLeft: "left in this game",
    modes: { supervised: "Supervised", self: "Self-managed", analytics: "Analytics only", none: "Not managed" },
    states: {
      idle: "Not playing", playing: "Playing", warning: "Almost out of time", grace: "Saving the game",
      exhausted: "Time is up", outside_window: "Outside allowed hours", blocked: "Blocked", offline: "Console off",
    },
  },
  es: {
    title: "NX Control",
    limitLater: "límite de hoy al encender la consola",
    updated: "NX Control {v} está instalado: recarga para usarlo",
    reload: "Recargar",
    lock: "Bloquear consola",
    locked: "Consola bloqueada",
    unlock: "Desbloquear",
    noProfiles: "No hay perfiles. Configúralos en NX Control, en la consola.",
    played: "Jugado hoy",
    left: "restantes",
    unlimited: "Sin límite hoy",
    noPlay: "Hoy no se juega",
    block: "Bloquear hoy",
    unblock: "Desbloquear",
    requests: "Solicitudes de tiempo",
    asks: "pide",
    approve: "Aprobar",
    deny: "Denegar",
    offline: "Consola apagada",
    lastSeen: "últimos datos",
    today: "Hoy",
    week: "Últimos 7 días",
    showWeek: "Últimos 7 días ▾",
    hideWeek: "Ocultar ▴",
    nothingToday: "Hoy no ha jugado",
    nothingWeek: "Sin juegos en los últimos 7 días",
    days: ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"],
    gameLeft: "restantes en este juego",
    modes: { supervised: "Supervisado", self: "Autogestionado", analytics: "Solo analítica", none: "Sin gestionar" },
    states: {
      idle: "No está jugando", playing: "Jugando", warning: "Queda poco tiempo", grace: "Guardando la partida",
      exhausted: "Tiempo agotado", outside_window: "Fuera de horario", blocked: "Bloqueado", offline: "Consola apagada",
    },
  },
  fr: {
    title: "NX Control",
    limitLater: "limite du jour à l\'allumage de la console",
    updated: "NX Control {v} est installé : rechargez pour l\'utiliser",
    reload: "Recharger",
    lock: "Verrouiller la console",
    locked: "Console verrouillée",
    unlock: "Déverrouiller",
    noProfiles: "Aucun profil. Configurez-les dans NX Control, sur la console.",
    played: "Joué aujourd'hui",
    left: "restantes",
    unlimited: "Sans limite aujourd'hui",
    noPlay: "Pas de jeu aujourd'hui",
    block: "Bloquer aujourd'hui",
    unblock: "Débloquer",
    requests: "Demandes de temps",
    asks: "demande",
    approve: "Accepter",
    deny: "Refuser",
    offline: "Console éteinte",
    lastSeen: "dernières données",
    today: "Aujourd'hui",
    week: "7 derniers jours",
    showWeek: "7 derniers jours ▾",
    hideWeek: "Masquer ▴",
    nothingToday: "Aucun jeu aujourd'hui",
    nothingWeek: "Aucun jeu ces 7 derniers jours",
    days: ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"],
    gameLeft: "restantes dans ce jeu",
    modes: { supervised: "Supervisé", self: "Autogéré", analytics: "Statistiques uniquement", none: "Non géré" },
    states: {
      idle: "Ne joue pas", playing: "En jeu", warning: "Bientôt plus de temps", grace: "Sauvegarde de la partie",
      exhausted: "Temps écoulé", outside_window: "Hors horaires", blocked: "Bloqué", offline: "Console éteinte",
    },
  },
  de: {
    title: "NX Control",
    limitLater: "Tageslimit beim Einschalten der Konsole",
    updated: "NX Control {v} ist installiert: neu laden, um es zu nutzen",
    reload: "Neu laden",
    lock: "Konsole sperren",
    locked: "Konsole gesperrt",
    unlock: "Entsperren",
    noProfiles: "Keine Profile gefunden. Richte sie in NX Control auf der Konsole ein.",
    played: "Heute gespielt",
    left: "übrig",
    unlimited: "Heute ohne Limit",
    noPlay: "Heute kein Spielen",
    block: "Heute sperren",
    unblock: "Entsperren",
    requests: "Zeitanfragen",
    asks: "bittet um",
    approve: "Genehmigen",
    deny: "Ablehnen",
    offline: "Konsole aus",
    lastSeen: "letzte Daten",
    today: "Heute",
    week: "Letzte 7 Tage",
    showWeek: "Letzte 7 Tage ▾",
    hideWeek: "Ausblenden ▴",
    nothingToday: "Heute keine Spiele",
    nothingWeek: "Keine Spiele in den letzten 7 Tagen",
    days: ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"],
    gameLeft: "übrig in diesem Spiel",
    modes: { supervised: "Beaufsichtigt", self: "Selbstverwaltet", analytics: "Nur Statistik", none: "Nicht verwaltet" },
    states: {
      idle: "Spielt nicht", playing: "Spielt", warning: "Zeit fast abgelaufen", grace: "Spiel wird gespeichert",
      exhausted: "Zeit abgelaufen", outside_window: "Außerhalb der Zeiten", blocked: "Gesperrt", offline: "Konsole aus",
    },
  },
  it: {
    title: "NX Control",
    limitLater: "limite di oggi all\'accensione della console",
    updated: "NX Control {v} è installato: ricarica per usarlo",
    reload: "Ricarica",
    lock: "Blocca la console",
    locked: "Console bloccata",
    unlock: "Sblocca",
    noProfiles: "Nessun profilo. Configurali in NX Control, sulla console.",
    played: "Giocato oggi",
    left: "rimanenti",
    unlimited: "Nessun limite oggi",
    noPlay: "Oggi niente gioco",
    block: "Blocca oggi",
    unblock: "Sblocca",
    requests: "Richieste di tempo",
    asks: "chiede",
    approve: "Approva",
    deny: "Rifiuta",
    offline: "Console spenta",
    lastSeen: "ultimi dati",
    today: "Oggi",
    week: "Ultimi 7 giorni",
    showWeek: "Ultimi 7 giorni ▾",
    hideWeek: "Nascondi ▴",
    nothingToday: "Nessun gioco oggi",
    nothingWeek: "Nessun gioco negli ultimi 7 giorni",
    days: ["Dom", "Lun", "Mar", "Mer", "Gio", "Ven", "Sab"],
    gameLeft: "rimanenti in questo gioco",
    modes: { supervised: "Supervisionato", self: "Autogestito", analytics: "Solo statistiche", none: "Non gestito" },
    states: {
      idle: "Non sta giocando", playing: "In gioco", warning: "Tempo quasi finito", grace: "Salvataggio della partita",
      exhausted: "Tempo scaduto", outside_window: "Fuori orario", blocked: "Bloccato", offline: "Console spenta",
    },
  },
  pt: {
    title: "NX Control",
    limitLater: "limite de hoje ao ligar a consola",
    updated: "O NX Control {v} está instalado: recarregue para o usar",
    reload: "Recarregar",
    lock: "Bloquear consola",
    locked: "Consola bloqueada",
    unlock: "Desbloquear",
    noProfiles: "Não há perfis. Configure-os no NX Control, na consola.",
    played: "Jogado hoje",
    left: "restantes",
    unlimited: "Sem limite hoje",
    noPlay: "Hoje não se joga",
    block: "Bloquear hoje",
    unblock: "Desbloquear",
    requests: "Pedidos de tempo",
    asks: "pede",
    approve: "Aprovar",
    deny: "Recusar",
    offline: "Consola desligada",
    lastSeen: "últimos dados",
    today: "Hoje",
    week: "Últimos 7 dias",
    showWeek: "Últimos 7 dias ▾",
    hideWeek: "Ocultar ▴",
    nothingToday: "Hoje não jogou",
    nothingWeek: "Sem jogos nos últimos 7 dias",
    days: ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"],
    gameLeft: "restantes neste jogo",
    modes: { supervised: "Supervisionado", self: "Autogerido", analytics: "Só estatísticas", none: "Não gerido" },
    states: {
      idle: "Não está a jogar", playing: "A jogar", warning: "Resta pouco tempo", grace: "A guardar o jogo",
      exhausted: "O tempo acabou", outside_window: "Fora do horário", blocked: "Bloqueado", offline: "Consola desligada",
    },
  },
};

const fmtDuration = (secs) => {
  if (secs === null || secs === undefined || secs < 0) return "–";
  const m = Math.ceil(secs / 60);
  if (m >= 60) return `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")} min`;
  return `${m} min`;
};

const colorFor = (name) => {
  let h = 0;
  for (const c of name || "?") h = (h * 31 + c.charCodeAt(0)) % 360;
  return `hsl(${h}, 55%, 45%)`;
};

const ago = (iso, lang) => {
  if (!iso) return "";
  const secs = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  try {
    const rtf = new Intl.RelativeTimeFormat(lang, { numeric: "auto" });
    if (secs < 3600) return rtf.format(-Math.round(secs / 60), "minute");
    if (secs < 86400) return rtf.format(-Math.round(secs / 3600), "hour");
    return rtf.format(-Math.round(secs / 86400), "day");
  } catch (e) {
    return new Date(iso).toLocaleString();
  }
};

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const DEFAULTS = {
  title: "",
  show_header: true,
  show_lock: true,
  show_all: false,
  layout: "full",
  time_display: "both",
  show_avatar: true,
  show_mode: true,
  show_status: true,
  show_progress: true,
  show_today_games: true,
  max_games: 6,
  week_report: "collapsed",
  show_grant: true,
  grant_minutes: [15, 30, 60],
  show_block: true,
  show_requests: true,
};

const grantLabel = (m) => (m >= 60 && m % 60 === 0 ? `+${m / 60} h` : `+${m} min`);

class NXControlCard extends HTMLElement {
  setConfig(config) {
    this._config = { ...DEFAULTS, ...(config || {}) };
    if (!Array.isArray(this._config.grant_minutes)) this._config.grant_minutes = DEFAULTS.grant_minutes;
    this._config.grant_minutes = this._config.grant_minutes.map(Number).filter((m) => m > 0).sort((a, b) => a - b);
    this._signature = null;
    this._expanded = this._expanded || new Set();
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._checkVersion();
    this._render();
  }

  connectedCallback() {
    // The Home Assistant app keeps the page open for days: check again when it comes back
    this._onVisible = this._onVisible || (() => { if (!document.hidden) this._checkVersion(true); });
    document.addEventListener("visibilitychange", this._onVisible);
  }

  disconnectedCallback() {
    if (this._onVisible) document.removeEventListener("visibilitychange", this._onVisible);
  }

  // Is this page running an older copy of the card than the installed integration?
  _checkVersion(force = false) {
    const now = Date.now();
    if (!this._hass || (!force && this._versionCheckedAt && now - this._versionCheckedAt < 10 * 60 * 1000)) return;
    this._versionCheckedAt = now;
    this._hass.callApi("GET", "nx_control/version").then((r) => {
      const update = r && r.version && r.version !== CARD_VERSION ? r.version : null;
      if (update !== (this._update || null)) {
        this._update = update;
        this._signature = null;
        this._render();
      }
    }).catch(() => {});
  }

  getCardSize() {
    return 2 + 2 * (this._profiles?.length || 1);
  }

  static getStubConfig() {
    return {};
  }

  static getConfigElement() {
    return document.createElement("nx-control-card-editor");
  }

  _displayName(a) {
    const names = this._config.names || {};
    const id = a.nx_control_profile_id;
    const real = a.profile_name || String(id || "").slice(0, 8);
    return names[id] || names[real] || real;
  }

  get _t() {
    const lang = (this._hass?.locale?.language || this._hass?.language || "en").slice(0, 2);
    return STRINGS[lang] || STRINGS.en;
  }

  _collect() {
    const states = Object.values(this._hass.states);
    const cid = this._config.console_id;
    const mine = (s) => !cid || s.attributes.nx_control_console_id === cid;

    let profiles = states.filter((s) => s.attributes.nx_control_profile_id && mine(s));
    if (!this._config.show_all) profiles = profiles.filter((s) => s.attributes.mode && s.attributes.mode !== "none");
    if (Array.isArray(this._config.profiles) && this._config.profiles.length) {
      const wanted = this._config.profiles.map((p) => String(p).toLowerCase());
      profiles = profiles
        .filter((s) =>
          wanted.includes(String(s.attributes.profile_name || "").toLowerCase()) ||
          wanted.includes(String(s.attributes.nx_control_profile_id).toLowerCase()))
        .sort((a, b) =>
          wanted.indexOf(String(a.attributes.profile_name || "").toLowerCase()) -
          wanted.indexOf(String(b.attributes.profile_name || "").toLowerCase()));
    } else {
      profiles.sort((a, b) => String(a.attributes.profile_name).localeCompare(String(b.attributes.profile_name)));
    }

    const pending = states.find((s) => Array.isArray(s.attributes.requests) && s.attributes.nx_control_console_id && mine(s));
    const lock = states.find((s) => s.entity_id.startsWith("switch.") && s.attributes.nx_control_console_id && mine(s));
    return { profiles, pending, lock };
  }

  _call(service, data, button) {
    if (button) button.disabled = true;
    const cid = this._config.console_id;
    this._hass
      .callService("nx_control", service, cid ? { ...data, console_id: cid } : data)
      .catch((err) => {
        const msg = err?.message || String(err);
        this.dispatchEvent(new CustomEvent("hass-notification", { detail: { message: msg }, bubbles: true, composed: true }));
      })
      .finally(() => {
        if (button) button.disabled = false;
      });
  }

  _gamesHtml(games, iconBase, emptyText) {
    if (!games || !games.length) return `<div class="sub">${emptyText}</div>`;
    const max = Math.max(...games.map((g) => g.seconds), 1);
    return `<div class="games">${games.map((g) => `
      <div class="game">
        ${iconBase ? `<img src="${esc(iconBase)}/${esc(g.program_id)}" alt="" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'noimg'}))">` : `<div class="noimg"></div>`}
        <div class="gname">${esc(g.title)}<div class="gbar" style="width:${Math.round((g.seconds / max) * 100)}%"></div></div>
        <div class="gtime">${fmtDuration(g.seconds)}</div>
      </div>`).join("")}</div>`;
  }

  _reportHtml(p, t, lang) {
    const a = p.attributes;
    const id = a.nx_control_profile_id;
    const c = this._config;
    const week = c.week_report;
    const open = week === "expanded" || (week !== "hidden" && this._expanded.has(id));
    const limit = Math.max(1, Number(c.max_games) || 6);
    let html = c.show_today_games
      ? `<div class="label">${t.today}</div>${this._gamesHtml((a.games_today || []).slice(0, limit), a.icon_base, t.nothingToday)}` : "";
    if (open) {
      const daily = a.daily || [];
      const max = Math.max(...daily.map((d) => d.seconds), 60);
      html += `
        <div class="label">${t.week} · ${fmtDuration(a.week_seconds || 0)}</div>
        <div class="chart">${daily.map((d, i) => {
          const day = new Date(d.date + "T12:00:00").getDay();
          return `<div class="col ${i === daily.length - 1 ? "today" : ""}" title="${esc(d.date)} · ${fmtDuration(d.seconds)}">
            <div class="b" style="height:${Math.round((d.seconds / max) * 100)}%"></div>
            <div class="d">${t.days[day]}</div></div>`;
        }).join("")}</div>
        ${this._gamesHtml((a.games_week || []).slice(0, limit), a.icon_base, t.nothingWeek)}`;
    }
    if (week === "collapsed") html += `<button class="link" data-toggle="${esc(id)}">${open ? t.hideWeek : t.showWeek}</button>`;
    return html;
  }

  _render() {
    if (!this._hass || !this._config || !this.shadowRoot) return;
    const { profiles, pending, lock } = this._collect();
    this._profiles = profiles;

    // Only re-render when something relevant changed
    const signature = JSON.stringify([
      profiles.map((p) => [p.state, p.attributes]),
      pending ? [pending.state, pending.attributes.requests] : null,
      [...(this._answered || [])],
      lock ? lock.state : null,
      this._hass.locale?.language,
      [...this._expanded],
      this._config,
      this._update,
    ]);
    if (signature === this._signature) return;
    this._signature = signature;

    const t = this._t;
    const consoleName = profiles[0]?.attributes.nx_control_console_name || pending?.attributes.nx_control_console_name || "";
    const title = this._config.title || consoleName || t.title;
    const lang = (this._hass?.locale?.language || this._hass?.language || "en").slice(0, 2);
    const offline = profiles.length > 0 && profiles.every((p) => p.state === "offline" || p.state === "unavailable" || p.attributes.online === false);
    const lastSeen = profiles.find((p) => p.attributes.last_seen)?.attributes.last_seen || pending?.attributes.last_seen;
    const locked = lock?.state === "on";
    const names = Object.fromEntries(profiles.map((p) => [p.attributes.nx_control_profile_id, this._displayName(p.attributes)]));
    // Requests just answered here disappear at once, without waiting for the next update
    this._answered = this._answered || new Set();
    const pendingIds = new Set((pending?.attributes.requests || []).map((r) => String(r.id)));
    for (const id of [...this._answered]) if (!pendingIds.has(id)) this._answered.delete(id);
    const requests = this._config.show_requests
      ? (pending?.attributes.requests || []).filter((r) => r.status === "pending" && !this._answered.has(String(r.id))) : [];

    const profileHtml = profiles.map((p) => {
      const a = p.attributes;
      const c = this._config;
      const name = this._displayName(a);
      const limited = a.limit_today !== null && a.limit_today !== undefined && a.limit_today >= 0;
      const used = a.used_today || 0;
      const pct = limited && a.limit_today > 0 ? Math.min(100, Math.round((used / a.limit_today) * 100)) : 0;
      const state = p.state in t.states ? p.state : "idle";
      const playing = ["playing", "warning", "grace"].includes(state);
      const alert = ["exhausted", "outside_window", "blocked", "grace"].includes(state);
      const canGrant = a.mode === "supervised" || a.mode === "self";
      const pblocked = a.profile_blocked ?? a.blocked;
      const status = playing && a.game ? `🎮 ${esc(a.game)}` : esc(t.states[state]);
      const leftText = `${fmtDuration(a.remaining_today)} ${t.left}`;
      const usedText = `${t.played} ${fmtDuration(used)}`;
      // Console off since yesterday with an older console version: today's limit is not known yet
      const unknownLimit = a.limit_today === null && ["supervised", "self"].includes(a.mode);
      const outside = offline && a.in_allowed_window === false && (limited || unknownLimit)
        ? ` · ${esc(t.states.outside_window)}` : "";
      const timeLine = unknownLimit
        ? `${usedText} · ${t.limitLater}`
        : limited
        ? a.limit_today === 0
          ? t.noPlay
          : c.time_display === "remaining" ? leftText : c.time_display === "used" ? usedText : `${leftText} · ${usedText}`
        : c.time_display === "remaining" ? t.unlimited : `${usedText} · ${t.unlimited}`;
      const timeText = timeLine + outside;
      const avatarHtml = c.show_avatar ? `
            <div class="avatar" style="background:${colorFor(name)}">
              <span>${esc(name.slice(0, 1).toUpperCase())}</span>
              ${a.avatar ? `<img src="${esc(a.avatar)}" alt="" onerror="this.remove()">` : ""}
            </div>` : "";
      const actionsHtml = canGrant && (c.show_grant || c.show_block) ? `
          <div class="actions">
            ${c.show_grant ? c.grant_minutes.map((m) => `<button class="grant" ${offline ? "disabled" : ""} data-profile="${esc(a.nx_control_profile_id)}" data-minutes="${m}">${grantLabel(m)}</button>`).join("") : ""}
            ${c.show_block ? `<button class="${pblocked ? "unblock" : "block danger"}" ${offline ? "disabled" : ""} data-profile="${esc(a.nx_control_profile_id)}">
              ${pblocked ? `🔓 ${t.unblock}` : `⛔ ${t.block}`}
            </button>` : ""}
          </div>` : "";

      if (c.layout === "compact") {
        const short = limited ? (a.limit_today === 0 ? t.noPlay : c.time_display === "used" ? fmtDuration(used) : fmtDuration(a.remaining_today)) : fmtDuration(used);
        return `
        <div class="profile compact ${alert && !offline ? "alert" : ""} ${playing ? "playing" : ""}">
          <div class="row">
            ${avatarHtml}
            <div class="info">
              <div class="name">${esc(name)}</div>
              ${c.show_status ? `<div class="status ${alert ? "warn" : ""}">${status}</div>` : ""}
            </div>
            <div class="big">${short}</div>
          </div>
          ${limited && c.show_progress ? `<div class="bar thin"><div class="fill ${pct >= 90 ? "red" : pct >= 70 ? "amber" : ""}" style="width:${pct}%"></div></div>` : ""}
          ${actionsHtml}
        </div>`;
      }
      const gameLine = playing && a.game_remaining >= 0 ? `<div class="sub">${fmtDuration(a.game_remaining)} ${t.gameLeft}</div>` : "";

      return `
        <div class="profile ${alert && !offline ? "alert" : ""} ${playing ? "playing" : ""}">
          <div class="row">
            ${avatarHtml}
            <div class="info">
              <div class="name">${esc(name)} ${c.show_mode ? `<span class="chip">${esc(t.modes[a.mode] || a.mode || "")}</span>` : ""}</div>
              ${c.show_status ? `<div class="status ${alert ? "warn" : ""}">${status}</div>` : ""}
            </div>
          </div>
          ${limited && c.show_progress ? `<div class="bar"><div class="fill ${pct >= 90 ? "red" : pct >= 70 ? "amber" : ""}" style="width:${pct}%"></div></div>` : ""}
          <div class="sub">${timeText}</div>
          ${gameLine}
          ${this._reportHtml(p, t, lang)}
          ${actionsHtml}
        </div>`;
    }).join("");

    const requestHtml = requests.length ? `
      <div class="section">${t.requests}</div>
      ${requests.map((r) => `
        <div class="request">
          <div class="info">
            <b>${esc(names[r.profile_id] || r.profile_id.slice(0, 8))}</b> ${t.asks} ${Math.round(r.seconds / 60)} min
            ${r.message ? `<div class="sub">“${esc(r.message)}”</div>` : ""}
          </div>
          <button class="deny secondary" data-request="${esc(r.id)}">${t.deny}</button>
          <button class="approve" data-request="${esc(r.id)}">${t.approve}</button>
        </div>`).join("")}` : "";

    this.shadowRoot.innerHTML = `
      <style>
        ha-card { padding: 16px; }
        .header { display:flex; align-items:center; gap:10px; margin-bottom:12px; }
        .logo { width:36px; height:36px; flex:none; }
        .title { font-size:1.2em; font-weight:600; flex:1; }
        .profile { border-radius:12px; padding:12px; margin-bottom:10px; background: var(--secondary-background-color); }
        .profile.alert { box-shadow: inset 4px 0 0 #e60012; }
        .profile.playing { box-shadow: inset 4px 0 0 var(--success-color, #43a047); }
        .row { display:flex; align-items:center; gap:12px; }
        .avatar { position:relative; width:44px; height:44px; border-radius:50%; color:#fff; font-weight:700; display:flex; align-items:center; justify-content:center; flex:none; font-size:1.1em; overflow:hidden; }
        .avatar img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }
        .games { margin-top:10px; display:flex; flex-direction:column; gap:6px; }
        .game { display:flex; align-items:center; gap:10px; }
        .game img, .game .noimg { width:32px; height:32px; border-radius:6px; flex:none; object-fit:cover; background: var(--divider-color); }
        .game .gname { flex:1; min-width:0; font-size:.9em; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .game .gtime { font-size:.85em; color: var(--secondary-text-color); white-space:nowrap; }
        .gbar { height:4px; border-radius:2px; background: var(--primary-color); opacity:.6; margin-top:2px; }
        .label { font-size:.8em; font-weight:600; text-transform:uppercase; letter-spacing:.04em; color: var(--secondary-text-color); margin-top:12px; }
        .chart { display:flex; align-items:flex-end; gap:6px; height:64px; margin-top:8px; }
        .col { flex:1; display:flex; flex-direction:column; align-items:center; gap:4px; height:100%; justify-content:flex-end; }
        .col .b { width:100%; max-width:26px; border-radius:4px 4px 0 0; background: var(--primary-color); min-height:2px; }
        .col.today .b { background:#e60012; }
        .col .d { font-size:.7em; color: var(--secondary-text-color); }
        button.link { background:none; color: var(--primary-color); padding:4px 0; box-shadow:none; }
        .info { flex:1; min-width:0; }
        .profile.compact { padding:8px 12px; margin-bottom:6px; }
        .profile.compact .avatar { width:34px; height:34px; font-size:.95em; }
        .big { font-weight:700; font-size:1.05em; white-space:nowrap; }
        .bar.thin { height:4px; margin:8px 0 0; }
        .header.bare { justify-content:flex-end; }
        .name { font-weight:600; }
        .chip { font-size:.75em; font-weight:500; padding:2px 8px; border-radius:10px; background: var(--primary-background-color); color: var(--secondary-text-color); margin-left:4px; }
        .status { color: var(--secondary-text-color); font-size:.9em; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .status.warn { color:#e60012; font-weight:600; }
        .bar { height:8px; border-radius:4px; background: var(--divider-color); margin:10px 0 6px; overflow:hidden; }
        .fill { height:100%; background: var(--primary-color); border-radius:4px; transition: width .4s; }
        .fill.amber { background:#ff9800; }
        .fill.red { background:#e60012; }
        .sub { font-size:.85em; color: var(--secondary-text-color); margin-top:4px; }
        .actions { display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; }
        button { border:none; border-radius:16px; padding:6px 12px; font: inherit; font-size:.85em; font-weight:600; cursor:pointer;
                 background: var(--primary-color); color: var(--text-primary-color, #fff); }
        button.secondary { background: transparent; color: var(--primary-text-color); box-shadow: inset 0 0 0 1px var(--divider-color); }
        button.lock { background: transparent; color: var(--primary-text-color); box-shadow: inset 0 0 0 1px var(--divider-color); }
        button.lock.on { background:#e60012; color:#fff; box-shadow:none; }
        button.approve { background: var(--success-color, #43a047); }
        button.danger { background:#e60012; color:#fff; margin-left:auto; }
        button.unblock { background: transparent; color: var(--primary-text-color); box-shadow: inset 0 0 0 1px #e60012; margin-left:auto; }
        button:disabled { opacity:.5; cursor: default; }
        .section { font-weight:600; margin:14px 0 8px; }
        .request { display:flex; align-items:center; gap:8px; padding:10px 12px; border-radius:12px; background: var(--secondary-background-color); margin-bottom:8px; }
        .empty { color: var(--secondary-text-color); padding: 8px 0; }
        .offline { display:flex; align-items:center; gap:8px; color: var(--secondary-text-color); padding: 4px 0 12px; font-size:.9em; }
        .offline .dot { width:8px; height:8px; border-radius:50%; background: var(--disabled-text-color, #888); }
        ha-card.is-offline .profile { opacity:.75; }
        .update { display:flex; align-items:center; gap:8px; padding:8px 12px; margin-bottom:12px; border-radius:12px;
                  background: rgba(230,0,18,.12); font-size:.9em; }
        .update span { flex:1; }
      </style>
      <ha-card class="${offline ? "is-offline" : ""}">
        ${this._update ? `<div class="update"><span>${t.updated.replace("{v}", esc(this._update))}</span><button class="reload">${t.reload}</button></div>` : ""}
        ${this._config.show_header || (lock && this._config.show_lock) ? `<div class="header ${this._config.show_header ? "" : "bare"}">
          ${this._config.show_header ? `<img class="logo" alt="" src="data:image/png;base64,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">` : ""}
          <div class="title">${this._config.show_header ? esc(title) : ""}</div>
          ${lock && this._config.show_lock ? `<button class="lock ${locked ? "on" : ""}" ${offline ? "disabled" : ""} data-lock="${locked ? "off" : "on"}">${locked ? `🔒 ${t.unlock}` : t.lock}</button>` : ""}
        </div>` : ""}
        ${offline ? `<div class="offline"><span class="dot"></span>${t.offline}${lastSeen ? ` · ${t.lastSeen} ${esc(ago(lastSeen, lang))}` : ""}</div>` : ""}
        ${profiles.length ? profileHtml : `<div class="empty">${t.noProfiles}</div>`}
        ${requestHtml}
      </ha-card>`;

    this.shadowRoot.querySelectorAll("button.grant").forEach((b) =>
      b.addEventListener("click", () => this._call("grant_time", { profile_id: b.dataset.profile, minutes: Number(b.dataset.minutes) }, b)));
    this.shadowRoot.querySelectorAll("button.block").forEach((b) =>
      b.addEventListener("click", () => this._call("block_profile", { profile_id: b.dataset.profile }, b)));
    this.shadowRoot.querySelectorAll("button.unblock").forEach((b) =>
      b.addEventListener("click", () => this._call("unblock_profile", { profile_id: b.dataset.profile }, b)));
    const answer = (service, b) => {
      if (this._answered.has(b.dataset.request)) return;      // a second tap on the same request
      this._answered.add(b.dataset.request);
      this._signature = null;
      this._render();
      this._call(service, { request_id: b.dataset.request }, null);
    };
    this.shadowRoot.querySelectorAll("button.approve").forEach((b) => b.addEventListener("click", () => answer("approve_request", b)));
    this.shadowRoot.querySelectorAll("button.deny").forEach((b) => b.addEventListener("click", () => answer("deny_request", b)));
    this.shadowRoot.querySelectorAll("button.link").forEach((b) =>
      b.addEventListener("click", () => {
        const id = b.dataset.toggle;
        if (this._expanded.has(id)) this._expanded.delete(id);
        else this._expanded.add(id);
        this._signature = null;
        this._render();
      }));
    const reloadBtn = this.shadowRoot.querySelector("button.reload");
    if (reloadBtn) reloadBtn.addEventListener("click", () => window.location.reload());
    const lockBtn = this.shadowRoot.querySelector("button.lock");
    if (lockBtn && lock) {
      lockBtn.addEventListener("click", () => {
        lockBtn.disabled = true;
        this._hass
          .callService("switch", lockBtn.dataset.lock === "on" ? "turn_on" : "turn_off", { entity_id: lock.entity_id })
          .finally(() => (lockBtn.disabled = false));
      });
    }
  }
}

const EDITOR_STRINGS = {
  en: {
    general: "General", title: "Title (empty: console name)", show_header: "Show header", show_lock: "\"Lock console\" button",
    show_all: "Also show users without rules",
    players: "Players", show_player: "Show", display_name: "Name on the card",
    look: "Layout", layout: "Layout", full: "Full", compact: "Compact (one line per player)",
    time_display: "Time shown", both: "Time left and played", remaining: "Time left", used: "Time played",
    show_avatar: "Avatar", show_mode: "Mode chip", show_status: "Status / current game", show_progress: "Progress bar",
    reports: "Reports", show_today_games: "Today's games", max_games: "Games listed", week_report: "Last 7 days",
    collapsed: "Collapsed (tap to open)", expanded: "Always open", hidden: "Hidden",
    actions: "Actions", show_grant: "Extra time buttons", grant_minutes: "Extra time options (minutes)",
    show_block: "\"Block today\" button", show_requests: "Time requests",
  },
  es: {
    general: "General", title: "Título (vacío: nombre de la consola)", show_header: "Mostrar cabecera", show_lock: "Botón \"Bloquear consola\"",
    show_all: "Mostrar también usuarios sin reglas",
    players: "Jugadores", show_player: "Mostrar", display_name: "Nombre en la tarjeta",
    look: "Diseño", layout: "Diseño", full: "Completo", compact: "Compacto (una línea por jugador)",
    time_display: "Tiempo a mostrar", both: "Restante y jugado", remaining: "Tiempo restante", used: "Tiempo jugado",
    show_avatar: "Avatar", show_mode: "Etiqueta del modo", show_status: "Estado / juego actual", show_progress: "Barra de progreso",
    reports: "Informes", show_today_games: "Juegos de hoy", max_games: "Juegos a listar", week_report: "Últimos 7 días",
    collapsed: "Plegado (pulsar para abrir)", expanded: "Siempre abierto", hidden: "Oculto",
    actions: "Acciones", show_grant: "Botones de tiempo extra", grant_minutes: "Opciones de tiempo extra (minutos)",
    show_block: "Botón \"Bloquear hoy\"", show_requests: "Solicitudes de tiempo",
  },
  fr: {
    general: "Général", title: "Titre (vide : nom de la console)", show_header: "Afficher l'en-tête", show_lock: "Bouton « Verrouiller la console »",
    show_all: "Afficher aussi les utilisateurs sans règles",
    players: "Joueurs", show_player: "Afficher", display_name: "Nom sur la carte",
    look: "Disposition", layout: "Disposition", full: "Complète", compact: "Compacte (une ligne par joueur)",
    time_display: "Temps affiché", both: "Restant et joué", remaining: "Temps restant", used: "Temps joué",
    show_avatar: "Avatar", show_mode: "Étiquette du mode", show_status: "État / jeu en cours", show_progress: "Barre de progression",
    reports: "Rapports", show_today_games: "Jeux du jour", max_games: "Jeux affichés", week_report: "7 derniers jours",
    collapsed: "Replié (toucher pour ouvrir)", expanded: "Toujours ouvert", hidden: "Masqué",
    actions: "Actions", show_grant: "Boutons de temps en plus", grant_minutes: "Options de temps en plus (minutes)",
    show_block: "Bouton « Bloquer aujourd'hui »", show_requests: "Demandes de temps",
  },
  de: {
    general: "Allgemein", title: "Titel (leer: Name der Konsole)", show_header: "Kopfzeile anzeigen", show_lock: "Schaltfläche „Konsole sperren“",
    show_all: "Auch Benutzer ohne Regeln anzeigen",
    players: "Spieler", show_player: "Anzeigen", display_name: "Name auf der Karte",
    look: "Layout", layout: "Layout", full: "Vollständig", compact: "Kompakt (eine Zeile pro Spieler)",
    time_display: "Angezeigte Zeit", both: "Verbleibend und gespielt", remaining: "Verbleibende Zeit", used: "Gespielte Zeit",
    show_avatar: "Avatar", show_mode: "Modus-Chip", show_status: "Status / aktuelles Spiel", show_progress: "Fortschrittsbalken",
    reports: "Berichte", show_today_games: "Heutige Spiele", max_games: "Angezeigte Spiele", week_report: "Letzte 7 Tage",
    collapsed: "Eingeklappt (zum Öffnen tippen)", expanded: "Immer offen", hidden: "Ausgeblendet",
    actions: "Aktionen", show_grant: "Schaltflächen für Extrazeit", grant_minutes: "Optionen für Extrazeit (Minuten)",
    show_block: "Schaltfläche „Heute sperren“", show_requests: "Zeitanfragen",
  },
  it: {
    general: "Generale", title: "Titolo (vuoto: nome della console)", show_header: "Mostra intestazione", show_lock: "Pulsante \"Blocca la console\"",
    show_all: "Mostra anche gli utenti senza regole",
    players: "Giocatori", show_player: "Mostra", display_name: "Nome sulla scheda",
    look: "Aspetto", layout: "Aspetto", full: "Completo", compact: "Compatto (una riga per giocatore)",
    time_display: "Tempo mostrato", both: "Rimanente e giocato", remaining: "Tempo rimanente", used: "Tempo giocato",
    show_avatar: "Avatar", show_mode: "Etichetta della modalità", show_status: "Stato / gioco attuale", show_progress: "Barra di avanzamento",
    reports: "Resoconti", show_today_games: "Giochi di oggi", max_games: "Giochi elencati", week_report: "Ultimi 7 giorni",
    collapsed: "Chiuso (tocca per aprire)", expanded: "Sempre aperto", hidden: "Nascosto",
    actions: "Azioni", show_grant: "Pulsanti per tempo extra", grant_minutes: "Opzioni di tempo extra (minuti)",
    show_block: "Pulsante \"Blocca oggi\"", show_requests: "Richieste di tempo",
  },
  pt: {
    general: "Geral", title: "Título (vazio: nome da consola)", show_header: "Mostrar cabeçalho", show_lock: "Botão \"Bloquear consola\"",
    show_all: "Mostrar também utilizadores sem regras",
    players: "Jogadores", show_player: "Mostrar", display_name: "Nome no cartão",
    look: "Aspeto", layout: "Aspeto", full: "Completo", compact: "Compacto (uma linha por jogador)",
    time_display: "Tempo mostrado", both: "Restante e jogado", remaining: "Tempo restante", used: "Tempo jogado",
    show_avatar: "Avatar", show_mode: "Etiqueta do modo", show_status: "Estado / jogo atual", show_progress: "Barra de progresso",
    reports: "Relatórios", show_today_games: "Jogos de hoje", max_games: "Jogos listados", week_report: "Últimos 7 dias",
    collapsed: "Fechado (tocar para abrir)", expanded: "Sempre aberto", hidden: "Oculto",
    actions: "Ações", show_grant: "Botões de tempo extra", grant_minutes: "Opções de tempo extra (minutos)",
    show_block: "Botão \"Bloquear hoje\"", show_requests: "Pedidos de tempo",
  },
};

class NXControlCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...(config || {}) };
    this._build();
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) this._build();
    else if (this._form) this._form.hass = hass;
  }

  get _t() {
    const lang = (this._hass?.locale?.language || this._hass?.language || "en").slice(0, 2);
    return EDITOR_STRINGS[lang] || EDITOR_STRINGS.en;
  }

  _players() {
    if (!this._hass) return [];
    const cid = this._config.console_id;
    return Object.values(this._hass.states)
      .filter((s) => s.attributes.nx_control_profile_id && (!cid || s.attributes.nx_control_console_id === cid))
      .filter((s) => this._config.show_all || (s.attributes.mode && s.attributes.mode !== "none"))
      .map((s) => ({ id: s.attributes.nx_control_profile_id, name: s.attributes.profile_name || s.attributes.nx_control_profile_id.slice(0, 8) }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  _schema(t, players) {
    const opts = (keys) => keys.map((k) => ({ value: k, label: t[k] }));
    return [
      { type: "expandable", name: "", flatten: true, title: t.general, expanded: true, schema: [
        { name: "title", selector: { text: {} } },
        { type: "grid", name: "", schema: [
          { name: "show_header", selector: { boolean: {} } },
          { name: "show_lock", selector: { boolean: {} } },
          { name: "show_all", selector: { boolean: {} } },
        ] },
      ] },
      { type: "expandable", name: "", flatten: true, title: t.players, schema: players.flatMap((p) => [
        { type: "grid", name: "", schema: [
          { name: `show__${p.id}`, label: `${t.show_player} ${p.name}`, selector: { boolean: {} } },
          { name: `name__${p.id}`, label: t.display_name, selector: { text: {} } },
        ] },
      ]) },
      { type: "expandable", name: "", flatten: true, title: t.look, schema: [
        { name: "layout", selector: { select: { mode: "dropdown", options: opts(["full", "compact"]) } } },
        { name: "time_display", selector: { select: { mode: "dropdown", options: opts(["both", "remaining", "used"]) } } },
        { type: "grid", name: "", schema: [
          { name: "show_avatar", selector: { boolean: {} } },
          { name: "show_mode", selector: { boolean: {} } },
          { name: "show_status", selector: { boolean: {} } },
          { name: "show_progress", selector: { boolean: {} } },
        ] },
      ] },
      { type: "expandable", name: "", flatten: true, title: t.reports, schema: [
        { name: "show_today_games", selector: { boolean: {} } },
        { name: "week_report", selector: { select: { mode: "dropdown", options: opts(["collapsed", "expanded", "hidden"]) } } },
        { name: "max_games", selector: { number: { min: 1, max: 10, mode: "slider" } } },
      ] },
      { type: "expandable", name: "", flatten: true, title: t.actions, schema: [
        { type: "grid", name: "", schema: [
          { name: "show_grant", selector: { boolean: {} } },
          { name: "show_block", selector: { boolean: {} } },
          { name: "show_requests", selector: { boolean: {} } },
        ] },
        { name: "grant_minutes", selector: { select: { multiple: true, mode: "list",
          options: [5, 10, 15, 20, 30, 45, 60, 90, 120].map((m) => ({ value: String(m), label: grantLabel(m) })) } } },
      ] },
    ];
  }

  _build() {
    if (!this._hass || !this._config) return;
    const t = this._t;
    const players = this._players();
    const c = { ...DEFAULTS, ...this._config };
    const selected = Array.isArray(c.profiles) && c.profiles.length ? c.profiles.map((x) => String(x).toLowerCase()) : null;
    const names = c.names || {};
    const data = { ...c, grant_minutes: (c.grant_minutes || []).map(String) };
    for (const p of players) {
      data[`show__${p.id}`] = !selected || selected.includes(p.name.toLowerCase()) || selected.includes(p.id.toLowerCase());
      data[`name__${p.id}`] = names[p.id] || names[p.name] || "";
    }
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (s) => s.label || this._t[s.name] || s.name;
      this._form.addEventListener("value-changed", (ev) => this._changed(ev.detail.value));
      this.appendChild(this._form);
    }
    this._players_cache = players;
    this._form.hass = this._hass;
    this._form.schema = this._schema(t, players);
    this._form.data = data;
  }

  _changed(value) {
    const players = this._players_cache || [];
    const out = { ...this._config };
    for (const [k, v] of Object.entries(value)) {
      if (k.startsWith("show__") || k.startsWith("name__")) continue;
      out[k] = v;
    }
    out.grant_minutes = (value.grant_minutes || []).map(Number).sort((a, b) => a - b);
    const shown = players.filter((p) => value[`show__${p.id}`] !== false);
    if (shown.length === players.length) delete out.profiles;
    else out.profiles = shown.map((p) => p.name);
    const names = {};
    for (const p of players) {
      const n = String(value[`name__${p.id}`] || "").trim();
      if (n && n !== p.name) names[p.name] = n;
    }
    if (Object.keys(names).length) out.names = names;
    else delete out.names;
    // Keep the YAML short: drop values equal to the defaults
    for (const [k, v] of Object.entries(DEFAULTS)) if (JSON.stringify(out[k]) === JSON.stringify(v)) delete out[k];
    if (out.title === "") delete out.title;
    this._config = out;
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: out }, bubbles: true, composed: true }));
  }
}

if (!customElements.get("nx-control-card-editor")) customElements.define("nx-control-card-editor", NXControlCardEditor);

// NX Control icons for Home Assistant: "nxc:family" (the NX Control pictogram), usable anywhere an
// icon is chosen, for example the sidebar icon of a dashboard. Loaded on every page with the card.
const NXC_ICONS = {
  family: "M7.5 4.08L7.95 4.14L8.25 4.23L8.7 4.44L9.1 4.73L9.37 5L9.6 5.3L9.82 5.7L9.97 6.15L10.04 6.6L10.05 6.95L10 7.3L9.91 7.65L9.71 8.1L9.48 8.45L9.22 8.75L9.25 8.77L14.7 8.76L14.24 8.15L14.03 7.7L13.93 7.3L13.88 6.95L13.88 6.6L13.96 6.15L14.08 5.75L14.32 5.3L14.55 5L14.8 4.75L15.15 4.49L15.8 4.19L16.25 4.1L16.75 4.08L17.2 4.14L17.55 4.24L17.95 4.43L18.25 4.63L18.77 5.15L18.97 5.45L19.16 5.85L19.25 6.15L19.32 6.6L19.32 6.95L19.26 7.4L19.11 7.85L18.96 8.15L18.5 8.76L22.1 8.78L22.5 8.9L22.65 8.99L22.8 9.17L22.92 9.4L22.97 9.65L22.97 11.2L22.91 11.5L22.82 11.7L22.7 11.84L22.4 12.02L22.05 12.08L19.69 12.1L19.79 12.55L20.04 13.25L21.02 15.6L21.21 16.3L21.23 16.55L21.15 16.74L21.07 16.85L20.8 16.97L18.7 16.97L18.63 17L18.62 18.95L18.52 19.4L18.4 19.6L18.3 19.7L18 19.82L16.85 19.81L16.7 19.71L16.63 19.6L16.6 19.2L16.68 19L16.85 18.88L17.55 18.85L17.62 18.8L17.62 16.35L17.65 16.25L17.75 16.11L17.9 16.03L18.05 16L20.15 16L20.06 15.65L19.33 13.9L18.83 12.5L18.64 11.65L18.64 11.4L18.68 11.3L18.82 11.15L19 11.09L21.95 11.08L21.98 11L21.98 9.8L21.95 9.74L21.9 9.73L2 9.75L1.97 9.8L1.97 11L2 11.07L5.05 11.09L5.25 11.19L5.35 11.35L5.38 18.7L5.4 18.84L6.35 18.85L6.45 18.82L6.47 17.45L6.49 17.35L6.6 17.19L6.75 17.12L7.15 17.12L7.3 17.19L7.41 17.35L7.42 19.45L7.36 19.6L7.25 19.72L7 19.82L5.1 19.82L4.8 19.72L4.59 19.55L4.44 19.3L4.38 19.05L4.36 12.1L1.9 12.08L1.55 12.01L1.35 11.9L1.09 11.6L1 11.3L1 9.5L1.09 9.2L1.25 8.99L1.4 8.89L1.75 8.78L5.3 8.78L5.43 8.75L5.17 8.45L4.94 8.1L4.68 7.45L4.61 6.95L4.61 6.65L4.73 5.95L5.05 5.3L5.28 5L5.55 4.73L5.95 4.44L6.25 4.29L6.55 4.19L6.95 4.1ZM7.05 5.05L6.7 5.14L6.4 5.28L6.11 5.5L5.9 5.75L5.74 6L5.63 6.3L5.56 6.65L5.56 6.95L5.63 7.3L5.75 7.6L5.99 7.95L6.15 8.11L6.5 8.35L6.75 8.46L7.15 8.55L7.5 8.55L7.75 8.51L8.15 8.35L8.39 8.2L8.65 7.97L8.9 7.6L9.02 7.3L9.09 6.95L9.09 6.65L9.03 6.3L8.91 6L8.64 5.6L8.4 5.39L8.15 5.23L7.75 5.07L7.45 5.03ZM16.3 5.05L15.95 5.15L15.7 5.27L15.4 5.49L15.2 5.71L15.02 6L14.88 6.35L14.83 6.65L14.83 6.95L14.89 7.25L15.03 7.6L15.18 7.85L15.41 8.1L15.8 8.37L16.05 8.47L16.45 8.56L16.75 8.56L17.05 8.5L17.4 8.37L17.65 8.21L17.9 7.99L18.12 7.7L18.26 7.4L18.37 6.95L18.37 6.6L18.32 6.35L18.16 5.95L17.91 5.6L17.65 5.37L17.4 5.21L17.05 5.08L16.75 5.03ZM9.3 10.87L9.75 10.89L10.2 11.03L10.65 11.32L10.9 11.57L11.11 11.9L11.22 12.15L11.31 12.6L11.29 13.1L11.12 13.6L10.91 13.95L10.71 14.15L10.7 14.2L10.75 14.21L13.52 14.2L13.51 14.15L13.2 13.78L12.98 13.3L12.91 12.9L12.93 12.45L13.08 11.95L13.34 11.55L13.6 11.29L14 11.04L14.3 10.93L14.65 10.87L15.15 10.89L15.35 10.94L15.6 11.03L15.89 11.2L16.05 11.32L16.36 11.65L16.51 11.9L16.61 12.15L16.71 12.6L16.72 12.9L16.67 13.2L16.52 13.6L16.41 13.8L16.1 14.2L17.85 14.24L17.95 14.3L18.07 14.45L18.1 14.8L18.04 15L17.94 15.1L17.8 15.16L16.2 15.17L16.1 15.2L16.19 15.65L16.49 16.6L16.74 17.25L17.02 17.85L17.06 18L16.95 18.17L16.75 18.26L16.25 18.27L16.18 18.3L16.17 19.45L16.1 19.65L16 19.75L15.85 19.82L15.55 19.82L15.31 19.7L15.22 19.5L15.2 18.3L15.1 18.27L14.6 18.27L14.49 18.3L14.49 19.45L14.42 19.65L14.3 19.77L14.2 19.82L13.8 19.81L13.63 19.7L13.54 19.5L13.52 18.3L13.45 18.27L12.8 18.26L12.6 18.15L12.57 18.1L12.54 17.95L12.57 17.85L13.57 15.3L13.59 15.2L13.5 15.17L10.8 15.17L10.77 15.25L10.77 19.4L10.73 19.6L10.65 19.71L10.4 19.82L10.05 19.82L9.84 19.7L9.73 19.45L9.72 17.9L9.1 17.88L9.02 17.9L9.01 17.95L9.01 19.4L8.96 19.6L8.85 19.74L8.65 19.82L8.25 19.81L8.05 19.67L7.98 19.55L7.96 19.4L7.96 15.2L7.85 15.17L6.15 15.15L6.05 15.1L5.94 14.95L5.92 14.5L6.05 14.3L6.25 14.22L8.12 14.2L8.11 14.15L7.78 13.75L7.58 13.3L7.53 13.1L7.51 12.65L7.59 12.2L7.69 11.95L7.83 11.7L8.2 11.29L8.6 11.04L9.05 10.9Z",
};
window.customIcons = window.customIcons || {};
window.customIcons.nxc = {
  getIcon: async (name) => ({ path: NXC_ICONS[name] || NXC_ICONS.family, viewBox: "0 0 24 24" }),
  getIconList: async () => Object.keys(NXC_ICONS).map((name) => ({ name })),
};

// The NX Control page in the sidebar (/nx-control): the card, full screen, with the usual header.
class NXControlPanel extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    this._build();
    if (this._card) this._card.hass = hass;
    if (this._menu) this._menu.hass = hass;
  }

  set narrow(narrow) {
    this._narrow = narrow;
    if (this._menu) this._menu.narrow = narrow;
  }

  set panel(panel) {
    this._panel = panel;
  }

  connectedCallback() {
    this._build();
  }

  _build() {
    if (this._built || !this._hass) return;
    this._built = true;
    const root = this.attachShadow({ mode: "open" });
    root.innerHTML = `
      <style>
        :host { display: block; min-height: 100vh; background: var(--primary-background-color); }
        .header { position: sticky; top: 0; z-index: 2; display: flex; align-items: center; gap: 8px;
                  height: var(--header-height, 56px); padding: 0 12px;
                  padding-top: env(safe-area-inset-top);
                  background: var(--app-header-background-color, var(--primary-color));
                  color: var(--app-header-text-color, var(--text-primary-color, #fff));
                  border-bottom: var(--app-header-border-bottom, none); }
        .title { font-size: 20px; font-weight: 400; margin-left: 4px; }
        .content { box-sizing: border-box; max-width: 640px; margin: 0 auto; padding: 16px 12px 32px; }
      </style>
      <div class="header"><ha-menu-button></ha-menu-button><div class="title">NX Control</div></div>
      <div class="content"></div>`;
    this._menu = root.querySelector("ha-menu-button");
    this._menu.hass = this._hass;
    this._menu.narrow = this._narrow;
    this._card = document.createElement("nx-control-card");
    this._card.setConfig({ show_header: true });
    this._card.hass = this._hass;
    root.querySelector(".content").appendChild(this._card);
  }
}
if (!customElements.get("nx-control-panel")) customElements.define("nx-control-panel", NXControlPanel);

const existing = customElements.get("nx-control-card");
if (existing && existing.version !== CARD_VERSION) {
  // Another copy was loaded first (usually an old dashboard resource): it stays in use until reload.
  console.warn(`NX Control card ${CARD_VERSION} was not loaded: version ${existing.version || "unknown"} ` +
    "was loaded first. Remove any NX Control entry in Settings > Dashboards > Resources and reload.");
}
if (!existing) {
  NXControlCard.version = CARD_VERSION;
  customElements.define("nx-control-card", NXControlCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "nx-control-card",
    name: "NX Control",
    description: "Play time of your Nintendo Switch: time left, current game, extra time, blocks and requests.",
    preview: true,
    documentationURL: "https://github.com/danialonso/nx-control",
  });
  console.info(`%c NX CONTROL CARD %c ${CARD_VERSION} `, "color:#fff;background:#e60012;font-weight:700;border-radius:3px 0 0 3px",
    "color:#e60012;background:#fff;font-weight:700;border-radius:0 3px 3px 0");
}
