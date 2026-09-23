# Nexus Ovoz OS

Gemini Live API asosidagi **macOS uchun o'zbekcha ovozli yordamchi daemon**. Mikrofon ovozi
to'g'ridan-to'g'ri Gemini'ga oqim sifatida yuboriladi, model javobni ovoz bilan qaytaradi va
kerak bo'lsa toollar orqali Mac'ni boshqaradi: dasturlarni ochish, ovoz/yorug'lik, brauzer,
YouTube, fayl va Excel, ekrandagi tugmalarni bosish, matn terish, diktovka.

Kirish tili — o'zbek, rus yoki ingliz (avtomatik); javob tili — foydalanuvchi gapirgan til
(asosiysi o'zbek lotin). Qisqa, iliq, tasdiq talab qiladigan amallarda ehtiyotkor.

---

## Arxitektura

```
 Mikrofon ──▶ AudioStreamer ──▶ GeminiLiveClient ──▶ Gemini Live API (WebSocket)
 (sounddevice)  RMS/gate/echo       │   ▲                   │
                                     │   │ tool natijasi     │ audio + transkript + tool_call
                                     ▼   │                   ▼
                              ToolRegistry ◀──────── _receive() ──▶ AudioPlayer ──▶ Dinamik
                       loop guard → taint → tasdiq → handler
                          │            │
              ┌───────────┴────────┐   └─ ConfirmationGate (og'zaki "ha" / UI tugmasi)
              ▼                    ▼
   macos_actions / browser_actions   kengaytmalar: file_actions, ax_actions
              │
              ▼
        EventBus (events.py) ──▶ server.py (FastAPI + WebSocket /ws) ──▶ ui/ (brauzer paneli)
```

| Modul | Vazifa |
|---|---|
| `nexus/main.py` | CLI kirish nuqtasi (`nexus`), daemon hayot sikli, metrikalar, `--check` |
| `nexus/config.py` | `.env` dan o'qiladigan `Settings` dataclass |
| `nexus/events.py` | Thread-safe `EventBus`: hodisalar (pub/sub) + UI buyruqlari (`dispatch_command`) |
| `nexus/audio_streamer.py` | Mikrofon oqimi (16 kHz PCM), RMS gate, PTT/mute, echo guard; `AudioPlayer` (24 kHz ijro, prebuffer) |
| `nexus/gemini_live_client.py` | Live sessiya: `send_realtime_input`, `receive()`, tool chaqiruvlarini alohida task'da bajarish, eksponensial backoff bilan qayta ulanish, session resumption |
| `nexus/tools/schemas.py` | Gemini `FunctionDeclaration` lug'atlari (tizim + brauzer) va `SYSTEM_INSTRUCTION` |
| `nexus/tools/registry.py` | `ToolRegistry`: validatsiya, timeout, loop guard, taint, tasdiq darvozasi, kengaytma modullarini yuklash |
| `nexus/macos_actions.py` | AppleScript/shell orqali macOS amallari, `CommandGuard` (terminal allowlist), ruxsat tekshiruvi |
| `nexus/browser_actions.py` | Safari/Chrome: tablar, DOM klik, sahifa matni, qidiruv natijalari, YouTube pleer |
| `nexus/file_actions.py` | Fayl/eslatma/Excel/CSV toollari (kengaytma) |
| `nexus/ax_actions.py` | macOS Accessibility (AX) toollari: elementlar ro'yxati, klik, ekran matni, menyular (kengaytma) |
| `nexus/safety.py` | `DANGEROUS_SHELL`, `path_is_sensitive`, `redact_secrets`, `ConfirmationGate`, `TaintTracker`, `LoopGuard` |
| `nexus/wake.py` | Ism bilan chaqirish (`always` / `name` / `smart`), Levenshtein bilan yumshoq moslik, follow-up oynasi |
| `nexus/dictation.py` | Diktovka rejimi: transkript to'g'ridan-to'g'ri teriladi, to'xtash iboralari |
| `nexus/server.py` | FastAPI: `/` (UI), `/health`, `/api/state`, `/ws` |
| `ui/` | Brauzer paneli (`index.html`, `app.js`, `styles.css`): holat, transkript, tool jurnali, sozlamalar, tasdiq tugmasi |
| `scripts/` | `check_setup.py`, `benchmark_live.py`, `voice_picker.py` |
| `tests/` | pytest (`asyncio_mode = auto`) |

---

## O'rnatish

Talablar: macOS, Python 3.11+ (loyiha 3.13 bilan sinalgan), [uv](https://docs.astral.sh/uv/), Gemini API kaliti.

```bash
cd nexus
uv venv --python 3.13
uv pip install -e ".[dev]"
cp .env.example .env        # so'ng GEMINI_API_KEY ni yozing
```

`pyproject.toml` bog'liqliklari: `google-genai`, `sounddevice`, `numpy`, `fastapi`, `uvicorn`,
`websockets`, `python-dotenv`, `psutil`, `openpyxl` (Excel), `pyobjc-framework-Cocoa/Quartz/ApplicationServices/WebKit`
(AX toollari va desktop oynasi). Dev: `pytest`, `pytest-asyncio`, `ruff`, `pyinstaller`.

### `.env` sozlamalari (asosiylari)

| O'zgaruvchi | Standart | Izoh |
|---|---|---|
| `GEMINI_API_KEY` | — | majburiy |
| `GEMINI_MODEL` | `gemini-2.5-flash-native-audio-preview-09-2025` | Live (native audio) modeli |
| `GEMINI_VOICE` | `Aoede` | 30 ta ovozdan biri (`scripts/voice_picker.py` bilan tanlang) |
| `INPUT_DEVICE` | bo'sh | mikrofon nomi yoki indeksi |
| `VAD_THRESHOLD` | `0.02` | lokal RMS bo'sag'asi (UI'dagi sezgirlik slayderi shuni boshqaradi) |
| `ECHO_GUARD` / `ECHO_BARGE_FACTOR` | `true` / `3.0` | yordamchi gapirayotganda mikrofonni bostirish; barge-in bo'sag'asi |
| `PLAYBACK_PREBUFFER_MS` | `220` | ijrodan oldingi jitter-bufer |
| `VAD_START_SENSITIVITY` / `VAD_END_SENSITIVITY` | `LOW` / `HIGH` | Gemini server-VAD (HIGH start — o'z ovozini eshitib qoladi) |
| `TRANSCRIPTION_LANGUAGES` | `uz-UZ,ru-RU,en-US` | kiruvchi transkripsiya tillari |
| `SESSION_RESUMPTION` / `CONTEXT_COMPRESSION` | `true` | uzoq sessiyalar uchun |
| `WAKE_NAME` / `WAKE_MODE` / `WAKE_FOLLOW_UP_S` | `Nexus` / `always` / `25` | ism bilan chaqirish |
| `UI_HOST` / `UI_PORT` / `SERVE_UI` | `127.0.0.1` / `8765` / `true` | UI ko'prigi |
| `ALLOW_TERMINAL` | `true` | `run_terminal_command` yoqilganmi |
| `SCREENSHOT_DIR` | `~/Desktop` | skrinshot papkasi |
| `DEFAULT_BROWSER` | `chrome` | `safari` yoki `chrome` (foydalanuvchi aytmasa) |
| `DND_SHORTCUT_ON` / `DND_SHORTCUT_OFF` | `Nexus DND On` / `Nexus DND Off` | Shortcuts nomlari |
| `NEXUS_DEFAULT_DIR` | `~/Desktop` | fayl toollarida nisbiy yo'l uchun standart papka |

---

## macOS ruxsatlari

Ruxsatlar **Nexus ishga tushirilgan dasturga** (Terminal, iTerm, VS Code ...) beriladi:
System Settings → Privacy & Security.

| Ruxsat | Nima uchun kerak |
|---|---|
| **Microphone** | ovoz oqimi (birinchi ishga tushishda so'raladi) |
| **Accessibility** | `type_text`, `press_hotkey`, AX toollari (`list_ui_elements`, `click_ui_element`, `read_screen_text`, `menu_command`, `set_text_field`), yorug'lik klavishlari |
| **Screen & System Audio Recording** | `take_screenshot` |
| **Automation → System Events, Finder, Safari/Chrome, Spotify/Music** | AppleScript orqali boshqaruv (birinchi chaqiruvda so'raladi) |
| **Safari: Develop → "Allow JavaScript from Apple Events"** | brauzer DOM toollari (`browser_click_button`, `browser_read_page`, `youtube_control` ...) |
| **Chrome: View → Developer → "Allow JavaScript from Apple Events"** | xuddi shu, Chrome uchun |
| **Shortcuts: "Nexus DND On" / "Nexus DND Off"** | `set_do_not_disturb` — Focus'ni yoqadigan/o'chiradigan ikki Shortcut yarating |

Tekshirish: `.venv/bin/python scripts/check_setup.py` (yoki `nexus --check`).

---

## Ishga tushirish

### Desktop ilova (asosiy yo'l — brauzer ochilmaydi)

Finder'da **`start.command`** ni ikki marta bosing (yoki terminalda `zsh start.command`). Skript:
`.venv` yo'q bo'lsa `uv venv --python 3.13 && uv pip install -e .` qiladi, `.env` yo'q bo'lsa
`.env.example` dan nusxalab ogohlantiradi, allaqachon ishlayotgan nusxa bo'lsa pid'ini ko'rsatadi,
so'ng `python -m nexus.main` ni ishga tushiradi. To'xtatish: menyu bar → ◉ → **Chiqish**, `Cmd+Q`,
yoki **`stop.command`** (SIGINT → 3 s → SIGKILL).

```bash
.venv/bin/python -m nexus.main        # desktop: o'z oynasi + orb + menyu bar (daemon shu jarayonda)
nexus                                 # xuddi shu (`.venv/bin/nexus`)
nexus --no-orb                        # desktop, orb overlay'siz
nexus --no-window                     # desktop, asosiy oynasiz (menyu bar + orb; oyna menyudan/orbdan ochiladi)
NEXUS_HIDE_DOCK=true nexus            # Dock'da ko'rinmaydi (faqat menyu bar)
nexus --headless                      # eski rejim: oynasiz daemon + web UI → http://127.0.0.1:8765
nexus --no-ui                         # faqat ovoz (UI serveri ham yo'q)
nexus --no-playback                   # javob ovozini ijro etmaslik
nexus --device "MacBook Pro Microphone"
nexus --list-devices                  # mikrofonlar ro'yxati
nexus --check                         # ruxsat va konfiguratsiya tekshiruvi
nexus --text "Safari ni och"          # bir martalik matn buyrug'i (mikrofonsiz, headless)
nexus --log-level DEBUG
```

Desktop qatlami (`nexus/desktop.py`) — sof pyobjc (AppKit + WebKit), `pywebview` ishlatilmaydi:

* **Oyna** — `NSWindow` (`titlebarAppearsTransparent`, `titleVisibility=hidden`, `fullSizeContentView`,
  `FullScreenPrimary` → yashil tugma = to'liq ekran), ichida `WKWebView` `http://127.0.0.1:8765/` ni
  ko'rsatadi. Standart o'lcham — ekranning 90 %, min 900×640; o'lcham/pozitsiya `~/.nexus/desktop.json`
  da saqlanadi. Qizil tugma oynani **yashiradi** (dastur ishlayveradi); qaytarish — menyu bar,
  Dock ikonkasi yoki orb. `Cmd+Q` / "Chiqish" / SIGINT — toza to'xtash.
* **Orb** — ~120×120 ramkasiz shaffof `NSPanel`, doim tepada (`NSFloatingWindowLevel+1`), barcha
  Spaces'da, klaviatura fokusini olmaydi (`canBecomeKeyWindow=False`, non-activating). Holat rangi,
  mikrofon amplitudasi va kichik yorliq (`ui/orb.html`, WS orqali). Bir marta bosish — oynani
  ko'rsatish/yashirish, ikki marta — mikrofon mute, o'ng tugma — menyu, surish mumkin (pozitsiya saqlanadi).
* **Menyu bar** — ikonka + holat satri; Oynani ko'rsatish, Orb ko'rsatish/yashirish, Mikrofonni
  o'chirish/yoqish, Diktovka, Hammasini to'xtatish, Sozlamalar (`.env` ni Finder'da ko'rsatadi), Chiqish.
* Daemon (`nexus.main.run`) alohida `nexus-daemon` thread'ida o'z asyncio loop'i bilan; GUI asosiy
  thread'da (`performSelectorOnMainThread` orqali hodisalar).

UI: holat indikatori, jonli transkript, tool jurnali, tarix, tizim ko'rsatkichlari, qurilma tanlash,
tasdiq tugmalari; pastda faqat matn kiritish maydoni. Mikrofon mute / diktovka / sezgirlik / playback /
wake rejimi va ism — ⚙ sozlamalar popover'ida (va menyu bar'da). Yorliqlar: `⌥M` mute, `⌥⎋` hammasini
to'xtatish, `⌥Y`/`⌥N` tasdiq. Tizim avtomatik tinglaydi (VAD doim yoqiq, PTT yo'q).

### `.app` yig'ish (ixtiyoriy)

```bash
uv pip install -e ".[dev]"            # pyinstaller
zsh scripts/build_app.sh              # → dist/Nexus Ovoz OS.app (Info.plist: mikrofon/Automation ta'riflari)
```

---

## Tool ro'yxati

Asosiy sxemalar `nexus/tools/schemas.py` da (45 ta), kengaytmalar `nexus/file_actions.py` (10 ta)
va `nexus/ax_actions.py` (7 ta) — jami **62 ta**. Registry kengaytmalarni `EXTENSION_MODULES`
orqali yuklaydi; modul `TOOL_DECLARATIONS` va `HANDLERS` eksport qiladi.

**Tizim (macos_actions):** `launch_app` (fuzzy nom), `list_applications`, `quit_app`, `set_volume`,
`mute_volume`, `volume_step`, `control_media`, `now_playing`, `set_brightness`, `run_terminal_command`,
`take_screenshot`, `get_system_info`, `open_folder`, `open_path`, `send_notification`, `lock_screen`,
`sleep_display`, `toggle_dark_mode`, `set_do_not_disturb`, `get_clipboard`, `set_clipboard`,
`type_text` (clipboard + Cmd+V — o'zbek/kirill buzilmaydi), `press_hotkey`, `list_running_apps`,
`hide_all_windows`, `empty_trash`, `say_text`, `start_dictation`, `stop_dictation`.

**Brauzer (browser_actions, Safari/Chrome):** `browser_open_url`, `browser_switch_tab`,
`browser_close_tab`, `browser_reload`, `browser_current_page`, `browser_list_tabs`, `browser_scroll`,
`browser_click_button`, `browser_click_selector`, `browser_read_page`, `browser_type_and_search`,
`web_search`, `search_get_results`, `search_open_result`, `search_navigate_page`, `youtube_control`.

**Fayl va Excel (file_actions):**

| Tool | Izoh |
|---|---|
| `read_file(path, max_chars=4000)` | matnli faylni o'qish, sirlar redaktsiya qilinadi |
| `write_file(path, content, mode)` | yangi fayl darhol; mavjud faylni `overwrite` — tasdiq bilan; `append` tasdiqsiz |
| `delete_file(path)` | faqat bitta fayl, doim tasdiq, Finder orqali **Savatga** ko'chiradi |
| `list_directory(path?)` | 100 tagacha element, papkalar `/` bilan |
| `write_note(text, file?)` | `~/Documents/nexus_notes.txt` ga `[YYYY-MM-DD HH:MM] matn` |
| `append_spreadsheet_row(values[], file?, sheet?, headers?)` | `.xlsx` (openpyxl) yoki `.csv` (utf-8-sig); standart `~/Documents/nexus.xlsx` |
| `set_spreadsheet_cell(cell, value, file?, sheet?)` | `B7` kabi katak; raqamlar raqam sifatida saqlanadi |
| `read_spreadsheet(file?, sheet?, max_rows=25)` | birinchi qatorlar matn ko'rinishida |
| `find_files(query, folder?, max_results=20)` | Spotlight (`mdfind -onlyin`) |
| `open_with_app(path, app)` | `open -a App fayl` |

Yo'l aliaslari: `desktop` / `ish stoli` / `рабочий стол` → `~/Desktop`; `downloads` / `yuklamalar` /
`загрузки` → `~/Downloads`; `documents` / `hujjatlar` / `документы` → `~/Documents`; `home` → `~`.
Faqat `~`, `/tmp`, `/Volumes` ostidagi yo'llar; sezgir yo'llar (`~/.ssh`, `~/.zshrc`, `.plist`, `.sh` ...) rad etiladi.

**Accessibility (ax_actions):**

| Tool | Izoh |
|---|---|
| `list_ui_elements(filter?, max_items=120)` | oldingi oynadagi tugma/havola/maydonlar: `{n, role, label, at:[x,y], size:[w,h]}` |
| `click_ui_element(label? / index? / x,y?)` | avval `AXPress`, bo'lmasa Quartz sichqoncha bosishi; ko'p mos kelsa `needs_choice` ro'yxati |
| `read_screen_text(max_chars=6000)` | oynaning haqiqiy matni (StaticText/Heading/Link/TextArea) |
| `list_menus()` | menyu paneli va bandlari |
| `menu_command(path)` | `["File","Save"]` yo'li bo'yicha `AXPress` |
| `get_focused_element()` | fokusdagi element (rol, yorliq, qiymat, tahrirlanadimi) |
| `set_text_field(label, text)` | matn maydoniga `AXValue` orqali yozish |

Chrome/Electron ilovalari uchun `AXManualAccessibility` avtomatik yoqiladi (veb-daraxt bir necha
soniyadan keyin to'liq paydo bo'ladi). AX yurishi `asyncio.to_thread` da — audio oqimi to'xtamaydi.

---

## Xavfsizlik modeli

Model "foydalanuvchi rozi bo'ldi" deb aytishiga ishonilmaydi — tasdiq faqat foydalanuvchining
**o'z transkriptidan** (so'rovdan keyin aytilgan qisqa "ha / mayli / bo'ladi / да / yes") yoki
**UI tugmasidan** (`confirm` buyrug'i) olinadi. Token TTL — 60 s (`CONFIRM_REQUEST` / `CONFIRM_RESOLVED`).

`ToolRegistry.execute` oqimi: validatsiya → **loop guard** → **taint** → tasdiq kerakmi →
`ConfirmationGate` → handler → (handler `needs_confirmation` qaytarsa → gate → `confirmed=True` bilan qayta) → taint belgilash.

* **Terminal (`CommandGuard`)** — uch bosqich: `allow` (allowlist: `ls`, `cat`, `grep`, `find`, `df`,
  `ps`, `ping -c`, `curl` GET, `git status/log/diff`, `brew list`, `mkdir`, `cp`, `mv` ... — tez yo'l,
  tasdiqsiz), `deny` (`DANGEROUS_SHELL`: `rm`, `sudo`, `kill`, `chmod`, `curl -o`, `python -c`,
  `osascript`, shell operatorlari `| ; && > $( ` — hech qachon bajarilmaydi), `confirm` (qolgani —
  og'zaki/UI tasdiq). Shell ishlatilmaydi (`create_subprocess_exec`).
* **Doim tasdiq:** `empty_trash`, `delete_file`, `sleep_display`; mavjud fayl ustiga `write_file`;
  sezgir yo'lga yozish; terminal old oynada bo'lsa `type_text` va `press_hotkey` (Enter).
* **Sezgir yo'llar** (`path_is_sensitive`): `~/.ssh`, `~/.gnupg`, `~/.aws`, uy papkasidagi dotfile'lar,
  `LaunchAgents`, `/etc`, `/usr`, `.plist/.sh/.command/.app` ... — o'qish/yozish rad etiladi.
* **Sir redaktsiyasi** (`redact_secrets`): `API_KEY=...`, `token: ...`, `sk-...`, `AIza...`, `ghp_...`,
  `Bearer ...` — fayl, clipboard va ekran matnida `***REDACTED***`.
* **Taint:** navbat ichida tashqi matn o'qilsa (`browser_read_page`, `read_file`, `read_spreadsheet`,
  `read_screen_text`, `list_ui_elements`, `get_clipboard`, `search_get_results` ...), shu navbatda
  "sizdirish yoki bajarish" toollari (`run_terminal_command`, `browser_open_url`, `web_search`,
  `type_text`, `write_file`, `click_ui_element`, `menu_command` ...) tasdiq talab qiladi — prompt
  injection'ga qarshi.
* **Loop guard:** bir navbatda 15 tadan ko'p chaqiruv yoki bir xil argumentlar bilan 3 martadan
  ko'p chaqiruv rad etiladi (modelga sabab tushuntiriladi).
* Tool natijasi 4000 belgigacha qisqartiriladi; har tool uchun 30 s timeout; `kill_all` barcha
  bajarilayotgan toollarni bekor qiladi.

---

## Wake va diktovka rejimlari

**Wake (`nexus/wake.py`)** — gap yordamchiga qaratilganmi?

* `always` — har gapga javob beradi (standart).
* `name` — faqat ism (`WAKE_NAME`, standart "Nexus") aytilganda; ism aytilgach `WAKE_FOLLOW_UP_S`
  (25 s) davomida ismsiz davom etish mumkin.
* `smart` — ism, follow-up oynasi yoki buyruqqa o'xshash qisqa gap.

Ism nutqda buziladi ("neksus", "нексус") — solishtirish Levenshtein masofasi bilan, tinish belgilari
va apostroflarsiz. UI'dan `wake_mode` / `set_name` buyruqlari bilan o'zgartiriladi.

**Diktovka (`nexus/dictation.py`)** — "yozib tur", "men aytaman sen yoz" (`start_dictation`) dan
keyin har aytilgan gap modelni kutmasdan to'g'ridan-to'g'ri old oynaga teriladi (clipboard + Cmd+V).
To'xtash iboralari gap oxirida yoki alohida: "to'xta", "bas", "tugat", "yetarli", "stop", "стоп",
"хватит". Terminal old oynada bo'lsa diktovka boshlanmaydi. UI'dan `dictation` buyrug'i.

---

## UI hodisalar kontrakti (`nexus/events.py`)

Hodisa: `{"type": "<TYPE>", "ts": <unix float>, "data": {...}}`. WebSocket `/ws` ulanganda avval
`HELLO` (`state`, `snapshot`, `history`) keladi; buyruq javobi `CMD_RESULT` (`reqId` bilan).

| Hodisa | `data` |
|---|---|
| `STATE_CHANGE` | `{"state": "idle\|listening\|processing\|tool_executing\|speaking\|dictating\|awaiting_confirmation"}` |
| `TRANSCRIPT` | `{"role": "user\|assistant", "text", "final": bool}` |
| `TOOL_CALLED` | `{"name", "args", "duration_ms", "ok", "output"}` |
| `AUDIO_LEVEL` | `{"rms": 0..1, "db": -60..0}` |
| `METRICS` | `{"cpu", "ram", "battery", "latency_ms", "uptime_s", ...}` |
| `CONNECTION` | `{"gemini": "connected\|reconnecting\|disconnected", "attempt", "detail"}` |
| `LOG` | `{"level": "info\|warn\|error", "message"}` |
| `DEVICES` | `{"devices": [{"index","name","default"}], "current"}` |
| `SETTINGS` | `{"muted","ptt","sensitivity","playback","wake_mode","name","dictating"}` |
| `CONFIRM_REQUEST` | `{"token","action","summary","reason","ttl_s"}` |
| `CONFIRM_RESOLVED` | `{"token","approved","source": "voice\|ui\|timeout\|cancelled"}` |

UI → daemon buyruqlari: `mute`, `ptt`, `ptt_press`, `sensitivity`, `set_device`, `list_devices`,
`kill_all`, `get_state`, `text`, `run_tool`, `confirm`, `wake_mode`, `set_name`, `dictation`
(formatlari `events.py` docstring'ida). HTTP: `GET /health`, `GET /api/state`.

---

## Skriptlar

```bash
.venv/bin/python scripts/check_setup.py           # kalit (faqat bor/yo'q + uzunligi), paketlar, audio,
                                                  # Accessibility / Screen Recording / Automation, mikrofon 2s
.venv/bin/python scripts/check_setup.py --live    # + Gemini Live "Say OK" pingi (15 s timeout)
.venv/bin/python scripts/check_setup.py --no-mic

.venv/bin/python scripts/benchmark_live.py        # 24 ta o'zbekcha buyruq → real Live sessiyada qaysi tool
                                                  # tanlanganini o'lchaydi (toollar BAJARILMAYDI — stub javob);
                                                  # jadval + benchmark_<vaqt>.json
.venv/bin/python scripts/benchmark_live.py --group fayl --json out.json

.venv/bin/python scripts/voice_picker.py          # 10 ta iliq ovoz namunasi → voice_samples/*.wav
.venv/bin/python scripts/voice_picker.py --all    # barcha 30 ta ovoz
.venv/bin/python scripts/voice_picker.py --voices Aoede,Kore --play --say "O'z matningiz"
```

---

## Testlar

```bash
.venv/bin/python -m pytest -q                       # hammasi
.venv/bin/python -m pytest tests/test_extensions.py # fayl/AX kengaytmalari (real AX/Finder'ga tegmaydi)
.venv/bin/python -m pytest tests/test_desktop.py    # desktop qatlamining GUI'siz qismlari
.venv/bin/ruff check nexus scripts tests
```

Testlar real macOS'ga tegmaydi: `osascript`/subprocess monkeypatch qilinadi, fayl toollari `tmp_path`
da ishlaydi, AX handlerlari uchun `collect_elements`/`run_menu` almashtiriladi.

---

## Muammolarni bartaraf etish

| Belgi | Sabab / yechim |
|---|---|
| Yordamchi o'z gapiga o'zi javob beradi (echo) | `ECHO_GUARD=true`, `VAD_START_SENSITIVITY=LOW`, `PLAYBACK_PREBUFFER_MS=220`; quloqchin ishlating yoki `ECHO_BARGE_FACTOR` ni oshiring |
| Har 10–20 s da "reconnecting" | `session.receive()` har navbat tugaganda to'xtaydi — bu uzilish emas; klient shu semantikani hisobga oladi. Haqiqiy uzilishda backoff 1→30 s (`RECONNECT_*`); 10 daqiqadan keyin uzilsa `SESSION_RESUMPTION` / `CONTEXT_COMPRESSION` yoqilganini tekshiring |
| `1007` / `1011` WebSocket xatosi | model faqat `AUDIO` modality'ni qabul qiladi; `enable_affective_dialog` yoqilmagan; model nomini `.env` da tekshiring |
| `type_text` / `press_hotkey` ishlamaydi | Accessibility ruxsati (Terminal/Python uchun); `check_setup.py` |
| `take_screenshot` qora rasm | Screen Recording ruxsati |
| Brauzer toollari "JavaScript from Apple Events" xatosi | Safari: Develop menyusi; Chrome: View → Developer → Allow JavaScript from Apple Events |
| `-1743` "Not authorized to send Apple events" | Privacy & Security → Automation → System Events / Finder / Safari / Chrome |
| `list_ui_elements` Chrome'da bo'sh | birinchi chaqiruvda `AXManualAccessibility` yoqiladi; 1–2 s kutib qayta chaqiring |
| `set_do_not_disturb` xatosi | Shortcuts ilovasida "Nexus DND On" / "Nexus DND Off" yarating |
| Mikrofon topilmadi / peak≈0 | `nexus --list-devices`, `INPUT_DEVICE`, Privacy → Microphone |
| Port 8765 band | `UI_PORT` ni o'zgartiring yoki eski daemon'ni yoping (`lsof -i :8765`) |
| Terminal buyrug'i rad etildi | `CommandGuard`: allowlist/deny ro'yxati (`nexus/macos_actions.py`); xavfli naqshlar `nexus/safety.py` |

Loglar: `LOG_LEVEL=DEBUG` yoki `nexus --log-level DEBUG`.

---

## `reference/` papkasi

`reference/AI/` — avvalgi avlod yordamchining (Gemini Live, ~7100 qator, PyQt orb) manba kodi;
`reference/ANALYSIS.md` — uning tahlili: arxitektura, Live API topilmalari (receive semantikasi,
VAD, resumption), eski toollar ro'yxati, yo'l qo'yilgan xatolar va Nexus rejasi. Bu kod **ishga
tushirilmaydi** va paketga kirmaydi — faqat ma'lumotnoma (`ui_elements.py` AX yondashuvi,
`benchmark.py` buyruqlar to'plami, `check_setup.py`, `voice_picker.py` shu yerdan qayta yozilgan).
