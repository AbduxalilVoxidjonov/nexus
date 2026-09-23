/* Nexus Ovoz OS — UI mantiqi (vanilla JS, kutubxonasiz).
 * Real ma'lumot: ws://<host>/ws (nexus/server.py) → EventBus hodisalari.
 */
(function () {
  "use strict";

  // ── Yordamchilar ──────────────────────────────────────────────────
  const $ = (id) => document.getElementById(id);
  const pad = (n) => String(n).padStart(2, "0");
  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const fmtTime = (ts) => {
    const d = ts ? new Date(ts * 1000) : new Date();
    return pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
  };
  const short = (s, n) => { s = String(s == null ? "" : s); return s.length > n ? s.slice(0, n - 1) + "…" : s; };
  const fmtDur = (sec) => {
    sec = Math.max(0, Math.floor(sec));
    const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60;
    // "s" ham soat, ham sekund bo'lib chalkashmasin: 1 soat 5 daq · 2 daq 11 s · 40 s
    return h > 0 ? h + " soat " + m + " daq" : m > 0 ? m + " daq " + s + " s" : s + " s";
  };
  const lsGet = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (_) { return d; } };
  const lsSet = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (_) { /* yo'q */ } };

  // ── Holat va ranglar ─────────────────────────────────────────────
  const ACCENT = { idle: "#7c848d", listening: "#22d3ee", processing: "#a78bfa", tool_executing: "#34d399", speaking: "#e879f9", dictating: "#a855f7", awaiting_confirmation: "#f59e0b" };
  const LABEL = { idle: "Kutmoqda", listening: "Tinglamoqda", processing: "Ishlov bermoqda", tool_executing: "Bajarilmoqda", speaking: "Gapirmoqda", dictating: "Yozib turibman", awaiting_confirmation: "Tasdiq kutilmoqda" };
  const AURA = {
    idle: "radial-gradient(circle, rgba(255,255,255,0.05), rgba(0,0,0,0) 68%)",
    listening: "radial-gradient(circle, rgba(167,139,250,0.34), rgba(34,211,238,0.16) 45%, rgba(0,0,0,0) 70%)",
    processing: "radial-gradient(circle, rgba(167,139,250,0.26), rgba(0,0,0,0) 68%)",
    tool_executing: "radial-gradient(circle, rgba(52,211,153,0.24), rgba(0,0,0,0) 68%)",
    speaking: "radial-gradient(circle, rgba(232,121,249,0.28), rgba(56,189,248,0.12) 45%, rgba(0,0,0,0) 70%)",
    dictating: "radial-gradient(circle, rgba(168,85,247,0.34), rgba(139,92,246,0.14) 45%, rgba(0,0,0,0) 70%)",
    awaiting_confirmation: "radial-gradient(circle, rgba(245,158,11,0.30), rgba(0,0,0,0) 68%)",
  };

  // Tool nomi → turkum, ikonka (SVG path), o'zbekcha nom
  const ICONS = {
    app: "M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z",
    volume: "M11 5L6 9H2v6h4l5 4V5zM15.5 8.5a5 5 0 010 7",
    media: "M5 3l14 9-14 9V3z",
    browser: "M12 2a10 10 0 100 20 10 10 0 000-20zM2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z",
    terminal: "M4 17l6-6-6-6M12 19h8",
    screenshot: "M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2zM12 17a4 4 0 100-8 4 4 0 000 8z",
    system: "M9 9h6v6H9zM4 4h16v16H4zM9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3",
    ui: "M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3zM13 13l6 6",
    file: "M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8",
    dictation: "M12 2a3 3 0 00-3 3v6a3 3 0 006 0V5a3 3 0 00-3-3zM19 10v1a7 7 0 01-14 0v-1M12 18v3M16 20l5-5-1.5-1.5-5 5V20h1.5z",
    error: "M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z",
  };
  const KIND_LABEL = { app: "Ilova", volume: "Ovoz", media: "Media", browser: "Brauzer", terminal: "Terminal", screenshot: "Skrinshot", system: "Tizim", ui: "UI", file: "Fayl", dictation: "Diktovka" };
  const KIND_RULES = [
    ["dictation", /dictat/i],
    ["ui", /^(list_ui_elements|click_ui_element|read_screen_text|list_menus|menu_command|get_focused_element|set_text_field)$|_ui_|ui_element|accessib|menu_/i],
    ["file", /^(read_file|write_file|delete_file|list_directory|write_note|find_files|open_with_app)$|spreadsheet|_file$|^file_|directory|folder/i],
    ["screenshot", /screenshot|screen_?shot|capture|skrinshot/i],
    ["volume", /volume|mute|sound|ovoz|audio_out/i],
    ["media", /media|play|pause|next|prev|track|music|spotify|itunes/i],
    ["browser", /browser|safari|chrome|url|web|search|open_url|tab/i],
    ["terminal", /terminal|shell|exec|run_?command|bash|zsh|script/i],
    ["app", /app|open|launch|quit|activate|focus|window|finder/i],
  ];
  const kindOf = (name) => { for (const [k, re] of KIND_RULES) if (re.test(name || "")) return k; return "system"; };

  const SUGGESTIONS = ["Safari'da YouTube'ni och", "Ovozni 40 ga qo'y", "Skrinshot ol", "Tizim holati"];
  const TRIGGERS = [
    { label: () => "Hey " + (S.settings.name || "Nexus"), key: "wake", action: null },
    { label: "Ovozni o'chir", key: "⌥ M", action: () => toggleMute() },
    { label: "Skrinshot ol", key: "matn", action: () => sendText("Skrinshot ol") },
    { label: "Hammasini to'xtat", key: "⌥ ⎋", action: () => killAll() },
  ];

  // ── Ilova holati ──────────────────────────────────────────────────
  const S = {
    ws: null, wsAttempt: 0, wsOpen: false, wsReconnects: 0, reqId: 0, pending: new Map(), wsTimer: null, manualClose: false,
    state: "idle",
    conn: { gemini: "disconnected", attempt: 0, detail: "" },
    metrics: {},
    settings: { muted: false, ptt: false, sensitivity: 0.68, playback: null, wake_mode: null, name: "Nexus", dictating: false },
    confirm: null, confirmTimer: null,
    devices: [], currentDevice: null, devicesOpen: false,
    level: 0, levelAt: 0,
    transcript: "", transcriptFinal: true,
    assistantText: "", currentTool: null,
    toolLog: [], history: [], curRow: null,
    filter: "Hammasi", tab: lsGet("nx.tab", "stream"),
    lastUserFinal: "", lastUserFinalTs: 0,
    msgCount: 0, toolCount: 0, toolOk: 0, geminiReconnects: 0,
    sessionStart: Date.now(), pttPressed: false,
    showSeconds: lsGet("nx.seconds", true), anim: lsGet("nx.anim", true),
  };

  // ── WebSocket ─────────────────────────────────────────────────────
  const wsUrl = () => (location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws";

  // Eski soketni identity bilan yopadi: uning onclose'i S.ws ni null qilmasin / reconnect rejalashtirmasin
  function closeSocket(reason) {
    const old = S.ws;
    if (!old) return;
    S.ws = null;
    S.wsOpen = false;
    old.onopen = old.onmessage = old.onerror = old.onclose = null;
    try { old.close(1000, reason || "reconnect"); } catch (_) { /* allaqachon yopiq */ }
    for (const [, p] of S.pending) p.resolve(null);
    S.pending.clear();
  }

  function connect(force) {
    clearTimeout(S.wsTimer);
    S.wsTimer = null;
    if (S.ws) {
      if (!force && (S.ws.readyState === WebSocket.OPEN || S.ws.readyState === WebSocket.CONNECTING)) return;
      closeSocket("reconnect");
    }
    S.manualClose = false;
    let ws;
    try { ws = new WebSocket(wsUrl()); } catch (e) { scheduleReconnect(); return; }
    S.ws = ws;
    renderConn();
    // Har bir handler `S.ws !== ws` bo'lsa chiqib ketadi: eski (almashtirilgan) soket hodisalari
    // yangi soket holatini buzmasin — aks holda ikkita jonli WS paydo bo'lardi.
    ws.onopen = () => {
      if (S.ws !== ws) return;
      S.wsOpen = true;
      if (S.wsAttempt > 0) S.wsReconnects += 1;
      S.wsAttempt = 0;
      renderConn();
    };
    ws.onmessage = (ev) => {
      if (S.ws !== ws) return;
      let msg;
      try { msg = JSON.parse(ev.data); } catch (_) { return; }
      handleMessage(msg);
    };
    ws.onclose = () => {
      if (S.ws !== ws) return;
      S.wsOpen = false;
      S.ws = null;
      for (const [, p] of S.pending) p.resolve(null);
      S.pending.clear();
      renderConn();
      if (!S.manualClose) scheduleReconnect();
    };
    ws.onerror = () => { /* onclose keladi (identity tekshiruvi o'sha yerda) */ };
  }

  function scheduleReconnect() {
    clearTimeout(S.wsTimer);
    S.wsAttempt += 1;
    const delay = Math.min(15000, 500 * Math.pow(2, Math.min(S.wsAttempt, 5))) + Math.random() * 300;
    renderConn();
    S.wsTimer = setTimeout(connect, delay);
  }

  // Har doim resolve bo'ladi: CMD_RESULT.data yoki null (aloqa yo'q / timeout)
  function send(cmd, extra, quiet) {
    const msg = Object.assign({ cmd }, extra || {});
    if (!S.ws || S.ws.readyState !== WebSocket.OPEN) {
      if (!quiet) toast("Daemon bilan aloqa yo'q — buyruq yuborilmadi: " + cmd, "warn");
      return Promise.resolve(null);
    }
    msg.reqId = ++S.reqId;
    return new Promise((resolve) => {
      S.pending.set(msg.reqId, { resolve, cmd, quiet: !!quiet });
      setTimeout(() => { if (S.pending.delete(msg.reqId)) { if (!quiet) toast("Javob kelmadi: " + cmd, "warn"); resolve(null); } }, 15000);
      try { S.ws.send(JSON.stringify(msg)); } catch (_) { S.pending.delete(msg.reqId); resolve(null); }
    });
  }

  // ── Xabarlarni qayta ishlash ──────────────────────────────────────
  function handleMessage(msg) {
    const t = msg.type, d = msg.data || {};
    switch (t) {
      case "HELLO": applySnapshot(d); break;
      case "CMD_RESULT": {
        const p = S.pending.get(msg.reqId);
        if (p) { S.pending.delete(msg.reqId); p.resolve(d); }
        if (d && d.ok === false) { if (!(p && p.quiet)) toast((p ? p.cmd + ": " : "") + (d.error || "xato"), "err"); }
        else if (p && p.cmd === "get_state" && d.snapshot) applySnapshot(d, true);
        break;
      }
      default: handleEvent(msg, false);
    }
  }

  function applySnapshot(d, keepLists) {
    if (d.state) { S.state = d.state; }
    const snap = d.snapshot || {};
    if (snap.METRICS) S.metrics = snap.METRICS;
    if (snap.SETTINGS) applySettings(snap.SETTINGS);
    if (snap.DEVICES) applyDevices(snap.DEVICES);
    if (snap.CONNECTION) S.conn = Object.assign({}, S.conn, snap.CONNECTION);
    if (!keepLists) {
      S.toolLog = []; S.history = []; S.curRow = null; S.msgCount = 0; S.toolCount = 0; S.toolOk = 0;
      S.transcript = ""; S.transcriptFinal = true; S.assistantText = ""; S.currentTool = null;
      for (const ev of d.history || []) handleEvent(ev, true);
    }
    if (!snap.DEVICES) send("list_devices", null, true);
    if (d.pending_confirm && d.pending_confirm.token) {
      const pc = d.pending_confirm;
      const elapsed = pc.ts ? Math.max(0, Date.now() / 1000 - pc.ts) : 0;
      setConfirm(Object.assign({}, pc, { ttl_s: Math.max(1, (pc.ttl_s || 30) - elapsed) }));
    } else if ("pending_confirm" in d) {
      setConfirm(null);
    }
    renderAll();
  }

  function handleEvent(ev, replay) {
    const d = ev.data || {};
    switch (ev.type) {
      case "STATE_CHANGE":
        S.state = d.state || S.state;
        if (S.state === "listening" && S.transcriptFinal && !replay) { /* yangi nutq kutilmoqda; eski matn qoladi */ }
        if (S.state !== "tool_executing") S.currentTool = null;
        renderState(); renderPTT(); renderDict();
        break;
      case "TRANSCRIPT":
        if (d.role === "user") {
          if (replay) { if (d.final) { S.msgCount += 1; pushUserRow(d.text, ev.ts); } break; }
          S.transcript = d.text || "";
          S.transcriptFinal = !!d.final;
          if (d.final && S.transcript.trim()) { S.msgCount += 1; S.lastUserFinal = S.transcript; S.lastUserFinalTs = ev.ts; pushUserRow(S.transcript, ev.ts); S.assistantText = ""; }
          renderTranscript(); if (d.final) renderHistory();
        } else {
          if (replay) { if (d.final) { S.msgCount += 1; pushReply(d.text, ev.ts); } break; }
          S.assistantText = d.text || "";
          if (d.final && S.assistantText.trim()) { S.msgCount += 1; pushReply(S.assistantText, ev.ts); renderHistory(); }
          renderTranscript();
        }
        if (!replay) renderStats();
        break;
      case "TOOL_CALLED": {
        const entry = makeToolEntry(d, ev.ts);
        S.toolLog.unshift(entry);
        if (S.toolLog.length > 200) S.toolLog.length = 200;
        S.toolCount += 1; if (entry.ok) S.toolOk += 1;
        pushTool(entry);
        if (!replay) { S.currentTool = entry.name; renderToolLog(); renderHistory(); renderTranscript(); renderStats(); renderShellLabel(); }
        break;
      }
      case "AUDIO_LEVEL":
        S.level = clamp(Number(d.rms) || 0, 0, 1); S.levelAt = performance.now();
        requestLevelRender();
        break;
      case "METRICS":
        S.metrics = d; renderMetrics(); break;
      case "CONNECTION":
        if (d.gemini === "reconnecting" && S.conn.gemini !== "reconnecting") S.geminiReconnects += 1;
        S.conn = Object.assign({}, S.conn, d); renderConn(); renderCards(); renderStats(); break;
      case "LOG":
        if (!replay && (d.level === "warn" || d.level === "error")) toast(d.message || "", d.level === "error" ? "err" : "warn");
        break;
      case "DEVICES":
        applyDevices(d); renderDevices(); renderCards(); break;
      case "SETTINGS":
        applySettings(d); renderPTT(); renderMute(); renderSens(); renderSettingsPanel(); renderCards(); renderDict(); renderSuggestions(); break;
      case "CONFIRM_REQUEST":
        if (!replay) { setConfirm(d); toast("Tasdiq so'ralmoqda: " + short(d.summary || d.action || "", 80), "warn"); }
        break;
      case "CONFIRM_RESOLVED":
        if (!replay) {
          if (!S.confirm || S.confirm.token === d.token) setConfirm(null);
          const src = d.source === "voice" ? "ovoz" : d.source === "ui" ? "UI" : d.source === "timeout" ? "vaqt" : (d.source || "");
          if (d.source === "timeout") toast("Vaqt tugadi — amal bekor qilindi", "warn");
          else toast((d.approved ? "Tasdiqlandi" : "Rad etildi") + (src ? " (" + src + ")" : ""), d.approved ? "ok" : "warn");
        }
        break;
      default: break;
    }
  }

  function applySettings(d) {
    if (typeof d.muted === "boolean") S.settings.muted = d.muted;
    if (typeof d.ptt === "boolean") S.settings.ptt = d.ptt;
    if (typeof d.sensitivity === "number") S.settings.sensitivity = clamp(d.sensitivity, 0, 1);
    if (typeof d.playback === "boolean") S.settings.playback = d.playback;
    if (typeof d.wake_mode === "string") S.settings.wake_mode = d.wake_mode;
    if (typeof d.name === "string" && d.name.trim()) S.settings.name = d.name.trim();
    if (typeof d.dictating === "boolean") S.settings.dictating = d.dictating;
  }
  function applyDevices(d) {
    S.devices = Array.isArray(d.devices) ? d.devices : [];
    S.currentDevice = d.current == null ? null : d.current;
  }

  function makeToolEntry(d, ts) {
    const name = d.name || "tool";
    const kind = kindOf(name);
    const args = d.args && typeof d.args === "object" ? d.args : {};
    const argStr = Object.keys(args).map((k) => k + "=" + short(typeof args[k] === "string" ? args[k] : JSON.stringify(args[k]), 40)).join(", ");
    const ok = d.ok !== false;
    const speech = S.lastUserFinal && ts - S.lastUserFinalTs < 90 ? S.lastUserFinal : "";
    const out = String(d.output == null ? "" : d.output).replace(/\s+/g, " ").trim();
    return {
      id: Math.random().toString(36).slice(2),
      ts, time: fmtTime(ts), name, kind, ok,
      speech,
      intent: name + (argStr ? " · " + argStr : ""),
      shell: out ? short(out, 120) : (ok ? "(natija bo'sh)" : "xato"),
      status: ok ? "bajarildi" : "xato",
      latency: typeof d.duration_ms === "number" ? (d.duration_ms >= 1000 ? (d.duration_ms / 1000).toFixed(1) + "s" : d.duration_ms + "ms") : "—",
      icon: ok ? (ICONS[kind] || ICONS.system) : ICONS.error,
    };
  }

  // Tarix qatorlari (user → javob/tool guruhlash)
  function pushUserRow(text, ts) {
    S.curRow = { speech: text, replies: [], tools: [], ts, time: fmtTime(ts) };
    S.history.unshift(S.curRow);
    if (S.history.length > 300) S.history.length = 300;
    S.lastUserFinal = text; S.lastUserFinalTs = ts;
  }
  function ensureRow(ts) {
    if (!S.curRow || ts - S.curRow.ts > 300) pushUserRow("—", ts);
    return S.curRow;
  }
  function pushReply(text, ts) { ensureRow(ts).replies.push(text); }
  function pushTool(entry) { ensureRow(entry.ts).tools.push(entry); }

  // ── Render: sarlavha ──────────────────────────────────────────────
  function renderConn() {
    const b = $("connBadge"), t = $("connText");
    b.classList.remove("warn", "err");
    if (!S.wsOpen) {
      b.classList.add("err");
      t.textContent = S.wsAttempt > 0 ? "UI qayta ulanmoqda (" + S.wsAttempt + ")" : "Ulanmoqda…";
    } else if (S.conn.gemini === "connected") {
      t.textContent = "Gemini Live · Faol";
    } else if (S.conn.gemini === "reconnecting") {
      b.classList.add("warn");
      t.textContent = "Qayta ulanmoqda (" + (S.conn.attempt || 0) + ")";
    } else {
      b.classList.add("err");
      t.textContent = "Uzilgan";
    }
    b.title = S.conn.detail || "";
    $("setWsUrl").textContent = wsUrl();
  }

  function renderClock() {
    const d = new Date();
    $("clock").textContent = pad(d.getHours()) + ":" + pad(d.getMinutes()) + (S.showSeconds ? ":" + pad(d.getSeconds()) : "");
  }

  // ── Render: vizualizator ──────────────────────────────────────────
  function renderState() {
    const st = ACCENT[S.state] ? S.state : "idle";
    const accent = ACCENT[st];
    $("stateLabel").textContent = LABEL[st] || st;
    const dot = $("stateDot");
    dot.style.background = accent; dot.style.boxShadow = "0 0 10px " + accent;
    dot.style.animation = st === "idle" ? "none" : "nx-pulse 1.4s ease-in-out infinite";

    const aura = $("aura");
    aura.style.background = AURA[st];
    aura.style.animationDuration = st === "listening" || st === "speaking" ? "2.2s" : "5s";

    const orb = $("orb");
    orb.style.borderColor = st === "idle" ? "rgba(255,255,255,0.11)" : accent + "44";
    orb.style.boxShadow = st === "idle" ? "inset 0 1px 0 rgba(255,255,255,0.07)" : "inset 0 1px 0 rgba(255,255,255,0.09), 0 0 46px -14px " + accent;

    const live = st === "listening" || st === "speaking" || st === "dictating";
    $("spinner").hidden = st !== "processing";
    $("shellIcon").hidden = st !== "tool_executing";
    $("confirmIcon").hidden = st !== "awaiting_confirmation";
    const bars = $("bars");
    bars.hidden = st === "processing" || st === "tool_executing" || st === "awaiting_confirmation";
    bars.classList.toggle("live", live);
    if (!live) bars.style.transform = "scaleY(0.16)";
    $("caret").style.color = accent;
    renderTranscript();
    renderLevel();
  }

  function renderShellLabel() {
    $("shellLabel").textContent = S.currentTool ? short(S.currentTool.toUpperCase(), 18) : "SHELL";
  }

  function renderTranscript() {
    const box = $("transcriptBox"), txt = $("transcript"), caret = $("caret");
    const has = !!S.transcript;
    box.classList.toggle("has", has);
    const placeholder = S.state === "listening" ? "Tinglamoqda…" : S.state === "dictating" ? "Diktovka: gapiring, matn faol maydonga yoziladi…"
      : S.state === "awaiting_confirmation" ? "Xavfli amal — “ha” deng yoki yuqoridagi kartada tasdiqlang." : "Gapiring yoki pastdagi maydonga buyruq yozing — yoki “Hey " + (S.settings.name || "Nexus") + "” deb ayting.";
    txt.classList.toggle("placeholder", !has);
    txt.textContent = has ? S.transcript : placeholder;
    txt.appendChild(caret);
    caret.classList.toggle("on", (S.state === "listening" || S.state === "dictating") && (!S.transcriptFinal || !has));

    const row = $("intentRow"), key = $("intentKey"), val = $("liveIntent");
    if (S.state === "tool_executing") {
      row.hidden = false; key.textContent = "Bajarilmoqda"; val.className = "v"; val.textContent = S.currentTool || "tool…";
    } else if (S.currentTool && S.state !== "idle") {
      row.hidden = false; key.textContent = "Aniqlangan niyat"; val.className = "v"; val.textContent = S.currentTool;
    } else if (S.assistantText) {
      row.hidden = false; key.textContent = "Javob"; val.className = "v assist"; val.textContent = short(S.assistantText, 160);
    } else {
      row.hidden = true;
    }
  }

  let levelRaf = 0;
  function requestLevelRender() { if (!levelRaf) levelRaf = requestAnimationFrame(() => { levelRaf = 0; renderLevel(); }); }
  function renderLevel() {
    const lvl = S.settings.muted ? 0 : S.level;
    const levelEl = $("levelBars");            // pastki panel olib tashlangan — bo'lmasa o'tkazib yuboriladi
    const bars = levelEl ? levelEl.children : [];
    const n = bars.length;
    for (let i = 0; i < n; i++) {
      const on = i / n < lvl;
      const el = bars[i];
      el.className = on ? ("on" + (i > 21 ? " hi" : i > 17 ? " mid" : "")) : "";
    }
    const orbBars = $("bars");
    if (orbBars.classList.contains("live")) {
      orbBars.style.transform = "scaleY(" + (0.28 + Math.min(1, lvl * 2.2) * 0.72).toFixed(3) + ")";
      $("aura").style.opacity = "";
    }
  }
  // Daraja ma'lumoti kelmay qolsa asta pasaytiramiz
  setInterval(() => { if (S.level > 0 && performance.now() - S.levelAt > 400) { S.level = Math.max(0, S.level - 0.12); renderLevel(); } }, 120);

  // ── Render: tool jurnali ──────────────────────────────────────────
  function renderFilters() {
    const kinds = Array.from(new Set(S.toolLog.map((e) => e.kind)));
    const items = ["Hammasi", "Muvaffaqiyatli", "Xatolar"].concat(kinds.map((k) => KIND_LABEL[k] || k));
    if (!items.includes(S.filter)) S.filter = "Hammasi";
    $("filters").innerHTML = items.map((f) => '<button type="button" class="nx-chip' + (S.filter === f ? " active" : "") + '" data-f="' + esc(f) + '">' + esc(f) + "</button>").join("");
  }
  function visibleLog() {
    const f = S.filter;
    if (f === "Hammasi") return S.toolLog;
    if (f === "Muvaffaqiyatli") return S.toolLog.filter((e) => e.ok);
    if (f === "Xatolar") return S.toolLog.filter((e) => !e.ok);
    return S.toolLog.filter((e) => (KIND_LABEL[e.kind] || e.kind) === f);
  }
  function renderToolLog() {
    renderFilters();
    $("logCount").textContent = String(S.toolLog.length);
    const list = visibleLog();
    const host = $("toolLog");
    if (!list.length) {
      host.innerHTML = '<div class="nx-empty">' + (S.toolLog.length ? "Bu filtrga mos yozuv yo'q." : "Hali tool chaqiruvlari yo'q.<br>Gapiring yoki pastdagi maydonga buyruq yozing.") + "</div>";
      return;
    }
    host.innerHTML = list.slice(0, 80).map((e) =>
      '<div class="nx-entry' + (e.ok ? "" : " err") + '">' +
        '<div class="row">' +
          '<div class="badge"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="' + e.icon + '"></path></svg></div>' +
          '<div class="body">' +
            '<div class="top"><span class="speech">' + esc(e.speech || (KIND_LABEL[e.kind] || "Tool") + " chaqiruvi") + '</span><span class="time">' + esc(e.time) + "</span></div>" +
            '<div class="intent">' + esc(e.intent) + "</div>" +
            '<div class="meta"><code class="nx-code">' + esc(e.shell) + '</code><span class="nx-status' + (e.ok ? "" : " err") + '">' + esc(e.status) + '</span><span class="nx-lat">' + esc(e.latency) + "</span></div>" +
          "</div>" +
        "</div>" +
      "</div>").join("");
  }

  // ── Render: tarix ─────────────────────────────────────────────────
  function renderHistory() {
    const q = ($("histSearch").value || "").trim().toLowerCase();
    const rows = S.history.filter((r) => !q || (r.speech + " " + r.replies.join(" ") + " " + r.tools.map((t) => t.name + " " + t.shell).join(" ")).toLowerCase().includes(q));
    $("histCount").textContent = String(S.history.length);
    const head = '<div class="th">OVOZLI BUYRUQ</div><div class="th">JAVOB / SHELL</div><div class="th">HOLAT</div><div class="th r">VAQT</div>';
    if (!rows.length) {
      $("histTable").innerHTML = head + '<div class="td wide">' + (S.history.length ? "Qidiruvga mos yozuv topilmadi." : "Sessiyada hali xabarlar yo'q.") + "</div>";
      return;
    }
    $("histTable").innerHTML = head + rows.slice(0, 200).map((r) => {
      const failed = r.tools.some((t) => !t.ok);
      const reply = r.replies.map((x) => esc(short(x, 240))).join("<br>") +
        r.tools.map((t) => '<code class="tool">' + esc(t.name) + " → " + esc(short(t.shell, 90)) + "</code>").join("");
      let status;
      if (r.tools.length) status = '<span class="nx-status' + (failed ? " err" : "") + '">' + (failed ? "xato" : "bajarildi") + "</span>";
      else if (r.replies.length) status = '<span class="nx-status assist">javob</span>';
      else status = '<span class="nx-status user">xabar</span>';
      return '<div class="td">' + esc(r.speech) + '</div><div class="td reply">' + (reply || "—") + '</div><div class="td">' + status + '</div><div class="td time r">' + esc(r.time) + "</div>";
    }).join("");
  }

  // ── Render: ko'rsatkichlar ────────────────────────────────────────
  function meterDefs() {
    const m = S.metrics || {};
    const num = (v) => (typeof v === "number" && isFinite(v) ? v : null);
    const cpu = num(m.cpu), ram = num(m.ram), bat = num(m.battery), lat = num(m.latency_ms);
    return [
      { label: "Protsessor yuklamasi", value: cpu == null ? "—" : Math.round(cpu) + "%", pct: cpu == null ? 0 : cpu, cls: "fill-cpu",
        sub: m.cores ? m.cores + " yadro" + (m.cpu_temp ? " · " + Math.round(m.cpu_temp) + "°C" : "") : "tizim bo'yicha" },
      { label: "Xotira (RAM)", value: ram == null ? "—" : Math.round(ram) + "%", pct: ram == null ? 0 : ram, cls: "fill-ram",
        sub: m.ram_used_gb && m.ram_total_gb ? m.ram_used_gb.toFixed(1) + " GB / " + m.ram_total_gb.toFixed(0) + " GB" : "birlashgan xotira" },
      { label: "Batareya", value: bat == null ? "—" : Math.round(bat) + "%", pct: bat == null ? 0 : bat, cls: "fill-bat",
        sub: bat == null ? "ma'lumot yo'q" : m.charging === true ? "quvvatlanmoqda" : m.charging === false ? "batareyadan" : "quvvat holati" },
      { label: "Kechikish (Gemini)", value: lat == null ? "— ms" : lat + " ms", pct: lat == null ? 0 : clamp(lat / 20, 0, 100), cls: "fill-lat",
        sub: lat == null ? "javob kutilmoqda" : lat < 400 ? "a'lo" : lat < 1000 ? "yaxshi" : "sekin" },
    ];
  }
  function renderMetrics() {
    const defs = meterDefs();
    $("latency").textContent = defs[3].value;
    const side = $("sideMeters");
    if (side.children.length !== defs.length) {
      side.innerHTML = defs.map((d) =>
        '<div class="nx-meter"><div class="hd"><span class="lbl">' + esc(d.label) + '</span><span class="val"></span></div>' +
        '<div class="track"><div class="fill ' + d.cls + '"></div></div><span class="sub"></span></div>').join("");
    }
    const big = $("bigMeters");
    if (big.children.length !== defs.length) {
      big.innerHTML = defs.map((d) =>
        '<div class="nx-mcard"><span class="lbl">' + esc(d.label) + '</span><span class="val"></span>' +
        '<div class="track"><div class="fill ' + d.cls + '"></div></div><span class="sub"></span></div>').join("");
    }
    [side, big].forEach((host) => {
      defs.forEach((d, i) => {
        const el = host.children[i];
        el.querySelector(".val").textContent = d.value;
        el.querySelector(".fill").style.width = clamp(d.pct, 0, 100) + "%";
        el.querySelector(".sub").textContent = d.sub;
      });
    });
    renderStats();
  }
  function renderStats() {
    const m = S.metrics || {};
    const uptime = typeof m.uptime_s === "number" ? m.uptime_s : (Date.now() - S.sessionStart) / 1000;
    const succ = S.toolCount ? Math.round((S.toolOk / S.toolCount) * 100) + "%" : "—";
    const stats = [
      { label: "Tool chaqiruvlari", value: String(S.toolCount) },
      { label: "Muvaffaqiyat", value: succ },
      { label: "Sessiya vaqti", value: fmtDur(uptime) },
      { label: "Xabarlar", value: String(S.msgCount) },
      { label: "Gemini qayta ulanishlar", value: String(typeof m.reconnects === "number" ? m.reconnects : S.geminiReconnects) },
      { label: "Tushib qolgan audio", value: typeof m.audio_dropped === "number" ? String(m.audio_dropped) : "—" },
      { label: "UI qayta ulanishlar", value: String(S.wsReconnects) },
    ];
    const host = $("stats");
    if (host.children.length !== stats.length) {
      host.innerHTML = stats.map((s) => '<div class="nx-scard"><span class="lbl">' + esc(s.label) + '</span><span class="val"></span></div>').join("");
    }
    stats.forEach((s, i) => { host.children[i].querySelector(".val").textContent = s.value; });
  }

  // ── Render: o'ng panel kartalari ──────────────────────────────────
  function renderCards() {
    const g = S.conn.gemini;
    const dot = $("cardGeminiDot");
    dot.className = "dot " + (g === "connected" ? "" : g === "reconnecting" ? "amber" : "red");
    $("cardGeminiName").textContent = "Gemini Live" + (g === "connected" ? " · Faol" : g === "reconnecting" ? " · Qayta ulanmoqda" : " · Uzilgan");
    $("cardGeminiSub").textContent = S.conn.detail ? short(S.conn.detail, 40) : (g === "connected" ? "native audio · real vaqt" : "ulanish kutilmoqda");
    const dev = S.devices.find((d) => d.index === S.currentDevice) || S.devices.find((d) => d.default);
    const pb = S.settings.playback == null ? "—" : S.settings.playback ? "yoniq" : "o'chiq";
    $("cardAudioSub").textContent = "mikrofon: " + (dev ? short(dev.name, 18) : "—") + " · playback: " + pb;
    $("cardAudioDot").className = "dot " + (S.settings.muted ? "red" : "violet");
  }

  function renderDevices() {
    const dev = S.devices.find((d) => d.index === S.currentDevice) || S.devices.find((d) => d.default);
    $("deviceName").textContent = dev ? dev.name : (S.devices.length ? "Qurilma tanlang" : "Qurilma tanlanmagan");
    const list = $("deviceList");
    list.hidden = !S.devicesOpen;
    if (!S.devices.length) {
      list.innerHTML = '<div class="nx-empty" style="padding:10px;">Qurilmalar ro\'yxati bo\'sh</div>';
      return;
    }
    list.innerHTML = S.devices.map((d) => {
      const sel = S.currentDevice != null ? d.index === S.currentDevice : !!d.default;
      return '<button type="button" class="nx-devitem' + (sel ? " sel" : "") + '" data-idx="' + d.index + '">' +
        '<span class="nm">' + esc(d.name) + (d.default ? "<small>standart</small>" : "") + '</span><span class="chk">✓</span></button>';
    }).join("");
  }

  function renderSuggestions() {
    $("suggestions").innerHTML = SUGGESTIONS.map((s) => '<button type="button" data-text="' + esc(s) + '">' + esc(short(s, 34)) + "</button>").join("");
    $("triggers").innerHTML = TRIGGERS.map((t, i) => '<div class="nx-trigger" data-i="' + i + '"><span class="l">' + esc(typeof t.label === "function" ? t.label() : t.label) + "</span><code>" + esc(t.key) + "</code></div>").join("");
  }

  // ── Render: pastki panel ──────────────────────────────────────────
  // PTT/mute/diktovka tugmalari pastki paneldan olib tashlangan (tizim avtomatik: VAD doim yoqiq,
  // PTT default o'chiq). Boshqaruv sozlamalar popover'ida (⚙) va menyu bar'da. Hammasi null-safe.
  function renderPTT() {
    const btn = $("pttBtn"), lbl = $("pttLabel");
    if (btn && lbl) {
      const active = S.pttPressed || (!S.settings.ptt && S.state === "listening");
      btn.classList.toggle("on", active);
      if (S.pttPressed) lbl.textContent = "Tinglamoqda… qo'yib yuboring";
      else if (S.settings.ptt) lbl.textContent = "Bosib turing va gapiring";
      else lbl.textContent = S.state === "listening" ? "Tinglamoqda (avto)" : "Gapirish uchun bosib turing";
    }
    const seg = $("modeSeg");
    if (seg) seg.querySelectorAll("button").forEach((b) => b.classList.toggle("active", (b.dataset.mode === "ptt") === S.settings.ptt));
  }
  function renderMute() {
    const m = S.settings.muted;
    const btn = $("muteBtn"), lbl = $("muteLabel"), ico = $("muteIcon");
    if (btn) btn.classList.toggle("on", m);
    if (lbl) lbl.textContent = m ? "Ovoz o'chiq" : "Mikrofon yoniq";
    if (ico) ico.setAttribute("d", m ? "M11 5L6 9H2v6h4l5 4V5zM22 9l-6 6M16 9l6 6" : "M11 5L6 9H2v6h4l5 4V5zM15.5 8.5a5 5 0 010 7M18.5 5.5a9 9 0 010 13");
    const t = $("setMute"), sub = $("setMuteSub");
    if (t) t.classList.toggle("on", !m);
    if (sub) sub.textContent = (m ? "o'chiq" : "yoniq") + " · ⌥M";
    renderLevel();
  }
  function renderSens() {
    const v = Math.round(S.settings.sensitivity * 100);
    const fill = $("sensFill"), knob = $("sensKnob"), val = $("sensValue"), sl = $("sensSlider");
    if (fill) fill.style.width = v + "%";
    if (knob) knob.style.left = "calc(" + v + "% - 7px)";
    if (val) val.textContent = String(v);
    if (sl) sl.setAttribute("aria-valuenow", String(v));
  }
  function renderSettingsPanel() {
    const pb = $("setPlayback");
    pb.classList.toggle("on", S.settings.playback === true);
    $("setPlaybackSub").textContent = S.settings.playback == null ? "javob ovozini ijro etish" : S.settings.playback ? "yoniq · javob ovozi eshitiladi" : "o'chiq · faqat matn";
    const nameEl = $("setName");
    if (document.activeElement !== nameEl) nameEl.value = S.settings.name || "";
    $("wakeSeg").querySelectorAll("button").forEach((b) => b.classList.toggle("active", b.dataset.wake === S.settings.wake_mode));
    $("setWakeSub").textContent = S.settings.wake_mode === "always" ? "doim tinglaydi" : S.settings.wake_mode === "name" ? "faqat “Hey " + (S.settings.name || "Nexus") + "” dan keyin" : S.settings.wake_mode === "smart" ? "ism yoki aniq buyruq" : "qachon tinglaydi";
    $("setAnim").classList.toggle("on", S.anim);
    $("setSeconds").classList.toggle("on", S.showSeconds);
    $("setStateSub").textContent = "holat: " + (LABEL[S.state] || S.state) + " · gemini: " + S.conn.gemini;
    document.body.classList.toggle("no-anim", !S.anim);
  }

  function renderTabs() {
    document.querySelectorAll(".nx-tab").forEach((b) => b.classList.toggle("active", b.dataset.tab === S.tab));
    ["stream", "history", "metrics"].forEach((t) => { $("tab-" + t).hidden = t !== S.tab; });
  }

  function renderAll() {
    renderConn(); renderState(); renderTranscript(); renderToolLog(); renderHistory(); renderMetrics();
    renderCards(); renderDevices(); renderPTT(); renderMute(); renderSens(); renderSettingsPanel(); renderTabs(); renderShellLabel();
    renderDict(); renderSuggestions(); renderConfirm();
  }

  function renderDict() {
    const on = !!S.settings.dictating || S.state === "dictating";
    const btn = $("dictBtn"), lbl = $("dictLabel"), t = $("setDict"), sub = $("setDictSub");
    if (btn) btn.classList.toggle("on", on);
    if (lbl) lbl.textContent = on ? "Diktovka faol" : "Diktovka";
    if (t) t.classList.toggle("on", on);
    if (sub) sub.textContent = on ? "faol · nutq matnga yozilmoqda" : "nutqni matnga yozish";
  }
  function toggleDictation() {
    const v = !(S.settings.dictating || S.state === "dictating");
    S.settings.dictating = v; renderDict();
    send("dictation", { value: v }).then((r) => { if (r && r.ok) toast(v ? "Diktovka yoqildi" : "Diktovka o'chirildi", "ok"); });
  }

  // ── Tasdiq kartasi ────────────────────────────────────────────────
  function setConfirm(d) {
    clearInterval(S.confirmTimer); S.confirmTimer = null;
    if (!d || !d.token) { S.confirm = null; renderConfirm(); return; }
    const ttl = Math.max(1, Number(d.ttl_s) || 30);
    S.confirm = { token: d.token, action: d.action || "", summary: d.summary || "", reason: d.reason || "", ttl, deadline: Date.now() + ttl * 1000 };
    renderConfirm();
    S.confirmTimer = setInterval(() => {
      if (!S.confirm) { clearInterval(S.confirmTimer); return; }
      if (Date.now() >= S.confirm.deadline) { setConfirm(null); return; }
      renderConfirm();
    }, 250);
  }
  function renderConfirm() {
    const card = $("confirmCard");
    const c = S.confirm;
    card.hidden = !c;
    if (!c) return;
    const left = Math.max(0, (c.deadline - Date.now()) / 1000);
    $("confirmAction").textContent = c.action || "amal";
    $("confirmSummary").textContent = c.summary || "";
    $("confirmReason").textContent = c.reason ? "Sabab: " + c.reason : "";
    $("confirmReason").hidden = !c.reason;
    $("confirmTtl").textContent = Math.ceil(left) + " s";
    $("confirmBar").style.width = clamp((left / c.ttl) * 100, 0, 100) + "%";
    card.classList.toggle("expiring", left < 5);
  }
  function answerConfirm(approve) {
    const c = S.confirm; if (!c) return;
    send("confirm", { token: c.token, approve: !!approve }).then((r) => {
      if (r && r.ok) { setConfirm(null); }
    });
  }

  // ── Toast ─────────────────────────────────────────────────────────
  function toast(text, kind) {
    if (!text) return;
    const host = $("toasts");
    const el = document.createElement("div");
    el.className = "nx-toast " + (kind || "");
    el.textContent = short(text, 220);
    host.appendChild(el);
    while (host.children.length > 4) host.removeChild(host.firstChild);
    setTimeout(() => { el.style.transition = "opacity .3s"; el.style.opacity = "0"; setTimeout(() => el.remove(), 320); }, kind === "err" ? 6000 : 3500);
  }

  // ── Buyruqlar ─────────────────────────────────────────────────────
  function sendText(text) {
    text = (text || "").trim();
    if (!text) return;
    S.transcript = text; S.transcriptFinal = true; S.lastUserFinal = text; S.lastUserFinalTs = Date.now() / 1000; S.assistantText = "";
    renderTranscript();
    send("text", { value: text }).then((r) => { if (r && r.ok) toast("Yuborildi: " + short(text, 60), "ok"); });
  }
  function toggleMute() {
    S.settings.muted = !S.settings.muted; renderMute(); renderCards();
    send("mute", { value: S.settings.muted });
  }
  function killAll() {
    send("kill_all").then((r) => { if (r && r.ok) toast("Barcha bajarilayotgan toollar to'xtatildi", "ok"); });
  }
  function setPttMode(on) {
    if (S.settings.ptt === on) return;
    S.settings.ptt = on; renderPTT();
    send("ptt", { value: on });
  }
  function pttDown() {
    if (S.pttPressed) return;
    S.pttPressed = true; renderPTT();
    if (!S.settings.ptt) setPttMode(true);
    send("ptt_press", { value: true });
  }
  function pttUp() {
    if (!S.pttPressed) return;
    S.pttPressed = false; renderPTT();
    send("ptt_press", { value: false });
  }

  let sensSendTimer = null, sensDragging = false;
  function setSensFromEvent(ev, commit) {
    const r = $("sensSlider").getBoundingClientRect();
    const v = clamp((ev.clientX - r.left) / r.width, 0, 1);
    S.settings.sensitivity = v; renderSens();
    if (commit) { clearTimeout(sensSendTimer); send("sensitivity", { value: Number(v.toFixed(3)) }); }
    else if (!sensSendTimer) sensSendTimer = setTimeout(() => { sensSendTimer = null; send("sensitivity", { value: Number(S.settings.sensitivity.toFixed(3)) }); }, 120);
  }

  // ── Hodisa tinglovchilar ──────────────────────────────────────────
  function bind() {
    document.querySelectorAll(".nx-tab").forEach((b) => b.addEventListener("click", () => { S.tab = b.dataset.tab; lsSet("nx.tab", S.tab); renderTabs(); }));

    $("filters").addEventListener("click", (e) => { const b = e.target.closest("[data-f]"); if (b) { S.filter = b.dataset.f; renderToolLog(); } });
    $("suggestions").addEventListener("click", (e) => { const b = e.target.closest("[data-text]"); if (b) sendText(b.dataset.text); });
    $("triggers").addEventListener("click", (e) => { const t = e.target.closest("[data-i]"); if (t) { const tr = TRIGGERS[+t.dataset.i]; if (tr && tr.action) tr.action(); } });
    $("histSearch").addEventListener("input", renderHistory);

    // Qurilma dropdown
    $("deviceBtn").addEventListener("click", (e) => {
      e.stopPropagation();
      S.devicesOpen = !S.devicesOpen;
      if (S.devicesOpen && !S.devices.length) send("list_devices", null, true);
      renderDevices();
    });
    $("deviceList").addEventListener("click", (e) => {
      const b = e.target.closest("[data-idx]"); if (!b) return;
      e.stopPropagation();
      const idx = parseInt(b.dataset.idx, 10);
      S.currentDevice = idx; S.devicesOpen = false; renderDevices(); renderCards();
      send("set_device", { index: idx }).then((r) => { if (r && r.ok) toast("Mikrofon o'zgartirildi", "ok"); });
    });

    // Sozlamalar
    $("settingsBtn").addEventListener("click", (e) => {
      e.stopPropagation();
      const p = $("settingsPanel"); p.hidden = !p.hidden; $("settingsBtn").classList.toggle("active", !p.hidden);
      if (!p.hidden) renderSettingsPanel();
    });
    $("settingsPanel").addEventListener("click", (e) => e.stopPropagation());
    $("setAnim").addEventListener("click", () => { S.anim = !S.anim; lsSet("nx.anim", S.anim); renderSettingsPanel(); });
    $("setSeconds").addEventListener("click", () => { S.showSeconds = !S.showSeconds; lsSet("nx.seconds", S.showSeconds); renderSettingsPanel(); renderClock(); });
    $("confirmYes").addEventListener("click", () => answerConfirm(true));
    $("confirmNo").addEventListener("click", () => answerConfirm(false));
    if ($("dictBtn")) $("dictBtn").addEventListener("click", toggleDictation);
    if ($("setDict")) $("setDict").addEventListener("click", toggleDictation);
    if ($("setMute")) $("setMute").addEventListener("click", toggleMute);
    $("setPlayback").addEventListener("click", () => {
      const v = !(S.settings.playback === true);
      S.settings.playback = v; renderSettingsPanel(); renderCards();
      send("playback", { value: v });
    });
    const commitName = () => {
      const v = $("setName").value.trim();
      if (!v || v === S.settings.name) { $("setName").value = S.settings.name || ""; return; }
      S.settings.name = v; renderSettingsPanel(); renderSuggestions(); renderTranscript();
      send("set_name", { value: v }).then((r) => { if (r && r.ok) toast("Ism o'zgartirildi: " + v, "ok"); });
    };
    $("setName").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); commitName(); e.target.blur(); } e.stopPropagation(); });
    $("setName").addEventListener("blur", commitName);
    $("wakeSeg").addEventListener("click", (e) => {
      const b = e.target.closest("[data-wake]"); if (!b) return;
      S.settings.wake_mode = b.dataset.wake; renderSettingsPanel();
      send("wake_mode", { value: b.dataset.wake });
    });
    $("setReconnect").addEventListener("click", () => {
      // Eski soket identity bilan yopiladi (closeSocket) — uning onclose'i qayta reconnect rejalashtirmaydi
      S.manualClose = true; closeSocket("manual"); S.wsAttempt = 0; renderConn();
      S.wsTimer = setTimeout(() => connect(true), 150);
    });
    $("setRefresh").addEventListener("click", () => { send("get_state"); send("list_devices", null, true); });
    document.addEventListener("click", () => {
      if (S.devicesOpen) { S.devicesOpen = false; renderDevices(); }
      const p = $("settingsPanel"); if (!p.hidden) { p.hidden = true; $("settingsBtn").classList.remove("active"); }
    });

    // PTT (faqat elementlar mavjud bo'lsa — hozirgi dizaynda yo'q)
    const ptt = $("pttBtn");
    if (ptt) {
      ptt.addEventListener("pointerdown", (e) => { e.preventDefault(); ptt.setPointerCapture(e.pointerId); pttDown(); });
      ["pointerup", "pointercancel"].forEach((t) => ptt.addEventListener(t, () => pttUp()));
      ptt.addEventListener("contextmenu", (e) => e.preventDefault());
    }
    if ($("modeSeg")) $("modeSeg").addEventListener("click", (e) => { const b = e.target.closest("[data-mode]"); if (b) setPttMode(b.dataset.mode === "ptt"); });

    if ($("muteBtn")) $("muteBtn").addEventListener("click", toggleMute);
    if ($("killBtn")) $("killBtn").addEventListener("click", killAll);

    // Sezgirlik slayderi (sozlamalar panelida)
    const sl = $("sensSlider");
    if (sl) sl.addEventListener("pointerdown", (e) => { sensDragging = true; sl.setPointerCapture(e.pointerId); setSensFromEvent(e, false); });
    if (sl) sl.addEventListener("pointermove", (e) => { if (sensDragging) setSensFromEvent(e, false); });
    if (sl) ["pointerup", "pointercancel"].forEach((t) => sl.addEventListener(t, (e) => { if (sensDragging) { sensDragging = false; setSensFromEvent(e, true); } }));
    if (sl) sl.addEventListener("keydown", (e) => {
      const step = e.key === "ArrowLeft" ? -0.02 : e.key === "ArrowRight" ? 0.02 : 0;
      if (!step) return;
      e.preventDefault();
      S.settings.sensitivity = clamp(S.settings.sensitivity + step, 0, 1); renderSens();
      clearTimeout(sensSendTimer); sensSendTimer = setTimeout(() => { sensSendTimer = null; send("sensitivity", { value: Number(S.settings.sensitivity.toFixed(3)) }); }, 200);
    });

    // Matn kiritish
    $("textInput").addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); sendText(e.target.value); e.target.value = ""; }
    });

    // Klaviatura: ⌥M = mute, ⌥Esc = kill_all (⌥Space PTT olib tashlandi — PTT rejimi UI'da yo'q)
    window.addEventListener("keydown", (e) => {
      if (!e.altKey) return;
      if (e.code === "KeyM") { e.preventDefault(); toggleMute(); }
      else if (e.code === "Escape") { e.preventDefault(); killAll(); }
      else if (e.code === "KeyY") { if (S.confirm) { e.preventDefault(); answerConfirm(true); } }
      else if (e.code === "KeyN") { if (S.confirm) { e.preventDefault(); answerConfirm(false); } }
    });
    window.addEventListener("blur", () => { if (S.pttPressed) pttUp(); });

    // Desktop (WKWebView): sarlavha panelidan oynani surish / ikki marta bosib kattalashtirish.
    // -webkit-app-region WKWebView'da ishlamaydi — nexus/desktop.py `performWindowDragWithEvent:` chaqiradi.
    const native = window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.nexus;
    const bar = document.querySelector(".nx-titlebar");
    if (native && bar) {
      const isControl = (el) => !!el.closest("button, input, select, a, .nx-settings, .nx-badge");
      bar.addEventListener("mousedown", (e) => { if (e.button === 0 && !isControl(e.target)) native.postMessage({ type: "drag" }); });
      bar.addEventListener("dblclick", (e) => { if (!isControl(e.target)) native.postMessage({ type: "zoom" }); });
    }
  }

  // ── Ishga tushirish ───────────────────────────────────────────────
  function init() {
    // Kirish darajasi ustunlari (agar elementi bo'lsa — hozirgi dizaynda pastki panelda yo'q)
    if ($("levelBars")) $("levelBars").innerHTML = new Array(26).fill("<span></span>").join("");
    renderSuggestions();
    bind();
    renderAll();
    renderClock();
    setInterval(() => { renderClock(); if (S.tab === "metrics") renderStats(); }, 1000);
    connect();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();

  // Diagnostika uchun
  window.NEXUS = { state: S, send, connect };
})();
