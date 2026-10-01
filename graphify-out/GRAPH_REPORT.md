# Graph Report - nexus  (2026-09-30)

## Corpus Check
- 42 files · ~96,452 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 4, .command 2, .example 1)

## Summary
- 1891 nodes · 4288 edges · 92 communities (78 shown, 14 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 275 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f4859bca`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- support.js
- file_actions.py
- ax_actions.py
- Result
- GeminiLiveClient
- make_client
- app.js
- test_tools.py
- EventBus
- Nexus Ovoz OS README
- ._build_handlers
- NexusDesktopApp
- MacOSController
- test_server.py
- registry.py
- test_desktop.py
- main.py
- screen_reader.py
- test_screen_reader.py
- ToolRegistry
- test_safety.py
- Any
- check_setup.py
- test_core.py
- WakeState
- _registry
- DesktopPrefs
- ws_reconnect_harness.js
- Settings
- web_answer.py
- ConfirmationGate
- test_wake_dictation.py
- AudioStreamer
- desktop.py
- CommandGuard
- test_registry_kill_all_runs_hook_and_cancels_gate
- DaemonRunner
- .connect
- config.py
- MetricsTicker
- TaintTracker
- FakeAudio
- ._evaluate_addressed
- macos_actions.py
- server.py
- match_app
- _bus
- Any
- .run
- snapshot
- BargeInGate
- Segmenter
- UIServer
- test_video_translate.py
- DictationState
- asyncio
- fake_screen
- VideoTranslator
- looks_like_command
- _recognize
- ._feed
- ._handle_server_content
- _FakeModels
- schemas.py
- NexusOrbPanel
- normalise
- error_text
- Any
- ocr_image
- is_config_rejection
- player_setup_js
- test_registry_no_confirmation_runs_immediately
- LoopGuard
- describe_screen
- test_registry_loads_extension_modules
- nexus/__init__.py
- video_translate.py
- build_app.sh
- .build_hotkey_script
- nexus-voice
- ._finalize_user_turn
- FakeStream
- ._handle_message
- ._run
- PlaybackClock
- _ConfirmTracker
- CLAUDE.md
- parse_latency
- _conversation
- .get_system_info
- .is_terminal_frontmost

## God Nodes (most connected - your core abstractions)
1. `EventBus` - 84 edges
2. `GeminiLiveClient` - 75 edges
3. `MacOSController` - 65 edges
4. `ToolRegistry` - 62 edges
5. `VideoTranslator` - 55 edges
6. `AudioStreamer` - 52 edges
7. `NexusDesktopApp` - 46 edges
8. `make_client()` - 41 edges
9. `Settings` - 34 edges
10. `WakeState` - 32 edges

## Surprising Connections (you probably didn't know these)
- `Echo guard + playback prebuffer + low VAD start sensitivity` --rationale_for--> `AudioStreamer`  [INFERRED]
  README.md → nexus/audio_streamer.py
- `session.receive() ends each turn (not a disconnect)` --rationale_for--> `GeminiLiveClient`  [INFERRED]
  README.md → nexus/gemini_live_client.py
- `Confirmation card (TASDIQ KUTILMOQDA, Yes/No, TTL)` --shares_data_with--> `ConfirmationGate`  [INFERRED]
  ui/index.html → nexus/safety.py
- `.env settings (GEMINI_MODEL, VAD_THRESHOLD, WAKE_MODE, UI_PORT ...)` --references--> `Settings`  [EXTRACTED]
  README.md → nexus/config.py
- `handle() event dispatcher` --shares_data_with--> `EventBus`  [INFERRED]
  ui/orb.html → nexus/events.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Tool execution safety pipeline** — readme_toolregistry_execute_flow, readme_loop_guard, readme_taint_guard, readme_commandguard_tiers, nexus_safety_confirmationgate [EXTRACTED 1.00]
- **Echo / self-hearing mitigation** — readme_echo_guard, reference_analysis_live_api_findings, nexus_audio_streamer_audiostreamer, nexus_audio_streamer_audioplayer [INFERRED 0.85]
- **WebSocket /ws event consumers** — readme_ui_event_contract, ui_index, ui_orb, nexus_events_eventbus [INFERRED 0.85]

## Communities (92 total, 14 thin omitted)

### Community 0 - "support.js"
Cohesion: 0.06
Nodes (75): boot(), bundledBlob(), cdnScriptFor(), collectProps(), compileAttr(), compileTemplate(), contentKey(), createComponentFactory() (+67 more)

### Community 1 - "file_actions.py"
Cohesion: 0.05
Nodes (65): csv, nexus, _append_csv(), _append_row_sync(), append_spreadsheet_row(), _append_xlsx(), _coerce_cell_value(), delete_file() (+57 more)

### Community 2 - "ax_actions.py"
Cohesion: 0.07
Nodes (72): applicationservices, difflib, _actions(), activate_element(), _app_root(), _attr(), available(), _clean_text() (+64 more)

### Community 3 - "Result"
Cohesion: 0.06
Nodes (30): app_name(), BrowserController, BrowserDOMController, build_search_url(), _fmt_time(), _js_error(), js_to_applescript(), normalize_url() (+22 more)

### Community 4 - "GeminiLiveClient"
Cohesion: 0.23
Nodes (3): GeminiLiveClient, Final transkript bo'lagini darhol teradi; to'xtash iborasi rejimni tugatadi., Session resumption + context compression

### Community 5 - "make_client"
Cohesion: 0.06
Nodes (47): SimpleNamespace, _audio_part(), FakeLiveConnect, FakeSession, make_client(), _msg(), 1011 'exceeded your current quota' → avval google_search grounding olib…, `turns` — har bir receive() iteratsiyasida beriladigan xabarlar ro'yxati (bo'sh… (+39 more)

### Community 6 - "app.js"
Cohesion: 0.12
Nodes (58): answerConfirm(), applyDevices(), applySettings(), applySnapshot(), bind(), closeSocket(), connect(), ensureRow() (+50 more)

### Community 7 - "test_tools.py"
Cohesion: 0.07
Nodes (33): nexus_tools, _no_sleep(), MonkeyPatch, Tool qatlami testlari — real macOS tizimiga tegmaydi (osascript/subprocess…, Barcha ichki JS'lar AppleScript literaliga qo'yilganda qo'shtirnoq muvozanati…, ScriptRecorder, test_as_str_escapes_quotes_and_backslashes(), test_browser_open_url_normalizes() (+25 more)

### Community 8 - "EventBus"
Cohesion: 0.09
Nodes (24): CommandHandler, EventBus, AbstractEventLoop, Any, Queue, Thread-safe pub/sub. `publish` istalgan thread'dan chaqirilishi mumkin., Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline, make_settings() (+16 more)

### Community 9 - "Nexus Ovoz OS README"
Cohesion: 0.05
Nodes (47): Nexus Ovoz OS design mockup (dc.html), Design mockup Component (simulated PTT command flow), Local models concept (Whisper.cpp small.uz + Qwen 7B Q4), Nexus Ovoz OS README, AXManualAccessibility for Chrome/Electron, CommandGuard allow/deny/confirm tiers, Desktop layer (pure pyobjc NSWindow + WKWebView, orb NSPanel, menu bar), Dictation mode (direct typing, stop phrases) (+39 more)

### Community 10 - "._build_handlers"
Cohesion: 0.06
Nodes (19): browser_click_button(), browser_click_selector(), browser_close_tab(), browser_current_page(), browser_list_tabs(), browser_open_url(), browser_read_page(), browser_reload() (+11 more)

### Community 11 - "NexusDesktopApp"
Cohesion: 0.09
Nodes (8): _load_url(), NexusDesktopApp, Any, NSApplication delegati: oyna, orb, menyu bar, daemon ko'prigi., SIGINT/SIGTERM → toza chiqish. Mach-port orqali AppKit run loop'ida qayta…, Daemon thread'idan chaqiriladi — hodisani GUI thread'iga uzatadi., `.env` ni Finder'da ko'rsatadi (yagona "tashqi ochish" — brauzer emas)., NSObject

### Community 12 - "MacOSController"
Cohesion: 0.14
Nodes (7): _clamp(), MacOSController, Result, SSID ni aniqlaydi. macOS 14+ da Location Services ruxsatisiz SSID `<redacted>`…, macOS bilan ishlash: ovoz, media, ilovalar, Finder, tizim, terminal., macOS 12+ da DND uchun ochiq API yo'q. Foydalanuvchi yaratgan Shortcuts…, Faol oynaga matn kiritadi: bufer + Cmd+V (keystroke o'zbek/kirill matnni…

### Community 13 - "test_server.py"
Cohesion: 0.16
Nodes (14): fastapi_testclient, pytest, TestClient, bus(), client(), _free_port(), fixture, nexus.server (FastAPI + WS ko'prigi) testlari. (+6 more)

### Community 14 - "registry.py"
Cohesion: 0.18
Nodes (15): collections, collections_abc, importlib, logging, math, Mikrofon oqimi va ovoz ijrosi (sounddevice / PortAudio). `AudioStreamer` —…, Daemon ichidagi hodisalar shinasi (event bus). Barcha modullar (audio, gemini,…, Gemini Multimodal Live API (WebSocket) sessiyasi. Ikki parallel task:… (+7 more)

### Community 15 - "test_desktop.py"
Cohesion: 0.09
Nodes (26): default_window_frame(), effective_state(), placeholder_html(), (rang, yorliq) — menyu bar / orb uchun., Menyu bar'dagi holat satri, masalan "● Tinglamoqda" yoki "● Kutmoqda (mikrofon…, Ekran o'rtasida, `visibleFrame`ning `fraction` (90%) qismi (yoki `size`), min…, `base_url/health` 2xx qaytarguncha kutadi. `keep_waiting()` False qaytarsa…, Server tayyor bo'lguncha (yoki daemon xato bilan to'xtasa) oynada… (+18 more)

### Community 16 - "main.py"
Cohesion: 0.09
Nodes (29): ArgumentParser, Event, Namespace, list_input_devices(), [{"index", "name", "default"}] — faqat kirish (mikrofon) qurilmalari., DesktopOptions, Desktop ilovani ishga tushiradi (asosiy thread'da bloklaydi). Qaytadi: chiqish…, argparse Namespace (nexus.main.build_parser) → DesktopOptions. (+21 more)

### Community 17 - "screen_reader.py"
Cohesion: 0.18
Nodes (16): capture_frontmost_window(), _shoot(), _front_app(), _front_window_info(), _image_size(), _largest_window(), _main_display_bounds(), Ekranni o'qish: mahalliy OCR (Apple Vision) va Gemini ko'rish — kengaytma… (+8 more)

### Community 18 - "test_screen_reader.py"
Cohesion: 0.10
Nodes (10): Vision normalizatsiyalangan bbox (0..1, y PASTDAN) → ekran (x, y, w, h),…, vision_box_to_screen(), tempfile, screen_reader (OCR + Gemini ko'rish) va ax_actions'dagi AX→OCR zaxira yo'li…, test_click_ui_element_by_ocr_index_from_cache(), test_list_ui_elements_merges_ax_and_ocr(), test_list_ui_elements_pure_ax_unchanged(), test_read_screen_ocr_tool_with_fake_ocr() (+2 more)

### Community 19 - "ToolRegistry"
Cohesion: 0.10
Nodes (9): Foydalanuvchi yangi gap boshladi: loop guard va taint tozalanadi., Foydalanuvchining yakuniy transkripti — og'zaki tasdiq uchun., Bajarilayotgan tool tasklarini bekor qiladi. Kutilayotgan tasdiq so'roviga…, ⌥⎋ / "kill_all": tool tasklar + kutilayotgan tasdiq bekor qilinadi, so'ng…, Gemini toollarini bajaruvchi markaziy ro'yxat., ToolRegistry, test_conversation_tools_registered(), test_registry_validates_required_and_enum() (+1 more)

### Community 20 - "test_safety.py"
Cohesion: 0.11
Nodes (22): looks_read_only(), True — buyruq DANGEROUS_SHELL naqshlaridan biriga mos keladi., True — buyruq HECH QANDAY bayroq bilan ham hech narsani o'zgartira olmaydi., Model yoki log ko'rishidan oldin kalitga o'xshagan narsalarni yashiradi., True = rozi, False = rad, None = javob emas. Rad etish (veto) gap uzunligidan…, redact_secrets(), shell_is_dangerous(), spoken_verdict() (+14 more)

### Community 21 - "Any"
Cohesion: 0.17
Nodes (6): Handler, Any, Handler javobini (tuple yoki dict) yagona formatga keltiradi., Bajarishdan OLDIN aniqlanadigan tasdiq sabablari (bo'sh — tasdiqsiz)., _to_text(), _truncate()

### Community 22 - "check_setup.py"
Cohesion: 0.27
Nodes (15): CDLL, check_accessibility(), check_automation(), check_devices(), check_key(), check_live(), check_mic_level(), check_packages() (+7 more)

### Community 23 - "test_core.py"
Cohesion: 0.06
Nodes (37): AudioPlayer, compute_rms(), echo_gate(), Yordamchi gapirayotganda mikrofon chunk'i o'tkazilsinmi? True = o'tkaz. Guard…, 24 kHz int16 mono ijro. `enqueue` istalgan thread/task'dan chaqirilishi mumkin.…, Buferdagi qolgan audioni (prebuffer to'lmagan bo'lsa ham) ijroga qo'yib…, Navbatni tozalaydi (interruption). Tashlangan chunklar sonini qaytaradi., Hozir ovoz chiqyaptimi (navbatda audio bor yoki oxirgi chunk yaqinda chiqqan). (+29 more)

### Community 24 - "WakeState"
Cohesion: 0.09
Nodes (13): Yordamchi hozir unga gapirilayotganini kuzatadi., Yordamchi javobi savol bilan tugadimi — keyingi oyna uzunroq bo'ladi., `follow_up` — aniq tugatilganda oddiy follow-up oynasi qoladi (xayrlashuv…, Suhbat rejimi yoqilgan, lekin `conversation_idle_s` jimlikdan keyin tugashi…, Oynani yangilash — yordamchi hozirgina foydalanuvchi uchun nimadir qildi., Oyna ochiq bo'lsa, uni `ts` (monotonic) dan boshlab hisoblaydi — masalan…, WakeState, test_wake_conversation_window_and_expiry() (+5 more)

### Community 25 - "_registry"
Cohesion: 0.15
Nodes (13): MonkeyPatch, Handler `needs_confirmation` qaytarsa registry gate'ni so'raydi va…, _registry(), test_registry_confirmation_via_bus_utterance_command(), test_registry_confirmations_command_toggles(), test_registry_dictation_tools(), test_registry_handler_needs_confirmation_dict(), test_registry_kill_all_cancels_pending_confirmation() (+5 more)

### Community 26 - "DesktopPrefs"
Cohesion: 0.12
Nodes (10): DesktopPrefs, _pair(), Path, ~/.nexus/desktop.json — orb pozitsiyasi, oyna o'lchami, orb ko'rinishi., Path, start.command: bo'sh/namunaviy GEMINI_API_KEY → Sozlamalarga yo'naltiruvchi…, test_prefs_ignores_corrupt_or_invalid(), test_prefs_roundtrip() (+2 more)

### Community 27 - "ws_reconnect_harness.js"
Cohesion: 0.12
Nodes (9): ref_fs, byId(), els, FakeWS, fs, listeners, makeEl(), sockets (+1 more)

### Community 28 - "Settings"
Cohesion: 0.10
Nodes (15): google-genai Client — hamma joyda bir xil sozlama bilan., Settings, create_app(), index(), Path, FastAPI ilovasini yaratadi (testlarda ham shu ishlatiladi)., test_config_defaults_gemini38(), test_wake_defaults_to_name_only() (+7 more)

### Community 29 - "web_answer.py"
Cohesion: 0.20
Nodes (15): inspect, build_request(), _create(), extract_sources(), extract_text(), _get(), _make_client(), Any (+7 more)

### Community 30 - "ConfirmationGate"
Cohesion: 0.20
Nodes (6): ConfirmationGate, _consume(), PendingConfirmation, Bir vaqtda faqat bitta faol tasdiq so'rovi. Yangi so'rov eskisini bekor qiladi., Foydalanuvchining yakuniy transkripti. So'rovdan OLDIN aytilgan gap hisobga…, Bus'dagi TRANSCRIPT (user, final) hodisalarini ham kuzatadi — gemini client…

### Community 31 - "test_wake_dictation.py"
Cohesion: 0.12
Nodes (26): is_stop_phrase(), Butun gap faqat to'xtash iborasidan iboratmi?, _candidates(), levenshtein(), name_in(), Levenshtein masofasi; `limit` berilsa undan oshgach hisoblashni to'xtatadi…, Qisqa ism aniq mos kelishi kerak; uzunroq ism 2-3 xatoni ko'taradi., (nomzod, boshlanish indeksi, so'zlar soni) — yakka so'zlar va qo'shni… (+18 more)

### Community 32 - "AudioStreamer"
Cohesion: 0.05
Nodes (28): AudioStreamer, _list_devices(), _mute(), _playback(), _ptt(), _ptt_press(), _sensitivity(), _set_device() (+20 more)

### Community 33 - "desktop.py"
Cohesion: 0.10
Nodes (23): appkit, foundation, default_orb_origin(), _env_true(), _hex_color(), _make_app_icon(), _make_webview(), Desktop ilova qatlami: o'z oynasi, doim tepada turadigan orb va menyu bar… (+15 more)

### Community 34 - "CommandGuard"
Cohesion: 0.15
Nodes (12): CommandGuard, Buyruqni qo'riqchi orqali bajaradi. `confirmed=True` — registry foydalanuvchi…, `run_terminal_command` uchun uch pog'onali qo'riqchi. `check()` → ("allow" |…, Tekshiruvdan o'tgan buyruqni bajarish uchun argv (`~` kengaytirilgan holda)., _truncate(), parametrize, test_guard_allows(), test_guard_argv_expands_tilde() (+4 more)

### Community 36 - "DaemonRunner"
Cohesion: 0.16
Nodes (5): DaemonRunner, `nexus.main.run()` ni alohida thread'da o'z event loop'i bilan yuritadi., To'xtatish signalini beradi (bloklamaydi) — tugashini `finished` orqali…, To'xtatish signalini beradi va thread tugashini kutadi. True = toza tugadi., GUI'dan daemon'ga buyruq (thread-safe, natija kutilmaydi).

### Community 38 - "config.py"
Cohesion: 0.08
Nodes (31): dotenv, api_key_env_path(), api_key_hint(), _describe_char(), _env_api_key(), env_candidates(), is_placeholder_api_key(), load_env_files() (+23 more)

### Community 39 - "MetricsTicker"
Cohesion: 0.24
Nodes (7): _first(), MetricsTicker, Any, Berilgan kalitlardan birinchi None bo'lmagan qiymat., Har `interval` sekundda cpu/ram/battery ni METRICS ga nashr qiladi., Nashr qilinadigan METRICS: snapshot'dagi eski maydonlar (reconnects,…, test_metrics_ticker_preserves_snapshot_fields()

### Community 40 - "TaintTracker"
Cohesion: 0.25
Nodes (3): Navbat ichida tashqi matn o'qilganini eslab qoladi., TaintTracker, test_taint_tracker()

### Community 41 - "FakeAudio"
Cohesion: 0.11
Nodes (9): FakeAudio, FakeRegistry, test_build_config_ptt_disables_vad_and_optional_fields(), test_conversation_command_and_idle_tick(), test_dismissal_keeps_silent_and_waits_for_name(), test_run_requires_api_key(), test_run_waits_for_api_key_from_settings(), test_user_turn_without_registry_hooks() (+1 more)

### Community 42 - "._evaluate_addressed"
Cohesion: 0.13
Nodes (7): Oxirgi real audio chunk karnayga chiqqan payt (time.monotonic; 0 — hali yo'q)., Registry gate'ida (ConfirmationGate) hal qilinmagan tasdiq so'rovi bormi?, Wake rejimi bo'yicha gap bizga qaratilganmi (qisman transkriptda ham). Baho…, Yo'q / hech narsa kerak emas" rad javobi sifatida qaralsinmi? Suhbat rejimida…, Joriy gap boshlangan payt (AudioStreamer RMS gate). Noma'lum yoki eskirgan…, Suhbat rejimi: ismsiz erkin suhbat; jimlikdan keyin o'zi tugaydi (`tick`)., Davriy tekshiruv (MetricsTicker): jimlik tufayli suhbat rejimini tugatish;…

### Community 43 - "macos_actions.py"
Cohesion: 0.16
Nodes (13): ctypes, datetime, json, macOS tizim amallari (AppleScript + xavfsiz shell). Barcha subprocess…, _cmd(), path_is_sensitive(), Path, Xavfsizlik qatlami: xavfli shell naqshlari, sezgir yo'llar, sir redaktsiyasi,… (+5 more)

### Community 44 - "server.py"
Cohesion: 0.22
Nodes (8): contextlib, errno, FastAPI, fastapi_responses, fastapi_staticfiles, UI ko'prigi: FastAPI + WebSocket server. EventBus hodisalarini brauzerdagi UI…, socket, uvicorn

### Community 45 - "match_app"
Cohesion: 0.18
Nodes (8): installed_apps(), match_app(), hits(), /Applications, /System/Applications, ~/Applications dagi .app nomlari (60s…, `needle` nomning boshida yoki ichidagi so'z boshida keladi ("word" ≠…, Aytilgan nomga mos o'rnatilgan ilovalar, eng yaqini birinchi. Tartib: aniq…, _starts_a_word(), test_match_app_fuzzy()

### Community 46 - "_bus"
Cohesion: 0.24
Nodes (11): _bus(), _drain(), Queue, Gemini client note_utterance'ni chaqirmasa ham, bus'dagi TRANSCRIPT (user,…, test_gate_listens_to_bus_transcripts(), test_gate_new_request_cancels_old(), test_gate_timeout(), test_gate_ui_confirm_command() (+3 more)

### Community 47 - "Any"
Cohesion: 0.21
Nodes (5): _key_hint(), Any, Path, UI (Sozlamalar) dan API kalit: tekshiradi, saqlaydi va sessiyani yangi kalit…, _to_function_declarations()

### Community 48 - ".run"
Cohesion: 0.21
Nodes (4): Cheksiz ulanish sikli; `stop()` chaqirilguncha qayta ulanaveradi., Kalit Sozlamalardan (`set_api_key`) kiritilguncha yoki `stop()` gacha kutadi., `timeout` sekund (None — cheksiz) kutadi; `stop()` yoki yangi API kalit…, Band holat (processing / tool_executing / speaking) tool ham, ijro ham, server…

### Community 49 - "snapshot"
Cohesion: 0.31
Nodes (10): _cmd_result(), api_state(), snapshot(), ws_endpoint(), handle_command(), receiver(), send(), sender() (+2 more)

### Community 50 - "BargeInGate"
Cohesion: 0.15
Nodes (9): BargeInGate, AbstractEventLoop, Ijro paytida mikrofon chunklarining echo/barge-in darvozasi (callback…, → (navbatga qo'yiladigan chunklar, sukunatga almashtirilganlar soni)., Nom (qism mos kelsa ham) yoki indeks → qurilma indeksi. None = standart., resolve_device(), test_barge_gate_flushes_held_when_playback_stops(), test_barge_gate_single_spike_becomes_silence() (+1 more)

### Community 51 - "Segmenter"
Cohesion: 0.38
Nodes (4): Uzluksiz nutqni tarjima bo'laklariga ajratadi: `push(rms)` True → bo'lakni shu…, Segmenter, test_segmenter_cuts_at_max(), test_segmenter_cuts_on_quiet_after_min()

### Community 52 - "UIServer"
Cohesion: 0.20
Nodes (4): _QuietServer, Signal handlerlarini o'rnatmaydigan uvicorn Server (signalni main.py…, uvicorn'ni fon taskda ishga tushiradigan o'ram., UIServer

### Community 53 - "test_video_translate.py"
Cohesion: 0.09
Nodes (23): attach(), fit_tempo(), is_quota_error(), BaseException, main.py: bus/settings/mikrofonni ulaydi; echo guard tarjima ijrosini ham…, AppleScript: JS ni video tabida bajaradi — Chrome'da `tab_id` bo'yicha (bir xil…, Kalit kvotasi (bir vaqtdagi sessiyalar soni yoki kunlik limit) tugadi., Tarjima (`out_s`) videodagi qolgan oralig'iga (`window_s`) sig'ishi uchun… (+15 more)

### Community 54 - "DictationState"
Cohesion: 0.17
Nodes (6): DictationState, (teriladigan matn, to'xtash kerakmi). "…hammasi shu, to'xta" → ("…hammasi shu",…, Diktovka holati va terilgan matn hisobi., split_stop(), test_dictation_state_lifecycle(), test_split_stop()

### Community 55 - "asyncio"
Cohesion: 0.14
Nodes (17): argparse, asyncio, all_declarations(), build_config(), main(), passed(), Model qaysi toolni tanlashini real Gemini Live sessiyasida o'lchash (toollar…, Asosiy sxemalar + kengaytma modullari (nomlar bo'yicha takrorsiz). (+9 more)

### Community 56 - "fake_screen"
Cohesion: 0.40
Nodes (5): ax_ready(), fake_screen(), fixture, MonkeyPatch, Skrinshot/JPEG bosqichini almashtiradi: real screencapture chaqirilmaydi.

### Community 57 - "VideoTranslator"
Cohesion: 0.11
Nodes (16): Bo'laklarni `seq` tartibida, video o'z oralig'iga (`src_start`) yetganda ijroga…, Javob bermagan bo'lakni navbat boshiga qaytaradi — boshqa (bo'sh) sessiya oladi., Tarjima ulgurmayapti (masalan, kvota kam — sessiyalar yetmaydi): gapni tashlab…, turn_complete kelmay qolgan sessiyani bo'shatadi (model jim qoldi)., Tarjima bo'lagi: kiruvchi audio (tayinlanguncha `buf`da) va modelning javobi…, activity_end dan keyin `no_response_s` ichida audio kelmadi — ijroda o'tkazib…, Tayinlanmagan bo'laklarni (FIFO) bo'sh sessiyalarga beradi., Sessiya bo'shadi — navbatdagi bo'lakni olishi mumkin. (+8 more)

### Community 58 - "looks_like_command"
Cohesion: 0.18
Nodes (7): looks_like_command(), SMART rejimi uchun evristika: qisqa gap + buyruq so'zi., Oxirgi chaqiruvdan keyingi oyna (follow-up yoki suhbat) hali ochiqmi?, Oyna `at` (monotonic; odatda gap BOSHLANGAN payt) da ochiq edimi? None — hozir.…, Matnda ism bormi? Bo'lsa follow-up oynasi ochiladi., Bu gapga javob berish kerakmi? (ism eshitilsa oynani ham ochadi). `at` — gap…, test_looks_like_command()

### Community 59 - "_recognize"
Cohesion: 0.33
Nodes (6): pick_languages(), Qo'llab-quvvatlanadigan tillardan kerakli tartibda tanlaydi ("uz" → "uz-UZ"…, Vision OCR: [(text, nx, ny, nw, nh, confidence)] — normalizatsiyalangan, y…, _recognize(), supported_languages(), test_pick_languages_prefers_uz_then_ru_en_and_skips_missing()

### Community 60 - "._feed"
Cohesion: 0.17
Nodes (8): build_ffmpeg_cmd(), feed_action(), Process, Navbatdagi chunk bilan nima qilish: "resync" | "wait" | "send". Audio videodan…, Seek: navbatdagi kiruvchi audio va hali ijro etilmagan tarjimalar tashlanadi., ffmpeg PCM → navbat (video vaqti bilan), videodan `LOOKAHEAD_S` oldinda; seek →…, test_build_ffmpeg_cmd(), test_feed_action()

### Community 61 - "._handle_server_content"
Cohesion: 0.20
Nodes (6): _asks_question(), _grounding_sources(), ToolRegistry.kill_all() ilgagi: klient tool tasklari bekor, ijro navbati…, Zaxira: registry bo'lmaganda (toolsiz rejim) `kill_all` buyrug'i., Yordamchi javobi foydalanuvchidan javob kutadimi ("Yana nima qilay?", "Labbay,…, `grounding_metadata.grounding_chunks[*].web.{uri,title}` → "title — uri"…

### Community 62 - "_FakeModels"
Cohesion: 0.31
Nodes (8): Exception, _fake_client(), _FakeModels, Any, test_describe_screen_default_question(), test_describe_screen_error_and_timeout(), test_describe_screen_uses_fake_client_and_cleans_tmp(), test_look_at_screen_handler_wraps_result()

### Community 63 - "schemas.py"
Cohesion: 0.39
Nodes (7): _b(), _decl(), _i(), _n(), Any, Gemini Live API uchun FunctionDeclaration lug'atlari va tizim ko'rsatmasi.…, _s()

### Community 64 - "NexusOrbPanel"
Cohesion: 0.33
Nodes (3): NexusOrbPanel, Ramkasiz, shaffof, doim tepada, klaviatura fokusini OLMAYDIGAN panel.…, NSPanel

### Community 65 - "normalise"
Cohesion: 0.33
Nodes (5): is_dismissal(), normalise(), Kichik harf, urg'u/apostrofsiz, tinish belgisiz; kirill → lotin., Yo'q, hozircha hech narsa", "kerak emas", "rahmat", "нет, ничего", "no,…, test_normalise_folds_case_apostrophes_and_cyrillic()

### Community 66 - "error_text"
Cohesion: 0.50
Nodes (4): error_text(), BaseException, Gemini xatosini foydalanuvchiga o'zbekcha qisqa jumla qilib beradi., test_error_text_is_uzbek()

### Community 67 - "Any"
Cohesion: 0.16
Nodes (11): is_silent(), Any, Bo'lak deyarli jim (o'rtacha RMS `SILENT_RMS` dan past)., Bitta Live sessiya: navbatdagi bo'lakni oladi, javobini bo'lakka yozadi., Parallel sessiyalar + dispetcher + tartibli ijro., Sessiya uzildi: joriy bo'lak yakunlangan deb belgilanadi, o'zi bo'sh ro'yxatdan…, Model javobini sessiyaning joriy bo'lagiga yozadi. True — navbat tugadi…, _Worker (+3 more)

### Community 68 - "ocr_image"
Cohesion: 0.16
Nodes (19): Box, available(), lines_as_elements(), lines_to_text(), ocr_image(), Satrlarni yuqoridan pastga, bir qatordagilarni chapdan o'ngga tartiblaydi. Ikki…, Tartiblangan satrlardan matn: bir qatordagilar ikki bo'shliq bilan, qatorlar…, OCR satrlarini list_ui_elements formatiga o'giradi: {n, role:'text', label, at,… (+11 more)

### Community 69 - "is_config_rejection"
Cohesion: 0.29
Nodes (7): is_api_key_error(), is_config_rejection(), BaseException, Server kalitni rad etdimi (noto'g'ri / bekor qilingan API kalit)?, Server konfiguratsiyani rad etgan bo'lsa navbatdagi modelga bog'liq maydonni…, Server konfiguratsiyani rad etdimi (WebSocket 1007 / invalid argument), kalit…, test_is_config_rejection()

### Community 70 - "player_setup_js"
Cohesion: 0.17
Nodes (7): player_setup_js(), `pos` dan `ahead` soniya oldinga tarjima tayyormi: ijroga qo'yilgan, yoki…, Video pauza, tarjima ovozi esa davom etadi — `seconds` dan keyin video qayta…, Buferlash: video pauzada turadi, oldinda `GATE_AHEAD_S` tarjima tayyor bo'lgach…, Pleyer: asl ovozni o'chirish/pasaytirish (0..1, manfiy — tegilmaydi) va ijro…, test_player_setup_js(), test_player_setup_js_keeps_volume_when_negative()

### Community 71 - "test_registry_no_confirmation_runs_immediately"
Cohesion: 0.29
Nodes (3): test_registry_no_confirmation_runs_immediately(), test_registry_tainted_turn_requires_confirmation(), read_page()

### Community 72 - "LoopGuard"
Cohesion: 0.20
Nodes (7): LoopGuard, Any, Bir navbatda haddan ko'p yoki bir xil chaqiruvlarni to'xtatadi., None — davom et; matn — rad etish sababi (modelga tushuntirish)., test_loop_guard_identical_calls(), test_loop_guard_max_calls_per_turn(), test_loop_guard_non_consecutive_identical_calls()

### Community 73 - "describe_screen"
Cohesion: 0.36
Nodes (10): describe_screen(), _extract_text(), _image_part(), look_at_screen(), _make_client(), Any, Oldingi oynani skrinshot qilib Gemini'ga ko'rsatadi. {ok, output, app, ...}., read_screen_ocr() (+2 more)

### Community 76 - "video_translate.py"
Cohesion: 0.12
Nodes (20): dataclasses, itertools, normalize_browser(), Diktovka rejimi: foydalanuvchi gapiradi — yordamchi teradi, to'xtash…, compute_backoff(), base * 2**attempt + jitter, max_delay bilan cheklangan. `jitter` None bo'lsa…, YouTube videosini jonli (sinxron) ovozli tarjima: ingliz → o'zbek. Oqim: yt-dlp…, translate_video() (+12 more)

### Community 84 - "._run"
Cohesion: 0.12
Nodes (14): AppleScript'ni `osascript` orqali bajaradi (stdin orqali, argument uzunligi…, run_applescript(), build_ytdlp_cmd(), find_tab_script(), parse_player_state(), AppleScript (Chrome): `video_id` ochiq tabni topib oldinga chiqaradi va id sini…, Faqat audio yuklanadi; stdout: 1-qator sarlavha, oxirgi qator fayl yo'li., yt-dlp: audio faylni vaqtinchalik papkaga yuklaydi. (ok, sarlavha | xato).… (+6 more)

### Community 85 - "PlaybackClock"
Cohesion: 0.10
Nodes (14): find_binary(), is_junk_translation(), PlaybackClock, PATH + Homebrew papkalari (.app ichidan ishga tushganda PATH qisqa bo'ladi)., Model tarjima o'rniga yorliq/izoh aytdi (`(Uzbek translation: …)`, `<no…, Brauzer pleyeri holatidan joriy video vaqtini baholaydi (so'rovlar orasida…, s16le mono PCM ni ohangini saqlab `tempo` barobar tezlashtiradi (ffmpeg…, time_stretch() (+6 more)

### Community 88 - "parse_latency"
Cohesion: 0.50
Nodes (3): parse_latency(), high"/"low" yoki sekund (str/float) → sounddevice `latency` argumenti., test_parse_latency()

### Community 89 - "_conversation"
Cohesion: 0.67
Nodes (3): _conversation(), start_conversation(), stop_conversation()

### Community 90 - ".get_system_info"
Cohesion: 0.50
Nodes (3): _fmt_uptime(), Any, _summarize_info()

## Ambiguous Edges - Review These
- `Gemini Live API (native audio, WebSocket)` → `Local models concept (Whisper.cpp small.uz + Qwen 7B Q4)`  [AMBIGUOUS]
  design/Nexus Ovoz OS.dc.html · relation: conceptually_related_to

## Knowledge Gaps
- **15 isolated node(s):** `nexus-voice`, `build_app.sh script`, `fs`, `src`, `listeners` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 582 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Gemini Live API (native audio, WebSocket)` and `Local models concept (Whisper.cpp small.uz + Qwen 7B Q4)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `ToolRegistry` connect `ToolRegistry` to `Result`, `test_tools.py`, `test_registry_no_confirmation_runs_immediately`, `EventBus`, `LoopGuard`, `TaintTracker`, `._build_handlers`, `MacOSController`, `Nexus Ovoz OS README`, `registry.py`, `test_registry_loads_extension_modules`, `main.py`, `test_safety.py`, `Any`, `test_video_translate.py`, `test_core.py`, `_registry`, `ConfirmationGate`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Why does `EventBus` connect `EventBus` to `GeminiLiveClient`, `make_client`, `test_tools.py`, `Nexus Ovoz OS README`, `test_server.py`, `registry.py`, `test_desktop.py`, `main.py`, `ToolRegistry`, `test_safety.py`, `test_core.py`, `_registry`, `Settings`, `AudioStreamer`, `MetricsTicker`, `FakeAudio`, `server.py`, `_bus`, `Any`, `snapshot`, `BargeInGate`, `UIServer`, `_ConfirmTracker`, `parse_latency`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Why does `GeminiLiveClient` connect `GeminiLiveClient` to `AudioStreamer`, `is_config_rejection`, `make_client`, `EventBus`, `Nexus Ovoz OS README`, `._evaluate_addressed`, `FakeAudio`, `registry.py`, `Any`, `.run`, `._finalize_user_turn`, `BargeInGate`, `._handle_message`, `main.py`, `DictationState`, `test_core.py`, `WakeState`, `._handle_server_content`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `EventBus` (e.g. with `AudioPlayer` and `AudioStreamer`) actually correct?**
  _`EventBus` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `GeminiLiveClient` (e.g. with `DictationState` and `EventBus`) actually correct?**
  _`GeminiLiveClient` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `MacOSController` (e.g. with `MetricsTicker` and `ToolRegistry`) actually correct?**
  _`MacOSController` has 3 INFERRED edges - model-reasoned connections that need verification._