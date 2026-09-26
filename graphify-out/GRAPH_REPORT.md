# Graph Report - nexus  (2026-09-26)

## Corpus Check
- 42 files · ~91,188 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 4, .command 2, .example 1)

## Summary
- 1802 nodes · 4045 edges · 89 communities (73 shown, 16 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 265 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c5efeeb9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- support.js
- file_actions.py
- ax_actions.py
- BrowserController
- GeminiLiveClient
- test_core.py
- app.js
- test_tools.py
- EventBus
- Nexus Ovoz OS README
- ._build_handlers
- NexusDesktopApp
- MacOSController
- video_translate.py
- FakeRegistry
- test_desktop.py
- main.py
- screen_reader.py
- test_screen_reader.py
- ToolRegistry
- test_safety.py
- Settings
- check_setup.py
- AudioPlayer
- WakeState
- _registry
- DesktopPrefs
- ws_reconnect_harness.js
- test_server.py
- web_answer.py
- ConfirmationGate
- name_in
- .register_commands
- config.py
- CommandGuard
- BrowserDOMController
- DaemonRunner
- .connect
- Result
- run
- TaintTracker
- SearchNavigationController
- vision_box_to_screen
- UIServer
- desktop.py
- match_app
- _bus
- audio_streamer.py
- macos_actions.py
- snapshot
- BargeInGate
- Segmenter
- server.py
- test_video_translate.py
- DictationState
- benchmark_live.py
- fake_screen
- Segment
- test_wake_dictation.py
- _recognize
- _ConfirmTracker
- FakeStream
- pathlib
- schemas.py
- is_config_rejection
- split_stop
- error_text
- Any
- ocr_image
- ._playout
- VideoTranslator
- SearchInputController
- LoopGuard
- describe_screen
- test_registry_loads_extension_modules
- nexus/__init__.py
- gemini_live_client.py
- build_app.sh
- .build_hotkey_script
- nexus-voice
- Gemini Live API findings (VAD, transcription langs, affective_dialog 1007/1011)
- .heard
- build_ytdlp_cmd
- PlaybackClock
- CLAUDE.md
- .get_system_info
- .is_terminal_frontmost
- test_registry_type_text_into_terminal_requires_confirmation

## God Nodes (most connected - your core abstractions)
1. `EventBus` - 78 edges
2. `MacOSController` - 65 edges
3. `GeminiLiveClient` - 60 edges
4. `ToolRegistry` - 58 edges
5. `VideoTranslator` - 55 edges
6. `AudioStreamer` - 47 edges
7. `NexusDesktopApp` - 46 edges
8. `Settings` - 34 edges
9. `make_client()` - 32 edges
10. `ConfirmationGate` - 29 edges

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

## Communities (89 total, 16 thin omitted)

### Community 0 - "support.js"
Cohesion: 0.06
Nodes (75): boot(), bundledBlob(), cdnScriptFor(), collectProps(), compileAttr(), compileTemplate(), contentKey(), createComponentFactory() (+67 more)

### Community 1 - "file_actions.py"
Cohesion: 0.05
Nodes (65): csv, nexus, _append_csv(), _append_row_sync(), append_spreadsheet_row(), _append_xlsx(), _coerce_cell_value(), delete_file() (+57 more)

### Community 2 - "ax_actions.py"
Cohesion: 0.07
Nodes (72): applicationservices, difflib, _actions(), activate_element(), _app_root(), _attr(), available(), _clean_text() (+64 more)

### Community 3 - "BrowserController"
Cohesion: 0.17
Nodes (9): app_name(), BrowserController, normalize_url(), Joriy tabda URL ni almashtiradi (yangi tab ochmasdan)., Tab ochish/yopish, URL olish, tab almashtirish, reload, ro'yxat., _as_str(), Python qiymatini AppleScript satr literaliga (qo'shtirnoq ichida) xavfsiz…, Runner (+1 more)

### Community 4 - "GeminiLiveClient"
Cohesion: 0.07
Nodes (18): GeminiLiveClient, _grounding_sources(), Any, `grounding_metadata.grounding_chunks[*].web.{uri,title}` → "title — uri"…, Cheksiz ulanish sikli; `stop()` chaqirilguncha qayta ulanaveradi., UI dan matn buyrug'i. Sessiya yo'q bo'lsa False., `receive()` har navbatda tugaydi — qayta chaqiramiz; bo'sh iteratsiya = uzilish., Registry gate'ida (ConfirmationGate) hal qilinmagan tasdiq so'rovi bormi? (+10 more)

### Community 5 - "test_core.py"
Cohesion: 0.07
Nodes (48): `extended-thinking` modelida daraja majburiy (bo'sh bo'lsa "high"); boshqa…, Sessiya juda qisqa yashagan bo'lsa (masalan, eskirgan handle) — handle…, should_drop_resume_handle(), thinking_level_for(), SimpleNamespace, _audio_part(), fake_sd(), FakeLiveConnect (+40 more)

### Community 6 - "app.js"
Cohesion: 0.12
Nodes (54): answerConfirm(), applyDevices(), applySettings(), applySnapshot(), bind(), closeSocket(), connect(), ensureRow() (+46 more)

### Community 7 - "test_tools.py"
Cohesion: 0.08
Nodes (30): _no_sleep(), MonkeyPatch, Tool qatlami testlari — real macOS tizimiga tegmaydi (osascript/subprocess…, Barcha ichki JS'lar AppleScript literaliga qo'yilganda qo'shtirnoq muvozanati…, ScriptRecorder, test_browser_open_url_normalizes(), test_is_terminal_frontmost(), test_js_permission_hint() (+22 more)

### Community 8 - "EventBus"
Cohesion: 0.05
Nodes (37): CommandHandler, AudioStreamer, AbstractEventLoop, Mikrofon → asyncio.Queue → Gemini. AUDIO_LEVEL va gate holatini nashr qiladi., Navbatga boshqaruv markeri (MARK_ACTIVITY_START/END) qo'yadi — audio bilan…, Yuboriladigan PCM chunklar yoki `str` markerlar (cheksiz; `stop()` da tugaydi)., Navbatdagi eski chunklarni tashlaydi (qayta ulanishda)., Sessiya yo'q — chunklar navbatga qo'yilmaydi (ulanishdan oldin / uzilganda). (+29 more)

### Community 9 - "Nexus Ovoz OS README"
Cohesion: 0.06
Nodes (44): Nexus Ovoz OS design mockup (dc.html), Design mockup Component (simulated PTT command flow), Local models concept (Whisper.cpp small.uz + Qwen 7B Q4), Nexus Ovoz OS README, AXManualAccessibility for Chrome/Electron, CommandGuard allow/deny/confirm tiers, Desktop layer (pure pyobjc NSWindow + WKWebView, orb NSPanel, menu bar), Dictation mode (direct typing, stop phrases) (+36 more)

### Community 10 - "._build_handlers"
Cohesion: 0.05
Nodes (22): browser_click_button(), browser_click_selector(), browser_close_tab(), browser_current_page(), browser_list_tabs(), browser_open_url(), browser_read_page(), browser_reload() (+14 more)

### Community 11 - "NexusDesktopApp"
Cohesion: 0.09
Nodes (8): _load_url(), NexusDesktopApp, Any, NSApplication delegati: oyna, orb, menyu bar, daemon ko'prigi., SIGINT/SIGTERM → toza chiqish. Mach-port orqali AppKit run loop'ida qayta…, Daemon thread'idan chaqiriladi — hodisani GUI thread'iga uzatadi., `.env` ni Finder'da ko'rsatadi (yagona "tashqi ochish" — brauzer emas)., NSObject

### Community 12 - "MacOSController"
Cohesion: 0.14
Nodes (7): _clamp(), MacOSController, Result, SSID ni aniqlaydi. macOS 14+ da Location Services ruxsatisiz SSID `<redacted>`…, macOS bilan ishlash: ovoz, media, ilovalar, Finder, tizim, terminal., macOS 12+ da DND uchun ochiq API yo'q. Foydalanuvchi yaratgan Shortcuts…, Faol oynaga matn kiritadi: bufer + Cmd+V (keystroke o'zbek/kirill matnni…

### Community 13 - "video_translate.py"
Cohesion: 0.25
Nodes (7): normalize_browser(), compute_backoff(), base * 2**attempt + jitter, max_delay bilan cheklangan. `jitter` None bo'lsa…, YouTube videosini jonli (sinxron) ovozli tarjima: ingliz → o'zbek. Oqim: yt-dlp…, translate_video(), os, test_compute_backoff()

### Community 15 - "test_desktop.py"
Cohesion: 0.08
Nodes (30): _env_api_key(), is_placeholder_api_key(), Kalit; namunaviy (placeholder) qiymat bo'lsa bo'sh qaytaradi., default_window_frame(), effective_state(), placeholder_html(), (rang, yorliq) — menyu bar / orb uchun., Menyu bar'dagi holat satri, masalan "● Tinglamoqda" yoki "● Kutmoqda (mikrofon… (+22 more)

### Community 16 - "main.py"
Cohesion: 0.16
Nodes (19): ArgumentParser, Namespace, list_input_devices(), [{"index", "name", "default"}] — faqat kirish (mikrofon) qurilmalari., DesktopOptions, Desktop ilovani ishga tushiradi (asosiy thread'da bloklaydi). Qaytadi: chiqish…, argparse Namespace (nexus.main.build_parser) → DesktopOptions., run_desktop() (+11 more)

### Community 17 - "screen_reader.py"
Cohesion: 0.14
Nodes (20): appkit, foundation, capture_frontmost_window(), _shoot(), _front_app(), _front_window_info(), _image_size(), _largest_window() (+12 more)

### Community 18 - "test_screen_reader.py"
Cohesion: 0.11
Nodes (13): Exception, shutil, _fake_client(), _FakeModels, screen_reader (OCR + Gemini ko'rish) va ax_actions'dagi AX→OCR zaxira yo'li…, test_click_ui_element_by_ocr_index_from_cache(), test_describe_screen_default_question(), test_describe_screen_error_and_timeout() (+5 more)

### Community 19 - "ToolRegistry"
Cohesion: 0.08
Nodes (16): Handler, Any, Foydalanuvchi yangi gap boshladi: loop guard va taint tozalanadi., Foydalanuvchining yakuniy transkripti — og'zaki tasdiq uchun., Bajarilayotgan tool tasklarini bekor qiladi. Kutilayotgan tasdiq so'roviga…, ⌥⎋ / "kill_all": tool tasklar + kutilayotgan tasdiq bekor qilinadi, so'ng…, Handler javobini (tuple yoki dict) yagona formatga keltiradi., Bajarishdan OLDIN aniqlanadigan tasdiq sabablari (bo'sh — tasdiqsiz). (+8 more)

### Community 20 - "test_safety.py"
Cohesion: 0.10
Nodes (26): looks_read_only(), path_is_sensitive(), Path, True — buyruq DANGEROUS_SHELL naqshlaridan biriga mos keladi., True — buyruq HECH QANDAY bayroq bilan ham hech narsani o'zgartira olmaydi., True — bu yerga yozish persistensiya yaratishi yoki sir sizdirishi mumkin., Model yoki log ko'rishidan oldin kalitga o'xshagan narsalarni yashiradi., True = rozi, False = rad, None = javob emas. Rad etish (veto) gap uzunligidan… (+18 more)

### Community 21 - "Settings"
Cohesion: 0.11
Nodes (14): google-genai Client — hamma joyda bir xil sozlama bilan., Settings, create_app(), index(), Path, FastAPI ilovasini yaratadi (testlarda ham shu ishlatiladi)., test_config_defaults_gemini38(), Tasdiq kutayotgan run_tool shu soketdan keladigan "confirm" ni to'sib… (+6 more)

### Community 22 - "check_setup.py"
Cohesion: 0.30
Nodes (14): CDLL, check_accessibility(), check_automation(), check_devices(), check_key(), check_live(), check_mic_level(), check_packages() (+6 more)

### Community 23 - "AudioPlayer"
Cohesion: 0.12
Nodes (10): AudioPlayer, 24 kHz int16 mono ijro. `enqueue` istalgan thread/task'dan chaqirilishi mumkin.…, Buferdagi qolgan audioni (prebuffer to'lmagan bo'lsa ham) ijroga qo'yib…, Navbatni tozalaydi (interruption). Tashlangan chunklar sonini qaytaradi., Hozir ovoz chiqyaptimi (navbatda audio bor yoki oxirgi chunk yaqinda chiqqan)., test_player_callback_and_clear(), test_player_is_playing_tail(), test_player_prebuffer_and_play_out() (+2 more)

### Community 24 - "WakeState"
Cohesion: 0.10
Nodes (11): Yordamchi hozir unga gapirilayotganini kuzatadi., Oxirgi chaqiruvdan keyingi oyna (follow-up yoki suhbat) hali ochiqmi?, `follow_up` — aniq tugatilganda oddiy follow-up oynasi qoladi (xayrlashuv…, Suhbat rejimi yoqilgan, lekin `conversation_idle_s` jimlikdan keyin tugashi…, Oynani yangilash — yordamchi hozirgina foydalanuvchi uchun nimadir qildi., WakeState, test_wake_conversation_window_and_expiry(), test_wake_defaults_to_name_only() (+3 more)

### Community 25 - "_registry"
Cohesion: 0.11
Nodes (15): MonkeyPatch, Handler `needs_confirmation` qaytarsa registry gate'ni so'raydi va…, kill_all: gate.cancel_pending("cancelled") chaqiriladi VA klient ilgagi…, _registry(), test_registry_confirmation_via_bus_utterance_command(), test_registry_confirmation_voice_approves(), test_registry_dictation_tools(), test_registry_handler_needs_confirmation_dict() (+7 more)

### Community 26 - "DesktopPrefs"
Cohesion: 0.09
Nodes (16): load_extra_env(), Faqat qo'shimcha manbalar (`~/.nexus/.env`, .app bundle) — loyiha `.env` isiz.…, DesktopPrefs, _pair(), Path, ~/.nexus/desktop.json — orb pozitsiyasi, oyna o'lchami, orb ko'rinishi., MonkeyPatch, Path (+8 more)

### Community 27 - "ws_reconnect_harness.js"
Cohesion: 0.12
Nodes (9): ref_fs, byId(), els, FakeWS, fs, listeners, makeEl(), sockets (+1 more)

### Community 28 - "test_server.py"
Cohesion: 0.17
Nodes (13): fastapi_testclient, TestClient, bus(), client(), _free_port(), fixture, nexus.server (FastAPI + WS ko'prigi) testlari., test_api_state() (+5 more)

### Community 29 - "web_answer.py"
Cohesion: 0.20
Nodes (15): inspect, build_request(), _create(), extract_sources(), extract_text(), _get(), _make_client(), Any (+7 more)

### Community 30 - "ConfirmationGate"
Cohesion: 0.20
Nodes (6): ConfirmationGate, _consume(), PendingConfirmation, Bir vaqtda faqat bitta faol tasdiq so'rovi. Yangi so'rov eskisini bekor qiladi., Foydalanuvchining yakuniy transkripti. So'rovdan OLDIN aytilgan gap hisobga…, Bus'dagi TRANSCRIPT (user, final) hodisalarini ham kuzatadi — gemini client…

### Community 31 - "name_in"
Cohesion: 0.14
Nodes (18): _candidates(), levenshtein(), name_in(), Levenshtein masofasi; `limit` berilsa undan oshgach hisoblashni to'xtatadi…, Qisqa ism aniq mos kelishi kerak; uzunroq ism 2-3 xatoni ko'taradi., (nomzod, boshlanish indeksi, so'zlar soni) — yakka so'zlar va qo'shni…, Matnda ism (yumshoq moslik bilan) bormi?, Matndan ismni (va oldidagi "hey/salom/ey" kabi undovni) olib tashlaydi. Asl… (+10 more)

### Community 32 - ".register_commands"
Cohesion: 0.10
Nodes (13): _list_devices(), _mute(), _playback(), _ptt(), _ptt_press(), _sensitivity(), _set_device(), Nom (qism mos kelsa ham) yoki indeks → qurilma indeksi. None = standart. (+5 more)

### Community 33 - "config.py"
Cohesion: 0.19
Nodes (10): dotenv, env_candidates(), load_env_files(), _project_env(), Path, Markaziy konfiguratsiya (.env / muhit o'zgaruvchilaridan o'qiladi). Modul…, Loyiha ildizidagi `.env` (`nexus/config.py` ga nisbatan) — boshqa papkadan…, `.env` manbalari, ustuvorlik tartibida (birinchisi ustun): 1. joriy papkadan… (+2 more)

### Community 34 - "CommandGuard"
Cohesion: 0.15
Nodes (12): CommandGuard, Buyruqni qo'riqchi orqali bajaradi. `confirmed=True` — registry foydalanuvchi…, `run_terminal_command` uchun uch pog'onali qo'riqchi. `check()` → ("allow" |…, Tekshiruvdan o'tgan buyruqni bajarish uchun argv (`~` kengaytirilgan holda)., _truncate(), parametrize, test_guard_allows(), test_guard_argv_expands_tilde() (+4 more)

### Community 35 - "BrowserDOMController"
Cohesion: 0.17
Nodes (9): BrowserDOMController, _fmt_time(), _js_error(), js_to_applescript(), _parse_json(), Any, Sahifa ichida JavaScript bajarish: scroll, click, matn olish., JS matnini AppleScript qo'shtirnoqli literal ichiga qo'yish uchun escaping… (+1 more)

### Community 36 - "DaemonRunner"
Cohesion: 0.16
Nodes (5): DaemonRunner, `nexus.main.run()` ni alohida thread'da o'z event loop'i bilan yuritadi., To'xtatish signalini beradi (bloklamaydi) — tugashini `finished` orqali…, To'xtatish signalini beradi va thread tugashini kutadi. True = toza tugadi., GUI'dan daemon'ga buyruq (thread-safe, natija kutilmaydi).

### Community 38 - "Result"
Cohesion: 0.29
Nodes (3): Result, YouTube pleyerini `document.querySelector('video')` orqali boshqaradi., YouTubeController

### Community 39 - "run"
Cohesion: 0.11
Nodes (15): Event, GeminiConfigError, Konfiguratsiya xatosi (masalan, API kaliti yo'q)., _first(), MetricsTicker, print_banner(), Any, Berilgan kalitlardan birinchi None bo'lmagan qiymat. (+7 more)

### Community 40 - "TaintTracker"
Cohesion: 0.25
Nodes (3): Navbat ichida tashqi matn o'qilganini eslab qoladi., TaintTracker, test_taint_tracker()

### Community 42 - "vision_box_to_screen"
Cohesion: 0.50
Nodes (4): Vision normalizatsiyalangan bbox (0..1, y PASTDAN) → ekran (x, y, w, h),…, vision_box_to_screen(), test_vision_box_bottom_line_lands_at_window_bottom(), test_vision_box_to_screen_flips_y_and_offsets_by_window()

### Community 43 - "UIServer"
Cohesion: 0.28
Nodes (3): uvicorn'ni fon taskda ishga tushiradigan o'ram., UIServer, socket

### Community 44 - "desktop.py"
Cohesion: 0.09
Nodes (22): default_orb_origin(), _env_true(), _hex_color(), _make_app_icon(), _make_webview(), NexusOrbPanel, Desktop ilova qatlami: o'z oynasi, doim tepada turadigan orb va menyu bar…, Oyna/orb hech bo'lmaganda `min_visible`×`min_visible` qismi bilan biror ekranda… (+14 more)

### Community 45 - "match_app"
Cohesion: 0.18
Nodes (8): installed_apps(), match_app(), hits(), /Applications, /System/Applications, ~/Applications dagi .app nomlari (60s…, `needle` nomning boshida yoki ichidagi so'z boshida keladi ("word" ≠…, Aytilgan nomga mos o'rnatilgan ilovalar, eng yaqini birinchi. Tartib: aniq…, _starts_a_word(), test_match_app_fuzzy()

### Community 46 - "_bus"
Cohesion: 0.29
Nodes (10): _bus(), _drain(), Queue, Gemini client note_utterance'ni chaqirmasa ham, bus'dagi TRANSCRIPT (user,…, test_gate_listens_to_bus_transcripts(), test_gate_new_request_cancels_old(), test_gate_timeout(), test_gate_ui_confirm_command() (+2 more)

### Community 47 - "audio_streamer.py"
Cohesion: 0.07
Nodes (27): math, compute_rms(), _default_input_index(), echo_gate(), gate_open(), parse_latency(), Any, Mikrofon oqimi va ovoz ijrosi (sounddevice / PortAudio). `AudioStreamer` —… (+19 more)

### Community 48 - "macos_actions.py"
Cohesion: 0.13
Nodes (22): collections, collections_abc, ctypes, datetime, importlib, json, logging, build_search_url() (+14 more)

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
Cohesion: 0.17
Nodes (9): contextlib, errno, FastAPI, fastapi_responses, fastapi_staticfiles, _QuietServer, UI ko'prigi: FastAPI + WebSocket server. EventBus hodisalarini brauzerdagi UI…, Signal handlerlarini o'rnatmaydigan uvicorn Server (signalni main.py… (+1 more)

### Community 53 - "test_video_translate.py"
Cohesion: 0.07
Nodes (30): attach(), build_ffmpeg_cmd(), feed_action(), find_tab_script(), is_quota_error(), player_setup_js(), BaseException, main.py: bus/settings/mikrofonni ulaydi; echo guard tarjima ijrosini ham… (+22 more)

### Community 54 - "DictationState"
Cohesion: 0.25
Nodes (3): DictationState, Diktovka holati va terilgan matn hisobi., test_dictation_state_lifecycle()

### Community 55 - "benchmark_live.py"
Cohesion: 0.33
Nodes (8): all_declarations(), build_config(), main(), passed(), Model qaysi toolni tanlashini real Gemini Live sessiyasida o'lchash (toollar…, Asosiy sxemalar + kengaytma modullari (nomlar bo'yicha takrorsiz)., Bitta buyruq: (chaqirilgan toollar [{name,args}], aytilgan matn, navbatlar…, run_case()

### Community 56 - "fake_screen"
Cohesion: 0.29
Nodes (6): ax_ready(), fake_screen(), Any, fixture, MonkeyPatch, Skrinshot/JPEG bosqichini almashtiradi: real screencapture chaqirilmaydi.

### Community 57 - "Segment"
Cohesion: 0.12
Nodes (12): is_silent(), Javob bermagan bo'lakni navbat boshiga qaytaradi — boshqa (bo'sh) sessiya oladi., Bo'lak deyarli jim (o'rtacha RMS `SILENT_RMS` dan past)., Tarjima bo'lagi: kiruvchi audio (tayinlanguncha `buf`da) va modelning javobi…, Tayinlanmagan bo'laklarni (FIFO) bo'sh sessiyalarga beradi., Segment, _FakePlayer, test_playout_drops_junk_translation() (+4 more)

### Community 58 - "test_wake_dictation.py"
Cohesion: 0.17
Nodes (15): is_stop_phrase(), Butun gap faqat to'xtash iborasidan iboratmi?, looks_like_command(), normalise(), SMART rejimi uchun evristika: qisqa gap + buyruq so'zi., Kichik harf, urg'u/apostrofsiz, tinish belgisiz; kirill → lotin., clock(), fixture (+7 more)

### Community 59 - "_recognize"
Cohesion: 0.33
Nodes (6): pick_languages(), Qo'llab-quvvatlanadigan tillardan kerakli tartibda tanlaydi ("uz" → "uz-UZ"…, Vision OCR: [(text, nx, ny, nw, nh, confidence)] — normalizatsiyalangan, y…, _recognize(), supported_languages(), test_pick_languages_prefers_uz_then_ru_en_and_skips_missing()

### Community 62 - "pathlib"
Cohesion: 0.24
Nodes (8): argparse, pathlib, main(), Path, Gemini ovozlarini o'zbekcha namunaviy jumla bilan tinglab tanlash.…, render(), save_wav(), wave

### Community 63 - "schemas.py"
Cohesion: 0.39
Nodes (7): _b(), _decl(), _i(), _n(), Any, Gemini Live API uchun FunctionDeclaration lug'atlari va tizim ko'rsatmasi.…, _s()

### Community 64 - "is_config_rejection"
Cohesion: 0.40
Nodes (5): is_config_rejection(), BaseException, Server konfiguratsiyani rad etgan bo'lsa navbatdagi modelga bog'liq maydonni…, Server konfiguratsiyani rad etdimi (WebSocket 1007 / invalid argument), kalit…, test_is_config_rejection()

### Community 65 - "split_stop"
Cohesion: 0.50
Nodes (3): (teriladigan matn, to'xtash kerakmi). "…hammasi shu, to'xta" → ("…hammasi shu",…, split_stop(), test_split_stop()

### Community 66 - "error_text"
Cohesion: 0.50
Nodes (4): error_text(), BaseException, Gemini xatosini foydalanuvchiga o'zbekcha qisqa jumla qilib beradi., test_error_text_is_uzbek()

### Community 67 - "Any"
Cohesion: 0.13
Nodes (14): parse_player_state(), Any, Bitta Live sessiya: navbatdagi bo'lakni oladi, javobini bo'lakka yozadi., Parallel sessiyalar + dispetcher + tartibli ijro., Sessiya uzildi: joriy bo'lak yakunlangan deb belgilanadi, o'zi bo'sh ro'yxatdan…, Model javobini sessiyaning joriy bo'lagiga yozadi. True — navbat tugadi…, stop_video_translation(), translator_instruction() (+6 more)

### Community 68 - "ocr_image"
Cohesion: 0.16
Nodes (19): Box, available(), lines_as_elements(), lines_to_text(), ocr_image(), Satrlarni yuqoridan pastga, bir qatordagilarni chapdan o'ngga tartiblaydi. Ikki…, Tartiblangan satrlardan matn: bir qatordagilar ikki bo'shliq bilan, qatorlar…, OCR satrlarini list_ui_elements formatiga o'giradi: {n, role:'text', label, at,… (+11 more)

### Community 69 - "._playout"
Cohesion: 0.15
Nodes (9): fit_tempo(), Bo'laklarni `seq` tartibida, video o'z oralig'iga (`src_start`) yetganda ijroga…, Tarjima ulgurmayapti (masalan, kvota kam — sessiyalar yetmaydi): gapni tashlab…, turn_complete kelmay qolgan sessiyani bo'shatadi (model jim qoldi)., Tarjima (`out_s`) videodagi qolgan oralig'iga (`window_s`) sig'ishi uchun…, activity_end dan keyin `no_response_s` ichida audio kelmadi — ijroda o'tkazib…, Sessiya bo'shadi — navbatdagi bo'lakni olishi mumkin., segment_expired() (+1 more)

### Community 70 - "VideoTranslator"
Cohesion: 0.13
Nodes (11): AppleScript'ni `osascript` orqali bajaradi (stdin orqali, argument uzunligi…, run_applescript(), Process, `pos` dan `ahead` soniya oldinga tarjima tayyormi: ijroga qo'yilgan, yoki…, Video pauza, tarjima ovozi esa davom etadi — `seconds` dan keyin video qayta…, Buferlash: video pauzada turadi, oldinda `GATE_AHEAD_S` tarjima tayyor bo'lgach…, JS ni video ochilgan tabda bajaradi (faol tab emas — foydalanuvchi boshqa tabga…, Pleyer holatini kuzatadi; tab boshqa sahifaga o'tsa yoki video tugasa — tugaydi. (+3 more)

### Community 72 - "LoopGuard"
Cohesion: 0.20
Nodes (7): LoopGuard, Any, Bir navbatda haddan ko'p yoki bir xil chaqiruvlarni to'xtatadi., None — davom et; matn — rad etish sababi (modelga tushuntirish)., test_loop_guard_identical_calls(), test_loop_guard_max_calls_per_turn(), test_loop_guard_non_consecutive_identical_calls()

### Community 73 - "describe_screen"
Cohesion: 0.36
Nodes (10): describe_screen(), _extract_text(), _image_part(), look_at_screen(), _make_client(), Any, Oldingi oynani skrinshot qilib Gemini'ga ko'rsatadi. {ok, output, app, ...}., read_screen_ocr() (+2 more)

### Community 76 - "gemini_live_client.py"
Cohesion: 0.16
Nodes (16): asyncio, dataclasses, itertools, Diktovka rejimi: foydalanuvchi gapiradi — yordamchi teradi, to'xtash…, Gemini Multimodal Live API (WebSocket) sessiyasi. Ikki parallel task:…, ends_conversation(), _has_phrase(), Ism bilan chaqirish (wake): gap yordamchiga qaratilganmi? Xonada boshqa odamlar… (+8 more)

### Community 81 - "Gemini Live API findings (VAD, transcription langs, affective_dialog 1007/1011)"
Cohesion: 0.67
Nodes (3): Echo guard + playback prebuffer + low VAD start sensitivity, session.receive() ends each turn (not a disconnect), Gemini Live API findings (VAD, transcription langs, affective_dialog 1007/1011)

### Community 84 - "build_ytdlp_cmd"
Cohesion: 0.29
Nodes (5): build_ytdlp_cmd(), Faqat audio yuklanadi; stdout: 1-qator sarlavha, oxirgi qator fayl yo'li., yt-dlp: audio faylni vaqtinchalik papkaga yuklaydi. (ok, sarlavha | xato).…, watch_url(), test_build_ytdlp_cmd()

### Community 85 - "PlaybackClock"
Cohesion: 0.10
Nodes (14): find_binary(), is_junk_translation(), PlaybackClock, PATH + Homebrew papkalari (.app ichidan ishga tushganda PATH qisqa bo'ladi)., Model tarjima o'rniga yorliq/izoh aytdi (`(Uzbek translation: …)`, `<no…, Brauzer pleyeri holatidan joriy video vaqtini baholaydi (so'rovlar orasida…, s16le mono PCM ni ohangini saqlab `tempo` barobar tezlashtiradi (ffmpeg…, time_stretch() (+6 more)

### Community 90 - ".get_system_info"
Cohesion: 0.50
Nodes (3): _fmt_uptime(), Any, _summarize_info()

## Ambiguous Edges - Review These
- `Gemini Live API (native audio, WebSocket)` → `Local models concept (Whisper.cpp small.uz + Qwen 7B Q4)`  [AMBIGUOUS]
  design/Nexus Ovoz OS.dc.html · relation: conceptually_related_to

## Knowledge Gaps
- **15 isolated node(s):** `nexus-voice`, `build_app.sh script`, `fs`, `src`, `listeners` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 554 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Gemini Live API (native audio, WebSocket)` and `Local models concept (Whisper.cpp small.uz + Qwen 7B Q4)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `EventBus` connect `EventBus` to `GeminiLiveClient`, `test_core.py`, `test_tools.py`, `Nexus Ovoz OS README`, `test_desktop.py`, `main.py`, `ToolRegistry`, `test_safety.py`, `Settings`, `AudioPlayer`, `_registry`, `DesktopPrefs`, `test_server.py`, `run`, `UIServer`, `_bus`, `audio_streamer.py`, `macos_actions.py`, `snapshot`, `server.py`, `_ConfirmTracker`, `gemini_live_client.py`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Why does `ToolRegistry` connect `ToolRegistry` to `BrowserController`, `test_core.py`, `test_tools.py`, `EventBus`, `Nexus Ovoz OS README`, `._build_handlers`, `MacOSController`, `video_translate.py`, `main.py`, `test_safety.py`, `_registry`, `ConfirmationGate`, `BrowserDOMController`, `Result`, `run`, `TaintTracker`, `SearchNavigationController`, `macos_actions.py`, `test_video_translate.py`, `SearchInputController`, `LoopGuard`, `test_registry_loads_extension_modules`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Why does `GeminiLiveClient` connect `GeminiLiveClient` to `is_config_rejection`, `test_core.py`, `run`, `EventBus`, `gemini_live_client.py`, `main.py`, `Gemini Live API findings (VAD, transcription langs, affective_dialog 1007/1011)`, `DictationState`, `WakeState`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `EventBus` (e.g. with `AudioPlayer` and `AudioStreamer`) actually correct?**
  _`EventBus` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `MacOSController` (e.g. with `MetricsTicker` and `ToolRegistry`) actually correct?**
  _`MacOSController` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `GeminiLiveClient` (e.g. with `DictationState` and `EventBus`) actually correct?**
  _`GeminiLiveClient` has 4 INFERRED edges - model-reasoned connections that need verification._