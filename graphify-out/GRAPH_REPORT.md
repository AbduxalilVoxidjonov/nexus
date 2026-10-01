# Graph Report - nexus  (2026-10-01)

## Corpus Check
- 52 files · ~110,482 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 4, .command 2, .example 1)

## Summary
- 2250 nodes · 4955 edges · 129 communities (99 shown, 30 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 333 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3e0ff70d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- support.js
- Any
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
- windows_screen.py
- state_style
- WindowsController
- screen_reader.py
- test_screen_reader.py
- ToolRegistry
- path_is_sensitive
- document_tree
- check_setup.py
- ._process_chunk
- WakeState
- _registry
- DesktopPrefs
- ws_reconnect_harness.js
- create_app
- Result
- ConfirmationGate
- test_wake_dictation.py
- AudioStreamer
- Any
- CommandGuard
- windows_browser.py
- DaemonRunner
- test_run_waits_for_api_key_from_settings
- config.py
- desktop.py
- test_windows.py
- test_core.py
- ._evaluate_addressed
- FakeAudio
- test_desktop.py
- video_translate.py
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
- Settings
- Segment
- ocr_image
- file_actions.py
- main.py
- ._handle_server_content
- Process
- schemas.py
- _ConfirmTracker
- normalise
- fake_screen
- Any
- ._translate
- is_config_rejection
- test_extensions.py
- test_registry_no_confirmation_runs_immediately
- LoopGuard
- ._build_window
- resolve_path
- nexus/__init__.py
- wake.py
- build_app.sh
- web_answer.py
- nexus-voice
- desktop_win.py
- FakeStream
- BaseException
- VideoTranslator
- PlaybackClock
- benchmark_live.py
- CLAUDE.md
- AudioPlayer
- WindowsCommandGuard
- reference/AI analysis (old Voice Assistant)
- looks_like_command
- test_safety.py
- match_app
- Orb overlay page (orb.html)
- is_junk_translation
- normalize_browser
- Process
- _conversation
- Path
- Result
- .get_system_info
- is_quota_error
- sandbox
- Security model (confirmation from user transcript/UI only)
- _cmd
- ._confirmation_pending
- fixture
- parametrize
- AbstractEventLoop
- BaseException
- test_registry_kill_all_runs_hook_and_cancels_gate
- Queue
- Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline
- Path
- test_is_terminal_frontmost
- pytest
- Settings
- _coerce_cell_value
- TaintTracker
- test_registry_loads_extension_modules
- EventBus
- Verdict
- test_ws_slow_command_does_not_block_following_commands
- installed_apps
- .build_hotkey_script
- _dictation
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
- `Echo guard + playback prebuffer + low VAD start sensitivity` --rationale_for--> `AudioStreamer`  [INFERRED]
  README.md → nexus/audio_streamer.py
- `session.receive() ends each turn (not a disconnect)` --rationale_for--> `GeminiLiveClient`  [INFERRED]
  README.md → nexus/gemini_live_client.py
- `ToolRegistry.execute flow: validate -> loop guard -> taint -> confirm -> handler` --references--> `ToolRegistry`  [EXTRACTED]
  README.md → nexus/tools/registry.py
- `CommandGuard allow/deny/confirm tiers` --references--> `CommandGuard`  [EXTRACTED]
  README.md → nexus/macos_actions.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Tool execution safety pipeline** — readme_toolregistry_execute_flow, readme_loop_guard, readme_taint_guard, readme_commandguard_tiers, nexus_safety_confirmationgate [EXTRACTED 1.00]
- **Echo / self-hearing mitigation** — readme_echo_guard, reference_analysis_live_api_findings, nexus_audio_streamer_audiostreamer, nexus_audio_streamer_audioplayer [INFERRED 0.85]
- **WebSocket /ws event consumers** — readme_ui_event_contract, ui_index, ui_orb, nexus_events_eventbus [INFERRED 0.85]

## Communities (129 total, 30 thin omitted)

### Community 0 - "support.js"
Cohesion: 0.06
Nodes (75): boot(), bundledBlob(), cdnScriptFor(), collectProps(), compileAttr(), compileTemplate(), contentKey(), createComponentFactory() (+67 more)

### Community 1 - "Any"
Cohesion: 0.28
Nodes (20): _append_csv(), _append_row_sync(), append_spreadsheet_row(), _append_xlsx(), delete_file(), _is_confirmed(), _open_book(), Any (+12 more)

### Community 2 - "ax_actions.py"
Cohesion: 0.06
Nodes (75): applicationservices, difflib, _actions(), activate_element(), _app_root(), _attr(), available(), _clean_text() (+67 more)

### Community 3 - "Result"
Cohesion: 0.06
Nodes (32): EventBus, app_name(), BrowserController, BrowserDOMController, build_search_url(), _fmt_time(), _js_error(), js_to_applescript() (+24 more)

### Community 4 - "GeminiLiveClient"
Cohesion: 0.18
Nodes (4): GeminiLiveClient, Har bir function_call ni registry orqali bajaradi va javobni sessiyaga…, Final transkript bo'lagini darhol teradi; to'xtash iborasi rejimni tugatadi., Session resumption + context compression

### Community 5 - "make_client"
Cohesion: 0.07
Nodes (42): GeminiLiveClient, SimpleNamespace, _audio_part(), FakeSession, make_client(), _msg(), EventBus, `turns` — har bir receive() iteratsiyasida beriladigan xabarlar ro'yxati (bo'sh… (+34 more)

### Community 6 - "app.js"
Cohesion: 0.12
Nodes (58): answerConfirm(), applyDevices(), applySettings(), applySnapshot(), bind(), closeSocket(), connect(), ensureRow() (+50 more)

### Community 7 - "test_tools.py"
Cohesion: 0.07
Nodes (31): nexus_tools, _no_sleep(), MonkeyPatch, Tool qatlami testlari — real macOS tizimiga tegmaydi (osascript/subprocess…, Barcha ichki JS'lar AppleScript literaliga qo'yilganda qo'shtirnoq muvozanati…, ScriptRecorder, test_as_str_escapes_quotes_and_backslashes(), test_browser_open_url_normalizes() (+23 more)

### Community 8 - "EventBus"
Cohesion: 0.17
Nodes (6): CommandHandler, EventBus, AbstractEventLoop, Any, Queue, Thread-safe pub/sub. `publish` istalgan thread'dan chaqirilishi mumkin.

### Community 9 - "Nexus Ovoz OS README"
Cohesion: 0.22
Nodes (11): Nexus Ovoz OS README, AXManualAccessibility for Chrome/Electron, Dictation mode (direct typing, stop phrases), .env settings (GEMINI_MODEL, VAD_THRESHOLD, WAKE_MODE, UI_PORT ...), EXTENSION_MODULES (TOOL_DECLARATIONS + HANDLERS), macOS permissions (Microphone, Accessibility, Screen Recording, Automation), Scripts: check_setup, benchmark_live, voice_picker, Tool catalog (62 tools: 45 core + 10 file + 7 AX) (+3 more)

### Community 10 - "._build_handlers"
Cohesion: 0.06
Nodes (16): browser_click_button(), browser_click_selector(), browser_close_tab(), browser_current_page(), browser_list_tabs(), browser_open_url(), browser_read_page(), browser_reload() (+8 more)

### Community 11 - "NexusDesktopApp"
Cohesion: 0.09
Nodes (8): _load_url(), NexusDesktopApp, Any, NSApplication delegati: oyna, orb, menyu bar, daemon ko'prigi., SIGINT/SIGTERM → toza chiqish. Mach-port orqali AppKit run loop'ida qayta…, Daemon thread'idan chaqiriladi — hodisani GUI thread'iga uzatadi., `.env` ni Finder'da ko'rsatadi (yagona "tashqi ochish" — brauzer emas)., NSObject

### Community 12 - "MacOSController"
Cohesion: 0.14
Nodes (7): _clamp(), MacOSController, Result, Buyruqni qo'riqchi orqali bajaradi. `confirmed=True` — registry foydalanuvchi…, macOS bilan ishlash: ovoz, media, ilovalar, Finder, tizim, terminal., macOS 12+ da DND uchun ochiq API yo'q. Foydalanuvchi yaratgan Shortcuts…, Faol oynaga matn kiritadi: bufer + Cmd+V (keystroke o'zbek/kirill matnni…

### Community 13 - "test_server.py"
Cohesion: 0.16
Nodes (14): fastapi_testclient, TestClient, bus(), client(), _free_port(), fixture, nexus.server (FastAPI + WS ko'prigi) testlari., test_api_state() (+6 more)

### Community 14 - "windows_screen.py"
Cohesion: 0.08
Nodes (62): io, work(), run(), _activate(), _ask_gemini(), capture_window_jpeg(), _click_point(), _click_sync() (+54 more)

### Community 15 - "state_style"
Cohesion: 0.22
Nodes (10): effective_state(), (rang, yorliq) — menyu bar / orb uchun., Menyu bar'dagi holat satri, masalan "● Tinglamoqda" yoki "● Kutmoqda (mikrofon…, Daemon holati + Gemini ulanishi + tasdiqdan bitta ko'rsatiladigan holat., state_style(), status_title(), parametrize, test_effective_state_priorities() (+2 more)

### Community 16 - "WindowsController"
Cohesion: 0.07
Nodes (7): MacOSController, _press_key(), PowerShell skriptini konsol oynasiz bajaradi; chiqish UTF-8., Windows bilan ishlash: ovoz, media, ilovalar, Explorer, tizim., Faol oynaga matn teradi (SendInput Unicode — bufer o'zgarmaydi)., run_powershell(), WindowsController

### Community 17 - "screen_reader.py"
Cohesion: 0.09
Nodes (41): appkit, foundation, available(), capture_frontmost_window(), describe_screen(), _shoot(), error_text(), _extract_text() (+33 more)

### Community 18 - "test_screen_reader.py"
Cohesion: 0.10
Nodes (15): Exception, inspect, subprocess, _fake_client(), _FakeModels, Any, screen_reader (OCR + Gemini ko'rish) va ax_actions'dagi AX→OCR zaxira yo'li…, test_click_ui_element_by_ocr_index_from_cache() (+7 more)

### Community 19 - "ToolRegistry"
Cohesion: 0.10
Nodes (11): Foydalanuvchi yangi gap boshladi: loop guard va taint tozalanadi., Foydalanuvchining yakuniy transkripti — og'zaki tasdiq uchun., Bajarilayotgan tool tasklarini bekor qiladi. Kutilayotgan tasdiq so'roviga…, ⌥⎋ / "kill_all": tool tasklar + kutilayotgan tasdiq bekor qilinadi, so'ng…, Gemini toollarini bajaruvchi markaziy ro'yxat., ToolRegistry, test_conversation_tools_registered(), test_registry_has_handler_for_every_declaration() (+3 more)

### Community 20 - "path_is_sensitive"
Cohesion: 0.13
Nodes (17): Verdict, Buyruqni tokenlarga bo'lish (POSIX qoidalari). Windows qo'riqchisi qayta…, looks_read_only(), path_is_sensitive(), Path, True — buyruq DANGEROUS_SHELL naqshlaridan biriga mos keladi., True — buyruq HECH QANDAY bayroq bilan ham hech narsani o'zgartira olmaydi., True — bu yerga yozish persistensiya yaratishi yoki sir sizdirishi mumkin. (+9 more)

### Community 21 - "document_tree"
Cohesion: 0.20
Nodes (9): Any, document_tree(), pick_page_document(), Sahifa hujjatining indeksi: sarlavhasi tab sarlavhasiga teng → eng ko'p…, Sahifa (DocumentControl) elementlari. Chromium veb-kontent daraxtini UIA mijozi…, work(), work(), test_document_tree_retries_until_filled() (+1 more)

### Community 22 - "check_setup.py"
Cohesion: 0.30
Nodes (14): CDLL, check_accessibility(), check_automation(), check_devices(), check_key(), check_live(), check_mic_level(), check_packages() (+6 more)

### Community 23 - "._process_chunk"
Cohesion: 0.12
Nodes (13): echo_gate(), gate_open(), Yordamchi gapirayotganda mikrofon chunk'i o'tkazilsinmi? True = o'tkaz. Guard…, Callback thread'da: darajani hisoblaydi, gate'ni yangilaydi, navbatga qo'yadi.…, Yordamchi buyruq ustida ishlayaptimi (o'ylayapti / tool bajaryapti /…, Yordamchi javobi paytida mikrofon to'liq bostirilsinmi?, Chunk Gemini'ga yuborilsinmi? (mute yoki PTT bosilmagan bo'lsa — yo'q)., should_forward() (+5 more)

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

### Community 28 - "create_app"
Cohesion: 0.20
Nodes (6): create_app(), index(), Path, Settings, FastAPI ilovasini yaratadi (testlarda ham shu ishlatiladi)., test_ws_receives_published_events()

### Community 29 - "Result"
Cohesion: 0.15
Nodes (5): Nisbiy siljish → klavishlar: 10 s lik l/j, qoldig'i 5 s lik o'qlar., Brauzer amallari — macOS'dagi BrowserController/DOM/YouTube/Search sinflari…, seek_presses(), WindowsBrowser, Result

### Community 30 - "ConfirmationGate"
Cohesion: 0.16
Nodes (9): ConfirmationGate, _consume(), PendingConfirmation, True = rozi, False = rad, None = javob emas. Rad etish (veto) gap uzunligidan…, Bir vaqtda faqat bitta faol tasdiq so'rovi. Yangi so'rov eskisini bekor qiladi., Foydalanuvchining yakuniy transkripti. So'rovdan OLDIN aytilgan gap hisobga…, Bus'dagi TRANSCRIPT (user, final) hodisalarini ham kuzatadi — gemini client…, spoken_verdict() (+1 more)

### Community 31 - "test_wake_dictation.py"
Cohesion: 0.12
Nodes (26): is_stop_phrase(), Butun gap faqat to'xtash iborasidan iboratmi?, _candidates(), levenshtein(), name_in(), Levenshtein masofasi; `limit` berilsa undan oshgach hisoblashni to'xtatadi…, Qisqa ism aniq mos kelishi kerak; uzunroq ism 2-3 xatoni ko'taradi., (nomzod, boshlanish indeksi, so'zlar soni) — yakka so'zlar va qo'shni… (+18 more)

### Community 32 - "AudioStreamer"
Cohesion: 0.07
Nodes (18): AudioStreamer, _list_devices(), _mute(), _playback(), _ptt(), _ptt_press(), _sensitivity(), _set_device() (+10 more)

### Community 33 - "Any"
Cohesion: 0.17
Nodes (6): Handler, Any, Handler javobini (tuple yoki dict) yagona formatga keltiradi., Bajarishdan OLDIN aniqlanadigan tasdiq sabablari (bo'sh — tasdiqsiz)., _to_text(), _truncate()

### Community 34 - "CommandGuard"
Cohesion: 0.22
Nodes (9): CommandGuard, `run_terminal_command` uchun uch pog'onali qo'riqchi. `check()` → ("allow" |…, Tekshiruvdan o'tgan buyruqni bajarish uchun argv (`~` kengaytirilgan holda)., parametrize, test_guard_allows(), test_guard_argv_expands_tilde(), test_guard_confirms(), test_guard_denies() (+1 more)

### Community 35 - "windows_browser.py"
Cohesion: 0.13
Nodes (18): ctypes, Windows'da brauzer boshqaruvi: UI Automation + klaviatura (Chrome, Edge,…, combo_events(), INPUT, _INPUTUNION, KEYBDINPUT, MOUSEINPUT, press_combo() (+10 more)

### Community 36 - "DaemonRunner"
Cohesion: 0.16
Nodes (5): DaemonRunner, `nexus.main.run()` ni alohida thread'da o'z event loop'i bilan yuritadi., To'xtatish signalini beradi (bloklamaydi) — tugashini `finished` orqali…, To'xtatish signalini beradi va thread tugashini kutadi. True = toza tugadi., GUI'dan daemon'ga buyruq (thread-safe, natija kutilmaydi).

### Community 37 - "test_run_waits_for_api_key_from_settings"
Cohesion: 0.10
Nodes (10): FakeLiveConnect, 1011 'exceeded your current quota' → avval google_search grounding olib…, client.aio.live.connect o'rnini bosuvchi: har chaqiruvda navbatdagi FakeSession., connect(), test_quota_error_drops_google_search_first(), connect(), test_run_drops_resume_handle_after_short_session(), test_run_reconnects_with_resume_handle_and_counts() (+2 more)

### Community 38 - "config.py"
Cohesion: 0.11
Nodes (24): dotenv, api_key_env_path(), api_key_hint(), _describe_char(), _env_api_key(), env_candidates(), is_placeholder_api_key(), load_env_files() (+16 more)

### Community 39 - "desktop.py"
Cohesion: 0.10
Nodes (17): DesktopOptions, _env_true(), _make_app_icon(), NexusOrbPanel, Desktop ilova qatlami: o'z oynasi, doim tepada turadigan orb va menyu bar…, Desktop ilovani ishga tushiradi (asosiy thread'da bloklaydi). Qaytadi: chiqish…, argparse Namespace (nexus.main.build_parser) → DesktopOptions., Ilova menyusida (chap yuqori) "python" o'rniga ilova nomi (bundle'siz ishga… (+9 more)

### Community 40 - "test_windows.py"
Cohesion: 0.04
Nodes (39): fixture, browser_key(), looks_like_result(), pick_window(), Tezlik: avval minimal (0.25) gacha tushirib, keyin kerakli qadamlar., chrome' / 'edge' / 'firefox' yoki None (istalgan). macOS'dagi 'safari' —…, Z-tartib bo'yicha birinchi mos brauzer oynasi (so'ralgani bo'lmasa — istalgan…, speed_presses() (+31 more)

### Community 41 - "test_core.py"
Cohesion: 0.07
Nodes (34): math, compute_rms(), int16 mono PCM baytlaridan (rms 0..1, db -60..0) qaytaradi., numpy, sounddevice, fake_sd(), make_settings(), fixture (+26 more)

### Community 42 - "._evaluate_addressed"
Cohesion: 0.13
Nodes (6): Oxirgi real audio chunk karnayga chiqqan payt (time.monotonic; 0 — hali yo'q)., UI dan matn buyrug'i. Sessiya yo'q bo'lsa False., Registry'ga foydalanuvchi navbatini bildiradi: og'zaki tasdiq (note_utterance)…, Wake rejimi bo'yicha gap bizga qaratilganmi (qisman transkriptda ham). Baho…, Joriy gap boshlangan payt (AudioStreamer RMS gate). Noma'lum yoki eskirgan…, Suhbat rejimi: ismsiz erkin suhbat; jimlikdan keyin o'zi tugaydi (`tick`).

### Community 43 - "FakeAudio"
Cohesion: 0.12
Nodes (8): FakeAudio, FakeRegistry, test_build_config_ptt_disables_vad_and_optional_fields(), test_conversation_command_and_idle_tick(), test_dismissal_keeps_silent_and_waits_for_name(), test_run_requires_api_key(), test_user_turn_without_registry_hooks(), test_wake_name_mode_suppresses_audio_and_tools()

### Community 44 - "test_desktop.py"
Cohesion: 0.11
Nodes (21): ArgumentParser, Namespace, `base_url/health` 2xx qaytarguncha kutadi. `keep_waiting()` False qaytarsa…, wait_for_server(), build_parser(), desktop_mode(), Desktop (oyna + orb + menyu bar) rejimi kerakmi? `--headless`, `--no-ui`…, MonkeyPatch (+13 more)

### Community 45 - "video_translate.py"
Cohesion: 0.12
Nodes (32): asyncio, collections, collections_abc, datetime, importlib, json, logging, Mikrofon oqimi va ovoz ijrosi (sounddevice / PortAudio). `AudioStreamer` —… (+24 more)

### Community 46 - "._window"
Cohesion: 0.13
Nodes (9): BrowserWindow, list_browser_windows(), _cb(), Ko'rinadigan brauzer oynalari, Z-tartibda (eng ustidagisi birinchi)., `fn(auto, root)` ni UIA ishga tushirilgan thread'da bajaradi., Sahifa (DocumentControl) ichidagi elementlar; hujjat topilmasa — butun oyna., Pleyer tugmasining nomi: "Pause (k)" — ijro etilmoqda, "Play (k)" — pauzada., work() (+1 more)

### Community 47 - "Any"
Cohesion: 0.14
Nodes (8): Any, EventBus, Path, `extended-thinking` modelida daraja majburiy (bo'sh bo'lsa "high"); boshqa…, `receive()` har navbatda tugaydi — qayta chaqiramiz; bo'sh iteratsiya = uzilish., thinking_level_for(), _to_function_declarations(), test_thinking_level_for()

### Community 48 - ".run"
Cohesion: 0.13
Nodes (14): compute_backoff(), GeminiConfigError, _key_hint(), UI (Sozlamalar) dan API kalit: tekshiradi, saqlaydi va sessiyani yangi kalit…, Konfiguratsiya xatosi (masalan, API kaliti yo'q)., Cheksiz ulanish sikli; `stop()` chaqirilguncha qayta ulanaveradi., Kalit Sozlamalardan (`set_api_key`) kiritilguncha yoki `stop()` gacha kutadi., `timeout` sekund (None — cheksiz) kutadi; `stop()` yoki yangi API kalit… (+6 more)

### Community 49 - "snapshot"
Cohesion: 0.46
Nodes (8): _cmd_result(), api_state(), snapshot(), ws_endpoint(), handle_command(), receiver(), send(), sender()

### Community 50 - "BargeInGate"
Cohesion: 0.25
Nodes (6): BargeInGate, Ijro paytida mikrofon chunklarining echo/barge-in darvozasi (callback…, → (navbatga qo'yiladigan chunklar, sukunatga almashtirilganlar soni)., test_barge_gate_flushes_held_when_playback_stops(), test_barge_gate_single_spike_becomes_silence(), test_barge_gate_sustained_opens_and_holds()

### Community 51 - "Segmenter"
Cohesion: 0.38
Nodes (4): Uzluksiz nutqni tarjima bo'laklariga ajratadi: `push(rms)` True → bo'lakni shu…, Segmenter, test_segmenter_cuts_at_max(), test_segmenter_cuts_on_quiet_after_min()

### Community 52 - "server.py"
Cohesion: 0.10
Nodes (13): contextlib, errno, FastAPI, fastapi_responses, fastapi_staticfiles, _QuietServer, UI ko'prigi: FastAPI + WebSocket server. EventBus hodisalarini brauzerdagi UI…, Signal handlerlarini o'rnatmaydigan uvicorn Server (signalni main.py… (+5 more)

### Community 53 - "test_video_translate.py"
Cohesion: 0.06
Nodes (30): nexus, build_ffmpeg_cmd(), build_ytdlp_cmd(), feed_action(), find_tab_script(), player_setup_js(), AppleScript: JS ni video tabida bajaradi — Chrome'da `tab_id` bo'yicha (bir xil…, AppleScript (Chrome): `video_id` ochiq tabni topib oldinga chiqaradi va id sini… (+22 more)

### Community 54 - "DictationState"
Cohesion: 0.17
Nodes (6): DictationState, (teriladigan matn, to'xtash kerakmi). "…hammasi shu, to'xta" → ("…hammasi shu",…, Diktovka holati va terilgan matn hisobi., split_stop(), test_dictation_state_lifecycle(), test_split_stop()

### Community 55 - ".tick"
Cohesion: 0.33
Nodes (3): Hozir ovoz chiqyaptimi (navbatda audio bor yoki oxirgi chunk yaqinda chiqqan)., Davriy tekshiruv (MetricsTicker): jimlik tufayli suhbat rejimini tugatish;…, Band holat (processing / tool_executing / speaking) tool ham, ijro ham, server…

### Community 56 - "Settings"
Cohesion: 0.18
Nodes (7): google-genai Client — hamma joyda bir xil sozlama bilan., Settings, test_config_defaults_gemini38(), test_wake_defaults_to_name_only(), test_confirm_request_push_and_confirm_cmd(), test_multiple_clients_and_unsubscribe(), test_ws_get_state_without_handler()

### Community 57 - "Segment"
Cohesion: 0.14
Nodes (12): fit_tempo(), Bo'laklarni `seq` tartibida, video o'z oralig'iga (`src_start`) yetganda ijroga…, Javob bermagan bo'lakni navbat boshiga qaytaradi — boshqa (bo'sh) sessiya oladi., Tarjima ulgurmayapti (masalan, kvota kam — sessiyalar yetmaydi): gapni tashlab…, turn_complete kelmay qolgan sessiyani bo'shatadi (model jim qoldi)., Tarjima (`out_s`) videodagi qolgan oralig'iga (`window_s`) sig'ishi uchun…, Tarjima bo'lagi: kiruvchi audio (tayinlanguncha `buf`da) va modelning javobi…, activity_end dan keyin `no_response_s` ichida audio kelmadi — ijroda o'tkazib… (+4 more)

### Community 58 - "ocr_image"
Cohesion: 0.13
Nodes (21): Box, lines_as_elements(), lines_to_text(), ocr_image(), Satrlarni yuqoridan pastga, bir qatordagilarni chapdan o'ngga tartiblaydi. Ikki…, Tartiblangan satrlardan matn: bir qatordagilar ikki bo'shliq bilan, qatorlar…, OCR satrlarini list_ui_elements formatiga o'giradi: {n, role:'text', label, at,…, Rasm faylini OCR qiladi → tartiblangan satrlar [{text, x, y, w, h}]. `bounds`… (+13 more)

### Community 59 - "file_actions.py"
Cohesion: 0.13
Nodes (11): _fallback_path_is_sensitive(), list_directory(), _list_directory_sync(), Fayl, eslatma va Excel/CSV toollari — kengaytma moduli. Eksport (registry…, read_file(), _read_file_sync(), AppleScript'ni `osascript` orqali bajaradi (stdin orqali, argument uzunligi…, run_applescript() (+3 more)

### Community 60 - "main.py"
Cohesion: 0.09
Nodes (27): Event, check_environment(), cli(), _first(), MetricsTicker, platform_controller(), print_banner(), Any (+19 more)

### Community 61 - "._handle_server_content"
Cohesion: 0.20
Nodes (6): _asks_question(), _grounding_sources(), ToolRegistry.kill_all() ilgagi: klient tool tasklari bekor, ijro navbati…, Zaxira: registry bo'lmaganda (toolsiz rejim) `kill_all` buyrug'i., Yordamchi javobi foydalanuvchidan javob kutadimi ("Yana nima qilay?", "Labbay,…, `grounding_metadata.grounding_chunks[*].web.{uri,title}` → "title — uri"…

### Community 63 - "schemas.py"
Cohesion: 0.39
Nodes (7): _b(), _decl(), _i(), _n(), Any, Gemini Live API uchun FunctionDeclaration lug'atlari va tizim ko'rsatmasi.…, _s()

### Community 64 - "_ConfirmTracker"
Cohesion: 0.24
Nodes (5): _ConfirmTracker, Any, EventBus, CONFIRM_REQUEST / CONFIRM_RESOLVED hodisalarini kuzatib, ochiq tasdiqni eslab…, _snapshot()

### Community 65 - "normalise"
Cohesion: 0.33
Nodes (5): is_dismissal(), normalise(), Kichik harf, urg'u/apostrofsiz, tinish belgisiz; kirill → lotin., Yo'q, hozircha hech narsa", "kerak emas", "rahmat", "нет, ничего", "no,…, test_normalise_folds_case_apostrophes_and_cyrillic()

### Community 66 - "fake_screen"
Cohesion: 0.40
Nodes (5): ax_ready(), fake_screen(), fixture, MonkeyPatch, Skrinshot/JPEG bosqichini almashtiradi: real screencapture chaqirilmaydi.

### Community 67 - "Any"
Cohesion: 0.11
Nodes (16): attach(), parse_player_state(), Any, main.py: bus/settings/mikrofonni ulaydi; echo guard tarjima ijrosini ham…, Bitta Live sessiya: navbatdagi bo'lakni oladi, javobini bo'lakka yozadi., Sessiya bo'shadi — navbatdagi bo'lakni olishi mumkin., Sessiya uzildi: joriy bo'lak yakunlangan deb belgilanadi, o'zi bo'sh ro'yxatdan…, Model javobini sessiyaning joriy bo'lagiga yozadi. True — navbat tugadi… (+8 more)

### Community 68 - "._translate"
Cohesion: 0.25
Nodes (5): is_silent(), Bo'lak deyarli jim (o'rtacha RMS `SILENT_RMS` dan past)., Parallel sessiyalar + dispetcher + tartibli ijro., Tayinlanmagan bo'laklarni (FIFO) bo'sh sessiyalarga beradi., test_silent_segment_is_not_sent()

### Community 69 - "is_config_rejection"
Cohesion: 0.29
Nodes (7): BaseException, is_api_key_error(), is_config_rejection(), Server kalitni rad etdimi (noto'g'ri / bekor qilingan API kalit)?, Server konfiguratsiyani rad etgan bo'lsa navbatdagi modelga bog'liq maydonni…, Server konfiguratsiyani rad etdimi (WebSocket 1007 / invalid argument), kalit…, test_is_config_rejection()

### Community 70 - "test_extensions.py"
Cohesion: 0.09
Nodes (18): csv, path_allowed(), Yo'l ruxsat etilgan ildizlar ostida va sezgir emasligini tekshiradi., POSIX_ONLY, parametrize, Kengaytma modullari (ax_actions, file_actions) testlari — real…, pyobjc yo'q holat: handler xato matni qaytaradi, istisno emas., `confirmed` sxemada bo'lmasligi shart — aks holda model gate'ni chetlab o'tadi. (+10 more)

### Community 71 - "test_registry_no_confirmation_runs_immediately"
Cohesion: 0.29
Nodes (3): test_registry_no_confirmation_runs_immediately(), test_registry_tainted_turn_requires_confirmation(), read_page()

### Community 72 - "LoopGuard"
Cohesion: 0.20
Nodes (7): LoopGuard, Any, Bir navbatda haddan ko'p yoki bir xil chaqiruvlarni to'xtatadi., None — davom et; matn — rad etish sababi (modelga tushuntirish)., test_loop_guard_identical_calls(), test_loop_guard_max_calls_per_turn(), test_loop_guard_non_consecutive_identical_calls()

### Community 73 - "._build_window"
Cohesion: 0.14
Nodes (16): default_orb_origin(), default_window_frame(), _hex_color(), _make_webview(), placeholder_html(), Oyna/orb hech bo'lmaganda `min_visible`×`min_visible` qismi bilan biror ekranda…, Ekranning pastki-o'ng burchagi (Dock/menyu bar hisobga olingan `visibleFrame`…, Ekran o'rtasida, `visibleFrame`ning `fraction` (90%) qismi (yoki `size`), min… (+8 more)

### Community 74 - "resolve_path"
Cohesion: 0.14
Nodes (14): find_files(), open_with_app(), Model aytgan yo'lni absolyut `Path`ga aylantiradi. Bo'sh bo'lsa `default` (yoki…, Spotlight (mdfind) yo'q joyda: nomida `query` bor fayllar (yashirin…, resolve_path(), _walk_find(), _kill_process_group(), Jarayonni va u tug'dirgan barcha bolalarni (process group) o'ldiradi. (+6 more)

### Community 76 - "wake.py"
Cohesion: 0.21
Nodes (11): dataclasses, itertools, Diktovka rejimi: foydalanuvchi gapiradi — yordamchi teradi, to'xtash…, ends_conversation(), _has_phrase(), Ism bilan chaqirish (wake): gap yordamchiga qaratilganmi? Xonada boshqa odamlar…, kel gaplashamiz", "suhbatlashaylik", "давай поговорим", "let's talk" …, bo'ldi, rahmat", "suhbatni tugat", "xayr" … (+3 more)

### Community 78 - "web_answer.py"
Cohesion: 0.33
Nodes (12): build_request(), _create(), extract_sources(), extract_text(), _get(), _make_client(), Any, `web_answer` tool — Google Search grounding bilan faktik/yangilik savollariga… (+4 more)

### Community 81 - "desktop_win.py"
Cohesion: 0.14
Nodes (15): DaemonRunner, DesktopOptions, Settings, Windows desktop qatlami: daemon alohida thread'da, UI — pywebview (Edge…, Konsolsiz .exe da xato ko'rinmay qolmasin — Windows xabar oynasi., UI serveri tinglay boshlaguncha kutadi., run_desktop(), show_error() (+7 more)

### Community 84 - "VideoTranslator"
Cohesion: 0.13
Nodes (10): `pos` dan `ahead` soniya oldinga tarjima tayyormi: ijroga qo'yilgan, yoki…, Video pauza, tarjima ovozi esa davom etadi — `seconds` dan keyin video qayta…, Buferlash: video pauzada turadi, oldinda `GATE_AHEAD_S` tarjima tayyor bo'lgach…, yt-dlp: audio faylni vaqtinchalik papkaga yuklaydi. (ok, sarlavha | xato).…, JS ni video ochilgan tabda bajaradi (faol tab emas — foydalanuvchi boshqa tabga…, Pleyer holatini kuzatadi; tab boshqa sahifaga o'tsa yoki video tugasa — tugaydi., Seek: navbatdagi kiruvchi audio va hali ijro etilmagan tarjimalar tashlanadi., ffmpeg PCM → navbat (video vaqti bilan), videodan `LOOKAHEAD_S` oldinda; seek →… (+2 more)

### Community 85 - "PlaybackClock"
Cohesion: 0.14
Nodes (8): find_binary(), PlaybackClock, PATH + Homebrew papkalari (.app ichidan ishga tushganda PATH qisqa bo'ladi)., Brauzer pleyeri holatidan joriy video vaqtini baholaydi (so'rovlar orasida…, s16le mono PCM ni ohangini saqlab `tempo` barobar tezlashtiradi (ffmpeg…, time_stretch(), test_clock_interpolates_and_halts(), test_time_stretch_shortens_audio()

### Community 86 - "benchmark_live.py"
Cohesion: 0.15
Nodes (15): argparse, all_declarations(), build_config(), main(), passed(), Model qaysi toolni tanlashini real Gemini Live sessiyasida o'lchash (toollar…, Asosiy sxemalar + kengaytma modullari (nomlar bo'yicha takrorsiz)., Bitta buyruq: (chaqirilgan toollar [{name,args}], aytilgan matn, navbatlar… (+7 more)

### Community 88 - "AudioPlayer"
Cohesion: 0.07
Nodes (24): AbstractEventLoop, AudioPlayer, _default_input_index(), list_input_devices(), parse_latency(), Any, EventBus, high"/"low" yoki sekund (str/float) → sounddevice `latency` argumenti. (+16 more)

### Community 89 - "WindowsCommandGuard"
Cohesion: 0.11
Nodes (15): CommandGuard, _truncate(), `run_terminal_command` qo'riqchisi — Windows (cmd) buyruqlari uchun. Asosiy…, Buyruqni qo'riqchi orqali `cmd` da bajaradi (UTF-8 kod sahifasi, shell…, WindowsCommandGuard, HotkeyError, parse_hotkey(), cmd+shift+s' → ([VK_CONTROL, VK_SHIFT], ord('S')). Xato bo'lsa `HotkeyError`. (+7 more)

### Community 90 - "reference/AI analysis (old Voice Assistant)"
Cohesion: 0.22
Nodes (10): Echo guard + playback prebuffer + low VAD start sensitivity, Nexus Ovoz OS (Uzbek voice assistant daemon), session.receive() ends each turn (not a disconnect), reference/AI analysis (old Voice Assistant), Gemini Live API findings (VAD, transcription langs, affective_dialog 1007/1011), Nexus plan P0/P1/P2, Old Voice Assistant (Gemini Live, ~7100 lines, PyQt orb), Product requirements (hands-free, Uzbek, barge-in, full control) (+2 more)

### Community 91 - "looks_like_command"
Cohesion: 0.18
Nodes (7): looks_like_command(), SMART rejimi uchun evristika: qisqa gap + buyruq so'zi., Oxirgi chaqiruvdan keyingi oyna (follow-up yoki suhbat) hali ochiqmi?, Oyna `at` (monotonic; odatda gap BOSHLANGAN payt) da ochiq edimi? None — hozir.…, Matnda ism bormi? Bo'lsa follow-up oynasi ochiladi., Bu gapga javob berish kerakmi? (ism eshitilsa oynani ham ochadi). `at` — gap…, test_looks_like_command()

### Community 92 - "test_safety.py"
Cohesion: 0.13
Nodes (20): Model yoki log ko'rishidan oldin kalitga o'xshagan narsalarni yashiradi., redact_secrets(), Queue, _bus(), _drain(), EventBus, Xavfsizlik qatlami testlari: DANGEROUS_SHELL, looks_read_only,…, Gemini client note_utterance'ni chaqirmasa ham, bus'dagi TRANSCRIPT (user,… (+12 more)

### Community 93 - "match_app"
Cohesion: 0.15
Nodes (9): match_app(), hits(), `needle` nomning boshida yoki ichidagi so'z boshida keladi ("word" ≠…, Aytilgan nomga mos o'rnatilgan ilovalar, eng yaqini birinchi. Tartib: aniq…, _starts_a_word(), Start menyusidagi yorliqlar: {ko'rinadigan nom: .lnk/.url yo'li} (60s kesh)., start_menu_apps(), _start_menu_dirs() (+1 more)

### Community 94 - "Orb overlay page (orb.html)"
Cohesion: 0.27
Nodes (10): Desktop layer (pure pyobjc NSWindow + WKWebView, orb NSPanel, menu bar), Orb overlay (floating non-activating NSPanel), UI -> daemon commands (mute, ptt, confirm, kill_all, text, wake_mode, dictation...), UI event contract ({type, ts, data} over /ws), Orb overlay page (orb.html), connect() WebSocket with exponential retry, draw() canvas orb renderer, effective() state resolver (+2 more)

### Community 95 - "is_junk_translation"
Cohesion: 0.33
Nodes (6): is_junk_translation(), Model tarjima o'rniga yorliq/izoh aytdi (`(Uzbek translation: …)`, `<no…, youtube_id(), parametrize, test_is_junk_translation(), test_youtube_id()

### Community 98 - "_conversation"
Cohesion: 0.67
Nodes (3): _conversation(), start_conversation(), stop_conversation()

### Community 101 - ".get_system_info"
Cohesion: 0.24
Nodes (5): _fmt_uptime(), Any, SSID ni aniqlaydi. macOS 14+ da Location Services ruxsatisiz SSID `<redacted>`…, _summarize_info(), Any

### Community 102 - "is_quota_error"
Cohesion: 0.67
Nodes (3): is_quota_error(), Kalit kvotasi (bir vaqtdagi sessiyalar soni yoki kunlik limit) tugadi., test_is_quota_error()

### Community 103 - "sandbox"
Cohesion: 0.67
Nodes (3): fixture, tmp_path ni ruxsat etilgan ildiz va default papka qiladi., sandbox()

### Community 104 - "Security model (confirmation from user transcript/UI only)"
Cohesion: 0.25
Nodes (9): CommandGuard allow/deny/confirm tiers, Loop guard (max 15 calls/turn, 3 identical), Secret redaction (redact_secrets), Security model (confirmation from user transcript/UI only), Sensitive path denial (path_is_sensitive), Taint guard (external content -> exfil/execute tools require confirmation), ToolRegistry.execute flow: validate -> loop guard -> taint -> confirm -> handler, Old code bugs (do not repeat) (+1 more)

### Community 114 - "Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline"
Cohesion: 0.25
Nodes (8): Nexus Ovoz OS design mockup (dc.html), Design mockup Component (simulated PTT command flow), Local models concept (Whisper.cpp small.uz + Qwen 7B Q4), Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline, Gemini Live API (native audio, WebSocket), Nexus browser/desktop panel (index.html), Confirmation card (TASDIQ KUTILMOQDA, Yes/No, TTL), Live transcript box

### Community 116 - "test_is_terminal_frontmost"
Cohesion: 0.50
Nodes (3): is_terminal_app(), Old oynadagi ilova terminal (Terminal/iTerm/Warp/...) bo'lsa True., test_is_terminal_frontmost()

### Community 117 - "pytest"
Cohesion: 0.29
Nodes (6): pytest, fixture, MonkeyPatch, Umumiy test sozlamalari., Registry testlari OS'dan mustaqil: Windows'da ham to'liq (macOS) tool ro'yxati…, _registry_as_macos()

### Community 119 - "_coerce_cell_value"
Cohesion: 0.67
Nodes (3): _coerce_cell_value(), 250000" → 250000, "3.5" → 3.5; qolgani satr. Telefon (+998...) va 007 satr…, test_coerce_cell_value()

### Community 120 - "TaintTracker"
Cohesion: 0.25
Nodes (3): Navbat ichida tashqi matn o'qilganini eslab qoladi., TaintTracker, test_taint_tracker()

### Community 130 - "_dictation"
Cohesion: 0.67
Nodes (3): _dictation(), start_dictation(), stop_dictation()

## Ambiguous Edges - Review These
- `Gemini Live API (native audio, WebSocket)` → `Local models concept (Whisper.cpp small.uz + Qwen 7B Q4)`  [AMBIGUOUS]
  design/Nexus Ovoz OS.dc.html · relation: conceptually_related_to

## Knowledge Gaps
- **18 isolated node(s):** `INPUT`, `_INPUTUNION`, `MOUSEINPUT`, `Live transcript box`, `Session resumption + context compression` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 693 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Gemini Live API (native audio, WebSocket)` and `Local models concept (Whisper.cpp small.uz + Qwen 7B Q4)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `ToolRegistry` connect `ToolRegistry` to `normalize_browser`, `Any`, `Result`, `test_registry_no_confirmation_runs_immediately`, `Security model (confirmation from user transcript/UI only)`, `test_core.py`, `._build_handlers`, `test_tools.py`, `video_translate.py`, `windows_screen.py`, `test_safety.py`, `WindowsController`, `Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline`, `test_video_translate.py`, `_registry`, `test_registry_loads_extension_modules`, `main.py`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Why does `NexusDesktopApp` connect `NexusDesktopApp` to `DaemonRunner`, `desktop.py`, `._build_window`, `test_desktop.py`, `Settings`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `AudioStreamer` connect `AudioStreamer` to `test_core.py`, `video_translate.py`, `Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline`, `._process_chunk`, `AudioPlayer`, `reference/AI analysis (old Voice Assistant)`, `main.py`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `GeminiLiveClient` (e.g. with `WakeState` and `run()`) actually correct?**
  _`GeminiLiveClient` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `ToolRegistry` (e.g. with `run()` and `WindowsController`) actually correct?**
  _`ToolRegistry` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `INPUT`, `_INPUTUNION`, `MOUSEINPUT` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._