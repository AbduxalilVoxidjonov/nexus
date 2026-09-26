# Graph Report - nexus  (2026-09-26)

## Corpus Check
- 42 files · ~89,698 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 4, .command 2, .example 1)

## Summary
- 1776 nodes · 3977 edges · 80 communities (68 shown, 12 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 261 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6bfc4f11`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- support.js
- file_actions.py
- ax_actions.py
- browser_actions.py
- GeminiLiveClient
- test_core.py
- app.js
- test_tools.py
- AudioStreamer
- Nexus Ovoz OS README
- ._build_handlers
- NexusDesktopApp
- MacOSController
- BrowserDOMController
- EventBus
- test_desktop.py
- main.py
- screen_reader.py
- test_screen_reader.py
- ToolRegistry
- test_safety.py
- Settings
- check_setup.py
- AudioPlayer
- test_wake_dictation.py
- _registry
- DesktopPrefs
- ws_reconnect_harness.js
- test_server.py
- web_answer.py
- ConfirmationGate
- name_in
- Result
- config.py
- CommandGuard
- ._feed
- DaemonRunner
- .connect
- SearchNavigationController
- MetricsTicker
- safety.py
- SearchInputController
- ocr_image
- server.py
- desktop.py
- macos_actions.py
- _bus
- audio_streamer.py
- registry.py
- snapshot
- BargeInGate
- vision_box_to_screen
- UIServer
- test_video_translate.py
- DictationState
- benchmark_live.py
- fake_screen
- VideoTranslator
- _FakeModels
- _recognize
- _ConfirmTracker
- FakeStream
- voice_picker.py
- schemas.py
- video_translate.py
- split_stop
- error_text
- Any
- .build_hotkey_script
- ._run
- test_registry_loads_extension_modules
- nexus/__init__.py
- time
- build_app.sh
- nexus-voice
- looks_like_command
- build_ytdlp_cmd
- PlaybackClock
- CLAUDE.md

## God Nodes (most connected - your core abstractions)
1. `EventBus` - 76 edges
2. `MacOSController` - 65 edges
3. `ToolRegistry` - 57 edges
4. `GeminiLiveClient` - 55 edges
5. `VideoTranslator` - 55 edges
6. `AudioStreamer` - 47 edges
7. `NexusDesktopApp` - 45 edges
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

## Communities (80 total, 12 thin omitted)

### Community 0 - "support.js"
Cohesion: 0.06
Nodes (75): boot(), bundledBlob(), cdnScriptFor(), collectProps(), compileAttr(), compileTemplate(), contentKey(), createComponentFactory() (+67 more)

### Community 1 - "file_actions.py"
Cohesion: 0.06
Nodes (61): csv, nexus, _append_csv(), _append_row_sync(), append_spreadsheet_row(), _append_xlsx(), _coerce_cell_value(), delete_file() (+53 more)

### Community 2 - "ax_actions.py"
Cohesion: 0.07
Nodes (74): applicationservices, difflib, _actions(), activate_element(), _app_root(), _attr(), available(), _clean_text() (+66 more)

### Community 3 - "browser_actions.py"
Cohesion: 0.15
Nodes (14): app_name(), BrowserController, build_search_url(), _js_error(), normalize_url(), Brauzer boshqaruvi (Safari / Google Chrome) — AppleScript + sahifa ichidagi…, Joriy tabda URL ni almashtiradi (yangi tab ochmasdan)., Tab ochish/yopish, URL olish, tab almashtirish, reload, ro'yxat. (+6 more)

### Community 4 - "GeminiLiveClient"
Cohesion: 0.08
Nodes (20): GeminiLiveClient, _grounding_sources(), is_config_rejection(), Any, BaseException, `grounding_metadata.grounding_chunks[*].web.{uri,title}` → "title — uri"…, Server konfiguratsiyani rad etgan bo'lsa navbatdagi modelga bog'liq maydonni…, Cheksiz ulanish sikli; `stop()` chaqirilguncha qayta ulanaveradi. (+12 more)

### Community 5 - "test_core.py"
Cohesion: 0.07
Nodes (50): compute_backoff(), `extended-thinking` modelida daraja majburiy (bo'sh bo'lsa "high"); boshqa…, base * 2**attempt + jitter, max_delay bilan cheklangan. `jitter` None bo'lsa…, Sessiya juda qisqa yashagan bo'lsa (masalan, eskirgan handle) — handle…, should_drop_resume_handle(), thinking_level_for(), SimpleNamespace, _audio_part() (+42 more)

### Community 6 - "app.js"
Cohesion: 0.13
Nodes (52): answerConfirm(), applyDevices(), applySettings(), applySnapshot(), bind(), closeSocket(), connect(), ensureRow() (+44 more)

### Community 7 - "test_tools.py"
Cohesion: 0.08
Nodes (30): _no_sleep(), MonkeyPatch, Tool qatlami testlari — real macOS tizimiga tegmaydi (osascript/subprocess…, Barcha ichki JS'lar AppleScript literaliga qo'yilganda qo'shtirnoq muvozanati…, ScriptRecorder, test_browser_open_url_normalizes(), test_is_terminal_frontmost(), test_js_permission_hint() (+22 more)

### Community 8 - "AudioStreamer"
Cohesion: 0.06
Nodes (19): AudioStreamer, _list_devices(), _mute(), _playback(), _ptt(), _ptt_press(), _sensitivity(), _set_device() (+11 more)

### Community 9 - "Nexus Ovoz OS README"
Cohesion: 0.05
Nodes (47): Nexus Ovoz OS design mockup (dc.html), Design mockup Component (simulated PTT command flow), Local models concept (Whisper.cpp small.uz + Qwen 7B Q4), Nexus Ovoz OS README, AXManualAccessibility for Chrome/Electron, CommandGuard allow/deny/confirm tiers, Desktop layer (pure pyobjc NSWindow + WKWebView, orb NSPanel, menu bar), Dictation mode (direct typing, stop phrases) (+39 more)

### Community 10 - "._build_handlers"
Cohesion: 0.06
Nodes (19): browser_click_button(), browser_click_selector(), browser_close_tab(), browser_current_page(), browser_list_tabs(), browser_open_url(), browser_read_page(), browser_reload() (+11 more)

### Community 11 - "NexusDesktopApp"
Cohesion: 0.10
Nodes (8): _load_url(), NexusDesktopApp, Any, NSApplication delegati: oyna, orb, menyu bar, daemon ko'prigi., SIGINT/SIGTERM → toza chiqish. Mach-port orqali AppKit run loop'ida qayta…, Daemon thread'idan chaqiriladi — hodisani GUI thread'iga uzatadi., `.env` ni Finder'da ko'rsatadi (yagona "tashqi ochish" — brauzer emas)., NSObject

### Community 12 - "MacOSController"
Cohesion: 0.14
Nodes (7): _clamp(), MacOSController, Result, SSID ni aniqlaydi. macOS 14+ da Location Services ruxsatisiz SSID `<redacted>`…, macOS bilan ishlash: ovoz, media, ilovalar, Finder, tizim, terminal., macOS 12+ da DND uchun ochiq API yo'q. Foydalanuvchi yaratgan Shortcuts…, Faol oynaga matn kiritadi: bufer + Cmd+V (keystroke o'zbek/kirill matnni…

### Community 13 - "BrowserDOMController"
Cohesion: 0.15
Nodes (9): BrowserDOMController, _fmt_time(), js_to_applescript(), _parse_json(), Any, Sahifa ichida JavaScript bajarish: scroll, click, matn olish., JS matnini AppleScript qo'shtirnoqli literal ichiga qo'yish uchun escaping…, Runner (+1 more)

### Community 14 - "EventBus"
Cohesion: 0.06
Nodes (28): CommandHandler, EventBus, AbstractEventLoop, Any, Queue, Thread-safe pub/sub. `publish` istalgan thread'dan chaqirilishi mumkin., FakeAudio, FakeRegistry (+20 more)

### Community 15 - "test_desktop.py"
Cohesion: 0.09
Nodes (26): default_window_frame(), effective_state(), placeholder_html(), (rang, yorliq) — menyu bar / orb uchun., Menyu bar'dagi holat satri, masalan "● Tinglamoqda" yoki "● Kutmoqda (mikrofon…, Ekran o'rtasida, `visibleFrame`ning `fraction` (90%) qismi (yoki `size`), min…, `base_url/health` 2xx qaytarguncha kutadi. `keep_waiting()` False qaytarsa…, Server tayyor bo'lguncha (yoki daemon xato bilan to'xtasa) oynada… (+18 more)

### Community 16 - "main.py"
Cohesion: 0.09
Nodes (28): ArgumentParser, Event, Namespace, list_input_devices(), [{"index", "name", "default"}] — faqat kirish (mikrofon) qurilmalari., DesktopOptions, _env_true(), Desktop ilovani ishga tushiradi (asosiy thread'da bloklaydi). Qaytadi: chiqish… (+20 more)

### Community 17 - "screen_reader.py"
Cohesion: 0.13
Nodes (28): appkit, foundation, capture_frontmost_window(), describe_screen(), _shoot(), _extract_text(), _front_app(), _front_window_info() (+20 more)

### Community 18 - "test_screen_reader.py"
Cohesion: 0.11
Nodes (10): _box(), screen_reader (OCR + Gemini ko'rish) va ax_actions'dagi AX→OCR zaxira yo'li…, test_click_ui_element_by_ocr_index_from_cache(), test_lines_as_elements_centres_and_roles(), test_lines_to_text_groups_rows_and_truncates(), test_list_ui_elements_merges_ax_and_ocr(), test_list_ui_elements_pure_ax_unchanged(), test_read_screen_ocr_tool_with_fake_ocr() (+2 more)

### Community 19 - "ToolRegistry"
Cohesion: 0.08
Nodes (16): Handler, Any, Foydalanuvchi yangi gap boshladi: loop guard va taint tozalanadi., Foydalanuvchining yakuniy transkripti — og'zaki tasdiq uchun., Bajarilayotgan tool tasklarini bekor qiladi. Kutilayotgan tasdiq so'roviga…, ⌥⎋ / "kill_all": tool tasklar + kutilayotgan tasdiq bekor qilinadi, so'ng…, Handler javobini (tuple yoki dict) yagona formatga keltiradi., Bajarishdan OLDIN aniqlanadigan tasdiq sabablari (bo'sh — tasdiqsiz). (+8 more)

### Community 20 - "test_safety.py"
Cohesion: 0.09
Nodes (28): looks_read_only(), LoopGuard, path_is_sensitive(), Path, True — buyruq DANGEROUS_SHELL naqshlaridan biriga mos keladi., True — buyruq HECH QANDAY bayroq bilan ham hech narsani o'zgartira olmaydi., True — bu yerga yozish persistensiya yaratishi yoki sir sizdirishi mumkin., Model yoki log ko'rishidan oldin kalitga o'xshagan narsalarni yashiradi. (+20 more)

### Community 21 - "Settings"
Cohesion: 0.10
Nodes (15): google-genai Client — hamma joyda bir xil sozlama bilan., Settings, create_app(), index(), Path, FastAPI ilovasini yaratadi (testlarda ham shu ishlatiladi)., test_config_defaults_gemini38(), test_wake_defaults_to_name_only() (+7 more)

### Community 22 - "check_setup.py"
Cohesion: 0.27
Nodes (15): CDLL, check_accessibility(), check_automation(), check_devices(), check_key(), check_live(), check_mic_level(), check_packages() (+7 more)

### Community 23 - "AudioPlayer"
Cohesion: 0.10
Nodes (14): AudioPlayer, parse_latency(), high"/"low" yoki sekund (str/float) → sounddevice `latency` argumenti., 24 kHz int16 mono ijro. `enqueue` istalgan thread/task'dan chaqirilishi mumkin.…, Buferdagi qolgan audioni (prebuffer to'lmagan bo'lsa ham) ijroga qo'yib…, Navbatni tozalaydi (interruption). Tashlangan chunklar sonini qaytaradi., Hozir ovoz chiqyaptimi (navbatda audio bor yoki oxirgi chunk yaqinda chiqqan)., Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline (+6 more)

### Community 24 - "test_wake_dictation.py"
Cohesion: 0.13
Nodes (13): Yordamchi hozir unga gapirilayotganini kuzatadi., Oxirgi chaqiruvdan keyingi follow-up oynasi hali ochiqmi?, Oynani yangilash — yordamchi hozirgina foydalanuvchi uchun nimadir qildi., WakeState, clock(), fixture, Wake (ism bilan chaqirish) va diktovka mantiqi testlari., test_wake_always_mode_acts_on_everything() (+5 more)

### Community 25 - "_registry"
Cohesion: 0.10
Nodes (16): MonkeyPatch, Handler `needs_confirmation` qaytarsa registry gate'ni so'raydi va…, kill_all: gate.cancel_pending("cancelled") chaqiriladi VA klient ilgagi…, _registry(), test_registry_confirmation_via_bus_utterance_command(), test_registry_confirmation_voice_approves(), test_registry_dictation_tools(), test_registry_handler_needs_confirmation_dict() (+8 more)

### Community 26 - "DesktopPrefs"
Cohesion: 0.12
Nodes (10): DesktopPrefs, _pair(), Path, ~/.nexus/desktop.json — orb pozitsiyasi, oyna o'lchami, orb ko'rinishi., Path, start.command: bo'sh/namunaviy GEMINI_API_KEY → aniq xabar, exit 1; haqiqiy…, test_prefs_ignores_corrupt_or_invalid(), test_prefs_roundtrip() (+2 more)

### Community 27 - "ws_reconnect_harness.js"
Cohesion: 0.12
Nodes (9): ref_fs, byId(), els, FakeWS, fs, listeners, makeEl(), sockets (+1 more)

### Community 28 - "test_server.py"
Cohesion: 0.16
Nodes (14): fastapi_testclient, pytest, TestClient, bus(), client(), _free_port(), fixture, nexus.server (FastAPI + WS ko'prigi) testlari. (+6 more)

### Community 29 - "web_answer.py"
Cohesion: 0.22
Nodes (14): build_request(), _create(), extract_sources(), extract_text(), _get(), _make_client(), Any, `web_answer` tool — Google Search grounding bilan faktik/yangilik savollariga… (+6 more)

### Community 30 - "ConfirmationGate"
Cohesion: 0.11
Nodes (13): Registry gate'ida (ConfirmationGate) hal qilinmagan tasdiq so'rovi bormi?, ConfirmationGate, _consume(), PendingConfirmation, Any, Bir vaqtda faqat bitta faol tasdiq so'rovi. Yangi so'rov eskisini bekor qiladi., Foydalanuvchining yakuniy transkripti. So'rovdan OLDIN aytilgan gap hisobga…, Bus'dagi TRANSCRIPT (user, final) hodisalarini ham kuzatadi — gemini client… (+5 more)

### Community 31 - "name_in"
Cohesion: 0.14
Nodes (18): _candidates(), levenshtein(), name_in(), Matnda ism (yumshoq moslik bilan) bormi?, Matndan ismni (va oldidagi "hey/salom/ey" kabi undovni) olib tashlaydi. Asl…, Levenshtein masofasi; `limit` berilsa undan oshgach hisoblashni to'xtatadi…, Qisqa ism aniq mos kelishi kerak; uzunroq ism 2-3 xatoni ko'taradi., (nomzod, boshlanish indeksi, so'zlar soni) — yakka so'zlar va qo'shni… (+10 more)

### Community 32 - "Result"
Cohesion: 0.29
Nodes (3): Result, YouTube pleyerini `document.querySelector('video')` orqali boshqaradi., YouTubeController

### Community 33 - "config.py"
Cohesion: 0.11
Nodes (21): dotenv, _env_api_key(), env_candidates(), is_placeholder_api_key(), load_env_files(), load_extra_env(), _project_env(), Path (+13 more)

### Community 34 - "CommandGuard"
Cohesion: 0.15
Nodes (12): CommandGuard, Buyruqni qo'riqchi orqali bajaradi. `confirmed=True` — registry foydalanuvchi…, `run_terminal_command` uchun uch pog'onali qo'riqchi. `check()` → ("allow" |…, Tekshiruvdan o'tgan buyruqni bajarish uchun argv (`~` kengaytirilgan holda)., _truncate(), parametrize, test_guard_allows(), test_guard_argv_expands_tilde() (+4 more)

### Community 35 - "._feed"
Cohesion: 0.17
Nodes (8): build_ffmpeg_cmd(), feed_action(), Process, Navbatdagi chunk bilan nima qilish: "resync" | "wait" | "send". Audio videodan…, Seek: navbatdagi kiruvchi audio va hali ijro etilmagan tarjimalar tashlanadi., ffmpeg PCM → navbat (video vaqti bilan), videodan `LOOKAHEAD_S` oldinda; seek →…, test_build_ffmpeg_cmd(), test_feed_action()

### Community 36 - "DaemonRunner"
Cohesion: 0.16
Nodes (5): DaemonRunner, `nexus.main.run()` ni alohida thread'da o'z event loop'i bilan yuritadi., To'xtatish signalini beradi (bloklamaydi) — tugashini `finished` orqali…, To'xtatish signalini beradi va thread tugashini kutadi. True = toza tugadi., GUI'dan daemon'ga buyruq (thread-safe, natija kutilmaydi).

### Community 39 - "MetricsTicker"
Cohesion: 0.24
Nodes (7): _first(), MetricsTicker, Any, Berilgan kalitlardan birinchi None bo'lmagan qiymat., Har `interval` sekundda cpu/ram/battery ni METRICS ga nashr qiladi., Nashr qilinadigan METRICS: snapshot'dagi eski maydonlar (reconnects,…, test_metrics_ticker_preserves_snapshot_fields()

### Community 40 - "safety.py"
Cohesion: 0.13
Nodes (9): collections, _cmd(), Xavfsizlik qatlami: xavfli shell naqshlari, sezgir yo'llar, sir redaktsiyasi,…, Faqat buyruq pozitsiyasidagi nomga mos keladigan regex., Navbat ichida tashqi matn o'qilganini eslab qoladi., TaintTracker, secrets, shlex (+1 more)

### Community 42 - "ocr_image"
Cohesion: 0.24
Nodes (12): Box, available(), lines_to_text(), ocr_image(), Satrlarni yuqoridan pastga, bir qatordagilarni chapdan o'ngga tartiblaydi. Ikki…, Tartiblangan satrlardan matn: bir qatordagilar ikki bo'shliq bilan, qatorlar…, Rasm faylini OCR qiladi → tartiblangan satrlar [{text, x, y, w, h}]. `bounds`…, Oldingi oynani skrinshot + OCR: {app, text, lines, window, count}. (+4 more)

### Community 43 - "server.py"
Cohesion: 0.22
Nodes (8): contextlib, errno, FastAPI, fastapi_responses, fastapi_staticfiles, UI ko'prigi: FastAPI + WebSocket server. EventBus hodisalarini brauzerdagi UI…, socket, uvicorn

### Community 44 - "desktop.py"
Cohesion: 0.09
Nodes (22): json, default_orb_origin(), _hex_color(), _make_app_icon(), _make_webview(), NexusOrbPanel, Desktop ilova qatlami: o'z oynasi, doim tepada turadigan orb va menyu bar…, Oyna/orb hech bo'lmaganda `min_visible`×`min_visible` qismi bilan biror ekranda… (+14 more)

### Community 45 - "macos_actions.py"
Cohesion: 0.08
Nodes (22): ctypes, _fmt_uptime(), installed_apps(), is_terminal_app(), _kill_process_group(), match_app(), hits(), Any (+14 more)

### Community 46 - "_bus"
Cohesion: 0.33
Nodes (9): _bus(), _drain(), Queue, Gemini client note_utterance'ni chaqirmasa ham, bus'dagi TRANSCRIPT (user,…, test_gate_listens_to_bus_transcripts(), test_gate_new_request_cancels_old(), test_gate_timeout(), test_gate_ui_confirm_command() (+1 more)

### Community 47 - "audio_streamer.py"
Cohesion: 0.09
Nodes (23): math, compute_rms(), echo_gate(), gate_open(), Mikrofon oqimi va ovoz ijrosi (sounddevice / PortAudio). `AudioStreamer` —…, Callback thread'da: darajani hisoblaydi, gate'ni yangilaydi, navbatga qo'yadi.…, int16 mono PCM baytlaridan (rms 0..1, db -60..0) qaytaradi., Chunk Gemini'ga yuborilsinmi? (mute yoki PTT bosilmagan bo'lsa — yo'q). (+15 more)

### Community 48 - "registry.py"
Cohesion: 0.24
Nodes (10): asyncio, collections_abc, importlib, inspect, logging, Daemon ichidagi hodisalar shinasi (event bus). Barcha modullar (audio, gemini,…, Gemini Multimodal Live API (WebSocket) sessiyasi. Ikki parallel task:…, Tool registry: Gemini function-call nomini handlerga yo'naltiradi, validatsiya,… (+2 more)

### Community 49 - "snapshot"
Cohesion: 0.31
Nodes (10): _cmd_result(), api_state(), snapshot(), ws_endpoint(), handle_command(), receiver(), send(), sender() (+2 more)

### Community 50 - "BargeInGate"
Cohesion: 0.17
Nodes (9): BargeInGate, AbstractEventLoop, Ijro paytida mikrofon chunklarining echo/barge-in darvozasi (callback…, → (navbatga qo'yiladigan chunklar, sukunatga almashtirilganlar soni)., Nom (qism mos kelsa ham) yoki indeks → qurilma indeksi. None = standart., resolve_device(), test_barge_gate_flushes_held_when_playback_stops(), test_barge_gate_single_spike_becomes_silence() (+1 more)

### Community 51 - "vision_box_to_screen"
Cohesion: 0.50
Nodes (4): Vision normalizatsiyalangan bbox (0..1, y PASTDAN) → ekran (x, y, w, h),…, vision_box_to_screen(), test_vision_box_bottom_line_lands_at_window_bottom(), test_vision_box_to_screen_flips_y_and_offsets_by_window()

### Community 52 - "UIServer"
Cohesion: 0.20
Nodes (4): _QuietServer, Signal handlerlarini o'rnatmaydigan uvicorn Server (signalni main.py…, uvicorn'ni fon taskda ishga tushiradigan o'ram., UIServer

### Community 53 - "test_video_translate.py"
Cohesion: 0.10
Nodes (17): AppleScript: JS ni video tabida bajaradi — Chrome'da `tab_id` bo'yicha (bir xil…, Uzluksiz nutqni tarjima bo'laklariga ajratadi: `push(rms)` True → bo'lakni shu…, Segmenter, video_tab_script(), _FakePlayer, video_translate: toza funksiyalar, sinxron soat, tool ro'yxatga olinishi, echo…, test_build_config_native_and_prompt(), test_playout_drops_junk_translation() (+9 more)

### Community 54 - "DictationState"
Cohesion: 0.25
Nodes (3): DictationState, Diktovka holati va terilgan matn hisobi., test_dictation_state_lifecycle()

### Community 55 - "benchmark_live.py"
Cohesion: 0.29
Nodes (9): datetime, all_declarations(), build_config(), main(), passed(), Model qaysi toolni tanlashini real Gemini Live sessiyasida o'lchash (toollar…, Asosiy sxemalar + kengaytma modullari (nomlar bo'yicha takrorsiz)., Bitta buyruq: (chaqirilgan toollar [{name,args}], aytilgan matn, navbatlar… (+1 more)

### Community 56 - "fake_screen"
Cohesion: 0.40
Nodes (5): ax_ready(), fake_screen(), fixture, MonkeyPatch, Skrinshot/JPEG bosqichini almashtiradi: real screencapture chaqirilmaydi.

### Community 57 - "VideoTranslator"
Cohesion: 0.13
Nodes (14): Bo'laklarni `seq` tartibida, video o'z oralig'iga (`src_start`) yetganda ijroga…, Javob bermagan bo'lakni navbat boshiga qaytaradi — boshqa (bo'sh) sessiya oladi., Video pauza, tarjima ovozi esa davom etadi — `seconds` dan keyin video qayta…, Tarjima ulgurmayapti (masalan, kvota kam — sessiyalar yetmaydi): gapni tashlab…, turn_complete kelmay qolgan sessiyani bo'shatadi (model jim qoldi)., Tarjima bo'lagi: kiruvchi audio (tayinlanguncha `buf`da) va modelning javobi…, activity_end dan keyin `no_response_s` ichida audio kelmadi — ijroda o'tkazib…, Tayinlanmagan bo'laklarni (FIFO) bo'sh sessiyalarga beradi. (+6 more)

### Community 58 - "_FakeModels"
Cohesion: 0.31
Nodes (8): Exception, _fake_client(), _FakeModels, Any, test_describe_screen_default_question(), test_describe_screen_error_and_timeout(), test_describe_screen_uses_fake_client_and_cleans_tmp(), test_look_at_screen_handler_wraps_result()

### Community 59 - "_recognize"
Cohesion: 0.33
Nodes (6): pick_languages(), Qo'llab-quvvatlanadigan tillardan kerakli tartibda tanlaydi ("uz" → "uz-UZ"…, Vision OCR: [(text, nx, ny, nw, nh, confidence)] — normalizatsiyalangan, y…, _recognize(), supported_languages(), test_pick_languages_prefers_uz_then_ru_en_and_skips_missing()

### Community 62 - "voice_picker.py"
Cohesion: 0.28
Nodes (7): argparse, main(), Path, Gemini ovozlarini o'zbekcha namunaviy jumla bilan tinglab tanlash.…, render(), save_wav(), wave

### Community 63 - "schemas.py"
Cohesion: 0.39
Nodes (7): _b(), _decl(), _i(), _n(), Any, Gemini Live API uchun FunctionDeclaration lug'atlari va tizim ko'rsatmasi.…, _s()

### Community 64 - "video_translate.py"
Cohesion: 0.08
Nodes (24): normalize_browser(), attach(), fit_tempo(), is_junk_translation(), is_quota_error(), BaseException, YouTube videosini jonli (sinxron) ovozli tarjima: ingliz → o'zbek. Oqim: yt-dlp…, main.py: bus/settings/mikrofonni ulaydi; echo guard tarjima ijrosini ham… (+16 more)

### Community 65 - "split_stop"
Cohesion: 0.50
Nodes (3): (teriladigan matn, to'xtash kerakmi). "…hammasi shu, to'xta" → ("…hammasi shu",…, split_stop(), test_split_stop()

### Community 66 - "error_text"
Cohesion: 0.50
Nodes (4): error_text(), BaseException, Gemini xatosini foydalanuvchiga o'zbekcha qisqa jumla qilib beradi., test_error_text_is_uzbek()

### Community 67 - "Any"
Cohesion: 0.17
Nodes (10): is_silent(), Any, Bo'lak deyarli jim (o'rtacha RMS `SILENT_RMS` dan past)., Bitta Live sessiya: navbatdagi bo'lakni oladi, javobini bo'lakka yozadi., Parallel sessiyalar + dispetcher + tartibli ijro., Sessiya bo'shadi — navbatdagi bo'lakni olishi mumkin., Sessiya uzildi: joriy bo'lak yakunlangan deb belgilanadi, o'zi bo'sh ro'yxatdan…, Model javobini sessiyaning joriy bo'lagiga yozadi. True — navbat tugadi… (+2 more)

### Community 70 - "._run"
Cohesion: 0.11
Nodes (15): AppleScript'ni `osascript` orqali bajaradi (stdin orqali, argument uzunligi…, run_applescript(), find_tab_script(), parse_player_state(), player_setup_js(), `pos` dan `ahead` soniya oldinga tarjima tayyormi: ijroga qo'yilgan, yoki…, Buferlash: video pauzada turadi, oldinda `GATE_AHEAD_S` tarjima tayyor bo'lgach…, AppleScript (Chrome): `video_id` ochiq tabni topib oldinga chiqaradi va id sini… (+7 more)

### Community 76 - "time"
Cohesion: 0.18
Nodes (13): dataclasses, itertools, is_stop_phrase(), Diktovka rejimi: foydalanuvchi gapiradi — yordamchi teradi, to'xtash…, Butun gap faqat to'xtash iborasidan iboratmi?, normalise(), Ism bilan chaqirish (wake): gap yordamchiga qaratilganmi? Xonada boshqa odamlar…, Kichik harf, urg'u/apostrofsiz, tinish belgisiz; kirill → lotin. (+5 more)

### Community 83 - "looks_like_command"
Cohesion: 0.29
Nodes (5): looks_like_command(), SMART rejimi uchun evristika: qisqa gap + buyruq so'zi., Matnda ism bormi? Bo'lsa follow-up oynasi ochiladi., Bu gapga javob berish kerakmi? (ism eshitilsa oynani ham ochadi)., test_looks_like_command()

### Community 84 - "build_ytdlp_cmd"
Cohesion: 0.29
Nodes (5): build_ytdlp_cmd(), Faqat audio yuklanadi; stdout: 1-qator sarlavha, oxirgi qator fayl yo'li., yt-dlp: audio faylni vaqtinchalik papkaga yuklaydi. (ok, sarlavha | xato).…, watch_url(), test_build_ytdlp_cmd()

### Community 85 - "PlaybackClock"
Cohesion: 0.14
Nodes (8): find_binary(), PlaybackClock, PATH + Homebrew papkalari (.app ichidan ishga tushganda PATH qisqa bo'ladi)., Brauzer pleyeri holatidan joriy video vaqtini baholaydi (so'rovlar orasida…, s16le mono PCM ni ohangini saqlab `tempo` barobar tezlashtiradi (ffmpeg…, time_stretch(), test_clock_interpolates_and_halts(), test_time_stretch_shortens_audio()

## Ambiguous Edges - Review These
- `Gemini Live API (native audio, WebSocket)` → `Local models concept (Whisper.cpp small.uz + Qwen 7B Q4)`  [AMBIGUOUS]
  design/Nexus Ovoz OS.dc.html · relation: conceptually_related_to

## Knowledge Gaps
- **15 isolated node(s):** `nexus-voice`, `build_app.sh script`, `fs`, `src`, `listeners` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 547 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Gemini Live API (native audio, WebSocket)` and `Local models concept (Whisper.cpp small.uz + Qwen 7B Q4)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `ToolRegistry` connect `ToolRegistry` to `browser_actions.py`, `test_core.py`, `test_tools.py`, `Nexus Ovoz OS README`, `._build_handlers`, `MacOSController`, `BrowserDOMController`, `EventBus`, `main.py`, `test_safety.py`, `AudioPlayer`, `_registry`, `ConfirmationGate`, `Result`, `SearchNavigationController`, `safety.py`, `SearchInputController`, `registry.py`, `test_video_translate.py`, `video_translate.py`, `test_registry_loads_extension_modules`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Why does `EventBus` connect `EventBus` to `GeminiLiveClient`, `test_core.py`, `test_tools.py`, `AudioStreamer`, `Nexus Ovoz OS README`, `test_desktop.py`, `main.py`, `ToolRegistry`, `test_safety.py`, `Settings`, `AudioPlayer`, `_registry`, `test_server.py`, `MetricsTicker`, `server.py`, `_bus`, `audio_streamer.py`, `registry.py`, `snapshot`, `BargeInGate`, `UIServer`, `_ConfirmTracker`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Why does `GeminiLiveClient` connect `GeminiLiveClient` to `test_core.py`, `AudioStreamer`, `Nexus Ovoz OS README`, `EventBus`, `registry.py`, `main.py`, `DictationState`, `AudioPlayer`, `test_wake_dictation.py`, `ConfirmationGate`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `EventBus` (e.g. with `AudioPlayer` and `AudioStreamer`) actually correct?**
  _`EventBus` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `MacOSController` (e.g. with `MetricsTicker` and `ToolRegistry`) actually correct?**
  _`MacOSController` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `ToolRegistry` (e.g. with `BrowserController` and `BrowserDOMController`) actually correct?**
  _`ToolRegistry` has 10 INFERRED edges - model-reasoned connections that need verification._