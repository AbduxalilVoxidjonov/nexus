# Graph Report - nexus  (2026-10-01)

## Corpus Check
- 50 files · ~108,664 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 4, .command 2, .example 1)

## Summary
- 2210 nodes · 4893 edges · 124 communities (98 shown, 26 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 319 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e1328f15`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- support.js
- Any
- ax_actions.py
- Result
- GeminiLiveClient
- test_core.py
- app.js
- test_tools.py
- EventBus
- Nexus Ovoz OS README
- ._build_handlers
- NexusDesktopApp
- MacOSController
- test_server.py
- windows_screen.py
- state_style
- WindowsController
- screen_reader.py
- test_screen_reader.py
- ToolRegistry
- path_is_sensitive
- desktop_win.py
- check_setup.py
- ._process_chunk
- WakeState
- _registry
- DesktopPrefs
- ws_reconnect_harness.js
- create_app
- web_answer.py
- ConfirmationGate
- test_wake_dictation.py
- AudioStreamer
- compute_backoff
- CommandGuard
- windows_input.py
- DaemonRunner
- FakeLiveConnect
- config.py
- run
- test_windows.py
- test_web_answer_parses_interaction
- ._evaluate_addressed
- FakeAudio
- test_desktop.py
- video_translate.py
- WindowsBrowser
- Any
- .run
- bus
- BargeInGate
- Segmenter
- server.py
- test_video_translate.py
- DictationState
- desktop.py
- fake_screen
- VideoTranslator
- reference/AI analysis (old Voice Assistant)
- _recognize
- Segment
- ._handle_server_content
- Process
- schemas.py
- NexusOrbPanel
- normalise
- error_text
- Any
- ocr_image
- is_config_rejection
- test_extensions.py
- test_registry_no_confirmation_runs_immediately
- LoopGuard
- ._build_window
- run_shell
- nexus/__init__.py
- wake.py
- build_app.sh
- .get_system_info
- nexus-voice
- file_actions.py
- FakeStream
- ._publish_metrics
- ._run
- PlaybackClock
- sys
- CLAUDE.md
- .__init__
- WindowsCommandGuard
- TaintTracker
- looks_like_command
- test_safety.py
- match_app
- _ps_quote
- windows_smoke.py
- test_registry_type_text_into_terminal_requires_confirmation
- AudioPlayer
- .build_hotkey_script
- .register_commands
- build_ytdlp_cmd
- .get_system_info
- cli
- browser
- is_junk_translation
- path_allowed
- ._confirmation_pending
- _cmd
- fixture
- parametrize
- AbstractEventLoop
- BaseException
- test_registry_kill_all_runs_hook_and_cancels_gate
- Queue
- Path
- Result
- is_quota_error
- pytest
- _coerce_cell_value
- is_terminal_app
- spoken_verdict
- test_registry_loads_extension_modules
- EventBus
- Verdict

## God Nodes (most connected - your core abstractions)
1. `GeminiLiveClient` - 58 edges
2. `MacOSController` - 57 edges
3. `ToolRegistry` - 56 edges
4. `VideoTranslator` - 55 edges
5. `WindowsController` - 52 edges
6. `WindowsBrowser` - 51 edges
7. `AudioStreamer` - 49 edges
8. `NexusDesktopApp` - 46 edges
9. `make_client()` - 41 edges
10. `FakeSession` - 32 edges

## Surprising Connections (you probably didn't know these)
- `Confirmation card (TASDIQ KUTILMOQDA, Yes/No, TTL)` --shares_data_with--> `ConfirmationGate`  [INFERRED]
  ui/index.html → nexus/safety.py
- `Echo guard + playback prebuffer + low VAD start sensitivity` --rationale_for--> `AudioStreamer`  [INFERRED]
  README.md → nexus/audio_streamer.py
- `session.receive() ends each turn (not a disconnect)` --rationale_for--> `GeminiLiveClient`  [INFERRED]
  README.md → nexus/gemini_live_client.py
- `ToolRegistry.execute flow: validate -> loop guard -> taint -> confirm -> handler` --references--> `ToolRegistry`  [EXTRACTED]
  README.md → nexus/tools/registry.py
- `.env settings (GEMINI_MODEL, VAD_THRESHOLD, WAKE_MODE, UI_PORT ...)` --references--> `Settings`  [EXTRACTED]
  README.md → nexus/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Tool execution safety pipeline** — readme_toolregistry_execute_flow, readme_loop_guard, readme_taint_guard, readme_commandguard_tiers, nexus_safety_confirmationgate [EXTRACTED 1.00]
- **Echo / self-hearing mitigation** — readme_echo_guard, reference_analysis_live_api_findings, nexus_audio_streamer_audiostreamer, nexus_audio_streamer_audioplayer [INFERRED 0.85]
- **WebSocket /ws event consumers** — readme_ui_event_contract, ui_index, ui_orb, nexus_events_eventbus [INFERRED 0.85]

## Communities (124 total, 26 thin omitted)

### Community 0 - "support.js"
Cohesion: 0.06
Nodes (75): boot(), bundledBlob(), cdnScriptFor(), collectProps(), compileAttr(), compileTemplate(), contentKey(), createComponentFactory() (+67 more)

### Community 1 - "Any"
Cohesion: 0.32
Nodes (18): _append_csv(), _append_row_sync(), append_spreadsheet_row(), _append_xlsx(), _open_book(), Any, Path, read_spreadsheet() (+10 more)

### Community 2 - "ax_actions.py"
Cohesion: 0.07
Nodes (72): applicationservices, difflib, _actions(), activate_element(), _app_root(), _attr(), available(), _clean_text() (+64 more)

### Community 3 - "Result"
Cohesion: 0.06
Nodes (26): EventBus, app_name(), BrowserController, BrowserDOMController, _fmt_time(), _js_error(), js_to_applescript(), normalize_url() (+18 more)

### Community 4 - "GeminiLiveClient"
Cohesion: 0.21
Nodes (5): GeminiLiveClient, UI dan matn buyrug'i. Sessiya yo'q bo'lsa False., Registry'ga foydalanuvchi navbatini bildiradi: og'zaki tasdiq (note_utterance)…, Final transkript bo'lagini darhol teradi; to'xtash iborasi rejimni tugatadi., Session resumption + context compression

### Community 5 - "test_core.py"
Cohesion: 0.07
Nodes (49): GeminiLiveClient, math, numpy, SimpleNamespace, sounddevice, _audio_part(), fake_sd(), FakeSession (+41 more)

### Community 6 - "app.js"
Cohesion: 0.12
Nodes (58): answerConfirm(), applyDevices(), applySettings(), applySnapshot(), bind(), closeSocket(), connect(), ensureRow() (+50 more)

### Community 7 - "test_tools.py"
Cohesion: 0.08
Nodes (30): _no_sleep(), MonkeyPatch, Tool qatlami testlari — real macOS tizimiga tegmaydi (osascript/subprocess…, Barcha ichki JS'lar AppleScript literaliga qo'yilganda qo'shtirnoq muvozanati…, ScriptRecorder, test_browser_open_url_normalizes(), test_is_terminal_frontmost(), test_js_permission_hint() (+22 more)

### Community 8 - "EventBus"
Cohesion: 0.17
Nodes (6): CommandHandler, EventBus, AbstractEventLoop, Any, Queue, Thread-safe pub/sub. `publish` istalgan thread'dan chaqirilishi mumkin.

### Community 9 - "Nexus Ovoz OS README"
Cohesion: 0.11
Nodes (25): Nexus Ovoz OS README, Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline, AXManualAccessibility for Chrome/Electron, Desktop layer (pure pyobjc NSWindow + WKWebView, orb NSPanel, menu bar), Dictation mode (direct typing, stop phrases), .env settings (GEMINI_MODEL, VAD_THRESHOLD, WAKE_MODE, UI_PORT ...), EXTENSION_MODULES (TOOL_DECLARATIONS + HANDLERS), macOS permissions (Microphone, Accessibility, Screen Recording, Automation) (+17 more)

### Community 10 - "._build_handlers"
Cohesion: 0.05
Nodes (25): build_search_url(), web_search(), browser_click_button(), browser_click_selector(), browser_close_tab(), browser_current_page(), browser_list_tabs(), browser_open_url() (+17 more)

### Community 11 - "NexusDesktopApp"
Cohesion: 0.09
Nodes (8): _load_url(), NexusDesktopApp, Any, NSApplication delegati: oyna, orb, menyu bar, daemon ko'prigi., SIGINT/SIGTERM → toza chiqish. Mach-port orqali AppKit run loop'ida qayta…, Daemon thread'idan chaqiriladi — hodisani GUI thread'iga uzatadi., `.env` ni Finder'da ko'rsatadi (yagona "tashqi ochish" — brauzer emas)., NSObject

### Community 12 - "MacOSController"
Cohesion: 0.12
Nodes (9): _clamp(), MacOSController, Result, AppleScript'ni `osascript` orqali bajaradi (stdin orqali, argument uzunligi…, Buyruqni qo'riqchi orqali bajaradi. `confirmed=True` — registry foydalanuvchi…, macOS bilan ishlash: ovoz, media, ilovalar, Finder, tizim, terminal., macOS 12+ da DND uchun ochiq API yo'q. Foydalanuvchi yaratgan Shortcuts…, Faol oynaga matn kiritadi: bufer + Cmd+V (keystroke o'zbek/kirill matnni… (+1 more)

### Community 13 - "test_server.py"
Cohesion: 0.11
Nodes (21): fastapi_testclient, google-genai Client — hamma joyda bir xil sozlama bilan., Settings, TestClient, test_config_defaults_gemini38(), test_wake_defaults_to_name_only(), client(), _free_port() (+13 more)

### Community 14 - "windows_screen.py"
Cohesion: 0.10
Nodes (53): io, work(), run(), _activate(), _ask_gemini(), capture_window_jpeg(), _click_point(), _click_sync() (+45 more)

### Community 15 - "state_style"
Cohesion: 0.22
Nodes (10): effective_state(), (rang, yorliq) — menyu bar / orb uchun., Menyu bar'dagi holat satri, masalan "● Tinglamoqda" yoki "● Kutmoqda (mikrofon…, Daemon holati + Gemini ulanishi + tasdiqdan bitta ko'rsatiladigan holat., state_style(), status_title(), parametrize, test_effective_state_priorities() (+2 more)

### Community 16 - "WindowsController"
Cohesion: 0.11
Nodes (8): MacOSController, _press_key(), Result, PowerShell skriptini konsol oynasiz bajaradi; chiqish UTF-8., Windows bilan ishlash: ovoz, media, ilovalar, Explorer, tizim., Faol oynaga matn teradi (SendInput Unicode — bufer o'zgarmaydi)., run_powershell(), WindowsController

### Community 17 - "screen_reader.py"
Cohesion: 0.12
Nodes (31): appkit, foundation, available(), capture_frontmost_window(), describe_screen(), _shoot(), _extract_text(), _front_app() (+23 more)

### Community 18 - "test_screen_reader.py"
Cohesion: 0.10
Nodes (16): Exception, Vision normalizatsiyalangan bbox (0..1, y PASTDAN) → ekran (x, y, w, h),…, vision_box_to_screen(), _fake_client(), _FakeModels, screen_reader (OCR + Gemini ko'rish) va ax_actions'dagi AX→OCR zaxira yo'li…, test_click_ui_element_by_ocr_index_from_cache(), test_describe_screen_default_question() (+8 more)

### Community 19 - "ToolRegistry"
Cohesion: 0.07
Nodes (18): Handler, Any, Foydalanuvchi yangi gap boshladi: loop guard va taint tozalanadi., Foydalanuvchining yakuniy transkripti — og'zaki tasdiq uchun., Bajarilayotgan tool tasklarini bekor qiladi. Kutilayotgan tasdiq so'roviga…, ⌥⎋ / "kill_all": tool tasklar + kutilayotgan tasdiq bekor qilinadi, so'ng…, Handler javobini (tuple yoki dict) yagona formatga keltiradi., Gemini toollarini bajaruvchi markaziy ro'yxat. (+10 more)

### Community 20 - "path_is_sensitive"
Cohesion: 0.14
Nodes (16): looks_read_only(), path_is_sensitive(), Path, True — buyruq DANGEROUS_SHELL naqshlaridan biriga mos keladi., True — buyruq HECH QANDAY bayroq bilan ham hech narsani o'zgartira olmaydi., True — bu yerga yozish persistensiya yaratishi yoki sir sizdirishi mumkin., shell_is_dangerous(), Bajarishdan OLDIN aniqlanadigan tasdiq sabablari (bo'sh — tasdiqsiz). (+8 more)

### Community 21 - "desktop_win.py"
Cohesion: 0.24
Nodes (9): DaemonRunner, DesktopOptions, Settings, Windows desktop qatlami: daemon alohida thread'da, UI — pywebview (Edge…, UI serveri tinglay boshlaguncha kutadi., run_desktop(), wait_for_port(), _wait_headless() (+1 more)

### Community 22 - "check_setup.py"
Cohesion: 0.30
Nodes (14): CDLL, check_accessibility(), check_automation(), check_devices(), check_key(), check_live(), check_mic_level(), check_packages() (+6 more)

### Community 23 - "._process_chunk"
Cohesion: 0.09
Nodes (19): compute_rms(), echo_gate(), gate_open(), Yordamchi gapirayotganda mikrofon chunk'i o'tkazilsinmi? True = o'tkaz. Guard…, Callback thread'da: darajani hisoblaydi, gate'ni yangilaydi, navbatga qo'yadi.…, Yordamchi buyruq ustida ishlayaptimi (o'ylayapti / tool bajaryapti /…, Yordamchi javobi paytida mikrofon to'liq bostirilsinmi?, int16 mono PCM baytlaridan (rms 0..1, db -60..0) qaytaradi. (+11 more)

### Community 24 - "WakeState"
Cohesion: 0.09
Nodes (13): Yordamchi hozir unga gapirilayotganini kuzatadi., Yordamchi javobi savol bilan tugadimi — keyingi oyna uzunroq bo'ladi., `follow_up` — aniq tugatilganda oddiy follow-up oynasi qoladi (xayrlashuv…, Suhbat rejimi yoqilgan, lekin `conversation_idle_s` jimlikdan keyin tugashi…, Oynani yangilash — yordamchi hozirgina foydalanuvchi uchun nimadir qildi., Oyna ochiq bo'lsa, uni `ts` (monotonic) dan boshlab hisoblaydi — masalan…, WakeState, test_wake_conversation_window_and_expiry() (+5 more)

### Community 25 - "_registry"
Cohesion: 0.17
Nodes (13): MonkeyPatch, Handler `needs_confirmation` qaytarsa registry gate'ni so'raydi va…, _registry(), test_registry_confirmation_via_bus_utterance_command(), test_registry_confirmation_voice_approves(), test_registry_confirmations_command_toggles(), test_registry_dictation_tools(), test_registry_handler_needs_confirmation_dict() (+5 more)

### Community 26 - "DesktopPrefs"
Cohesion: 0.12
Nodes (10): DesktopPrefs, _make_app_icon(), _pair(), Path, Desktop ilovani ishga tushiradi (asosiy thread'da bloklaydi). Qaytadi: chiqish…, ~/.nexus/desktop.json — orb pozitsiyasi, oyna o'lchami, orb ko'rinishi., Ilova menyusida (chap yuqori) "python" o'rniga ilova nomi (bundle'siz ishga…, Dock uchun oddiy ikonka: qorong'i doira ichida moviy shar (bundle'siz — python… (+2 more)

### Community 27 - "ws_reconnect_harness.js"
Cohesion: 0.12
Nodes (9): ref_fs, byId(), els, FakeWS, fs, listeners, makeEl(), sockets (+1 more)

### Community 28 - "create_app"
Cohesion: 0.12
Nodes (10): _ConfirmTracker, create_app(), index(), EventBus, Path, Settings, FastAPI ilovasini yaratadi (testlarda ham shu ishlatiladi)., CONFIRM_REQUEST / CONFIRM_RESOLVED hodisalarini kuzatib, ochiq tasdiqni eslab… (+2 more)

### Community 29 - "web_answer.py"
Cohesion: 0.30
Nodes (13): inspect, build_request(), _create(), extract_sources(), extract_text(), _get(), _make_client(), Any (+5 more)

### Community 30 - "ConfirmationGate"
Cohesion: 0.20
Nodes (6): ConfirmationGate, _consume(), PendingConfirmation, Bir vaqtda faqat bitta faol tasdiq so'rovi. Yangi so'rov eskisini bekor qiladi., Foydalanuvchining yakuniy transkripti. So'rovdan OLDIN aytilgan gap hisobga…, Bus'dagi TRANSCRIPT (user, final) hodisalarini ham kuzatadi — gemini client…

### Community 31 - "test_wake_dictation.py"
Cohesion: 0.12
Nodes (26): is_stop_phrase(), Butun gap faqat to'xtash iborasidan iboratmi?, _candidates(), levenshtein(), name_in(), Levenshtein masofasi; `limit` berilsa undan oshgach hisoblashni to'xtatadi…, Qisqa ism aniq mos kelishi kerak; uzunroq ism 2-3 xatoni ko'taradi., (nomzod, boshlanish indeksi, so'zlar soni) — yakka so'zlar va qo'shni… (+18 more)

### Community 32 - "AudioStreamer"
Cohesion: 0.09
Nodes (21): AudioStreamer, Mikrofon → asyncio.Queue → Gemini. AUDIO_LEVEL va gate holatini nashr qiladi., Navbatga boshqaruv markeri (MARK_ACTIVITY_START/END) qo'yadi — audio bilan…, Yuboriladigan PCM chunklar yoki `str` markerlar (cheksiz; `stop()` da tugaydi)., Navbatdagi eski chunklarni tashlaydi (qayta ulanishda)., Sessiya yo'q — chunklar navbatga qo'yilmaydi (ulanishdan oldin / uzilganda)., Sessiya tayyor — eski chunklarni tashlab, oqimni davom ettiradi., make_settings() (+13 more)

### Community 33 - "compute_backoff"
Cohesion: 0.67
Nodes (3): compute_backoff(), base * 2**attempt + jitter, max_delay bilan cheklangan. `jitter` None bo'lsa…, test_compute_backoff()

### Community 34 - "CommandGuard"
Cohesion: 0.17
Nodes (11): CommandGuard, Verdict, `run_terminal_command` uchun uch pog'onali qo'riqchi. `check()` → ("allow" |…, Buyruqni tokenlarga bo'lish (POSIX qoidalari). Windows qo'riqchisi qayta…, Tekshiruvdan o'tgan buyruqni bajarish uchun argv (`~` kengaytirilgan holda)., parametrize, test_guard_allows(), test_guard_argv_expands_tilde() (+3 more)

### Community 35 - "windows_input.py"
Cohesion: 0.11
Nodes (23): combo_events(), HotkeyError, INPUT, _INPUTUNION, KEYBDINPUT, MOUSEINPUT, parse_hotkey(), press_combo() (+15 more)

### Community 36 - "DaemonRunner"
Cohesion: 0.18
Nodes (5): DaemonRunner, `nexus.main.run()` ni alohida thread'da o'z event loop'i bilan yuritadi., To'xtatish signalini beradi (bloklamaydi) — tugashini `finished` orqali…, To'xtatish signalini beradi va thread tugashini kutadi. True = toza tugadi., GUI'dan daemon'ga buyruq (thread-safe, natija kutilmaydi).

### Community 37 - "FakeLiveConnect"
Cohesion: 0.12
Nodes (9): FakeLiveConnect, 1011 'exceeded your current quota' → avval google_search grounding olib…, client.aio.live.connect o'rnini bosuvchi: har chaqiruvda navbatdagi FakeSession., test_config_fallback_order_on_1007(), connect(), test_quota_error_drops_google_search_first(), connect(), test_run_reconnects_with_resume_handle_and_counts() (+1 more)

### Community 38 - "config.py"
Cohesion: 0.10
Nodes (27): dotenv, api_key_env_path(), api_key_hint(), _describe_char(), _env_api_key(), env_candidates(), is_placeholder_api_key(), load_env_files() (+19 more)

### Community 39 - "run"
Cohesion: 0.11
Nodes (19): Event, check_environment(), _first(), MetricsTicker, platform_controller(), print_banner(), Any, EventBus (+11 more)

### Community 40 - "test_windows.py"
Cohesion: 0.07
Nodes (20): nexus_tools, looks_like_result(), Tezlik: avval minimal (0.25) gacha tushirib, keyin kerakli qadamlar., speed_presses(), _ctrl(), Windows qatlami: macOS'da ham ishlaydigan (OS chaqiruvlari mock qilingan)…, test_clipboard_passes_text_via_stdin(), test_collect_elements_filters_and_dedupes() (+12 more)

### Community 42 - "._evaluate_addressed"
Cohesion: 0.13
Nodes (7): Oxirgi real audio chunk karnayga chiqqan payt (time.monotonic; 0 — hali yo'q)., Hozir ovoz chiqyaptimi (navbatda audio bor yoki oxirgi chunk yaqinda chiqqan)., Wake rejimi bo'yicha gap bizga qaratilganmi (qisman transkriptda ham). Baho…, Joriy gap boshlangan payt (AudioStreamer RMS gate). Noma'lum yoki eskirgan…, Suhbat rejimi: ismsiz erkin suhbat; jimlikdan keyin o'zi tugaydi (`tick`)., Davriy tekshiruv (MetricsTicker): jimlik tufayli suhbat rejimini tugatish;…, Band holat (processing / tool_executing / speaking) tool ham, ijro ham, server…

### Community 43 - "FakeAudio"
Cohesion: 0.09
Nodes (12): FakeAudio, FakeRegistry, Registry yo'q (toolsiz rejim) — klient zaxira `kill_all` handlerini ro'yxatdan…, test_build_config_ptt_disables_vad_and_optional_fields(), test_client_kill_all_fallback_without_registry(), test_client_kill_all_via_registry_hook(), test_conversation_command_and_idle_tick(), test_conversation_mode_flow() (+4 more)

### Community 44 - "test_desktop.py"
Cohesion: 0.09
Nodes (27): ArgumentParser, Namespace, `base_url/health` 2xx qaytarguncha kutadi. `keep_waiting()` False qaytarsa…, wait_for_server(), build_parser(), desktop_mode(), Desktop (oyna + orb + menyu bar) rejimi kerakmi? `--headless`, `--no-ui`…, MonkeyPatch (+19 more)

### Community 45 - "video_translate.py"
Cohesion: 0.11
Nodes (34): asyncio, collections, collections_abc, ctypes, datetime, importlib, json, logging (+26 more)

### Community 46 - "WindowsBrowser"
Cohesion: 0.07
Nodes (22): browser_key(), BrowserWindow, list_browser_windows(), _cb(), pick_window(), Any, Result, Nisbiy siljish → klavishlar: 10 s lik l/j, qoldig'i 5 s lik o'qlar. (+14 more)

### Community 47 - "Any"
Cohesion: 0.12
Nodes (10): _key_hint(), Any, EventBus, Path, Har bir function_call ni registry orqali bajaradi va javobni sessiyaga…, `extended-thinking` modelida daraja majburiy (bo'sh bo'lsa "high"); boshqa…, UI (Sozlamalar) dan API kalit: tekshiradi, saqlaydi va sessiyani yangi kalit…, thinking_level_for() (+2 more)

### Community 48 - ".run"
Cohesion: 0.16
Nodes (9): GeminiConfigError, Konfiguratsiya xatosi (masalan, API kaliti yo'q)., Cheksiz ulanish sikli; `stop()` chaqirilguncha qayta ulanaveradi., Kalit Sozlamalardan (`set_api_key`) kiritilguncha yoki `stop()` gacha kutadi., `timeout` sekund (None — cheksiz) kutadi; `stop()` yoki yangi API kalit…, Sessiya juda qisqa yashagan bo'lsa (masalan, eskirgan handle) — handle…, should_drop_resume_handle(), RuntimeError (+1 more)

### Community 49 - "bus"
Cohesion: 0.22
Nodes (11): _cmd_result(), api_state(), snapshot(), ws_endpoint(), handle_command(), receiver(), send(), sender() (+3 more)

### Community 50 - "BargeInGate"
Cohesion: 0.25
Nodes (6): BargeInGate, Ijro paytida mikrofon chunklarining echo/barge-in darvozasi (callback…, → (navbatga qo'yiladigan chunklar, sukunatga almashtirilganlar soni)., test_barge_gate_flushes_held_when_playback_stops(), test_barge_gate_single_spike_becomes_silence(), test_barge_gate_sustained_opens_and_holds()

### Community 51 - "Segmenter"
Cohesion: 0.38
Nodes (4): Uzluksiz nutqni tarjima bo'laklariga ajratadi: `push(rms)` True → bo'lakni shu…, Segmenter, test_segmenter_cuts_at_max(), test_segmenter_cuts_on_quiet_after_min()

### Community 52 - "server.py"
Cohesion: 0.12
Nodes (12): contextlib, errno, FastAPI, fastapi_responses, fastapi_staticfiles, _QuietServer, UI ko'prigi: FastAPI + WebSocket server. EventBus hodisalarini brauzerdagi UI…, Signal handlerlarini o'rnatmaydigan uvicorn Server (signalni main.py… (+4 more)

### Community 53 - "test_video_translate.py"
Cohesion: 0.08
Nodes (25): attach(), build_ffmpeg_cmd(), feed_action(), fit_tempo(), parse_player_state(), main.py: bus/settings/mikrofonni ulaydi; echo guard tarjima ijrosini ham…, AppleScript: JS ni video tabida bajaradi — Chrome'da `tab_id` bo'yicha (bir xil…, Tarjima (`out_s`) videodagi qolgan oralig'iga (`window_s`) sig'ishi uchun… (+17 more)

### Community 54 - "DictationState"
Cohesion: 0.17
Nodes (6): DictationState, (teriladigan matn, to'xtash kerakmi). "…hammasi shu, to'xta" → ("…hammasi shu",…, Diktovka holati va terilgan matn hisobi., split_stop(), test_dictation_state_lifecycle(), test_split_stop()

### Community 55 - "desktop.py"
Cohesion: 0.22
Nodes (7): Desktop ilova qatlami: o'z oynasi, doim tepada turadigan orb va menyu bar…, objc, signal, threading, urllib_error, urllib_request, webkit

### Community 56 - "fake_screen"
Cohesion: 0.29
Nodes (6): ax_ready(), fake_screen(), Any, fixture, MonkeyPatch, Skrinshot/JPEG bosqichini almashtiradi: real screencapture chaqirilmaydi.

### Community 57 - "VideoTranslator"
Cohesion: 0.21
Nodes (5): Bo'laklarni `seq` tartibida, video o'z oralig'iga (`src_start`) yetganda ijroga…, Video pauza, tarjima ovozi esa davom etadi — `seconds` dan keyin video qayta…, Tarjima ulgurmayapti (masalan, kvota kam — sessiyalar yetmaydi): gapni tashlab…, turn_complete kelmay qolgan sessiyani bo'shatadi (model jim qoldi)., VideoTranslator

### Community 58 - "reference/AI analysis (old Voice Assistant)"
Cohesion: 0.14
Nodes (15): Nexus Ovoz OS design mockup (dc.html), Design mockup Component (simulated PTT command flow), Local models concept (Whisper.cpp small.uz + Qwen 7B Q4), Echo guard + playback prebuffer + low VAD start sensitivity, Gemini Live API (native audio, WebSocket), Nexus Ovoz OS (Uzbek voice assistant daemon), session.receive() ends each turn (not a disconnect), reference/AI analysis (old Voice Assistant) (+7 more)

### Community 59 - "_recognize"
Cohesion: 0.33
Nodes (6): pick_languages(), Qo'llab-quvvatlanadigan tillardan kerakli tartibda tanlaydi ("uz" → "uz-UZ"…, Vision OCR: [(text, nx, ny, nw, nh, confidence)] — normalizatsiyalangan, y…, _recognize(), supported_languages(), test_pick_languages_prefers_uz_then_ru_en_and_skips_missing()

### Community 60 - "Segment"
Cohesion: 0.12
Nodes (14): is_silent(), Javob bermagan bo'lakni navbat boshiga qaytaradi — boshqa (bo'sh) sessiya oladi., Bo'lak deyarli jim (o'rtacha RMS `SILENT_RMS` dan past)., Tarjima bo'lagi: kiruvchi audio (tayinlanguncha `buf`da) va modelning javobi…, activity_end dan keyin `no_response_s` ichida audio kelmadi — ijroda o'tkazib…, Tayinlanmagan bo'laklarni (FIFO) bo'sh sessiyalarga beradi., Segment, segment_expired() (+6 more)

### Community 61 - "._handle_server_content"
Cohesion: 0.20
Nodes (6): _asks_question(), _grounding_sources(), ToolRegistry.kill_all() ilgagi: klient tool tasklari bekor, ijro navbati…, Zaxira: registry bo'lmaganda (toolsiz rejim) `kill_all` buyrug'i., Yordamchi javobi foydalanuvchidan javob kutadimi ("Yana nima qilay?", "Labbay,…, `grounding_metadata.grounding_chunks[*].web.{uri,title}` → "title — uri"…

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
Nodes (10): Any, Bitta Live sessiya: navbatdagi bo'lakni oladi, javobini bo'lakka yozadi., Parallel sessiyalar + dispetcher + tartibli ijro., Sessiya bo'shadi — navbatdagi bo'lakni olishi mumkin., Sessiya uzildi: joriy bo'lak yakunlangan deb belgilanadi, o'zi bo'sh ro'yxatdan…, Model javobini sessiyaning joriy bo'lagiga yozadi. True — navbat tugadi…, stop_video_translation(), _Worker (+2 more)

### Community 68 - "ocr_image"
Cohesion: 0.16
Nodes (18): Box, _image_size(), lines_as_elements(), lines_to_text(), ocr_image(), Satrlarni yuqoridan pastga, bir qatordagilarni chapdan o'ngga tartiblaydi. Ikki…, Tartiblangan satrlardan matn: bir qatordagilar ikki bo'shliq bilan, qatorlar…, OCR satrlarini list_ui_elements formatiga o'giradi: {n, role:'text', label, at,… (+10 more)

### Community 69 - "is_config_rejection"
Cohesion: 0.29
Nodes (7): BaseException, is_api_key_error(), is_config_rejection(), Server kalitni rad etdimi (noto'g'ri / bekor qilingan API kalit)?, Server konfiguratsiyani rad etgan bo'lsa navbatdagi modelga bog'liq maydonni…, Server konfiguratsiyani rad etdimi (WebSocket 1007 / invalid argument), kalit…, test_is_config_rejection()

### Community 70 - "test_extensions.py"
Cohesion: 0.08
Nodes (19): nexus, fixture, parametrize, Kengaytma modullari (ax_actions, file_actions) testlari — real…, tmp_path ni ruxsat etilgan ildiz va default papka qiladi., pyobjc yo'q holat: handler xato matni qaytaradi, istisno emas., `confirmed` sxemada bo'lmasligi shart — aks holda model gate'ni chetlab o'tadi., sandbox() (+11 more)

### Community 71 - "test_registry_no_confirmation_runs_immediately"
Cohesion: 0.29
Nodes (3): test_registry_no_confirmation_runs_immediately(), test_registry_tainted_turn_requires_confirmation(), read_page()

### Community 72 - "LoopGuard"
Cohesion: 0.20
Nodes (7): LoopGuard, Any, Bir navbatda haddan ko'p yoki bir xil chaqiruvlarni to'xtatadi., None — davom et; matn — rad etish sababi (modelga tushuntirish)., test_loop_guard_identical_calls(), test_loop_guard_max_calls_per_turn(), test_loop_guard_non_consecutive_identical_calls()

### Community 73 - "._build_window"
Cohesion: 0.14
Nodes (16): default_orb_origin(), default_window_frame(), _hex_color(), _make_webview(), placeholder_html(), Oyna/orb hech bo'lmaganda `min_visible`×`min_visible` qismi bilan biror ekranda…, Ekranning pastki-o'ng burchagi (Dock/menyu bar hisobga olingan `visibleFrame`…, Ekran o'rtasida, `visibleFrame`ning `fraction` (90%) qismi (yoki `size`), min… (+8 more)

### Community 74 - "run_shell"
Cohesion: 0.18
Nodes (10): find_files(), open_with_app(), Spotlight (mdfind) yo'q joyda: nomida `query` bor fayllar (yashirin…, _walk_find(), _kill_process_group(), Jarayonni va u tug'dirgan barcha bolalarni (process group) o'ldiradi., Dasturni shell'siz ishga tushiradi. `(ok, stdout yoki stderr)` qaytaradi., run_shell() (+2 more)

### Community 76 - "wake.py"
Cohesion: 0.21
Nodes (11): dataclasses, itertools, Diktovka rejimi: foydalanuvchi gapiradi — yordamchi teradi, to'xtash…, ends_conversation(), _has_phrase(), Ism bilan chaqirish (wake): gap yordamchiga qaratilganmi? Xonada boshqa odamlar…, kel gaplashamiz", "suhbatlashaylik", "давай поговорим", "let's talk" …, bo'ldi, rahmat", "suhbatni tugat", "xayr" … (+3 more)

### Community 78 - ".get_system_info"
Cohesion: 0.40
Nodes (3): Any, SSID ni aniqlaydi. macOS 14+ da Location Services ruxsatisiz SSID `<redacted>`…, _summarize_info()

### Community 81 - "file_actions.py"
Cohesion: 0.15
Nodes (12): csv, delete_file(), _fallback_path_is_sensitive(), _is_confirmed(), list_directory(), _list_directory_sync(), Fayl, eslatma va Excel/CSV toollari — kengaytma moduli. Eksport (registry…, Model aytgan yo'lni absolyut `Path`ga aylantiradi. Bo'sh bo'lsa `default` (yoki… (+4 more)

### Community 84 - "._run"
Cohesion: 0.10
Nodes (14): find_tab_script(), player_setup_js(), Process, `pos` dan `ahead` soniya oldinga tarjima tayyormi: ijroga qo'yilgan, yoki…, Buferlash: video pauzada turadi, oldinda `GATE_AHEAD_S` tarjima tayyor bo'lgach…, AppleScript (Chrome): `video_id` ochiq tabni topib oldinga chiqaradi va id sini…, Pleyer: asl ovozni o'chirish/pasaytirish (0..1, manfiy — tegilmaydi) va ijro…, JS ni video ochilgan tabda bajaradi (faol tab emas — foydalanuvchi boshqa tabga… (+6 more)

### Community 85 - "PlaybackClock"
Cohesion: 0.14
Nodes (8): find_binary(), PlaybackClock, PATH + Homebrew papkalari (.app ichidan ishga tushganda PATH qisqa bo'ladi)., Brauzer pleyeri holatidan joriy video vaqtini baholaydi (so'rovlar orasida…, s16le mono PCM ni ohangini saqlab `tempo` barobar tezlashtiradi (ffmpeg…, time_stretch(), test_clock_interpolates_and_halts(), test_time_stretch_shortens_audio()

### Community 86 - "sys"
Cohesion: 0.15
Nodes (16): argparse, all_declarations(), build_config(), main(), passed(), Model qaysi toolni tanlashini real Gemini Live sessiyasida o'lchash (toollar…, Asosiy sxemalar + kengaytma modullari (nomlar bo'yicha takrorsiz)., Bitta buyruq: (chaqirilgan toollar [{name,args}], aytilgan matn, navbatlar… (+8 more)

### Community 88 - ".__init__"
Cohesion: 0.09
Nodes (16): AbstractEventLoop, _list_devices(), _set_device(), _default_input_index(), list_input_devices(), parse_latency(), Any, EventBus (+8 more)

### Community 89 - "WindowsCommandGuard"
Cohesion: 0.20
Nodes (6): CommandGuard, _truncate(), `run_terminal_command` qo'riqchisi — Windows (cmd) buyruqlari uchun. Asosiy…, Buyruqni qo'riqchi orqali `cmd` da bajaradi (UTF-8 kod sahifasi, shell…, WindowsCommandGuard, Verdict

### Community 90 - "TaintTracker"
Cohesion: 0.13
Nodes (11): Navbat ichida tashqi matn o'qilganini eslab qoladi., TaintTracker, CommandGuard allow/deny/confirm tiers, Loop guard (max 15 calls/turn, 3 identical), Secret redaction (redact_secrets), Security model (confirmation from user transcript/UI only), Sensitive path denial (path_is_sensitive), Taint guard (external content -> exfil/execute tools require confirmation) (+3 more)

### Community 91 - "looks_like_command"
Cohesion: 0.18
Nodes (7): looks_like_command(), SMART rejimi uchun evristika: qisqa gap + buyruq so'zi., Oxirgi chaqiruvdan keyingi oyna (follow-up yoki suhbat) hali ochiqmi?, Oyna `at` (monotonic; odatda gap BOSHLANGAN payt) da ochiq edimi? None — hozir.…, Matnda ism bormi? Bo'lsa follow-up oynasi ochiladi., Bu gapga javob berish kerakmi? (ism eshitilsa oynani ham ochadi). `at` — gap…, test_looks_like_command()

### Community 92 - "test_safety.py"
Cohesion: 0.13
Nodes (19): Model yoki log ko'rishidan oldin kalitga o'xshagan narsalarni yashiradi., redact_secrets(), Queue, _bus(), _drain(), EventBus, Xavfsizlik qatlami testlari: DANGEROUS_SHELL, looks_read_only,…, Gemini client note_utterance'ni chaqirmasa ham, bus'dagi TRANSCRIPT (user,… (+11 more)

### Community 93 - "match_app"
Cohesion: 0.13
Nodes (11): installed_apps(), match_app(), hits(), /Applications, /System/Applications, ~/Applications dagi .app nomlari (60s…, `needle` nomning boshida yoki ichidagi so'z boshida keladi ("word" ≠…, Aytilgan nomga mos o'rnatilgan ilovalar, eng yaqini birinchi. Tartib: aniq…, _starts_a_word(), Path (+3 more)

### Community 94 - "_ps_quote"
Cohesion: 0.67
Nodes (3): _ps_quote(), PowerShell bitta qo'shtirnoqli literal., test_ps_quote_escapes_single_quotes()

### Community 95 - "windows_smoke.py"
Cohesion: 0.31
Nodes (8): browser_smoke(), check(), main(), Path, Windows smoke testi: registry, xavfsiz toollar va UI serveri haqiqiy Windows'da…, Muhitga bog'liq tekshiruv (brauzerning birinchi ishga tushishi va h.k.) —…, soft(), tempfile

### Community 97 - "AudioPlayer"
Cohesion: 0.12
Nodes (11): AudioPlayer, 24 kHz int16 mono ijro. `enqueue` istalgan thread/task'dan chaqirilishi mumkin.…, Buferdagi qolgan audioni (prebuffer to'lmagan bo'lsa ham) ijroga qo'yib…, Navbatni tozalaydi (interruption). Tashlangan chunklar sonini qaytaradi., test_interrupted_cancels_tools_and_generation_complete_plays_out(), test_player_arms_stalled_short_reply(), test_player_callback_and_clear(), test_player_is_playing_tail() (+3 more)

### Community 99 - ".register_commands"
Cohesion: 0.16
Nodes (8): _mute(), _playback(), _ptt(), _ptt_press(), _sensitivity(), Sezgirlik (0..1) → RMS bo'sag'asi. 1.0 = juda sezgir (past bo'sag'a)., sensitivity_to_threshold(), test_sensitivity_threshold_monotonic()

### Community 100 - "build_ytdlp_cmd"
Cohesion: 0.29
Nodes (5): build_ytdlp_cmd(), Faqat audio yuklanadi; stdout: 1-qator sarlavha, oxirgi qator fayl yo'li., yt-dlp: audio faylni vaqtinchalik papkaga yuklaydi. (ok, sarlavha | xato).…, watch_url(), test_build_ytdlp_cmd()

### Community 102 - "cli"
Cohesion: 0.18
Nodes (9): DesktopOptions, _env_true(), argparse Namespace (nexus.main.build_parser) → DesktopOptions., cli(), Path, Konsol + aylanma log fayl (`~/.nexus/logs/nexus.log`, 2 MB × 3) — .app'da ham…, Windows konsoli/pipe cp1252 bo'lishi mumkin — o'zbekcha belgilar (ʼ, —)…, setup_logging() (+1 more)

### Community 103 - "browser"
Cohesion: 0.25
Nodes (8): browser(), fake_keys(), fake_window(), _bw(), keys(), fixture, test_youtube_refuses_non_youtube_tab(), other()

### Community 104 - "is_junk_translation"
Cohesion: 0.33
Nodes (6): is_junk_translation(), Model tarjima o'rniga yorliq/izoh aytdi (`(Uzbek translation: …)`, `<no…, youtube_id(), parametrize, test_is_junk_translation(), test_youtube_id()

### Community 105 - "path_allowed"
Cohesion: 0.29
Nodes (6): path_allowed(), Yo'l ruxsat etilgan ildizlar ostida va sezgir emasligini tekshiradi., POSIX_ONLY, test_allowed_paths(), test_delete_file_moves_to_trash_via_finder(), test_outside_home_rejected()

### Community 116 - "is_quota_error"
Cohesion: 0.50
Nodes (4): is_quota_error(), BaseException, Kalit kvotasi (bir vaqtdagi sessiyalar soni yoki kunlik limit) tugadi., test_is_quota_error()

### Community 117 - "pytest"
Cohesion: 0.29
Nodes (6): pytest, fixture, MonkeyPatch, Umumiy test sozlamalari., Registry testlari OS'dan mustaqil: Windows'da ham to'liq (macOS) tool ro'yxati…, _registry_as_macos()

### Community 119 - "_coerce_cell_value"
Cohesion: 0.67
Nodes (3): _coerce_cell_value(), 250000" → 250000, "3.5" → 3.5; qolgani satr. Telefon (+998...) va 007 satr…, test_coerce_cell_value()

### Community 121 - "spoken_verdict"
Cohesion: 0.67
Nodes (3): True = rozi, False = rad, None = javob emas. Rad etish (veto) gap uzunligidan…, spoken_verdict(), test_spoken_verdict()

## Ambiguous Edges - Review These
- `Gemini Live API (native audio, WebSocket)` → `Local models concept (Whisper.cpp small.uz + Qwen 7B Q4)`  [AMBIGUOUS]
  design/Nexus Ovoz OS.dc.html · relation: conceptually_related_to

## Knowledge Gaps
- **18 isolated node(s):** `INPUT`, `_INPUTUNION`, `MOUSEINPUT`, `Live transcript box`, `Session resumption + context compression` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 678 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Gemini Live API (native audio, WebSocket)` and `Local models concept (Whisper.cpp small.uz + Qwen 7B Q4)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `GeminiLiveClient` connect `GeminiLiveClient` to `AudioStreamer`, `is_config_rejection`, `Nexus Ovoz OS README`, `._evaluate_addressed`, `._confirmation_pending`, `video_translate.py`, `Any`, `.run`, `._publish_metrics`, `.__init__`, `WakeState`, `reference/AI analysis (old Voice Assistant)`, `._handle_server_content`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `ToolRegistry` connect `ToolRegistry` to `Result`, `test_registry_loads_extension_modules`, `run`, `test_registry_no_confirmation_runs_immediately`, `Nexus Ovoz OS README`, `._build_handlers`, `FakeAudio`, `test_tools.py`, `video_translate.py`, `WindowsBrowser`, `WindowsController`, `path_is_sensitive`, `test_video_translate.py`, `_registry`, `TaintTracker`, `test_safety.py`, `windows_smoke.py`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Why does `WindowsBrowser` connect `WindowsBrowser` to `Result`, `browser`, `test_windows.py`, `video_translate.py`, `ToolRegistry`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `GeminiLiveClient` (e.g. with `WakeState` and `session.receive() ends each turn (not a disconnect)`) actually correct?**
  _`GeminiLiveClient` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `ToolRegistry` (e.g. with `run()` and `WindowsController`) actually correct?**
  _`ToolRegistry` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `VideoTranslator` (e.g. with `AudioPlayer` and `BrowserController`) actually correct?**
  _`VideoTranslator` has 2 INFERRED edges - model-reasoned connections that need verification._