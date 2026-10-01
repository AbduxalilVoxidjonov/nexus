# Graph Report - nexus  (2026-10-01)

## Corpus Check
- 52 files · ~110,293 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 4, .command 2, .example 1)

## Summary
- 2246 nodes · 4948 edges · 131 communities (100 shown, 31 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 333 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `74ba4159`
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
- Result
- screen_reader.py
- test_screen_reader.py
- ToolRegistry
- path_is_sensitive
- desktop.py
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
- AudioStreamer
- Any
- CommandGuard
- windows_input.py
- Settings
- test_run_waits_for_api_key_from_settings
- config.py
- cli
- test_windows.py
- test_core.py
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
- file_actions.py
- run
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
- run_shell
- nexus/__init__.py
- gemini_live_client.py
- build_app.sh
- web_answer.py
- nexus-voice
- desktop_win.py
- FakeStream
- BaseException
- ._run
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
- windows_smoke.py
- vision_box_to_screen
- Process
- player_setup_js
- Path
- Result
- .get_system_info
- _recognize
- .open
- Security model (confirmation from user transcript/UI only)
- sensitivity_to_threshold
- ._confirmation_pending
- error_text
- fixture
- parametrize
- AbstractEventLoop
- BaseException
- test_registry_kill_all_runs_hook_and_cancels_gate
- Queue
- Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline
- Path
- is_terminal_app
- pytest
- Settings
- _coerce_cell_value
- TaintTracker
- test_registry_loads_extension_modules
- EventBus
- .kill_all
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

## Communities (131 total, 31 thin omitted)

### Community 0 - "support.js"
Cohesion: 0.06
Nodes (75): boot(), bundledBlob(), cdnScriptFor(), collectProps(), compileAttr(), compileTemplate(), contentKey(), createComponentFactory() (+67 more)

### Community 1 - "Any"
Cohesion: 0.31
Nodes (20): _append_csv(), _append_row_sync(), _append_xlsx(), delete_file(), _is_confirmed(), _list_directory_sync(), _open_book(), path_allowed() (+12 more)

### Community 2 - "ax_actions.py"
Cohesion: 0.06
Nodes (75): applicationservices, difflib, _actions(), activate_element(), _app_root(), _attr(), available(), _clean_text() (+67 more)

### Community 3 - "Result"
Cohesion: 0.06
Nodes (28): app_name(), BrowserController, BrowserDOMController, _fmt_time(), _js_error(), js_to_applescript(), normalize_url(), _parse_json() (+20 more)

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
Cohesion: 0.08
Nodes (27): _no_sleep(), MonkeyPatch, Tool qatlami testlari — real macOS tizimiga tegmaydi (osascript/subprocess…, Barcha ichki JS'lar AppleScript literaliga qo'yilganda qo'shtirnoq muvozanati…, ScriptRecorder, test_browser_open_url_normalizes(), test_is_terminal_frontmost(), test_launch_app_uses_fuzzy_match() (+19 more)

### Community 8 - "EventBus"
Cohesion: 0.16
Nodes (7): CommandHandler, EventBus, AbstractEventLoop, Any, Queue, Thread-safe pub/sub. `publish` istalgan thread'dan chaqirilishi mumkin., test_ws_get_state_without_handler()

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
Cohesion: 0.14
Nodes (8): _clamp(), MacOSController, Result, AppleScript'ni `osascript` orqali bajaradi (stdin orqali, argument uzunligi…, macOS bilan ishlash: ovoz, media, ilovalar, Finder, tizim, terminal., macOS 12+ da DND uchun ochiq API yo'q. Foydalanuvchi yaratgan Shortcuts…, Faol oynaga matn kiritadi: bufer + Cmd+V (keystroke o'zbek/kirill matnni…, run_applescript()

### Community 13 - "test_server.py"
Cohesion: 0.16
Nodes (14): fastapi_testclient, TestClient, bus(), client(), _free_port(), fixture, nexus.server (FastAPI + WS ko'prigi) testlari., test_api_state() (+6 more)

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
Cohesion: 0.12
Nodes (31): appkit, foundation, available(), capture_frontmost_window(), describe_screen(), _shoot(), _extract_text(), _front_app() (+23 more)

### Community 18 - "test_screen_reader.py"
Cohesion: 0.11
Nodes (13): Exception, inspect, _fake_client(), _FakeModels, screen_reader (OCR + Gemini ko'rish) va ax_actions'dagi AX→OCR zaxira yo'li…, test_click_ui_element_by_ocr_index_from_cache(), test_describe_screen_default_question(), test_describe_screen_error_and_timeout() (+5 more)

### Community 19 - "ToolRegistry"
Cohesion: 0.10
Nodes (12): EventBus, Foydalanuvchi yangi gap boshladi: loop guard va taint tozalanadi., Foydalanuvchining yakuniy transkripti — og'zaki tasdiq uchun., Gemini toollarini bajaruvchi markaziy ro'yxat., ToolRegistry, test_conversation_tools_registered(), test_registry_has_handler_for_every_declaration(), test_registry_unknown_tool() (+4 more)

### Community 20 - "path_is_sensitive"
Cohesion: 0.13
Nodes (17): Verdict, Buyruqni tokenlarga bo'lish (POSIX qoidalari). Windows qo'riqchisi qayta…, looks_read_only(), path_is_sensitive(), Path, True — buyruq DANGEROUS_SHELL naqshlaridan biriga mos keladi., True — buyruq HECH QANDAY bayroq bilan ham hech narsani o'zgartira olmaydi., True — bu yerga yozish persistensiya yaratishi yoki sir sizdirishi mumkin. (+9 more)

### Community 21 - "desktop.py"
Cohesion: 0.11
Nodes (22): asyncio, collections, collections_abc, Mikrofon oqimi va ovoz ijrosi (sounddevice / PortAudio). `AudioStreamer` —…, Desktop ilova qatlami: o'z oynasi, doim tepada turadigan orb va menyu bar…, Daemon ichidagi hodisalar shinasi (event bus). Barcha modullar (audio, gemini,…, Nexus Ovoz OS — CLI kirish nuqtasi (`nexus` buyrug'i). nexus # desktop ilova:…, YouTube videosini jonli (sinxron) ovozli tarjima: ingliz → o'zbek. Oqim: yt-dlp… (+14 more)

### Community 22 - "check_setup.py"
Cohesion: 0.16
Nodes (21): argparse, CDLL, check_accessibility(), check_automation(), check_devices(), check_key(), check_live(), check_mic_level() (+13 more)

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
Cohesion: 0.12
Nodes (10): _ConfirmTracker, create_app(), index(), EventBus, Path, Settings, FastAPI ilovasini yaratadi (testlarda ham shu ishlatiladi)., CONFIRM_REQUEST / CONFIRM_RESOLVED hodisalarini kuzatib, ochiq tasdiqni eslab… (+2 more)

### Community 29 - "WindowsBrowser"
Cohesion: 0.11
Nodes (4): looks_like_result(), Brauzer amallari — macOS'dagi BrowserController/DOM/YouTube/Search sinflari…, WindowsBrowser, test_looks_like_result()

### Community 30 - "ConfirmationGate"
Cohesion: 0.16
Nodes (9): ConfirmationGate, _consume(), PendingConfirmation, True = rozi, False = rad, None = javob emas. Rad etish (veto) gap uzunligidan…, Bir vaqtda faqat bitta faol tasdiq so'rovi. Yangi so'rov eskisini bekor qiladi., Foydalanuvchining yakuniy transkripti. So'rovdan OLDIN aytilgan gap hisobga…, Bus'dagi TRANSCRIPT (user, final) hodisalarini ham kuzatadi — gemini client…, spoken_verdict() (+1 more)

### Community 31 - "test_wake_dictation.py"
Cohesion: 0.12
Nodes (26): is_stop_phrase(), Butun gap faqat to'xtash iborasidan iboratmi?, _candidates(), levenshtein(), name_in(), Levenshtein masofasi; `limit` berilsa undan oshgach hisoblashni to'xtatadi…, Qisqa ism aniq mos kelishi kerak; uzunroq ism 2-3 xatoni ko'taradi., (nomzod, boshlanish indeksi, so'zlar soni) — yakka so'zlar va qo'shni… (+18 more)

### Community 32 - "AudioStreamer"
Cohesion: 0.06
Nodes (24): AbstractEventLoop, AudioStreamer, _list_devices(), _mute(), _playback(), _ptt(), _ptt_press(), _sensitivity() (+16 more)

### Community 33 - "Any"
Cohesion: 0.15
Nodes (8): Handler, normalize_browser(), Any, Handler javobini (tuple yoki dict) yagona formatga keltiradi., Bajarishdan OLDIN aniqlanadigan tasdiq sabablari (bo'sh — tasdiqsiz)., _to_text(), _truncate(), translate_video()

### Community 34 - "CommandGuard"
Cohesion: 0.16
Nodes (11): CommandGuard, Buyruqni qo'riqchi orqali bajaradi. `confirmed=True` — registry foydalanuvchi…, `run_terminal_command` uchun uch pog'onali qo'riqchi. `check()` → ("allow" |…, Tekshiruvdan o'tgan buyruqni bajarish uchun argv (`~` kengaytirilgan holda)., _truncate(), parametrize, test_guard_allows(), test_guard_argv_expands_tilde() (+3 more)

### Community 35 - "windows_input.py"
Cohesion: 0.10
Nodes (26): Nisbiy siljish → klavishlar: 10 s lik l/j, qoldig'i 5 s lik o'qlar., seek_presses(), combo_events(), HotkeyError, INPUT, _INPUTUNION, KEYBDINPUT, MOUSEINPUT (+18 more)

### Community 36 - "Settings"
Cohesion: 0.11
Nodes (10): google-genai Client — hamma joyda bir xil sozlama bilan., Settings, DaemonRunner, `nexus.main.run()` ni alohida thread'da o'z event loop'i bilan yuritadi., To'xtatish signalini beradi (bloklamaydi) — tugashini `finished` orqali…, To'xtatish signalini beradi va thread tugashini kutadi. True = toza tugadi., GUI'dan daemon'ga buyruq (thread-safe, natija kutilmaydi)., test_config_defaults_gemini38() (+2 more)

### Community 37 - "test_run_waits_for_api_key_from_settings"
Cohesion: 0.10
Nodes (10): FakeLiveConnect, 1011 'exceeded your current quota' → avval google_search grounding olib…, client.aio.live.connect o'rnini bosuvchi: har chaqiruvda navbatdagi FakeSession., connect(), test_quota_error_drops_google_search_first(), connect(), test_run_drops_resume_handle_after_short_session(), test_run_reconnects_with_resume_handle_and_counts() (+2 more)

### Community 38 - "config.py"
Cohesion: 0.11
Nodes (25): dotenv, api_key_env_path(), _describe_char(), _env_api_key(), env_candidates(), is_placeholder_api_key(), load_env_files(), load_extra_env() (+17 more)

### Community 39 - "cli"
Cohesion: 0.14
Nodes (13): DesktopOptions, _env_true(), Desktop ilovani ishga tushiradi (asosiy thread'da bloklaydi). Qaytadi: chiqish…, argparse Namespace (nexus.main.build_parser) → DesktopOptions., Ilova menyusida (chap yuqori) "python" o'rniga ilova nomi (bundle'siz ishga…, run_desktop(), _set_process_display_name(), cli() (+5 more)

### Community 40 - "test_windows.py"
Cohesion: 0.04
Nodes (39): fixture, nexus_tools, browser_key(), pick_window(), Tezlik: avval minimal (0.25) gacha tushirib, keyin kerakli qadamlar., chrome' / 'edge' / 'firefox' yoki None (istalgan). macOS'dagi 'safari' —…, Z-tartib bo'yicha birinchi mos brauzer oynasi (so'ralgani bo'lmasa — istalgan…, speed_presses() (+31 more)

### Community 41 - "test_core.py"
Cohesion: 0.08
Nodes (31): math, compute_rms(), int16 mono PCM baytlaridan (rms 0..1, db -60..0) qaytaradi., numpy, sounddevice, fake_sd(), make_settings(), fixture (+23 more)

### Community 42 - "._evaluate_addressed"
Cohesion: 0.13
Nodes (6): Oxirgi real audio chunk karnayga chiqqan payt (time.monotonic; 0 — hali yo'q)., UI dan matn buyrug'i. Sessiya yo'q bo'lsa False., Registry'ga foydalanuvchi navbatini bildiradi: og'zaki tasdiq (note_utterance)…, Wake rejimi bo'yicha gap bizga qaratilganmi (qisman transkriptda ham). Baho…, Joriy gap boshlangan payt (AudioStreamer RMS gate). Noma'lum yoki eskirgan…, Suhbat rejimi: ismsiz erkin suhbat; jimlikdan keyin o'zi tugaydi (`tick`).

### Community 43 - "FakeAudio"
Cohesion: 0.12
Nodes (8): FakeAudio, FakeRegistry, test_background_voice_does_not_cut_addressed_reply(), test_build_config_ptt_disables_vad_and_optional_fields(), test_conversation_command_and_idle_tick(), test_run_requires_api_key(), test_user_turn_without_registry_hooks(), test_wake_name_mode_suppresses_audio_and_tools()

### Community 44 - "test_desktop.py"
Cohesion: 0.11
Nodes (21): ArgumentParser, Namespace, `base_url/health` 2xx qaytarguncha kutadi. `keep_waiting()` False qaytarsa…, wait_for_server(), build_parser(), desktop_mode(), Desktop (oyna + orb + menyu bar) rejimi kerakmi? `--headless`, `--no-ui`…, MonkeyPatch (+13 more)

### Community 45 - "macos_actions.py"
Cohesion: 0.13
Nodes (26): ctypes, datetime, importlib, json, logging, Brauzer boshqaruvi (Safari / Google Chrome) — AppleScript + sahifa ichidagi…, macOS tizim amallari (AppleScript + xavfsiz shell). Barcha subprocess…, _cmd() (+18 more)

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
Cohesion: 0.31
Nodes (10): _cmd_result(), api_state(), snapshot(), ws_endpoint(), handle_command(), receiver(), send(), sender() (+2 more)

### Community 50 - "BargeInGate"
Cohesion: 0.25
Nodes (6): BargeInGate, Ijro paytida mikrofon chunklarining echo/barge-in darvozasi (callback…, → (navbatga qo'yiladigan chunklar, sukunatga almashtirilganlar soni)., test_barge_gate_flushes_held_when_playback_stops(), test_barge_gate_single_spike_becomes_silence(), test_barge_gate_sustained_opens_and_holds()

### Community 51 - "Segmenter"
Cohesion: 0.38
Nodes (4): Uzluksiz nutqni tarjima bo'laklariga ajratadi: `push(rms)` True → bo'lakni shu…, Segmenter, test_segmenter_cuts_at_max(), test_segmenter_cuts_on_quiet_after_min()

### Community 52 - "server.py"
Cohesion: 0.13
Nodes (12): contextlib, errno, FastAPI, fastapi_responses, fastapi_staticfiles, _QuietServer, UI ko'prigi: FastAPI + WebSocket server. EventBus hodisalarini brauzerdagi UI…, Signal handlerlarini o'rnatmaydigan uvicorn Server (signalni main.py… (+4 more)

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
Cohesion: 0.16
Nodes (18): Box, _image_size(), lines_as_elements(), lines_to_text(), ocr_image(), Satrlarni yuqoridan pastga, bir qatordagilarni chapdan o'ngga tartiblaydi. Ikki…, Tartiblangan satrlardan matn: bir qatordagilar ikki bo'shliq bilan, qatorlar…, OCR satrlarini list_ui_elements formatiga o'giradi: {n, role:'text', label, at,… (+10 more)

### Community 59 - "file_actions.py"
Cohesion: 0.14
Nodes (14): append_spreadsheet_row(), _fallback_path_is_sensitive(), find_files(), list_directory(), Fayl, eslatma va Excel/CSV toollari — kengaytma moduli. Eksport (registry…, Model aytgan yo'lni absolyut `Path`ga aylantiradi. Bo'sh bo'lsa `default` (yoki…, Spotlight (mdfind) yo'q joyda: nomida `query` bor fayllar (yashirin…, read_file() (+6 more)

### Community 60 - "run"
Cohesion: 0.11
Nodes (19): Event, check_environment(), _first(), MetricsTicker, platform_controller(), print_banner(), Any, EventBus (+11 more)

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
Cohesion: 0.07
Nodes (21): csv, nexus, POSIX_ONLY, fixture, parametrize, Kengaytma modullari (ax_actions, file_actions) testlari — real…, tmp_path ni ruxsat etilgan ildiz va default papka qiladi., pyobjc yo'q holat: handler xato matni qaytaradi, istisno emas. (+13 more)

### Community 71 - "test_registry_no_confirmation_runs_immediately"
Cohesion: 0.29
Nodes (3): test_registry_no_confirmation_runs_immediately(), test_registry_tainted_turn_requires_confirmation(), read_page()

### Community 72 - "LoopGuard"
Cohesion: 0.20
Nodes (7): LoopGuard, Any, Bir navbatda haddan ko'p yoki bir xil chaqiruvlarni to'xtatadi., None — davom et; matn — rad etish sababi (modelga tushuntirish)., test_loop_guard_identical_calls(), test_loop_guard_max_calls_per_turn(), test_loop_guard_non_consecutive_identical_calls()

### Community 73 - "._build_window"
Cohesion: 0.13
Nodes (18): default_orb_origin(), default_window_frame(), _hex_color(), _make_app_icon(), _make_webview(), placeholder_html(), Oyna/orb hech bo'lmaganda `min_visible`×`min_visible` qismi bilan biror ekranda…, Ekranning pastki-o'ng burchagi (Dock/menyu bar hisobga olingan `visibleFrame`… (+10 more)

### Community 74 - "run_shell"
Cohesion: 0.25
Nodes (7): open_with_app(), _kill_process_group(), Jarayonni va u tug'dirgan barcha bolalarni (process group) o'ldiradi., Dasturni shell'siz ishga tushiradi. `(ok, stdout yoki stderr)` qaytaradi., run_shell(), _suppress, Process

### Community 76 - "gemini_live_client.py"
Cohesion: 0.16
Nodes (15): dataclasses, itertools, api_key_hint(), UI uchun niqoblangan ko'rinish: `AIza…x1y2` (kalitning o'zi hech qachon UI ga…, Diktovka rejimi: foydalanuvchi gapiradi — yordamchi teradi, to'xtash…, Gemini Multimodal Live API (WebSocket) sessiyasi. Ikki parallel task:…, ends_conversation(), _has_phrase() (+7 more)

### Community 78 - "web_answer.py"
Cohesion: 0.33
Nodes (12): build_request(), _create(), extract_sources(), extract_text(), _get(), _make_client(), Any, `web_answer` tool — Google Search grounding bilan faktik/yangilik savollariga… (+4 more)

### Community 81 - "desktop_win.py"
Cohesion: 0.24
Nodes (10): DaemonRunner, DesktopOptions, Settings, Windows desktop qatlami: daemon alohida thread'da, UI — pywebview (Edge…, Konsolsiz .exe da xato ko'rinmay qolmasin — Windows xabar oynasi., UI serveri tinglay boshlaguncha kutadi., run_desktop(), show_error() (+2 more)

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
Cohesion: 0.10
Nodes (15): AudioPlayer, parse_latency(), EventBus, high"/"low" yoki sekund (str/float) → sounddevice `latency` argumenti., 24 kHz int16 mono ijro. `enqueue` istalgan thread/task'dan chaqirilishi mumkin.…, Buferdagi qolgan audioni (prebuffer to'lmagan bo'lsa ham) ijroga qo'yib…, Navbatni tozalaydi (interruption). Tashlangan chunklar sonini qaytaradi., test_interrupted_cancels_tools_and_generation_complete_plays_out() (+7 more)

### Community 89 - "WindowsCommandGuard"
Cohesion: 0.22
Nodes (5): CommandGuard, `run_terminal_command` qo'riqchisi — Windows (cmd) buyruqlari uchun. Asosiy…, Buyruqni qo'riqchi orqali `cmd` da bajaradi (UTF-8 kod sahifasi, shell…, WindowsCommandGuard, Verdict

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

### Community 95 - "windows_smoke.py"
Cohesion: 0.29
Nodes (9): browser_smoke(), check(), main(), Windows smoke testi: registry, xavfsiz toollar va UI serveri haqiqiy Windows'da…, Muhitga bog'liq tekshiruv (brauzerning birinchi ishga tushishi va h.k.) —…, Diagnostika: brauzer oynasining UIA daraxtida nima bor (Chromium veb-kontenti…, soft(), uia_dump() (+1 more)

### Community 96 - "vision_box_to_screen"
Cohesion: 0.50
Nodes (4): Vision normalizatsiyalangan bbox (0..1, y PASTDAN) → ekran (x, y, w, h),…, vision_box_to_screen(), test_vision_box_bottom_line_lands_at_window_bottom(), test_vision_box_to_screen_flips_y_and_offsets_by_window()

### Community 98 - "player_setup_js"
Cohesion: 0.29
Nodes (5): player_setup_js(), Video pauza, tarjima ovozi esa davom etadi — `seconds` dan keyin video qayta…, Pleyer: asl ovozni o'chirish/pasaytirish (0..1, manfiy — tegilmaydi) va ijro…, test_player_setup_js(), test_player_setup_js_keeps_volume_when_negative()

### Community 101 - ".get_system_info"
Cohesion: 0.24
Nodes (5): _fmt_uptime(), Any, SSID ni aniqlaydi. macOS 14+ da Location Services ruxsatisiz SSID `<redacted>`…, _summarize_info(), Any

### Community 102 - "_recognize"
Cohesion: 0.33
Nodes (6): pick_languages(), Qo'llab-quvvatlanadigan tillardan kerakli tartibda tanlaydi ("uz" → "uz-UZ"…, Vision OCR: [(text, nx, ny, nw, nh, confidence)] — normalizatsiyalangan, y…, _recognize(), supported_languages(), test_pick_languages_prefers_uz_then_ru_en_and_skips_missing()

### Community 104 - "Security model (confirmation from user transcript/UI only)"
Cohesion: 0.25
Nodes (9): CommandGuard allow/deny/confirm tiers, Loop guard (max 15 calls/turn, 3 identical), Secret redaction (redact_secrets), Security model (confirmation from user transcript/UI only), Sensitive path denial (path_is_sensitive), Taint guard (external content -> exfil/execute tools require confirmation), ToolRegistry.execute flow: validate -> loop guard -> taint -> confirm -> handler, Old code bugs (do not repeat) (+1 more)

### Community 105 - "sensitivity_to_threshold"
Cohesion: 0.67
Nodes (3): Sezgirlik (0..1) → RMS bo'sag'asi. 1.0 = juda sezgir (past bo'sag'a)., sensitivity_to_threshold(), test_sensitivity_threshold_monotonic()

### Community 107 - "error_text"
Cohesion: 0.50
Nodes (4): error_text(), BaseException, Gemini xatosini foydalanuvchiga o'zbekcha qisqa jumla qilib beradi., test_error_text_is_uzbek()

### Community 114 - "Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline"
Cohesion: 0.25
Nodes (8): Nexus Ovoz OS design mockup (dc.html), Design mockup Component (simulated PTT command flow), Local models concept (Whisper.cpp small.uz + Qwen 7B Q4), Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline, Gemini Live API (native audio, WebSocket), Nexus browser/desktop panel (index.html), Confirmation card (TASDIQ KUTILMOQDA, Yes/No, TTL), Live transcript box

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
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 691 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Gemini Live API (native audio, WebSocket)` and `Local models concept (Whisper.cpp small.uz + Qwen 7B Q4)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `ToolRegistry` connect `ToolRegistry` to `Any`, `test_registry_no_confirmation_runs_immediately`, `Security model (confirmation from user transcript/UI only)`, `test_core.py`, `._build_handlers`, `test_tools.py`, `macos_actions.py`, `test_safety.py`, `Result`, `Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline`, `test_video_translate.py`, `_registry`, `test_registry_loads_extension_modules`, `run`, `.kill_all`, `windows_smoke.py`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `run()` connect `run` to `AudioStreamer`, `GeminiLiveClient`, `config.py`, `cli`, `ToolRegistry`, `server.py`, `desktop.py`, `test_video_translate.py`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `GeminiLiveClient` connect `GeminiLiveClient` to `AudioStreamer`, `is_config_rejection`, `._evaluate_addressed`, `._confirmation_pending`, `gemini_live_client.py`, `Any`, `.run`, `Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline`, `.tick`, `WakeState`, `reference/AI analysis (old Voice Assistant)`, `run`, `._handle_server_content`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `GeminiLiveClient` (e.g. with `WakeState` and `run()`) actually correct?**
  _`GeminiLiveClient` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `ToolRegistry` (e.g. with `run()` and `WindowsController`) actually correct?**
  _`ToolRegistry` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `INPUT`, `_INPUTUNION`, `MOUSEINPUT` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._