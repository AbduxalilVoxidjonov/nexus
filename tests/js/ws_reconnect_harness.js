// ui/app.js ni soxta DOM + soxta WebSocket bilan yuklaydi va "Qayta ulanish" oqimini tekshiradi.
// Ishlatish: node tests/js/ws_reconnect_harness.js ui/app.js  → JSON natija (tests/test_server.py chaqiradi).
// Regressiya: eski soketning kech kelgan onclose'i (identity tekshiruvisiz) S.ws=null qilib
// ikkinchi reconnect rejalashtirar, natijada ikkita jonli WS paydo bo'lardi.
const fs = require("fs");
const src = fs.readFileSync(process.argv[2], "utf8");

const listeners = new Map(); // id -> {event: [fn]}
function makeEl(id) {
  const store = { id, hidden: false, textContent: "", innerHTML: "", value: "", dataset: {}, style: {} };
  const cls = { add() {}, remove() {}, toggle() {}, contains() { return false; } };
  return new Proxy(store, {
    get(t, k) {
      if (k === "classList") return cls;
      if (k === "addEventListener") return (ev, fn) => { const m = listeners.get(id) || {}; (m[ev] = m[ev] || []).push(fn); listeners.set(id, m); };
      if (k === "querySelectorAll") return () => [];
      if (k === "querySelector") return () => makeEl(id + "/q");
      if (k === "closest") return () => null;
      if (k === "children") return new Proxy([], { get: (a, i) => (typeof i === "string" && /^\d+$/.test(i)) ? makeEl(id + "/c" + i) : a[i] });
      if (k === "getBoundingClientRect") return () => ({ width: 100, height: 100, left: 0, top: 0 });
      if (k in t) return t[k];
      if (typeof k === "string" && /^(focus|blur|click|scrollTo|scrollIntoView|setAttribute|removeAttribute|appendChild|remove|select|play|pause)$/.test(k)) return () => {};
      return undefined;
    },
    set(t, k, v) { t[k] = v; return true; },
  });
}
const els = new Map();
const byId = (id) => { if (!els.has(id)) els.set(id, makeEl(id)); return els.get(id); };

global.document = {
  readyState: "complete",
  getElementById: byId,
  querySelector: () => null,
  querySelectorAll: () => [],
  addEventListener: () => {},
  createElement: () => makeEl("_tmp"),
  body: makeEl("body"),
  documentElement: makeEl("html"),
  hidden: false,
};
global.window = global; global.addEventListener = () => {}; global.removeEventListener = () => {};
global.location = { protocol: "http:", host: "127.0.0.1:8765", hash: "" };
global.localStorage = { getItem: () => null, setItem() {}, removeItem() {} };
global.navigator = { userAgent: "node", platform: "MacIntel" };
global.performance = global.performance || { now: () => Date.now() };
global.requestAnimationFrame = (fn) => setTimeout(fn, 0);
global.matchMedia = () => ({ matches: false, addEventListener() {} });

const sockets = [];
class FakeWS {
  constructor(url) {
    this.url = url; this.readyState = FakeWS.CONNECTING; this.closeCalls = 0;
    this.onopen = this.onclose = this.onmessage = this.onerror = null;
    sockets.push(this);
  }
  close() { this.closeCalls += 1; if (this.readyState !== FakeWS.CLOSED) this.readyState = FakeWS.CLOSING; }
  send() {}
  // test yordamchilari
  _open() { this.readyState = FakeWS.OPEN; if (this.onopen) this.onopen({}); }
  _closed() { this.readyState = FakeWS.CLOSED; if (this.onclose) this.onclose({}); }
}
FakeWS.CONNECTING = 0; FakeWS.OPEN = 1; FakeWS.CLOSING = 2; FakeWS.CLOSED = 3;
global.WebSocket = FakeWS;

new Function(src)();  // IIFE: init() darhol (readyState=complete), connect() → ws#1
const S = window.NEXUS.state;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const out = {};
  sockets[0]._open();
  out.first_open = S.ws === sockets[0] && S.wsOpen === true;
  // "Qayta ulanish" tugmasi
  const h = (listeners.get("setReconnect") || {}).click;
  if (!h) { console.log(JSON.stringify({ error: "setReconnect handler yo'q" })); process.exit(2); }
  h[0]({});
  await sleep(250);                 // 150 ms → connect(true) → ws#2
  out.sockets_after_click = sockets.length;
  out.old_closed_called = sockets[0].closeCalls >= 1;
  // Eski soketning onclose'i KECH keladi (brauzerda har doim shunday)
  sockets[0]._closed();
  sockets[1]._open();
  await sleep(1800);                // scheduleReconnect (≥1 s) ishlagan bo'lsa ws#3 paydo bo'ladi
  out.sockets_total = sockets.length;
  out.live = sockets.filter((s) => s.readyState === FakeWS.OPEN || s.readyState === FakeWS.CONNECTING).length;
  out.current_is_second = S.ws === sockets[1];
  out.ws_open = S.wsOpen;
  console.log(JSON.stringify(out));
  process.exit(0);
})();
