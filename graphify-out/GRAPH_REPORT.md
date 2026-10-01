# Graph Report - nexus  (2026-10-01)

## Corpus Check
- 52 files · ~110,164 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 4, .command 2, .example 1)

## Summary
- 2243 nodes · 4943 edges · 134 communities (103 shown, 31 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 329 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6e80a246`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- support.js
- file_actions.py
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
- Result
- screen_reader.py
- test_screen_reader.py
- ToolRegistry
- path_is_sensitive
- video_translate.py
- check_setup.py
- ._process_chunk
- WakeState
- _registry
- DesktopPrefs
- ws_reconnect_harness.js
- create_app
- WindowsBrowser
- ConfirmationGate
- test_wake_dictation.py
- .register_commands
- Any
- CommandGuard
- windows_input.py
- DaemonRunner
- test_run_waits_for_api_key_from_settings
- config.py
- main.py
- test_windows.py
- AudioStreamer
- ._evaluate_addressed
- FakeAudio
- test_desktop.py
- macos_actions.py
- ._window
- Any
- .run
- snapshot
- BargeInGate
- Segmenter
- server.py
- test_video_translate.py
- DictationState
- .tick
- web_search
- VideoTranslator
- ocr_image
- desktop.py
- MetricsTicker
- ._handle_server_content
- Process
- schemas.py
- NexusOrbPanel
- normalise
- fake_screen
- Any
- build_ytdlp_cmd
- is_config_rejection
- test_extensions.py
- test_registry_no_confirmation_runs_immediately
- LoopGuard
- ._build_window
- resolve_path
- nexus/__init__.py
- gemini_live_client.py
- build_app.sh
- describe_screen
- nexus-voice
- desktop_win.py
- FakeStream
- BaseException
- ._run
- PlaybackClock
- benchmark_live.py
- CLAUDE.md
- AudioPlayer
- redact_secrets
- reference/AI analysis (old Voice Assistant)
- looks_like_command
- test_safety.py
- match_app
- Orb overlay page (orb.html)
- windows_smoke.py
- .click_by_text
- Process
- player_setup_js
- Path
- Result
- .get_system_info
- _recognize
- _bw
- Security model (confirmation from user transcript/UI only)
- path_allowed
- ._confirmation_pending
- error_text
- fixture
- parametrize
- AbstractEventLoop
- BaseException
- test_registry_kill_all_runs_hook_and_cancels_gate
- Queue
- Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline
- _FakeModels
- is_terminal_app
- _registry_as_macos
- Settings
- _coerce_cell_value
- TaintTracker
- spoken_verdict
- test_registry_loads_extension_modules
- voice_picker.py
- EventBus
- .kill_all
- Verdict
- test_ws_slow_command_does_not_block_following_commands
- installed_apps
- .build_hotkey_script
- _dictation
- _cmd
- Any
- Result

## God Nodes (most connected - your core abstractions)
1. `GeminiLiveClient` - 59 edges
2. `MacOSController` - 57 edges
3. `VideoTranslator` - 55 edges
4. `ToolRegistry` - 54 edges
5. `WindowsController` - 50 edges
6. `WindowsBrowser` - 49 edges
7. `AudioStreamer` - 49 edges
8. `NexusDesktopApp` - 46 edges
9. `make_client()` - 41 edges
10. `FakeSession` - 32 edges

## Surprising Connections (you probably didn't know these)
- `Confirmation card (TASDIQ KUTILMOQDA, Yes/No, TTL)` --shares_data_with--> `ConfirmationGate`  [INFERRED]
  ui/index.html → nexus/safety.py
- `session.receive() ends each turn (not a disconnect)` --rationale_for--> `GeminiLiveClient`  [INFERRED]
  README.md → nexus/gemini_live_client.py
- `Echo guard + playback prebuffer + low VAD start sensitivity` --rationale_for--> `AudioStreamer`  [INFERRED]
  README.md → nexus/audio_streamer.py
- `.env settings (GEMINI_MODEL, VAD_THRESHOLD, WAKE_MODE, UI_PORT ...)` --references--> `Settings`  [EXTRACTED]
  README.md → nexus/config.py
- `ToolRegistry.execute flow: validate -> loop guard -> taint -> confirm -> handler` --references--> `ToolRegistry`  [EXTRACTED]
  README.md → nexus/tools/registry.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Tool execution safety pipeline** — readme_toolregistry_execute_flow, readme_loop_guard, readme_taint_guard, readme_commandguard_tiers, nexus_safety_confirmationgate [EXTRACTED 1.00]
- **Echo / self-hearing mitigation** — readme_echo_guard, reference_analysis_live_api_findings, nexus_audio_streamer_audiostreamer, nexus_audio_streamer_audioplayer [INFERRED 0.85]
- **WebSocket /ws event consumers** — readme_ui_event_contract, ui_index, ui_orb, nexus_events_eventbus [INFERRED 0.85]

## Communities (134 total, 31 thin omitted)

### Community 0 - "support.js"
Cohesion: 0.06
Nodes (75): boot(), bundledBlob(), cdnScriptFor(), collectProps(), compileAttr(), compileTemplate(), contentKey(), createComponentFactory() (+67 more)

### Community 1 - "file_actions.py"
Cohesion: 0.19
Nodes (26): _append_csv(), _append_row_sync(), append_spreadsheet_row(), _append_xlsx(), delete_file(), _fallback_path_is_sensitive(), _is_confirmed(), list_directory() (+18 more)

### Community 2 - "ax_actions.py"
Cohesion: 0.07
Nodes (72): applicationservices, difflib, _actions(), activate_element(), _app_root(), _attr(), available(), _clean_text() (+64 more)

### Community 3 - "Result"
Cohesion: 0.06
Nodes (28): app_name(), BrowserController, BrowserDOMController, _fmt_time(), _js_error(), js_to_applescript(), normalize_url(), _parse_json() (+20 more)

### Community 4 - "GeminiLiveClient"
Cohesion: 0.18
Nodes (4): GeminiLiveClient, Har bir function_call ni registry orqali bajaradi va javobni sessiyaga…, Final transkript bo'lagini darhol teradi; to'xtash iborasi rejimni tugatadi., Session resumption + context compression

### Community 5 - "test_core.py"
Cohesion: 0.07
Nodes (49): GeminiLiveClient, math, numpy, SimpleNamespace, sounddevice, _audio_part(), fake_sd(), FakeSession (+41 more)

### Community 6 - "app.js"
Cohesion: 0.12
Nodes (58): answerConfirm(), applyDevices(), applySettings(), applySnapshot(), bind(), closeSocket(), connect(), ensureRow() (+50 more)

### Community 7 - "test_tools.py"
Cohesion: 0.08
Nodes (27): _no_sleep(), MonkeyPatch, Tool qatlami testlari — real macOS tizimiga tegmaydi (osascript/subprocess…, Barcha ichki JS'lar AppleScript literaliga qo'yilganda qo'shtirnoq muvozanati…, ScriptRecorder, test_browser_open_url_normalizes(), test_is_terminal_frontmost(), test_launch_app_uses_fuzzy_match() (+19 more)

### Community 8 - "EventBus"
Cohesion: 0.17
Nodes (6): CommandHandler, EventBus, AbstractEventLoop, Any, Queue, Thread-safe pub/sub. `publish` istalgan thread'dan chaqirilishi mumkin.

### Community 9 - "Nexus Ovoz OS README"
Cohesion: 0.22
Nodes (11): Nexus Ovoz OS README, AXManualAccessibility for Chrome/Electron, Dictation mode (direct typing, stop phrases), .env settings (GEMINI_MODEL, VAD_THRESHOLD, WAKE_MODE, UI_PORT ...), EXTENSION_MODULES (TOOL_DECLARATIONS + HANDLERS), macOS permissions (Microphone, Accessibility, Screen Recording, Automation), Scripts: check_setup, benchmark_live, voice_picker, Tool catalog (62 tools: 45 core + 10 file + 7 AX) (+3 more)

### Community 10 - "._build_handlers"
Cohesion: 0.06
Nodes (18): browser_click_button(), browser_click_selector(), browser_close_tab(), browser_current_page(), browser_list_tabs(), browser_open_url(), browser_read_page(), browser_reload() (+10 more)

### Community 11 - "NexusDesktopApp"
Cohesion: 0.09
Nodes (8): _load_url(), NexusDesktopApp, Any, NSApplication delegati: oyna, orb, menyu bar, daemon ko'prigi., SIGINT/SIGTERM → toza chiqish. Mach-port orqali AppKit run loop'ida qayta…, Daemon thread'idan chaqiriladi — hodisani GUI thread'iga uzatadi., `.env` ni Finder'da ko'rsatadi (yagona "tashqi ochish" — brauzer emas)., NSObject

### Community 12 - "MacOSController"
Cohesion: 0.13
Nodes (9): _clamp(), MacOSController, Result, SSID ni aniqlaydi. macOS 14+ da Location Services ruxsatisiz SSID `<redacted>`…, AppleScript'ni `osascript` orqali bajaradi (stdin orqali, argument uzunligi…, macOS bilan ishlash: ovoz, media, ilovalar, Finder, tizim, terminal., macOS 12+ da DND uchun ochiq API yo'q. Foydalanuvchi yaratgan Shortcuts…, Faol oynaga matn kiritadi: bufer + Cmd+V (keystroke o'zbek/kirill matnni… (+1 more)

### Community 13 - "test_server.py"
Cohesion: 0.12
Nodes (20): fastapi_testclient, google-genai Client — hamma joyda bir xil sozlama bilan., Settings, TestClient, test_config_defaults_gemini38(), test_wake_defaults_to_name_only(), client(), _free_port() (+12 more)

### Community 14 - "windows_screen.py"
Cohesion: 0.10
Nodes (53): io, work(), run(), _activate(), _ask_gemini(), capture_window_jpeg(), _click_point(), _click_sync() (+45 more)

### Community 15 - "state_style"
Cohesion: 0.22
Nodes (10): effective_state(), (rang, yorliq) — menyu bar / orb uchun., Menyu bar'dagi holat satri, masalan "● Tinglamoqda" yoki "● Kutmoqda (mikrofon…, Daemon holati + Gemini ulanishi + tasdiqdan bitta ko'rsatiladigan holat., state_style(), status_title(), parametrize, test_effective_state_priorities() (+2 more)

### Community 16 - "Result"
Cohesion: 0.10
Nodes (11): MacOSController, _press_key(), _ps_quote(), PowerShell bitta qo'shtirnoqli literal., PowerShell skriptini konsol oynasiz bajaradi; chiqish UTF-8., Windows bilan ishlash: ovoz, media, ilovalar, Explorer, tizim., Faol oynaga matn teradi (SendInput Unicode — bufer o'zgarmaydi)., run_powershell() (+3 more)

### Community 17 - "screen_reader.py"
Cohesion: 0.15
Nodes (19): appkit, foundation, capture_frontmost_window(), _shoot(), _front_app(), _front_window_info(), _image_size(), _largest_window() (+11 more)

### Community 18 - "test_screen_reader.py"
Cohesion: 0.10
Nodes (14): Vision normalizatsiyalangan bbox (0..1, y PASTDAN) → ekran (x, y, w, h),…, vision_box_to_screen(), _box(), screen_reader (OCR + Gemini ko'rish) va ax_actions'dagi AX→OCR zaxira yo'li…, test_click_ui_element_by_ocr_index_from_cache(), test_lines_as_elements_centres_and_roles(), test_lines_to_text_groups_rows_and_truncates(), test_list_ui_elements_merges_ax_and_ocr() (+6 more)

### Community 19 - "ToolRegistry"
Cohesion: 0.10
Nodes (12): EventBus, Foydalanuvchi yangi gap boshladi: loop guard va taint tozalanadi., Foydalanuvchining yakuniy transkripti — og'zaki tasdiq uchun., Gemini toollarini bajaruvchi markaziy ro'yxat., ToolRegistry, test_conversation_tools_registered(), test_registry_has_handler_for_every_declaration(), test_registry_unknown_tool() (+4 more)

### Community 20 - "path_is_sensitive"
Cohesion: 0.13
Nodes (17): Verdict, Buyruqni tokenlarga bo'lish (POSIX qoidalari). Windows qo'riqchisi qayta…, looks_read_only(), path_is_sensitive(), Path, True — buyruq DANGEROUS_SHELL naqshlaridan biriga mos keladi., True — buyruq HECH QANDAY bayroq bilan ham hech narsani o'zgartira olmaydi., True — bu yerga yozish persistensiya yaratishi yoki sir sizdirishi mumkin. (+9 more)

### Community 21 - "video_translate.py"
Cohesion: 0.21
Nodes (10): asyncio, YouTube videosini jonli (sinxron) ovozli tarjima: ingliz → o'zbek. Oqim: yt-dlp…, mark_gui_ready(), Windows: video tarjima uchun YouTube'ni Nexus'ning o'z WebView2 oynasida…, check(), main(), Windows: pywebview (WebView2) oynasida JS bajarish — video tarjima kanali…, sys (+2 more)

### Community 22 - "check_setup.py"
Cohesion: 0.14
Nodes (27): CDLL, inspect, build_request(), _create(), extract_sources(), extract_text(), _get(), _make_client() (+19 more)

### Community 23 - "._process_chunk"
Cohesion: 0.09
Nodes (19): compute_rms(), echo_gate(), gate_open(), Yordamchi gapirayotganda mikrofon chunk'i o'tkazilsinmi? True = o'tkaz. Guard…, Callback thread'da: darajani hisoblaydi, gate'ni yangilaydi, navbatga qo'yadi.…, Yordamchi buyruq ustida ishlayaptimi (o'ylayapti / tool bajaryapti /…, Yordamchi javobi paytida mikrofon to'liq bostirilsinmi?, int16 mono PCM baytlaridan (rms 0..1, db -60..0) qaytaradi. (+11 more)

### Community 24 - "WakeState"
Cohesion: 0.09
Nodes (13): Yordamchi hozir unga gapirilayotganini kuzatadi., Yordamchi javobi savol bilan tugadimi — keyingi oyna uzunroq bo'ladi., `follow_up` — aniq tugatilganda oddiy follow-up oynasi qoladi (xayrlashuv…, Suhbat rejimi yoqilgan, lekin `conversation_idle_s` jimlikdan keyin tugashi…, Oynani yangilash — yordamchi hozirgina foydalanuvchi uchun nimadir qildi., Oyna ochiq bo'lsa, uni `ts` (monotonic) dan boshlab hisoblaydi — masalan…, WakeState, test_wake_conversation_window_and_expiry() (+5 more)

### Community 25 - "_registry"
Cohesion: 0.15
Nodes (13): MonkeyPatch, Handler `needs_confirmation` qaytarsa registry gate'ni so'raydi va…, _registry(), test_registry_confirmation_via_bus_utterance_command(), test_registry_confirmations_command_toggles(), test_registry_dictation_tools(), test_registry_handler_needs_confirmation_dict(), test_registry_kill_all_cancels_pending_confirmation() (+5 more)

### Community 26 - "DesktopPrefs"
Cohesion: 0.09
Nodes (13): DesktopOptions, DesktopPrefs, _env_true(), _make_app_icon(), _pair(), Path, Desktop ilovani ishga tushiradi (asosiy thread'da bloklaydi). Qaytadi: chiqish…, argparse Namespace (nexus.main.build_parser) → DesktopOptions. (+5 more)

### Community 27 - "ws_reconnect_harness.js"
Cohesion: 0.12
Nodes (9): ref_fs, byId(), els, FakeWS, fs, listeners, makeEl(), sockets (+1 more)

### Community 28 - "create_app"
Cohesion: 0.12
Nodes (10): _ConfirmTracker, create_app(), api_state(), index(), EventBus, Path, Settings, FastAPI ilovasini yaratadi (testlarda ham shu ishlatiladi). (+2 more)

### Community 29 - "WindowsBrowser"
Cohesion: 0.14
Nodes (5): Nisbiy siljish → klavishlar: 10 s lik l/j, qoldig'i 5 s lik o'qlar., Brauzer amallari — macOS'dagi BrowserController/DOM/YouTube/Search sinflari…, seek_presses(), WindowsBrowser, test_seek_presses()

### Community 30 - "ConfirmationGate"
Cohesion: 0.14
Nodes (11): ConfirmationGate, _consume(), PendingConfirmation, Any, Bir vaqtda faqat bitta faol tasdiq so'rovi. Yangi so'rov eskisini bekor qiladi., Foydalanuvchining yakuniy transkripti. So'rovdan OLDIN aytilgan gap hisobga…, Bus'dagi TRANSCRIPT (user, final) hodisalarini ham kuzatadi — gemini client…, test_gate_ignores_long_sentence_with_ha() (+3 more)

### Community 31 - "test_wake_dictation.py"
Cohesion: 0.12
Nodes (26): is_stop_phrase(), Butun gap faqat to'xtash iborasidan iboratmi?, _candidates(), levenshtein(), name_in(), Levenshtein masofasi; `limit` berilsa undan oshgach hisoblashni to'xtatadi…, Qisqa ism aniq mos kelishi kerak; uzunroq ism 2-3 xatoni ko'taradi., (nomzod, boshlanish indeksi, so'zlar soni) — yakka so'zlar va qo'shni… (+18 more)

### Community 32 - ".register_commands"
Cohesion: 0.08
Nodes (16): _list_devices(), _mute(), _playback(), _ptt(), _ptt_press(), _sensitivity(), _set_device(), _default_input_index() (+8 more)

### Community 33 - "Any"
Cohesion: 0.15
Nodes (8): Handler, normalize_browser(), Any, Handler javobini (tuple yoki dict) yagona formatga keltiradi., Bajarishdan OLDIN aniqlanadigan tasdiq sabablari (bo'sh — tasdiqsiz)., _to_text(), _truncate(), translate_video()

### Community 34 - "CommandGuard"
Cohesion: 0.22
Nodes (9): CommandGuard, `run_terminal_command` uchun uch pog'onali qo'riqchi. `check()` → ("allow" |…, Tekshiruvdan o'tgan buyruqni bajarish uchun argv (`~` kengaytirilgan holda)., parametrize, test_guard_allows(), test_guard_argv_expands_tilde(), test_guard_confirms(), test_guard_denies() (+1 more)

### Community 35 - "windows_input.py"
Cohesion: 0.08
Nodes (27): CommandGuard, `run_terminal_command` qo'riqchisi — Windows (cmd) buyruqlari uchun. Asosiy…, WindowsCommandGuard, combo_events(), HotkeyError, INPUT, _INPUTUNION, KEYBDINPUT (+19 more)

### Community 36 - "DaemonRunner"
Cohesion: 0.16
Nodes (5): DaemonRunner, `nexus.main.run()` ni alohida thread'da o'z event loop'i bilan yuritadi., To'xtatish signalini beradi (bloklamaydi) — tugashini `finished` orqali…, To'xtatish signalini beradi va thread tugashini kutadi. True = toza tugadi., GUI'dan daemon'ga buyruq (thread-safe, natija kutilmaydi).

### Community 37 - "test_run_waits_for_api_key_from_settings"
Cohesion: 0.10
Nodes (11): FakeLiveConnect, 1011 'exceeded your current quota' → avval google_search grounding olib…, client.aio.live.connect o'rnini bosuvchi: har chaqiruvda navbatdagi FakeSession., test_config_fallback_order_on_1007(), connect(), test_quota_error_drops_google_search_first(), connect(), test_run_drops_resume_handle_after_short_session() (+3 more)

### Community 38 - "config.py"
Cohesion: 0.11
Nodes (25): dotenv, api_key_env_path(), _describe_char(), _env_api_key(), env_candidates(), is_placeholder_api_key(), load_env_files(), load_extra_env() (+17 more)

### Community 39 - "main.py"
Cohesion: 0.11
Nodes (22): argparse, Event, Namespace, nexus, list_input_devices(), [{"index", "name", "default"}] — faqat kirish (mikrofon) qurilmalari., check_environment(), cli() (+14 more)

### Community 40 - "test_windows.py"
Cohesion: 0.05
Nodes (25): nexus_tools, Tezlik: avval minimal (0.25) gacha tushirib, keyin kerakli qadamlar., speed_presses(), Bitta video oynasi: ochish (yoki mavjudida yangi URL), JS bajarish, yopilganini…, WebViewVideoHost, _ctrl(), Windows qatlami: macOS'da ham ishlaydigan (OS chaqiruvlari mock qilingan)…, test_clipboard_passes_text_via_stdin() (+17 more)

### Community 41 - "AudioStreamer"
Cohesion: 0.09
Nodes (21): AudioStreamer, Mikrofon → asyncio.Queue → Gemini. AUDIO_LEVEL va gate holatini nashr qiladi., Navbatga boshqaruv markeri (MARK_ACTIVITY_START/END) qo'yadi — audio bilan…, Yuboriladigan PCM chunklar yoki `str` markerlar (cheksiz; `stop()` da tugaydi)., Navbatdagi eski chunklarni tashlaydi (qayta ulanishda)., Sessiya yo'q — chunklar navbatga qo'yilmaydi (ulanishdan oldin / uzilganda)., Sessiya tayyor — eski chunklarni tashlab, oqimni davom ettiradi., make_settings() (+13 more)

### Community 42 - "._evaluate_addressed"
Cohesion: 0.13
Nodes (6): Oxirgi real audio chunk karnayga chiqqan payt (time.monotonic; 0 — hali yo'q)., UI dan matn buyrug'i. Sessiya yo'q bo'lsa False., Registry'ga foydalanuvchi navbatini bildiradi: og'zaki tasdiq (note_utterance)…, Wake rejimi bo'yicha gap bizga qaratilganmi (qisman transkriptda ham). Baho…, Joriy gap boshlangan payt (AudioStreamer RMS gate). Noma'lum yoki eskirgan…, Suhbat rejimi: ismsiz erkin suhbat; jimlikdan keyin o'zi tugaydi (`tick`).

### Community 43 - "FakeAudio"
Cohesion: 0.10
Nodes (11): FakeAudio, FakeRegistry, Registry yo'q (toolsiz rejim) — klient zaxira `kill_all` handlerini ro'yxatdan…, test_build_config_ptt_disables_vad_and_optional_fields(), test_client_kill_all_fallback_without_registry(), test_client_kill_all_via_registry_hook(), test_conversation_command_and_idle_tick(), test_conversation_mode_flow() (+3 more)

### Community 44 - "test_desktop.py"
Cohesion: 0.10
Nodes (24): ArgumentParser, `base_url/health` 2xx qaytarguncha kutadi. `keep_waiting()` False qaytarsa…, wait_for_server(), build_parser(), MonkeyPatch, Path, nexus.desktop — GUI'siz (sof-Python) qismlarning testlari. Cocoa…, start.command: bo'sh/namunaviy GEMINI_API_KEY → Sozlamalarga yo'naltiruvchi… (+16 more)

### Community 45 - "macos_actions.py"
Cohesion: 0.13
Nodes (26): collections, collections_abc, ctypes, datetime, importlib, json, logging, Mikrofon oqimi va ovoz ijrosi (sounddevice / PortAudio). `AudioStreamer` —… (+18 more)

### Community 46 - "._window"
Cohesion: 0.10
Nodes (14): Any, BrowserWindow, document_tree(), list_browser_windows(), _cb(), Sahifa (DocumentControl) elementlari. Chromium veb-kontent daraxtini UIA mijozi…, Ko'rinadigan brauzer oynalari, Z-tartibda (eng ustidagisi birinchi)., `fn(auto, root)` ni UIA ishga tushirilgan thread'da bajaradi. (+6 more)

### Community 47 - "Any"
Cohesion: 0.14
Nodes (8): Any, EventBus, Path, `extended-thinking` modelida daraja majburiy (bo'sh bo'lsa "high"); boshqa…, `receive()` har navbatda tugaydi — qayta chaqiramiz; bo'sh iteratsiya = uzilish., thinking_level_for(), _to_function_declarations(), test_thinking_level_for()

### Community 48 - ".run"
Cohesion: 0.13
Nodes (14): compute_backoff(), GeminiConfigError, _key_hint(), UI (Sozlamalar) dan API kalit: tekshiradi, saqlaydi va sessiyani yangi kalit…, Konfiguratsiya xatosi (masalan, API kaliti yo'q)., Cheksiz ulanish sikli; `stop()` chaqirilguncha qayta ulanaveradi., Kalit Sozlamalardan (`set_api_key`) kiritilguncha yoki `stop()` gacha kutadi., `timeout` sekund (None — cheksiz) kutadi; `stop()` yoki yangi API kalit… (+6 more)

### Community 49 - "snapshot"
Cohesion: 0.36
Nodes (9): _cmd_result(), snapshot(), ws_endpoint(), handle_command(), receiver(), send(), sender(), Any (+1 more)

### Community 50 - "BargeInGate"
Cohesion: 0.25
Nodes (6): BargeInGate, Ijro paytida mikrofon chunklarining echo/barge-in darvozasi (callback…, → (navbatga qo'yiladigan chunklar, sukunatga almashtirilganlar soni)., test_barge_gate_flushes_held_when_playback_stops(), test_barge_gate_single_spike_becomes_silence(), test_barge_gate_sustained_opens_and_holds()

### Community 51 - "Segmenter"
Cohesion: 0.38
Nodes (4): Uzluksiz nutqni tarjima bo'laklariga ajratadi: `push(rms)` True → bo'lakni shu…, Segmenter, test_segmenter_cuts_at_max(), test_segmenter_cuts_on_quiet_after_min()

### Community 52 - "server.py"
Cohesion: 0.10
Nodes (14): contextlib, errno, FastAPI, fastapi_responses, fastapi_staticfiles, _QuietServer, UI ko'prigi: FastAPI + WebSocket server. EventBus hodisalarini brauzerdagi UI…, Signal handlerlarini o'rnatmaydigan uvicorn Server (signalni main.py… (+6 more)

### Community 53 - "test_video_translate.py"
Cohesion: 0.08
Nodes (25): attach(), build_ffmpeg_cmd(), fit_tempo(), is_quota_error(), parse_player_state(), main.py: bus/settings/mikrofonni ulaydi; echo guard tarjima ijrosini ham…, AppleScript: JS ni video tabida bajaradi — Chrome'da `tab_id` bo'yicha (bir xil…, Kalit kvotasi (bir vaqtdagi sessiyalar soni yoki kunlik limit) tugadi. (+17 more)

### Community 54 - "DictationState"
Cohesion: 0.17
Nodes (6): DictationState, (teriladigan matn, to'xtash kerakmi). "…hammasi shu, to'xta" → ("…hammasi shu",…, Diktovka holati va terilgan matn hisobi., split_stop(), test_dictation_state_lifecycle(), test_split_stop()

### Community 55 - ".tick"
Cohesion: 0.33
Nodes (3): Hozir ovoz chiqyaptimi (navbatda audio bor yoki oxirgi chunk yaqinda chiqqan)., Davriy tekshiruv (MetricsTicker): jimlik tufayli suhbat rejimini tugatish;…, Band holat (processing / tool_executing / speaking) tool ham, ijro ham, server…

### Community 56 - "web_search"
Cohesion: 0.50
Nodes (4): build_search_url(), web_search(), web_search_h(), test_build_search_url()

### Community 57 - "VideoTranslator"
Cohesion: 0.11
Nodes (16): Bo'laklarni `seq` tartibida, video o'z oralig'iga (`src_start`) yetganda ijroga…, Javob bermagan bo'lakni navbat boshiga qaytaradi — boshqa (bo'sh) sessiya oladi., Tarjima ulgurmayapti (masalan, kvota kam — sessiyalar yetmaydi): gapni tashlab…, turn_complete kelmay qolgan sessiyani bo'shatadi (model jim qoldi)., Tarjima bo'lagi: kiruvchi audio (tayinlanguncha `buf`da) va modelning javobi…, activity_end dan keyin `no_response_s` ichida audio kelmadi — ijroda o'tkazib…, Tayinlanmagan bo'laklarni (FIFO) bo'sh sessiyalarga beradi., Sessiya bo'shadi — navbatdagi bo'lakni olishi mumkin. (+8 more)

### Community 58 - "ocr_image"
Cohesion: 0.19
Nodes (15): Box, available(), lines_as_elements(), lines_to_text(), ocr_image(), Satrlarni yuqoridan pastga, bir qatordagilarni chapdan o'ngga tartiblaydi. Ikki…, Tartiblangan satrlardan matn: bir qatordagilar ikki bo'shliq bilan, qatorlar…, OCR satrlarini list_ui_elements formatiga o'giradi: {n, role:'text', label, at,… (+7 more)

### Community 59 - "desktop.py"
Cohesion: 0.25
Nodes (6): Desktop ilova qatlami: o'z oynasi, doim tepada turadigan orb va menyu bar…, objc, signal, urllib_error, urllib_request, webkit

### Community 60 - "MetricsTicker"
Cohesion: 0.17
Nodes (11): _first(), MetricsTicker, platform_controller(), Any, EventBus, Berilgan kalitlardan birinchi None bo'lmagan qiymat., Joriy OS uchun tizim kontrolleri (macOS — AppleScript, Windows —…, Har `interval` sekundda cpu/ram/battery ni METRICS ga nashr qiladi. (+3 more)

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

### Community 66 - "fake_screen"
Cohesion: 0.29
Nodes (6): ax_ready(), fake_screen(), Any, fixture, MonkeyPatch, Skrinshot/JPEG bosqichini almashtiradi: real screencapture chaqirilmaydi.

### Community 67 - "Any"
Cohesion: 0.15
Nodes (12): is_silent(), Any, Bo'lak deyarli jim (o'rtacha RMS `SILENT_RMS` dan past)., Bitta Live sessiya: navbatdagi bo'lakni oladi, javobini bo'lakka yozadi., Parallel sessiyalar + dispetcher + tartibli ijro., Sessiya uzildi: joriy bo'lak yakunlangan deb belgilanadi, o'zi bo'sh ro'yxatdan…, Model javobini sessiyaning joriy bo'lagiga yozadi. True — navbat tugadi…, stop_video_translation() (+4 more)

### Community 68 - "build_ytdlp_cmd"
Cohesion: 0.29
Nodes (5): build_ytdlp_cmd(), Faqat audio yuklanadi; stdout: 1-qator sarlavha, oxirgi qator fayl yo'li., yt-dlp: audio faylni vaqtinchalik papkaga yuklaydi. (ok, sarlavha | xato).…, watch_url(), test_build_ytdlp_cmd()

### Community 69 - "is_config_rejection"
Cohesion: 0.29
Nodes (7): BaseException, is_api_key_error(), is_config_rejection(), Server kalitni rad etdimi (noto'g'ri / bekor qilingan API kalit)?, Server konfiguratsiyani rad etgan bo'lsa navbatdagi modelga bog'liq maydonni…, Server konfiguratsiyani rad etdimi (WebSocket 1007 / invalid argument), kalit…, test_is_config_rejection()

### Community 70 - "test_extensions.py"
Cohesion: 0.08
Nodes (15): csv, pytest, Umumiy test sozlamalari., fixture, Kengaytma modullari (ax_actions, file_actions) testlari — real…, tmp_path ni ruxsat etilgan ildiz va default papka qiladi., pyobjc yo'q holat: handler xato matni qaytaradi, istisno emas., `confirmed` sxemada bo'lmasligi shart — aks holda model gate'ni chetlab o'tadi. (+7 more)

### Community 71 - "test_registry_no_confirmation_runs_immediately"
Cohesion: 0.29
Nodes (3): test_registry_no_confirmation_runs_immediately(), test_registry_tainted_turn_requires_confirmation(), read_page()

### Community 72 - "LoopGuard"
Cohesion: 0.22
Nodes (6): LoopGuard, Bir navbatda haddan ko'p yoki bir xil chaqiruvlarni to'xtatadi., None — davom et; matn — rad etish sababi (modelga tushuntirish)., test_loop_guard_identical_calls(), test_loop_guard_max_calls_per_turn(), test_loop_guard_non_consecutive_identical_calls()

### Community 73 - "._build_window"
Cohesion: 0.14
Nodes (16): default_orb_origin(), default_window_frame(), _hex_color(), _make_webview(), placeholder_html(), Oyna/orb hech bo'lmaganda `min_visible`×`min_visible` qismi bilan biror ekranda…, Ekranning pastki-o'ng burchagi (Dock/menyu bar hisobga olingan `visibleFrame`…, Ekran o'rtasida, `visibleFrame`ning `fraction` (90%) qismi (yoki `size`), min… (+8 more)

### Community 74 - "resolve_path"
Cohesion: 0.14
Nodes (14): find_files(), open_with_app(), Model aytgan yo'lni absolyut `Path`ga aylantiradi. Bo'sh bo'lsa `default` (yoki…, Spotlight (mdfind) yo'q joyda: nomida `query` bor fayllar (yashirin…, resolve_path(), _walk_find(), _kill_process_group(), Jarayonni va u tug'dirgan barcha bolalarni (process group) o'ldiradi. (+6 more)

### Community 76 - "gemini_live_client.py"
Cohesion: 0.14
Nodes (17): dataclasses, itertools, api_key_hint(), UI uchun niqoblangan ko'rinish: `AIza…x1y2` (kalitning o'zi hech qachon UI ga…, Diktovka rejimi: foydalanuvchi gapiradi — yordamchi teradi, to'xtash…, Gemini Multimodal Live API (WebSocket) sessiyasi. Ikki parallel task:…, ends_conversation(), _has_phrase() (+9 more)

### Community 78 - "describe_screen"
Cohesion: 0.36
Nodes (10): describe_screen(), _extract_text(), _image_part(), look_at_screen(), _make_client(), Any, Oldingi oynani skrinshot qilib Gemini'ga ko'rsatadi. {ok, output, app, ...}., read_screen_ocr() (+2 more)

### Community 81 - "desktop_win.py"
Cohesion: 0.21
Nodes (11): DaemonRunner, DesktopOptions, Settings, Windows desktop qatlami: daemon alohida thread'da, UI — pywebview (Edge…, Konsolsiz .exe da xato ko'rinmay qolmasin — Windows xabar oynasi., UI serveri tinglay boshlaguncha kutadi., run_desktop(), show_error() (+3 more)

### Community 84 - "._run"
Cohesion: 0.10
Nodes (12): feed_action(), find_tab_script(), `pos` dan `ahead` soniya oldinga tarjima tayyormi: ijroga qo'yilgan, yoki…, Buferlash: video pauzada turadi, oldinda `GATE_AHEAD_S` tarjima tayyor bo'lgach…, AppleScript (Chrome): `video_id` ochiq tabni topib oldinga chiqaradi va id sini…, Navbatdagi chunk bilan nima qilish: "resync" | "wait" | "send". Audio videodan…, JS ni video ochilgan tabda bajaradi (faol tab emas — foydalanuvchi boshqa tabga…, Pleyer holatini kuzatadi; tab boshqa sahifaga o'tsa yoki video tugasa — tugaydi. (+4 more)

### Community 85 - "PlaybackClock"
Cohesion: 0.10
Nodes (14): find_binary(), is_junk_translation(), PlaybackClock, PATH + Homebrew papkalari (.app ichidan ishga tushganda PATH qisqa bo'ladi)., Model tarjima o'rniga yorliq/izoh aytdi (`(Uzbek translation: …)`, `<no…, Brauzer pleyeri holatidan joriy video vaqtini baholaydi (so'rovlar orasida…, s16le mono PCM ni ohangini saqlab `tempo` barobar tezlashtiradi (ffmpeg…, time_stretch() (+6 more)

### Community 86 - "benchmark_live.py"
Cohesion: 0.33
Nodes (8): all_declarations(), build_config(), main(), passed(), Model qaysi toolni tanlashini real Gemini Live sessiyasida o'lchash (toollar…, Asosiy sxemalar + kengaytma modullari (nomlar bo'yicha takrorsiz)., Bitta buyruq: (chaqirilgan toollar [{name,args}], aytilgan matn, navbatlar…, run_case()

### Community 88 - "AudioPlayer"
Cohesion: 0.08
Nodes (17): AbstractEventLoop, AudioPlayer, parse_latency(), Any, EventBus, high"/"low" yoki sekund (str/float) → sounddevice `latency` argumenti., 24 kHz int16 mono ijro. `enqueue` istalgan thread/task'dan chaqirilishi mumkin.…, Buferdagi qolgan audioni (prebuffer to'lmagan bo'lsa ham) ijroga qo'yib… (+9 more)

### Community 89 - "redact_secrets"
Cohesion: 0.27
Nodes (5): Buyruqni qo'riqchi orqali bajaradi. `confirmed=True` — registry foydalanuvchi…, _truncate(), Model yoki log ko'rishidan oldin kalitga o'xshagan narsalarni yashiradi., redact_secrets(), Buyruqni qo'riqchi orqali `cmd` da bajaradi (UTF-8 kod sahifasi, shell…

### Community 90 - "reference/AI analysis (old Voice Assistant)"
Cohesion: 0.22
Nodes (10): Echo guard + playback prebuffer + low VAD start sensitivity, Nexus Ovoz OS (Uzbek voice assistant daemon), session.receive() ends each turn (not a disconnect), reference/AI analysis (old Voice Assistant), Gemini Live API findings (VAD, transcription langs, affective_dialog 1007/1011), Nexus plan P0/P1/P2, Old Voice Assistant (Gemini Live, ~7100 lines, PyQt orb), Product requirements (hands-free, Uzbek, barge-in, full control) (+2 more)

### Community 91 - "looks_like_command"
Cohesion: 0.18
Nodes (7): looks_like_command(), SMART rejimi uchun evristika: qisqa gap + buyruq so'zi., Oxirgi chaqiruvdan keyingi oyna (follow-up yoki suhbat) hali ochiqmi?, Oyna `at` (monotonic; odatda gap BOSHLANGAN payt) da ochiq edimi? None — hozir.…, Matnda ism bormi? Bo'lsa follow-up oynasi ochiladi., Bu gapga javob berish kerakmi? (ism eshitilsa oynani ham ochadi). `at` — gap…, test_looks_like_command()

### Community 92 - "test_safety.py"
Cohesion: 0.18
Nodes (14): Queue, _bus(), _drain(), EventBus, Xavfsizlik qatlami testlari: DANGEROUS_SHELL, looks_read_only,…, Gemini client note_utterance'ni chaqirmasa ham, bus'dagi TRANSCRIPT (user,…, test_gate_listens_to_bus_transcripts(), test_gate_new_request_cancels_old() (+6 more)

### Community 93 - "match_app"
Cohesion: 0.18
Nodes (9): match_app(), hits(), `needle` nomning boshida yoki ichidagi so'z boshida keladi ("word" ≠…, Aytilgan nomga mos o'rnatilgan ilovalar, eng yaqini birinchi. Tartib: aniq…, _starts_a_word(), Start menyusidagi yorliqlar: {ko'rinadigan nom: .lnk/.url yo'li} (60s kesh)., start_menu_apps(), _start_menu_dirs() (+1 more)

### Community 94 - "Orb overlay page (orb.html)"
Cohesion: 0.27
Nodes (10): Desktop layer (pure pyobjc NSWindow + WKWebView, orb NSPanel, menu bar), Orb overlay (floating non-activating NSPanel), UI -> daemon commands (mute, ptt, confirm, kill_all, text, wake_mode, dictation...), UI event contract ({type, ts, data} over /ws), Orb overlay page (orb.html), connect() WebSocket with exponential retry, draw() canvas orb renderer, effective() state resolver (+2 more)

### Community 95 - "windows_smoke.py"
Cohesion: 0.24
Nodes (8): browser_smoke(), check(), main(), Path, Windows smoke testi: registry, xavfsiz toollar va UI serveri haqiqiy Windows'da…, Muhitga bog'liq tekshiruv (brauzerning birinchi ishga tushishi va h.k.) —…, soft(), bus()

### Community 98 - "player_setup_js"
Cohesion: 0.29
Nodes (5): player_setup_js(), Video pauza, tarjima ovozi esa davom etadi — `seconds` dan keyin video qayta…, Pleyer: asl ovozni o'chirish/pasaytirish (0..1, manfiy — tegilmaydi) va ijro…, test_player_setup_js(), test_player_setup_js_keeps_volume_when_negative()

### Community 101 - ".get_system_info"
Cohesion: 0.32
Nodes (4): _fmt_uptime(), Any, _summarize_info(), Any

### Community 102 - "_recognize"
Cohesion: 0.33
Nodes (6): pick_languages(), Qo'llab-quvvatlanadigan tillardan kerakli tartibda tanlaydi ("uz" → "uz-UZ"…, Vision OCR: [(text, nx, ny, nw, nh, confidence)] — normalizatsiyalangan, y…, _recognize(), supported_languages(), test_pick_languages_prefers_uz_then_ru_en_and_skips_missing()

### Community 103 - "_bw"
Cohesion: 0.15
Nodes (14): fixture, browser_key(), pick_window(), chrome' / 'edge' / 'firefox' yoki None (istalgan). macOS'dagi 'safari' —…, Z-tartib bo'yicha birinchi mos brauzer oynasi (so'ralgani bo'lmasa — istalgan…, browser(), fake_keys(), fake_window() (+6 more)

### Community 104 - "Security model (confirmation from user transcript/UI only)"
Cohesion: 0.25
Nodes (9): CommandGuard allow/deny/confirm tiers, Loop guard (max 15 calls/turn, 3 identical), Secret redaction (redact_secrets), Security model (confirmation from user transcript/UI only), Sensitive path denial (path_is_sensitive), Taint guard (external content -> exfil/execute tools require confirmation), ToolRegistry.execute flow: validate -> loop guard -> taint -> confirm -> handler, Old code bugs (do not repeat) (+1 more)

### Community 105 - "path_allowed"
Cohesion: 0.18
Nodes (11): path_allowed(), Yo'l ruxsat etilgan ildizlar ostida va sezgir emasligini tekshiradi., POSIX_ONLY, parametrize, test_allowed_paths(), test_declarations_match_handlers(), test_delete_file_moves_to_trash_via_finder(), test_handlers_are_async_and_return_contract() (+3 more)

### Community 107 - "error_text"
Cohesion: 0.50
Nodes (4): error_text(), BaseException, Gemini xatosini foydalanuvchiga o'zbekcha qisqa jumla qilib beradi., test_error_text_is_uzbek()

### Community 114 - "Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline"
Cohesion: 0.25
Nodes (8): Nexus Ovoz OS design mockup (dc.html), Design mockup Component (simulated PTT command flow), Local models concept (Whisper.cpp small.uz + Qwen 7B Q4), Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline, Gemini Live API (native audio, WebSocket), Nexus browser/desktop panel (index.html), Confirmation card (TASDIQ KUTILMOQDA, Yes/No, TTL), Live transcript box

### Community 115 - "_FakeModels"
Cohesion: 0.39
Nodes (7): Exception, _fake_client(), _FakeModels, test_describe_screen_default_question(), test_describe_screen_error_and_timeout(), test_describe_screen_uses_fake_client_and_cleans_tmp(), test_look_at_screen_handler_wraps_result()

### Community 117 - "_registry_as_macos"
Cohesion: 0.50
Nodes (4): fixture, MonkeyPatch, Registry testlari OS'dan mustaqil: Windows'da ham to'liq (macOS) tool ro'yxati…, _registry_as_macos()

### Community 119 - "_coerce_cell_value"
Cohesion: 0.67
Nodes (3): _coerce_cell_value(), 250000" → 250000, "3.5" → 3.5; qolgani satr. Telefon (+998...) va 007 satr…, test_coerce_cell_value()

### Community 120 - "TaintTracker"
Cohesion: 0.25
Nodes (3): Navbat ichida tashqi matn o'qilganini eslab qoladi., TaintTracker, test_taint_tracker()

### Community 121 - "spoken_verdict"
Cohesion: 0.67
Nodes (3): True = rozi, False = rad, None = javob emas. Rad etish (veto) gap uzunligidan…, spoken_verdict(), test_spoken_verdict()

### Community 123 - "voice_picker.py"
Cohesion: 0.32
Nodes (6): main(), Path, Gemini ovozlarini o'zbekcha namunaviy jumla bilan tinglab tanlash.…, render(), save_wav(), wave

### Community 130 - "_dictation"
Cohesion: 0.67
Nodes (3): _dictation(), start_dictation(), stop_dictation()

## Ambiguous Edges - Review These
- `Gemini Live API (native audio, WebSocket)` → `Local models concept (Whisper.cpp small.uz + Qwen 7B Q4)`  [AMBIGUOUS]
  design/Nexus Ovoz OS.dc.html · relation: conceptually_related_to

## Knowledge Gaps
- **18 isolated node(s):** `INPUT`, `_INPUTUNION`, `MOUSEINPUT`, `Session resumption + context compression`, `Live transcript box` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 690 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Gemini Live API (native audio, WebSocket)` and `Local models concept (Whisper.cpp small.uz + Qwen 7B Q4)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `ToolRegistry` connect `ToolRegistry` to `Any`, `main.py`, `Security model (confirmation from user transcript/UI only)`, `test_registry_no_confirmation_runs_immediately`, `._build_handlers`, `FakeAudio`, `test_tools.py`, `macos_actions.py`, `Result`, `Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline`, `test_video_translate.py`, `_registry`, `test_registry_loads_extension_modules`, `test_safety.py`, `.kill_all`, `windows_smoke.py`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Why does `GeminiLiveClient` connect `GeminiLiveClient` to `is_config_rejection`, `main.py`, `AudioStreamer`, `._evaluate_addressed`, `._confirmation_pending`, `gemini_live_client.py`, `Any`, `.run`, `Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline`, `.tick`, `AudioPlayer`, `WakeState`, `reference/AI analysis (old Voice Assistant)`, `._handle_server_content`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `NexusDesktopApp` connect `NexusDesktopApp` to `DaemonRunner`, `._build_window`, `test_desktop.py`, `test_server.py`, `desktop.py`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `GeminiLiveClient` (e.g. with `WakeState` and `run()`) actually correct?**
  _`GeminiLiveClient` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `ToolRegistry` (e.g. with `run()` and `WindowsController`) actually correct?**
  _`ToolRegistry` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `INPUT`, `_INPUTUNION`, `MOUSEINPUT` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._