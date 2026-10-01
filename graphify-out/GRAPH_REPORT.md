# Graph Report - nexus  (2026-10-01)

## Corpus Check
- 47 files · ~99,983 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 4, .command 2, .example 1)

## Summary
- 2003 nodes · 4393 edges · 105 communities (88 shown, 17 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 270 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a04aab01`
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
- desktop.py
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
- name_in
- AudioStreamer
- video_translate.py
- CommandGuard
- test_registry_kill_all_runs_hook_and_cancels_gate
- Settings
- FakeLiveConnect
- config.py
- main.py
- vision_box_to_screen
- make_settings
- ._evaluate_addressed
- describe_screen
- test_desktop.py
- macos_actions.py
- test_safety.py
- Any
- .run
- snapshot
- BargeInGate
- Segmenter
- server.py
- test_video_translate.py
- dictation.py
- asyncio
- fake_screen
- Segment
- reference/AI analysis (old Voice Assistant)
- _recognize
- ._feed
- ._handle_server_content
- Process
- schemas.py
- NexusOrbPanel
- is_dismissal
- error_text
- Any
- ocr_image
- is_config_rejection
- VideoTranslator
- test_registry_no_confirmation_runs_immediately
- LoopGuard
- ._build_window
- test_registry_loads_extension_modules
- nexus/__init__.py
- wake.py
- build_app.sh
- .get_system_info
- nexus-voice
- ._finalize_user_turn
- FakeStream
- ._handle_message
- ._run
- PlaybackClock
- _ConfirmTracker
- CLAUDE.md
- AudioPlayer
- Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline
- TaintTracker
- test_wake_dictation.py
- is_junk_translation
- _starts_a_word
- Orb overlay page (orb.html)
- bus
- test_ws_slow_command_does_not_block_following_commands
- Security model (confirmation from user transcript/UI only)
- .build_hotkey_script
- .tick
- build_ytdlp_cmd
- spoken_verdict
- AbstractEventLoop
- BaseException
- Queue

## God Nodes (most connected - your core abstractions)
1. `MacOSController` - 61 edges
2. `ToolRegistry` - 58 edges
3. `GeminiLiveClient` - 58 edges
4. `VideoTranslator` - 55 edges
5. `AudioStreamer` - 49 edges
6. `WindowsController` - 47 edges
7. `NexusDesktopApp` - 46 edges
8. `make_client()` - 41 edges
9. `FakeSession` - 32 edges
10. `WakeState` - 31 edges

## Surprising Connections (you probably didn't know these)
- `Confirmation card (TASDIQ KUTILMOQDA, Yes/No, TTL)` --shares_data_with--> `ConfirmationGate`  [INFERRED]
  ui/index.html → nexus/safety.py
- `Echo guard + playback prebuffer + low VAD start sensitivity` --rationale_for--> `AudioStreamer`  [INFERRED]
  README.md → nexus/audio_streamer.py
- `session.receive() ends each turn (not a disconnect)` --rationale_for--> `GeminiLiveClient`  [INFERRED]
  README.md → nexus/gemini_live_client.py
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

## Communities (105 total, 17 thin omitted)

### Community 0 - "support.js"
Cohesion: 0.06
Nodes (75): boot(), bundledBlob(), cdnScriptFor(), collectProps(), compileAttr(), compileTemplate(), contentKey(), createComponentFactory() (+67 more)

### Community 1 - "file_actions.py"
Cohesion: 0.05
Nodes (68): csv, _append_csv(), _append_row_sync(), append_spreadsheet_row(), _append_xlsx(), _coerce_cell_value(), delete_file(), _fallback_path_is_sensitive() (+60 more)

### Community 2 - "ax_actions.py"
Cohesion: 0.06
Nodes (80): applicationservices, difflib, _actions(), activate_element(), _app_root(), _attr(), available(), _clean_text() (+72 more)

### Community 3 - "Result"
Cohesion: 0.06
Nodes (23): app_name(), BrowserController, BrowserDOMController, _fmt_time(), _js_error(), normalize_url(), _parse_json(), Any (+15 more)

### Community 4 - "GeminiLiveClient"
Cohesion: 0.23
Nodes (3): GeminiLiveClient, Final transkript bo'lagini darhol teradi; to'xtash iborasi rejimni tugatadi., Session resumption + context compression

### Community 5 - "test_core.py"
Cohesion: 0.07
Nodes (49): GeminiLiveClient, SimpleNamespace, sounddevice, _audio_part(), FakeSession, make_client(), _msg(), EventBus (+41 more)

### Community 6 - "app.js"
Cohesion: 0.12
Nodes (58): answerConfirm(), applyDevices(), applySettings(), applySnapshot(), bind(), closeSocket(), connect(), ensureRow() (+50 more)

### Community 7 - "test_tools.py"
Cohesion: 0.08
Nodes (30): _no_sleep(), MonkeyPatch, Tool qatlami testlari — real macOS tizimiga tegmaydi (osascript/subprocess…, Barcha ichki JS'lar AppleScript literaliga qo'yilganda qo'shtirnoq muvozanati…, ScriptRecorder, test_browser_open_url_normalizes(), test_is_terminal_frontmost(), test_js_permission_hint() (+22 more)

### Community 8 - "EventBus"
Cohesion: 0.16
Nodes (7): CommandHandler, EventBus, AbstractEventLoop, Any, Queue, Thread-safe pub/sub. `publish` istalgan thread'dan chaqirilishi mumkin., test_ws_get_state_without_handler()

### Community 9 - "Nexus Ovoz OS README"
Cohesion: 0.22
Nodes (11): Nexus Ovoz OS README, AXManualAccessibility for Chrome/Electron, Dictation mode (direct typing, stop phrases), .env settings (GEMINI_MODEL, VAD_THRESHOLD, WAKE_MODE, UI_PORT ...), EXTENSION_MODULES (TOOL_DECLARATIONS + HANDLERS), macOS permissions (Microphone, Accessibility, Screen Recording, Automation), Scripts: check_setup, benchmark_live, voice_picker, Tool catalog (62 tools: 45 core + 10 file + 7 AX) (+3 more)

### Community 10 - "._build_handlers"
Cohesion: 0.05
Nodes (25): build_search_url(), web_search(), browser_click_button(), browser_click_selector(), browser_close_tab(), browser_current_page(), browser_list_tabs(), browser_open_url() (+17 more)

### Community 11 - "NexusDesktopApp"
Cohesion: 0.09
Nodes (8): _load_url(), NexusDesktopApp, Any, NSApplication delegati: oyna, orb, menyu bar, daemon ko'prigi., SIGINT/SIGTERM → toza chiqish. Mach-port orqali AppKit run loop'ida qayta…, Daemon thread'idan chaqiriladi — hodisani GUI thread'iga uzatadi., `.env` ni Finder'da ko'rsatadi (yagona "tashqi ochish" — brauzer emas)., NSObject

### Community 12 - "MacOSController"
Cohesion: 0.11
Nodes (10): _clamp(), MacOSController, Result, SSID ni aniqlaydi. macOS 14+ da Location Services ruxsatisiz SSID `<redacted>`…, Buyruqni qo'riqchi orqali bajaradi. `confirmed=True` — registry foydalanuvchi…, macOS bilan ishlash: ovoz, media, ilovalar, Finder, tizim, terminal., Old oynadagi ilova terminal (Terminal/iTerm/Warp/...) bo'lsa True., macOS 12+ da DND uchun ochiq API yo'q. Foydalanuvchi yaratgan Shortcuts… (+2 more)

### Community 13 - "test_server.py"
Cohesion: 0.21
Nodes (12): fastapi_testclient, TestClient, client(), _free_port(), fixture, nexus.server (FastAPI + WS ko'prigi) testlari., test_api_state(), test_health() (+4 more)

### Community 14 - "desktop.py"
Cohesion: 0.11
Nodes (18): DesktopOptions, _env_true(), _make_app_icon(), placeholder_html(), Desktop ilova qatlami: o'z oynasi, doim tepada turadigan orb va menyu bar…, Desktop ilovani ishga tushiradi (asosiy thread'da bloklaydi). Qaytadi: chiqish…, argparse Namespace (nexus.main.build_parser) → DesktopOptions., Server tayyor bo'lguncha (yoki daemon xato bilan to'xtasa) oynada… (+10 more)

### Community 15 - "state_style"
Cohesion: 0.22
Nodes (10): effective_state(), (rang, yorliq) — menyu bar / orb uchun., Menyu bar'dagi holat satri, masalan "● Tinglamoqda" yoki "● Kutmoqda (mikrofon…, Daemon holati + Gemini ulanishi + tasdiqdan bitta ko'rsatiladigan holat., state_style(), status_title(), parametrize, test_effective_state_priorities() (+2 more)

### Community 16 - "WindowsController"
Cohesion: 0.06
Nodes (28): fixture, nexus, nexus_tools, _press_key(), _ps_quote(), Any, Path, Result (+20 more)

### Community 17 - "screen_reader.py"
Cohesion: 0.15
Nodes (19): appkit, foundation, capture_frontmost_window(), _shoot(), _front_app(), _front_window_info(), _image_size(), _largest_window() (+11 more)

### Community 18 - "test_screen_reader.py"
Cohesion: 0.10
Nodes (17): Exception, _box(), _fake_client(), _FakeModels, Any, screen_reader (OCR + Gemini ko'rish) va ax_actions'dagi AX→OCR zaxira yo'li…, test_click_ui_element_by_ocr_index_from_cache(), test_describe_screen_default_question() (+9 more)

### Community 19 - "ToolRegistry"
Cohesion: 0.08
Nodes (16): Handler, Any, Foydalanuvchi yangi gap boshladi: loop guard va taint tozalanadi., Foydalanuvchining yakuniy transkripti — og'zaki tasdiq uchun., Bajarilayotgan tool tasklarini bekor qiladi. Kutilayotgan tasdiq so'roviga…, ⌥⎋ / "kill_all": tool tasklar + kutilayotgan tasdiq bekor qilinadi, so'ng…, Handler javobini (tuple yoki dict) yagona formatga keltiradi., Gemini toollarini bajaruvchi markaziy ro'yxat. (+8 more)

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
Cohesion: 0.08
Nodes (21): compute_rms(), echo_gate(), gate_open(), Yordamchi gapirayotganda mikrofon chunk'i o'tkazilsinmi? True = o'tkaz. Guard…, Callback thread'da: darajani hisoblaydi, gate'ni yangilaydi, navbatga qo'yadi.…, Yordamchi buyruq ustida ishlayaptimi (o'ylayapti / tool bajaryapti /…, Yordamchi javobi paytida mikrofon to'liq bostirilsinmi?, int16 mono PCM baytlaridan (rms 0..1, db -60..0) qaytaradi. (+13 more)

### Community 24 - "WakeState"
Cohesion: 0.07
Nodes (16): Yordamchi hozir unga gapirilayotganini kuzatadi., Oxirgi chaqiruvdan keyingi oyna (follow-up yoki suhbat) hali ochiqmi?, Oyna `at` (monotonic; odatda gap BOSHLANGAN payt) da ochiq edimi? None — hozir.…, Yordamchi javobi savol bilan tugadimi — keyingi oyna uzunroq bo'ladi., `follow_up` — aniq tugatilganda oddiy follow-up oynasi qoladi (xayrlashuv…, Suhbat rejimi yoqilgan, lekin `conversation_idle_s` jimlikdan keyin tugashi…, Matnda ism bormi? Bo'lsa follow-up oynasi ochiladi., Oynani yangilash — yordamchi hozirgina foydalanuvchi uchun nimadir qildi. (+8 more)

### Community 25 - "_registry"
Cohesion: 0.14
Nodes (14): EventBus, MonkeyPatch, Handler `needs_confirmation` qaytarsa registry gate'ni so'raydi va…, _registry(), test_registry_confirmation_via_bus_utterance_command(), test_registry_confirmations_command_toggles(), test_registry_dictation_tools(), test_registry_handler_needs_confirmation_dict() (+6 more)

### Community 26 - "DesktopPrefs"
Cohesion: 0.17
Nodes (4): DesktopPrefs, _pair(), Path, ~/.nexus/desktop.json — orb pozitsiyasi, oyna o'lchami, orb ko'rinishi.

### Community 27 - "ws_reconnect_harness.js"
Cohesion: 0.12
Nodes (9): ref_fs, byId(), els, FakeWS, fs, listeners, makeEl(), sockets (+1 more)

### Community 28 - "create_app"
Cohesion: 0.14
Nodes (8): create_app(), Path, Settings, FastAPI ilovasini yaratadi (testlarda ham shu ishlatiladi)., test_confirm_request_push_and_confirm_cmd(), test_index_disabled_when_serve_ui_false(), test_multiple_clients_and_unsubscribe(), test_ws_receives_published_events()

### Community 29 - "web_answer.py"
Cohesion: 0.30
Nodes (13): inspect, build_request(), _create(), extract_sources(), extract_text(), _get(), _make_client(), Any (+5 more)

### Community 30 - "ConfirmationGate"
Cohesion: 0.16
Nodes (9): ConfirmationGate, _consume(), PendingConfirmation, Bir vaqtda faqat bitta faol tasdiq so'rovi. Yangi so'rov eskisini bekor qiladi., Foydalanuvchining yakuniy transkripti. So'rovdan OLDIN aytilgan gap hisobga…, Bus'dagi TRANSCRIPT (user, final) hodisalarini ham kuzatadi — gemini client…, test_gate_ignores_long_sentence_with_ha(), test_gate_ignores_utterance_before_request() (+1 more)

### Community 31 - "name_in"
Cohesion: 0.14
Nodes (18): _candidates(), levenshtein(), name_in(), Levenshtein masofasi; `limit` berilsa undan oshgach hisoblashni to'xtatadi…, Qisqa ism aniq mos kelishi kerak; uzunroq ism 2-3 xatoni ko'taradi., (nomzod, boshlanish indeksi, so'zlar soni) — yakka so'zlar va qo'shni…, Matnda ism (yumshoq moslik bilan) bormi?, Matndan ismni (va oldidagi "hey/salom/ey" kabi undovni) olib tashlaydi. Asl… (+10 more)

### Community 32 - "AudioStreamer"
Cohesion: 0.06
Nodes (24): AudioStreamer, _list_devices(), _mute(), _playback(), _ptt(), _ptt_press(), _sensitivity(), _set_device() (+16 more)

### Community 33 - "video_translate.py"
Cohesion: 0.15
Nodes (14): js_to_applescript(), normalize_browser(), Brauzer boshqaruvi (Safari / Google Chrome) — AppleScript + sahifa ichidagi…, JS matnini AppleScript qo'shtirnoqli literal ichiga qo'yish uchun escaping…, compute_backoff(), base * 2**attempt + jitter, max_delay bilan cheklangan. `jitter` None bo'lsa…, AppleScript'ni `osascript` orqali bajaradi (stdin orqali, argument uzunligi…, run_applescript() (+6 more)

### Community 34 - "CommandGuard"
Cohesion: 0.19
Nodes (10): CommandGuard, `run_terminal_command` uchun uch pog'onali qo'riqchi. `check()` → ("allow" |…, Tekshiruvdan o'tgan buyruqni bajarish uchun argv (`~` kengaytirilgan holda)., parametrize, test_guard_allows(), test_guard_argv_expands_tilde(), test_guard_confirms(), test_guard_denies() (+2 more)

### Community 36 - "Settings"
Cohesion: 0.13
Nodes (8): google-genai Client — hamma joyda bir xil sozlama bilan., Settings, DaemonRunner, `nexus.main.run()` ni alohida thread'da o'z event loop'i bilan yuritadi., To'xtatish signalini beradi (bloklamaydi) — tugashini `finished` orqali…, To'xtatish signalini beradi va thread tugashini kutadi. True = toza tugadi., GUI'dan daemon'ga buyruq (thread-safe, natija kutilmaydi)., test_config_defaults_gemini38()

### Community 37 - "FakeLiveConnect"
Cohesion: 0.13
Nodes (6): FakeLiveConnect, 1011 'exceeded your current quota' → avval google_search grounding olib…, client.aio.live.connect o'rnini bosuvchi: har chaqiruvda navbatdagi FakeSession., connect(), test_quota_error_drops_google_search_first(), connect()

### Community 38 - "config.py"
Cohesion: 0.10
Nodes (27): dotenv, api_key_env_path(), api_key_hint(), _describe_char(), _env_api_key(), env_candidates(), is_placeholder_api_key(), load_env_files() (+19 more)

### Community 39 - "main.py"
Cohesion: 0.09
Nodes (27): Event, check_environment(), cli(), _first(), MetricsTicker, platform_controller(), print_banner(), Any (+19 more)

### Community 40 - "vision_box_to_screen"
Cohesion: 0.50
Nodes (4): Vision normalizatsiyalangan bbox (0..1, y PASTDAN) → ekran (x, y, w, h),…, vision_box_to_screen(), test_vision_box_bottom_line_lands_at_window_bottom(), test_vision_box_to_screen_flips_y_and_offsets_by_window()

### Community 41 - "make_settings"
Cohesion: 0.07
Nodes (27): FakeAudio, FakeRegistry, make_settings(), Registry yo'q (toolsiz rejim) — klient zaxira `kill_all` handlerini ro'yxatdan…, sine_pcm(), test_background_voice_does_not_cut_addressed_reply(), test_build_config_ptt_disables_vad_and_optional_fields(), test_bus_commands() (+19 more)

### Community 42 - "._evaluate_addressed"
Cohesion: 0.18
Nodes (5): Oxirgi real audio chunk karnayga chiqqan payt (time.monotonic; 0 — hali yo'q)., Registry gate'ida (ConfirmationGate) hal qilinmagan tasdiq so'rovi bormi?, Wake rejimi bo'yicha gap bizga qaratilganmi (qisman transkriptda ham). Baho…, Yo'q / hech narsa kerak emas" rad javobi sifatida qaralsinmi? Suhbat rejimida…, Joriy gap boshlangan payt (AudioStreamer RMS gate). Noma'lum yoki eskirgan…

### Community 43 - "describe_screen"
Cohesion: 0.36
Nodes (10): describe_screen(), _extract_text(), _image_part(), look_at_screen(), _make_client(), Any, Oldingi oynani skrinshot qilib Gemini'ga ko'rsatadi. {ok, output, app, ...}., read_screen_ocr() (+2 more)

### Community 44 - "test_desktop.py"
Cohesion: 0.09
Nodes (27): ArgumentParser, Namespace, `base_url/health` 2xx qaytarguncha kutadi. `keep_waiting()` False qaytarsa…, wait_for_server(), build_parser(), desktop_mode(), Desktop (oyna + orb + menyu bar) rejimi kerakmi? `--headless`, `--no-ui`…, MonkeyPatch (+19 more)

### Community 45 - "macos_actions.py"
Cohesion: 0.10
Nodes (35): collections, collections_abc, ctypes, datetime, importlib, json, logging, math (+27 more)

### Community 46 - "test_safety.py"
Cohesion: 0.18
Nodes (14): Queue, _bus(), _drain(), Xavfsizlik qatlami testlari: DANGEROUS_SHELL, looks_read_only,…, Gemini client note_utterance'ni chaqirmasa ham, bus'dagi TRANSCRIPT (user,…, test_gate_listens_to_bus_transcripts(), test_gate_new_request_cancels_old(), test_gate_timeout() (+6 more)

### Community 47 - "Any"
Cohesion: 0.19
Nodes (9): _key_hint(), Any, EventBus, Path, `extended-thinking` modelida daraja majburiy (bo'sh bo'lsa "high"); boshqa…, UI (Sozlamalar) dan API kalit: tekshiradi, saqlaydi va sessiyani yangi kalit…, thinking_level_for(), _to_function_declarations() (+1 more)

### Community 48 - ".run"
Cohesion: 0.16
Nodes (9): GeminiConfigError, Konfiguratsiya xatosi (masalan, API kaliti yo'q)., Cheksiz ulanish sikli; `stop()` chaqirilguncha qayta ulanaveradi., Kalit Sozlamalardan (`set_api_key`) kiritilguncha yoki `stop()` gacha kutadi., `timeout` sekund (None — cheksiz) kutadi; `stop()` yoki yangi API kalit…, Sessiya juda qisqa yashagan bo'lsa (masalan, eskirgan handle) — handle…, should_drop_resume_handle(), RuntimeError (+1 more)

### Community 49 - "snapshot"
Cohesion: 0.46
Nodes (8): _cmd_result(), api_state(), snapshot(), ws_endpoint(), handle_command(), receiver(), send(), sender()

### Community 50 - "BargeInGate"
Cohesion: 0.11
Nodes (13): AbstractEventLoop, BargeInGate, parse_latency(), EventBus, high"/"low" yoki sekund (str/float) → sounddevice `latency` argumenti., Ijro paytida mikrofon chunklarining echo/barge-in darvozasi (callback…, → (navbatga qo'yiladigan chunklar, sukunatga almashtirilganlar soni)., Nom (qism mos kelsa ham) yoki indeks → qurilma indeksi. None = standart. (+5 more)

### Community 51 - "Segmenter"
Cohesion: 0.38
Nodes (4): Uzluksiz nutqni tarjima bo'laklariga ajratadi: `push(rms)` True → bo'lakni shu…, Segmenter, test_segmenter_cuts_at_max(), test_segmenter_cuts_on_quiet_after_min()

### Community 52 - "server.py"
Cohesion: 0.12
Nodes (12): contextlib, errno, FastAPI, fastapi_responses, fastapi_staticfiles, _QuietServer, UI ko'prigi: FastAPI + WebSocket server. EventBus hodisalarini brauzerdagi UI…, Signal handlerlarini o'rnatmaydigan uvicorn Server (signalni main.py… (+4 more)

### Community 53 - "test_video_translate.py"
Cohesion: 0.10
Nodes (17): fit_tempo(), AppleScript: JS ni video tabida bajaradi — Chrome'da `tab_id` bo'yicha (bir xil…, Tarjima (`out_s`) videodagi qolgan oralig'iga (`window_s`) sig'ishi uchun…, translator_instruction(), video_tab_script(), _FakePlayer, video_translate: toza funksiyalar, sinxron soat, tool ro'yxatga olinishi, echo…, test_build_config_native_and_prompt() (+9 more)

### Community 54 - "dictation.py"
Cohesion: 0.14
Nodes (8): dataclasses, DictationState, Diktovka rejimi: foydalanuvchi gapiradi — yordamchi teradi, to'xtash…, (teriladigan matn, to'xtash kerakmi). "…hammasi shu, to'xta" → ("…hammasi shu",…, Diktovka holati va terilgan matn hisobi., split_stop(), test_dictation_state_lifecycle(), test_split_stop()

### Community 55 - "asyncio"
Cohesion: 0.12
Nodes (19): argparse, asyncio, all_declarations(), build_config(), main(), passed(), Model qaysi toolni tanlashini real Gemini Live sessiyasida o'lchash (toollar…, Asosiy sxemalar + kengaytma modullari (nomlar bo'yicha takrorsiz). (+11 more)

### Community 56 - "fake_screen"
Cohesion: 0.40
Nodes (5): ax_ready(), fake_screen(), fixture, MonkeyPatch, Skrinshot/JPEG bosqichini almashtiradi: real screencapture chaqirilmaydi.

### Community 57 - "Segment"
Cohesion: 0.13
Nodes (15): is_silent(), Javob bermagan bo'lakni navbat boshiga qaytaradi — boshqa (bo'sh) sessiya oladi., Bo'lak deyarli jim (o'rtacha RMS `SILENT_RMS` dan past)., Tarjima bo'lagi: kiruvchi audio (tayinlanguncha `buf`da) va modelning javobi…, Bitta Live sessiya: navbatdagi bo'lakni oladi, javobini bo'lakka yozadi., activity_end dan keyin `no_response_s` ichida audio kelmadi — ijroda o'tkazib…, Tayinlanmagan bo'laklarni (FIFO) bo'sh sessiyalarga beradi., Sessiya bo'shadi — navbatdagi bo'lakni olishi mumkin. (+7 more)

### Community 58 - "reference/AI analysis (old Voice Assistant)"
Cohesion: 0.22
Nodes (10): Echo guard + playback prebuffer + low VAD start sensitivity, Nexus Ovoz OS (Uzbek voice assistant daemon), session.receive() ends each turn (not a disconnect), reference/AI analysis (old Voice Assistant), Gemini Live API findings (VAD, transcription langs, affective_dialog 1007/1011), Nexus plan P0/P1/P2, Old Voice Assistant (Gemini Live, ~7100 lines, PyQt orb), Product requirements (hands-free, Uzbek, barge-in, full control) (+2 more)

### Community 59 - "_recognize"
Cohesion: 0.33
Nodes (6): pick_languages(), Qo'llab-quvvatlanadigan tillardan kerakli tartibda tanlaydi ("uz" → "uz-UZ"…, Vision OCR: [(text, nx, ny, nw, nh, confidence)] — normalizatsiyalangan, y…, _recognize(), supported_languages(), test_pick_languages_prefers_uz_then_ru_en_and_skips_missing()

### Community 60 - "._feed"
Cohesion: 0.17
Nodes (8): build_ffmpeg_cmd(), feed_action(), Process, Navbatdagi chunk bilan nima qilish: "resync" | "wait" | "send". Audio videodan…, Seek: navbatdagi kiruvchi audio va hali ijro etilmagan tarjimalar tashlanadi., ffmpeg PCM → navbat (video vaqti bilan), videodan `LOOKAHEAD_S` oldinda; seek →…, test_build_ffmpeg_cmd(), test_feed_action()

### Community 61 - "._handle_server_content"
Cohesion: 0.20
Nodes (6): _asks_question(), _grounding_sources(), ToolRegistry.kill_all() ilgagi: klient tool tasklari bekor, ijro navbati…, Zaxira: registry bo'lmaganda (toolsiz rejim) `kill_all` buyrug'i., Yordamchi javobi foydalanuvchidan javob kutadimi ("Yana nima qilay?", "Labbay,…, `grounding_metadata.grounding_chunks[*].web.{uri,title}` → "title — uri"…

### Community 63 - "schemas.py"
Cohesion: 0.39
Nodes (7): _b(), _decl(), _i(), _n(), Any, Gemini Live API uchun FunctionDeclaration lug'atlari va tizim ko'rsatmasi.…, _s()

### Community 64 - "NexusOrbPanel"
Cohesion: 0.33
Nodes (3): NexusOrbPanel, Ramkasiz, shaffof, doim tepada, klaviatura fokusini OLMAYDIGAN panel.…, NSPanel

### Community 66 - "error_text"
Cohesion: 0.50
Nodes (4): error_text(), BaseException, Gemini xatosini foydalanuvchiga o'zbekcha qisqa jumla qilib beradi., test_error_text_is_uzbek()

### Community 67 - "Any"
Cohesion: 0.13
Nodes (12): attach(), is_quota_error(), Any, BaseException, main.py: bus/settings/mikrofonni ulaydi; echo guard tarjima ijrosini ham…, Kalit kvotasi (bir vaqtdagi sessiyalar soni yoki kunlik limit) tugadi., Parallel sessiyalar + dispetcher + tartibli ijro., Sessiya uzildi: joriy bo'lak yakunlangan deb belgilanadi, o'zi bo'sh ro'yxatdan… (+4 more)

### Community 68 - "ocr_image"
Cohesion: 0.21
Nodes (14): Box, available(), lines_as_elements(), lines_to_text(), ocr_image(), Satrlarni yuqoridan pastga, bir qatordagilarni chapdan o'ngga tartiblaydi. Ikki…, Tartiblangan satrlardan matn: bir qatordagilar ikki bo'shliq bilan, qatorlar…, OCR satrlarini list_ui_elements formatiga o'giradi: {n, role:'text', label, at,… (+6 more)

### Community 69 - "is_config_rejection"
Cohesion: 0.29
Nodes (7): BaseException, is_api_key_error(), is_config_rejection(), Server kalitni rad etdimi (noto'g'ri / bekor qilingan API kalit)?, Server konfiguratsiyani rad etgan bo'lsa navbatdagi modelga bog'liq maydonni…, Server konfiguratsiyani rad etdimi (WebSocket 1007 / invalid argument), kalit…, test_is_config_rejection()

### Community 70 - "VideoTranslator"
Cohesion: 0.21
Nodes (5): Bo'laklarni `seq` tartibida, video o'z oralig'iga (`src_start`) yetganda ijroga…, Video pauza, tarjima ovozi esa davom etadi — `seconds` dan keyin video qayta…, Tarjima ulgurmayapti (masalan, kvota kam — sessiyalar yetmaydi): gapni tashlab…, turn_complete kelmay qolgan sessiyani bo'shatadi (model jim qoldi)., VideoTranslator

### Community 71 - "test_registry_no_confirmation_runs_immediately"
Cohesion: 0.29
Nodes (3): test_registry_no_confirmation_runs_immediately(), test_registry_tainted_turn_requires_confirmation(), read_page()

### Community 72 - "LoopGuard"
Cohesion: 0.20
Nodes (7): LoopGuard, Any, Bir navbatda haddan ko'p yoki bir xil chaqiruvlarni to'xtatadi., None — davom et; matn — rad etish sababi (modelga tushuntirish)., test_loop_guard_identical_calls(), test_loop_guard_max_calls_per_turn(), test_loop_guard_non_consecutive_identical_calls()

### Community 73 - "._build_window"
Cohesion: 0.18
Nodes (13): default_orb_origin(), default_window_frame(), _hex_color(), _make_webview(), Oyna/orb hech bo'lmaganda `min_visible`×`min_visible` qismi bilan biror ekranda…, Ekranning pastki-o'ng burchagi (Dock/menyu bar hisobga olingan `visibleFrame`…, Ekran o'rtasida, `visibleFrame`ning `fraction` (90%) qismi (yoki `size`), min…, rect_on_screens() (+5 more)

### Community 76 - "wake.py"
Cohesion: 0.27
Nodes (9): itertools, ends_conversation(), _has_phrase(), Ism bilan chaqirish (wake): gap yordamchiga qaratilganmi? Xonada boshqa odamlar…, kel gaplashamiz", "suhbatlashaylik", "давай поговорим", "let's talk" …, bo'ldi, rahmat", "suhbatni tugat", "xayr" …, wants_conversation(), test_conversation_phrases() (+1 more)

### Community 81 - "._finalize_user_turn"
Cohesion: 0.22
Nodes (3): UI dan matn buyrug'i. Sessiya yo'q bo'lsa False., Registry'ga foydalanuvchi navbatini bildiradi: og'zaki tasdiq (note_utterance)…, Suhbat rejimi: ismsiz erkin suhbat; jimlikdan keyin o'zi tugaydi (`tick`).

### Community 84 - "._run"
Cohesion: 0.12
Nodes (13): find_tab_script(), parse_player_state(), player_setup_js(), `pos` dan `ahead` soniya oldinga tarjima tayyormi: ijroga qo'yilgan, yoki…, Buferlash: video pauzada turadi, oldinda `GATE_AHEAD_S` tarjima tayyor bo'lgach…, AppleScript (Chrome): `video_id` ochiq tabni topib oldinga chiqaradi va id sini…, Pleyer: asl ovozni o'chirish/pasaytirish (0..1, manfiy — tegilmaydi) va ijro…, JS ni video ochilgan tabda bajaradi (faol tab emas — foydalanuvchi boshqa tabga… (+5 more)

### Community 85 - "PlaybackClock"
Cohesion: 0.14
Nodes (8): find_binary(), PlaybackClock, PATH + Homebrew papkalari (.app ichidan ishga tushganda PATH qisqa bo'ladi)., Brauzer pleyeri holatidan joriy video vaqtini baholaydi (so'rovlar orasida…, s16le mono PCM ni ohangini saqlab `tempo` barobar tezlashtiradi (ffmpeg…, time_stretch(), test_clock_interpolates_and_halts(), test_time_stretch_shortens_audio()

### Community 86 - "_ConfirmTracker"
Cohesion: 0.24
Nodes (5): _ConfirmTracker, Any, EventBus, CONFIRM_REQUEST / CONFIRM_RESOLVED hodisalarini kuzatib, ochiq tasdiqni eslab…, _snapshot()

### Community 88 - "AudioPlayer"
Cohesion: 0.12
Nodes (10): AudioPlayer, 24 kHz int16 mono ijro. `enqueue` istalgan thread/task'dan chaqirilishi mumkin.…, Buferdagi qolgan audioni (prebuffer to'lmagan bo'lsa ham) ijroga qo'yib…, Navbatni tozalaydi (interruption). Tashlangan chunklar sonini qaytaradi., test_player_arms_stalled_short_reply(), test_player_callback_and_clear(), test_player_is_playing_tail(), test_player_prebuffer_and_play_out() (+2 more)

### Community 89 - "Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline"
Cohesion: 0.25
Nodes (8): Nexus Ovoz OS design mockup (dc.html), Design mockup Component (simulated PTT command flow), Local models concept (Whisper.cpp small.uz + Qwen 7B Q4), Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline, Gemini Live API (native audio, WebSocket), Nexus browser/desktop panel (index.html), Confirmation card (TASDIQ KUTILMOQDA, Yes/No, TTL), Live transcript box

### Community 90 - "TaintTracker"
Cohesion: 0.25
Nodes (3): Navbat ichida tashqi matn o'qilganini eslab qoladi., TaintTracker, test_taint_tracker()

### Community 91 - "test_wake_dictation.py"
Cohesion: 0.15
Nodes (16): is_stop_phrase(), Butun gap faqat to'xtash iborasidan iboratmi?, looks_like_command(), normalise(), Kichik harf, urg'u/apostrofsiz, tinish belgisiz; kirill → lotin., SMART rejimi uchun evristika: qisqa gap + buyruq so'zi., clock(), fixture (+8 more)

### Community 92 - "is_junk_translation"
Cohesion: 0.33
Nodes (6): is_junk_translation(), Model tarjima o'rniga yorliq/izoh aytdi (`(Uzbek translation: …)`, `<no…, youtube_id(), parametrize, test_is_junk_translation(), test_youtube_id()

### Community 93 - "_starts_a_word"
Cohesion: 0.30
Nodes (5): hits(), `needle` nomning boshida yoki ichidagi so'z boshida keladi ("word" ≠…, _starts_a_word(), _cmd(), Faqat buyruq pozitsiyasidagi nomga mos keladigan regex.

### Community 94 - "Orb overlay page (orb.html)"
Cohesion: 0.27
Nodes (10): Desktop layer (pure pyobjc NSWindow + WKWebView, orb NSPanel, menu bar), Orb overlay (floating non-activating NSPanel), UI -> daemon commands (mute, ptt, confirm, kill_all, text, wake_mode, dictation...), UI event contract ({type, ts, data} over /ws), Orb overlay page (orb.html), connect() WebSocket with exponential retry, draw() canvas orb renderer, effective() state resolver (+2 more)

### Community 95 - "bus"
Cohesion: 0.40
Nodes (3): check(), main(), bus()

### Community 97 - "Security model (confirmation from user transcript/UI only)"
Cohesion: 0.25
Nodes (9): CommandGuard allow/deny/confirm tiers, Loop guard (max 15 calls/turn, 3 identical), Secret redaction (redact_secrets), Security model (confirmation from user transcript/UI only), Sensitive path denial (path_is_sensitive), Taint guard (external content -> exfil/execute tools require confirmation), ToolRegistry.execute flow: validate -> loop guard -> taint -> confirm -> handler, Old code bugs (do not repeat) (+1 more)

### Community 99 - ".tick"
Cohesion: 0.33
Nodes (3): Hozir ovoz chiqyaptimi (navbatda audio bor yoki oxirgi chunk yaqinda chiqqan)., Davriy tekshiruv (MetricsTicker): jimlik tufayli suhbat rejimini tugatish;…, Band holat (processing / tool_executing / speaking) tool ham, ijro ham, server…

### Community 100 - "build_ytdlp_cmd"
Cohesion: 0.29
Nodes (5): build_ytdlp_cmd(), Faqat audio yuklanadi; stdout: 1-qator sarlavha, oxirgi qator fayl yo'li., yt-dlp: audio faylni vaqtinchalik papkaga yuklaydi. (ok, sarlavha | xato).…, watch_url(), test_build_ytdlp_cmd()

### Community 108 - "spoken_verdict"
Cohesion: 0.67
Nodes (3): True = rozi, False = rad, None = javob emas. Rad etish (veto) gap uzunligidan…, spoken_verdict(), test_spoken_verdict()

## Ambiguous Edges - Review These
- `Gemini Live API (native audio, WebSocket)` → `Local models concept (Whisper.cpp small.uz + Qwen 7B Q4)`  [AMBIGUOUS]
  design/Nexus Ovoz OS.dc.html · relation: conceptually_related_to

## Knowledge Gaps
- **15 isolated node(s):** `Session resumption + context compression`, `Live transcript box`, `EXTENSION_MODULES (TOOL_DECLARATIONS + HANDLERS)`, `macOS permissions (Microphone, Accessibility, Screen Recording, Automation)`, `Scripts: check_setup, benchmark_live, voice_picker` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 618 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Gemini Live API (native audio, WebSocket)` and `Local models concept (Whisper.cpp small.uz + Qwen 7B Q4)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `ToolRegistry` connect `ToolRegistry` to `Result`, `test_tools.py`, `._build_handlers`, `MacOSController`, `WindowsController`, `path_is_sensitive`, `_registry`, `ConfirmationGate`, `video_translate.py`, `main.py`, `make_settings`, `macos_actions.py`, `test_safety.py`, `test_registry_no_confirmation_runs_immediately`, `LoopGuard`, `test_registry_loads_extension_modules`, `Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline`, `TaintTracker`, `bus`, `Security model (confirmation from user transcript/UI only)`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Why does `GeminiLiveClient` connect `GeminiLiveClient` to `AudioStreamer`, `.tick`, `is_config_rejection`, `._evaluate_addressed`, `macos_actions.py`, `Any`, `.run`, `._finalize_user_turn`, `BargeInGate`, `._handle_message`, `WakeState`, `Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline`, `reference/AI analysis (old Voice Assistant)`, `._handle_server_content`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline` connect `Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline` to `AudioStreamer`, `GeminiLiveClient`, `EventBus`, `Nexus Ovoz OS README`, `ToolRegistry`, `AudioPlayer`, `ConfirmationGate`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `MacOSController` (e.g. with `platform_controller()` and `ToolRegistry`) actually correct?**
  _`MacOSController` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `ToolRegistry` (e.g. with `run()` and `MacOSController`) actually correct?**
  _`ToolRegistry` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `GeminiLiveClient` (e.g. with `WakeState` and `session.receive() ends each turn (not a disconnect)`) actually correct?**
  _`GeminiLiveClient` has 2 INFERRED edges - model-reasoned connections that need verification._