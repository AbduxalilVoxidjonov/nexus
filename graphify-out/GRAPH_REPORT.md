# Graph Report - nexus  (2026-10-01)

## Corpus Check
- 46 files · ~99,851 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: (none) 4, .command 2, .example 1)

## Summary
- 1991 nodes · 4430 edges · 100 communities (84 shown, 16 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 271 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0abbeb26`
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
- desktop.py
- state_style
- WindowsController
- screen_reader.py
- test_screen_reader.py
- ToolRegistry
- test_safety.py
- desktop_win.py
- check_setup.py
- test_core.py
- WakeState
- _registry
- DesktopPrefs
- ws_reconnect_harness.js
- create_app
- web_answer.py
- ConfirmationGate
- name_in
- AudioStreamer
- benchmark_live.py
- CommandGuard
- test_registry_kill_all_runs_hook_and_cancels_gate
- DaemonRunner
- .connect
- config.py
- run
- vision_box_to_screen
- FakeAudio
- ._evaluate_addressed
- is_quota_error
- test_desktop.py
- macos_actions.py
- _bus
- Any
- .run
- bus
- BargeInGate
- Segmenter
- server.py
- test_video_translate.py
- DictationState
- main.py
- fake_screen
- ._dispatch
- looks_like_command
- _recognize
- feed_action
- ._handle_server_content
- Process
- schemas.py
- NexusOrbPanel
- normalise
- error_text
- Any
- ocr_image
- is_config_rejection
- Segment
- test_registry_no_confirmation_runs_immediately
- LoopGuard
- ._build_window
- test_registry_loads_extension_modules
- nexus/__init__.py
- video_translate.py
- build_app.sh
- _as_str
- nexus-voice
- ._finalize_user_turn
- FakeStream
- ._handle_message
- VideoTranslator
- PlaybackClock
- _ConfirmTracker
- CLAUDE.md
- AudioPlayer
- test_wake_dictation.py
- ._process_chunk
- Orb overlay page (orb.html)
- TaintTracker
- .tick
- build_ytdlp_cmd
- spoken_verdict
- AbstractEventLoop
- BaseException
- fixture
- Queue

## God Nodes (most connected - your core abstractions)
1. `GeminiLiveClient` - 72 edges
2. `MacOSController` - 62 edges
3. `ToolRegistry` - 62 edges
4. `VideoTranslator` - 55 edges
5. `WindowsController` - 50 edges
6. `AudioStreamer` - 50 edges
7. `NexusDesktopApp` - 46 edges
8. `make_client()` - 41 edges
9. `EventBus` - 35 edges
10. `WakeState` - 32 edges

## Surprising Connections (you probably didn't know these)
- `Confirmation card (TASDIQ KUTILMOQDA, Yes/No, TTL)` --shares_data_with--> `ConfirmationGate`  [INFERRED]
  ui/index.html → nexus/safety.py
- `Echo guard + playback prebuffer + low VAD start sensitivity` --rationale_for--> `AudioStreamer`  [INFERRED]
  README.md → nexus/audio_streamer.py
- `session.receive() ends each turn (not a disconnect)` --rationale_for--> `GeminiLiveClient`  [INFERRED]
  README.md → nexus/gemini_live_client.py
- `CommandGuard allow/deny/confirm tiers` --references--> `CommandGuard`  [EXTRACTED]
  README.md → nexus/macos_actions.py
- `ToolRegistry.execute flow: validate -> loop guard -> taint -> confirm -> handler` --references--> `ToolRegistry`  [EXTRACTED]
  README.md → nexus/tools/registry.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Tool execution safety pipeline** — readme_toolregistry_execute_flow, readme_loop_guard, readme_taint_guard, readme_commandguard_tiers, nexus_safety_confirmationgate [EXTRACTED 1.00]
- **Echo / self-hearing mitigation** — readme_echo_guard, reference_analysis_live_api_findings, nexus_audio_streamer_audiostreamer, nexus_audio_streamer_audioplayer [INFERRED 0.85]
- **WebSocket /ws event consumers** — readme_ui_event_contract, ui_index, ui_orb, nexus_events_eventbus [INFERRED 0.85]

## Communities (100 total, 16 thin omitted)

### Community 0 - "support.js"
Cohesion: 0.06
Nodes (75): boot(), bundledBlob(), cdnScriptFor(), collectProps(), compileAttr(), compileTemplate(), contentKey(), createComponentFactory() (+67 more)

### Community 1 - "file_actions.py"
Cohesion: 0.05
Nodes (67): csv, _append_csv(), _append_row_sync(), append_spreadsheet_row(), _append_xlsx(), _coerce_cell_value(), delete_file(), _fallback_path_is_sensitive() (+59 more)

### Community 2 - "ax_actions.py"
Cohesion: 0.07
Nodes (72): applicationservices, difflib, _actions(), activate_element(), _app_root(), _attr(), available(), _clean_text() (+64 more)

### Community 3 - "Result"
Cohesion: 0.06
Nodes (27): app_name(), BrowserController, BrowserDOMController, _fmt_time(), _js_error(), js_to_applescript(), normalize_url(), _parse_json() (+19 more)

### Community 4 - "GeminiLiveClient"
Cohesion: 0.23
Nodes (3): GeminiLiveClient, Final transkript bo'lagini darhol teradi; to'xtash iborasi rejimni tugatadi., Session resumption + context compression

### Community 5 - "make_client"
Cohesion: 0.06
Nodes (49): SimpleNamespace, _audio_part(), FakeLiveConnect, FakeSession, make_client(), _msg(), EventBus, 1011 'exceeded your current quota' → avval google_search grounding olib… (+41 more)

### Community 6 - "app.js"
Cohesion: 0.12
Nodes (58): answerConfirm(), applyDevices(), applySettings(), applySnapshot(), bind(), closeSocket(), connect(), ensureRow() (+50 more)

### Community 7 - "test_tools.py"
Cohesion: 0.08
Nodes (27): nexus_tools, _no_sleep(), MonkeyPatch, Tool qatlami testlari — real macOS tizimiga tegmaydi (osascript/subprocess…, Barcha ichki JS'lar AppleScript literaliga qo'yilganda qo'shtirnoq muvozanati…, ScriptRecorder, test_is_terminal_frontmost(), test_launch_app_uses_fuzzy_match() (+19 more)

### Community 8 - "EventBus"
Cohesion: 0.17
Nodes (6): CommandHandler, EventBus, AbstractEventLoop, Any, Queue, Thread-safe pub/sub. `publish` istalgan thread'dan chaqirilishi mumkin.

### Community 9 - "Nexus Ovoz OS README"
Cohesion: 0.16
Nodes (15): Nexus Ovoz OS README, Mic -> AudioStreamer -> GeminiLiveClient -> ToolRegistry -> EventBus -> UI pipeline, AXManualAccessibility for Chrome/Electron, Dictation mode (direct typing, stop phrases), .env settings (GEMINI_MODEL, VAD_THRESHOLD, WAKE_MODE, UI_PORT ...), EXTENSION_MODULES (TOOL_DECLARATIONS + HANDLERS), macOS permissions (Microphone, Accessibility, Screen Recording, Automation), Scripts: check_setup, benchmark_live, voice_picker (+7 more)

### Community 10 - "._build_handlers"
Cohesion: 0.05
Nodes (25): build_search_url(), web_search(), browser_click_button(), browser_click_selector(), browser_close_tab(), browser_current_page(), browser_list_tabs(), browser_open_url() (+17 more)

### Community 11 - "NexusDesktopApp"
Cohesion: 0.09
Nodes (8): _load_url(), NexusDesktopApp, Any, NSApplication delegati: oyna, orb, menyu bar, daemon ko'prigi., SIGINT/SIGTERM → toza chiqish. Mach-port orqali AppKit run loop'ida qayta…, Daemon thread'idan chaqiriladi — hodisani GUI thread'iga uzatadi., `.env` ni Finder'da ko'rsatadi (yagona "tashqi ochish" — brauzer emas)., NSObject

### Community 12 - "MacOSController"
Cohesion: 0.12
Nodes (8): _clamp(), MacOSController, Result, SSID ni aniqlaydi. macOS 14+ da Location Services ruxsatisiz SSID `<redacted>`…, macOS bilan ishlash: ovoz, media, ilovalar, Finder, tizim, terminal., Old oynadagi ilova terminal (Terminal/iTerm/Warp/...) bo'lsa True., macOS 12+ da DND uchun ochiq API yo'q. Foydalanuvchi yaratgan Shortcuts…, Faol oynaga matn kiritadi: bufer + Cmd+V (keystroke o'zbek/kirill matnni…

### Community 13 - "test_server.py"
Cohesion: 0.13
Nodes (19): fastapi_testclient, google-genai Client — hamma joyda bir xil sozlama bilan., Settings, TestClient, test_config_defaults_gemini38(), client(), _free_port(), fixture (+11 more)

### Community 14 - "desktop.py"
Cohesion: 0.13
Nodes (18): collections, collections_abc, importlib, json, Mikrofon oqimi va ovoz ijrosi (sounddevice / PortAudio). `AudioStreamer` —…, Brauzer boshqaruvi (Safari / Google Chrome) — AppleScript + sahifa ichidagi…, Desktop ilova qatlami: o'z oynasi, doim tepada turadigan orb va menyu bar…, Daemon ichidagi hodisalar shinasi (event bus). Barcha modullar (audio, gemini,… (+10 more)

### Community 15 - "state_style"
Cohesion: 0.22
Nodes (10): effective_state(), (rang, yorliq) — menyu bar / orb uchun., Menyu bar'dagi holat satri, masalan "● Tinglamoqda" yoki "● Kutmoqda (mikrofon…, Daemon holati + Gemini ulanishi + tasdiqdan bitta ko'rsatiladigan holat., state_style(), status_title(), parametrize, test_effective_state_priorities() (+2 more)

### Community 16 - "WindowsController"
Cohesion: 0.05
Nodes (32): fixture, nexus, path_is_sensitive(), Path, True — bu yerga yozish persistensiya yaratishi yoki sir sizdirishi mumkin., _press_key(), _ps_quote(), Any (+24 more)

### Community 17 - "screen_reader.py"
Cohesion: 0.12
Nodes (31): appkit, foundation, available(), capture_frontmost_window(), describe_screen(), _shoot(), _extract_text(), _front_app() (+23 more)

### Community 18 - "test_screen_reader.py"
Cohesion: 0.10
Nodes (14): Exception, _fake_client(), _FakeModels, Any, screen_reader (OCR + Gemini ko'rish) va ax_actions'dagi AX→OCR zaxira yo'li…, test_click_ui_element_by_ocr_index_from_cache(), test_describe_screen_default_question(), test_describe_screen_error_and_timeout() (+6 more)

### Community 19 - "ToolRegistry"
Cohesion: 0.07
Nodes (17): Handler, Any, Foydalanuvchi yangi gap boshladi: loop guard va taint tozalanadi., Foydalanuvchining yakuniy transkripti — og'zaki tasdiq uchun., Bajarilayotgan tool tasklarini bekor qiladi. Kutilayotgan tasdiq so'roviga…, ⌥⎋ / "kill_all": tool tasklar + kutilayotgan tasdiq bekor qilinadi, so'ng…, Handler javobini (tuple yoki dict) yagona formatga keltiradi., Bajarishdan OLDIN aniqlanadigan tasdiq sabablari (bo'sh — tasdiqsiz). (+9 more)

### Community 20 - "test_safety.py"
Cohesion: 0.13
Nodes (17): looks_read_only(), True — buyruq DANGEROUS_SHELL naqshlaridan biriga mos keladi., True — buyruq HECH QANDAY bayroq bilan ham hech narsani o'zgartira olmaydi., shell_is_dangerous(), parametrize, Xavfsizlik qatlami testlari: DANGEROUS_SHELL, looks_read_only,…, test_dangerous_shell_matches(), test_dangerous_shell_no_false_positive() (+9 more)

### Community 21 - "desktop_win.py"
Cohesion: 0.24
Nodes (9): DaemonRunner, DesktopOptions, Settings, Windows desktop qatlami: daemon alohida thread'da, UI — pywebview (Edge…, UI serveri tinglay boshlaguncha kutadi., run_desktop(), wait_for_port(), _wait_headless() (+1 more)

### Community 22 - "check_setup.py"
Cohesion: 0.30
Nodes (14): CDLL, check_accessibility(), check_automation(), check_devices(), check_key(), check_live(), check_mic_level(), check_packages() (+6 more)

### Community 23 - "test_core.py"
Cohesion: 0.06
Nodes (45): math, compute_rms(), echo_gate(), Yordamchi gapirayotganda mikrofon chunk'i o'tkazilsinmi? True = o'tkaz. Guard…, int16 mono PCM baytlaridan (rms 0..1, db -60..0) qaytaradi., Sezgirlik (0..1) → RMS bo'sag'asi. 1.0 = juda sezgir (past bo'sag'a)., sensitivity_to_threshold(), `extended-thinking` modelida daraja majburiy (bo'sh bo'lsa "high"); boshqa… (+37 more)

### Community 24 - "WakeState"
Cohesion: 0.09
Nodes (12): Yordamchi hozir unga gapirilayotganini kuzatadi., Yordamchi javobi savol bilan tugadimi — keyingi oyna uzunroq bo'ladi., `follow_up` — aniq tugatilganda oddiy follow-up oynasi qoladi (xayrlashuv…, Suhbat rejimi yoqilgan, lekin `conversation_idle_s` jimlikdan keyin tugashi…, Oynani yangilash — yordamchi hozirgina foydalanuvchi uchun nimadir qildi., Oyna ochiq bo'lsa, uni `ts` (monotonic) dan boshlab hisoblaydi — masalan…, WakeState, test_wake_conversation_window_and_expiry() (+4 more)

### Community 25 - "_registry"
Cohesion: 0.15
Nodes (13): MonkeyPatch, Handler `needs_confirmation` qaytarsa registry gate'ni so'raydi va…, _registry(), test_registry_confirmation_via_bus_utterance_command(), test_registry_confirmations_command_toggles(), test_registry_dictation_tools(), test_registry_handler_needs_confirmation_dict(), test_registry_kill_all_cancels_pending_confirmation() (+5 more)

### Community 26 - "DesktopPrefs"
Cohesion: 0.08
Nodes (17): DesktopOptions, DesktopPrefs, _env_true(), _make_app_icon(), _pair(), Path, Desktop ilovani ishga tushiradi (asosiy thread'da bloklaydi). Qaytadi: chiqish…, argparse Namespace (nexus.main.build_parser) → DesktopOptions. (+9 more)

### Community 27 - "ws_reconnect_harness.js"
Cohesion: 0.12
Nodes (9): ref_fs, byId(), els, FakeWS, fs, listeners, makeEl(), sockets (+1 more)

### Community 28 - "create_app"
Cohesion: 0.14
Nodes (7): create_app(), index(), Path, FastAPI ilovasini yaratadi (testlarda ham shu ishlatiladi)., Tasdiq kutayotgan run_tool shu soketdan keladigan "confirm" ni to'sib…, test_confirm_request_push_and_confirm_cmd(), test_ws_slow_command_does_not_block_following_commands()

### Community 29 - "web_answer.py"
Cohesion: 0.30
Nodes (13): inspect, build_request(), _create(), extract_sources(), extract_text(), _get(), _make_client(), Any (+5 more)

### Community 30 - "ConfirmationGate"
Cohesion: 0.20
Nodes (6): ConfirmationGate, _consume(), PendingConfirmation, Bir vaqtda faqat bitta faol tasdiq so'rovi. Yangi so'rov eskisini bekor qiladi., Foydalanuvchining yakuniy transkripti. So'rovdan OLDIN aytilgan gap hisobga…, Bus'dagi TRANSCRIPT (user, final) hodisalarini ham kuzatadi — gemini client…

### Community 31 - "name_in"
Cohesion: 0.16
Nodes (15): _candidates(), levenshtein(), name_in(), Levenshtein masofasi; `limit` berilsa undan oshgach hisoblashni to'xtatadi…, (nomzod, boshlanish indeksi, so'zlar soni) — yakka so'zlar va qo'shni…, Matnda ism (yumshoq moslik bilan) bormi?, Matndan ismni (va oldidagi "hey/salom/ey" kabi undovni) olib tashlaydi. Asl…, strip_name() (+7 more)

### Community 32 - "AudioStreamer"
Cohesion: 0.06
Nodes (24): AbstractEventLoop, AudioStreamer, _list_devices(), _mute(), _playback(), _ptt(), _ptt_press(), _sensitivity() (+16 more)

### Community 33 - "benchmark_live.py"
Cohesion: 0.33
Nodes (8): all_declarations(), build_config(), main(), passed(), Model qaysi toolni tanlashini real Gemini Live sessiyasida o'lchash (toollar…, Asosiy sxemalar + kengaytma modullari (nomlar bo'yicha takrorsiz)., Bitta buyruq: (chaqirilgan toollar [{name,args}], aytilgan matn, navbatlar…, run_case()

### Community 34 - "CommandGuard"
Cohesion: 0.15
Nodes (12): CommandGuard, Buyruqni qo'riqchi orqali bajaradi. `confirmed=True` — registry foydalanuvchi…, `run_terminal_command` uchun uch pog'onali qo'riqchi. `check()` → ("allow" |…, Tekshiruvdan o'tgan buyruqni bajarish uchun argv (`~` kengaytirilgan holda)., _truncate(), parametrize, test_guard_allows(), test_guard_argv_expands_tilde() (+4 more)

### Community 36 - "DaemonRunner"
Cohesion: 0.18
Nodes (5): DaemonRunner, `nexus.main.run()` ni alohida thread'da o'z event loop'i bilan yuritadi., To'xtatish signalini beradi (bloklamaydi) — tugashini `finished` orqali…, To'xtatish signalini beradi va thread tugashini kutadi. True = toza tugadi., GUI'dan daemon'ga buyruq (thread-safe, natija kutilmaydi).

### Community 38 - "config.py"
Cohesion: 0.11
Nodes (24): dotenv, api_key_env_path(), api_key_hint(), _describe_char(), env_candidates(), load_env_files(), load_extra_env(), _project_env() (+16 more)

### Community 39 - "run"
Cohesion: 0.11
Nodes (19): Event, check_environment(), _first(), MetricsTicker, platform_controller(), print_banner(), Any, EventBus (+11 more)

### Community 40 - "vision_box_to_screen"
Cohesion: 0.50
Nodes (4): Vision normalizatsiyalangan bbox (0..1, y PASTDAN) → ekran (x, y, w, h),…, vision_box_to_screen(), test_vision_box_bottom_line_lands_at_window_bottom(), test_vision_box_to_screen_flips_y_and_offsets_by_window()

### Community 41 - "FakeAudio"
Cohesion: 0.10
Nodes (12): GeminiConfigError, Konfiguratsiya xatosi (masalan, API kaliti yo'q)., RuntimeError, FakeAudio, FakeRegistry, test_background_voice_does_not_cut_addressed_reply(), test_build_config_ptt_disables_vad_and_optional_fields(), test_conversation_command_and_idle_tick() (+4 more)

### Community 42 - "._evaluate_addressed"
Cohesion: 0.18
Nodes (5): Oxirgi real audio chunk karnayga chiqqan payt (time.monotonic; 0 — hali yo'q)., Registry gate'ida (ConfirmationGate) hal qilinmagan tasdiq so'rovi bormi?, Wake rejimi bo'yicha gap bizga qaratilganmi (qisman transkriptda ham). Baho…, Yo'q / hech narsa kerak emas" rad javobi sifatida qaralsinmi? Suhbat rejimida…, Joriy gap boshlangan payt (AudioStreamer RMS gate). Noma'lum yoki eskirgan…

### Community 43 - "is_quota_error"
Cohesion: 0.50
Nodes (4): is_quota_error(), BaseException, Kalit kvotasi (bir vaqtdagi sessiyalar soni yoki kunlik limit) tugadi., test_is_quota_error()

### Community 44 - "test_desktop.py"
Cohesion: 0.08
Nodes (30): ArgumentParser, Namespace, _env_api_key(), is_placeholder_api_key(), Kalit; namunaviy (placeholder) qiymat bo'lsa bo'sh qaytaradi., `base_url/health` 2xx qaytarguncha kutadi. `keep_waiting()` False qaytarsa…, wait_for_server(), build_parser() (+22 more)

### Community 45 - "macos_actions.py"
Cohesion: 0.11
Nodes (24): ctypes, datetime, logging, _fmt_uptime(), installed_apps(), is_terminal_app(), match_app(), hits() (+16 more)

### Community 46 - "_bus"
Cohesion: 0.22
Nodes (12): Queue, _bus(), _drain(), EventBus, Gemini client note_utterance'ni chaqirmasa ham, bus'dagi TRANSCRIPT (user,…, test_gate_listens_to_bus_transcripts(), test_gate_new_request_cancels_old(), test_gate_timeout() (+4 more)

### Community 47 - "Any"
Cohesion: 0.26
Nodes (6): _key_hint(), Any, EventBus, Path, UI (Sozlamalar) dan API kalit: tekshiradi, saqlaydi va sessiyani yangi kalit…, _to_function_declarations()

### Community 48 - ".run"
Cohesion: 0.21
Nodes (3): Cheksiz ulanish sikli; `stop()` chaqirilguncha qayta ulanaveradi., Kalit Sozlamalardan (`set_api_key`) kiritilguncha yoki `stop()` gacha kutadi., `timeout` sekund (None — cheksiz) kutadi; `stop()` yoki yangi API kalit…

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
Cohesion: 0.11
Nodes (12): contextlib, errno, FastAPI, fastapi_responses, fastapi_staticfiles, _QuietServer, UI ko'prigi: FastAPI + WebSocket server. EventBus hodisalarini brauzerdagi UI…, Signal handlerlarini o'rnatmaydigan uvicorn Server (signalni main.py… (+4 more)

### Community 53 - "test_video_translate.py"
Cohesion: 0.08
Nodes (25): build_ffmpeg_cmd(), find_tab_script(), player_setup_js(), AppleScript: JS ni video tabida bajaradi — Chrome'da `tab_id` bo'yicha (bir xil…, AppleScript (Chrome): `video_id` ochiq tabni topib oldinga chiqaradi va id sini…, Pleyer: asl ovozni o'chirish/pasaytirish (0..1, manfiy — tegilmaydi) va ijro…, stop_video_translation(), translator_instruction() (+17 more)

### Community 54 - "DictationState"
Cohesion: 0.17
Nodes (6): DictationState, (teriladigan matn, to'xtash kerakmi). "…hammasi shu, to'xta" → ("…hammasi shu",…, Diktovka holati va terilgan matn hisobi., split_stop(), test_dictation_state_lifecycle(), test_split_stop()

### Community 55 - "main.py"
Cohesion: 0.14
Nodes (15): argparse, asyncio, Nexus Ovoz OS — CLI kirish nuqtasi (`nexus` buyrug'i). nexus # desktop ilova:…, main(), Path, Gemini ovozlarini o'zbekcha namunaviy jumla bilan tinglab tanlash.…, render(), save_wav() (+7 more)

### Community 56 - "fake_screen"
Cohesion: 0.40
Nodes (5): ax_ready(), fake_screen(), fixture, MonkeyPatch, Skrinshot/JPEG bosqichini almashtiradi: real screencapture chaqirilmaydi.

### Community 57 - "._dispatch"
Cohesion: 0.20
Nodes (6): is_silent(), turn_complete kelmay qolgan sessiyani bo'shatadi (model jim qoldi)., Bo'lak deyarli jim (o'rtacha RMS `SILENT_RMS` dan past)., Tayinlanmagan bo'laklarni (FIFO) bo'sh sessiyalarga beradi., Sessiya bo'shadi — navbatdagi bo'lakni olishi mumkin., test_silent_segment_is_not_sent()

### Community 58 - "looks_like_command"
Cohesion: 0.18
Nodes (7): looks_like_command(), SMART rejimi uchun evristika: qisqa gap + buyruq so'zi., Oxirgi chaqiruvdan keyingi oyna (follow-up yoki suhbat) hali ochiqmi?, Oyna `at` (monotonic; odatda gap BOSHLANGAN payt) da ochiq edimi? None — hozir.…, Matnda ism bormi? Bo'lsa follow-up oynasi ochiladi., Bu gapga javob berish kerakmi? (ism eshitilsa oynani ham ochadi). `at` — gap…, test_looks_like_command()

### Community 59 - "_recognize"
Cohesion: 0.33
Nodes (6): pick_languages(), Qo'llab-quvvatlanadigan tillardan kerakli tartibda tanlaydi ("uz" → "uz-UZ"…, Vision OCR: [(text, nx, ny, nw, nh, confidence)] — normalizatsiyalangan, y…, _recognize(), supported_languages(), test_pick_languages_prefers_uz_then_ru_en_and_skips_missing()

### Community 60 - "feed_action"
Cohesion: 0.67
Nodes (3): feed_action(), Navbatdagi chunk bilan nima qilish: "resync" | "wait" | "send". Audio videodan…, test_feed_action()

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
Cohesion: 0.14
Nodes (13): attach(), parse_player_state(), Any, main.py: bus/settings/mikrofonni ulaydi; echo guard tarjima ijrosini ham…, Bitta Live sessiya: navbatdagi bo'lakni oladi, javobini bo'lakka yozadi., Parallel sessiyalar + dispetcher + tartibli ijro., Sessiya uzildi: joriy bo'lak yakunlangan deb belgilanadi, o'zi bo'sh ro'yxatdan…, Model javobini sessiyaning joriy bo'lagiga yozadi. True — navbat tugadi… (+5 more)

### Community 68 - "ocr_image"
Cohesion: 0.17
Nodes (17): Box, _image_size(), lines_as_elements(), lines_to_text(), ocr_image(), Satrlarni yuqoridan pastga, bir qatordagilarni chapdan o'ngga tartiblaydi. Ikki…, Tartiblangan satrlardan matn: bir qatordagilar ikki bo'shliq bilan, qatorlar…, OCR satrlarini list_ui_elements formatiga o'giradi: {n, role:'text', label, at,… (+9 more)

### Community 69 - "is_config_rejection"
Cohesion: 0.29
Nodes (7): BaseException, is_api_key_error(), is_config_rejection(), Server kalitni rad etdimi (noto'g'ri / bekor qilingan API kalit)?, Server konfiguratsiyani rad etgan bo'lsa navbatdagi modelga bog'liq maydonni…, Server konfiguratsiyani rad etdimi (WebSocket 1007 / invalid argument), kalit…, test_is_config_rejection()

### Community 70 - "Segment"
Cohesion: 0.16
Nodes (11): fit_tempo(), Bo'laklarni `seq` tartibida, video o'z oralig'iga (`src_start`) yetganda ijroga…, Javob bermagan bo'lakni navbat boshiga qaytaradi — boshqa (bo'sh) sessiya oladi., Tarjima ulgurmayapti (masalan, kvota kam — sessiyalar yetmaydi): gapni tashlab…, Tarjima (`out_s`) videodagi qolgan oralig'iga (`window_s`) sig'ishi uchun…, Tarjima bo'lagi: kiruvchi audio (tayinlanguncha `buf`da) va modelning javobi…, activity_end dan keyin `no_response_s` ichida audio kelmadi — ijroda o'tkazib…, Segment (+3 more)

### Community 71 - "test_registry_no_confirmation_runs_immediately"
Cohesion: 0.29
Nodes (3): test_registry_no_confirmation_runs_immediately(), test_registry_tainted_turn_requires_confirmation(), read_page()

### Community 72 - "LoopGuard"
Cohesion: 0.20
Nodes (7): LoopGuard, Any, Bir navbatda haddan ko'p yoki bir xil chaqiruvlarni to'xtatadi., None — davom et; matn — rad etish sababi (modelga tushuntirish)., test_loop_guard_identical_calls(), test_loop_guard_max_calls_per_turn(), test_loop_guard_non_consecutive_identical_calls()

### Community 73 - "._build_window"
Cohesion: 0.14
Nodes (16): default_orb_origin(), default_window_frame(), _hex_color(), _make_webview(), placeholder_html(), Oyna/orb hech bo'lmaganda `min_visible`×`min_visible` qismi bilan biror ekranda…, Ekranning pastki-o'ng burchagi (Dock/menyu bar hisobga olingan `visibleFrame`…, Ekran o'rtasida, `visibleFrame`ning `fraction` (90%) qismi (yoki `size`), min… (+8 more)

### Community 76 - "video_translate.py"
Cohesion: 0.12
Nodes (23): dataclasses, itertools, normalize_browser(), Diktovka rejimi: foydalanuvchi gapiradi — yordamchi teradi, to'xtash…, compute_backoff(), Gemini Multimodal Live API (WebSocket) sessiyasi. Ikki parallel task:…, base * 2**attempt + jitter, max_delay bilan cheklangan. `jitter` None bo'lsa…, YouTube videosini jonli (sinxron) ovozli tarjima: ingliz → o'zbek. Oqim: yt-dlp… (+15 more)

### Community 78 - "_as_str"
Cohesion: 0.22
Nodes (6): _as_str(), Any, Python qiymatini AppleScript satr literaliga (qo'shtirnoq ichida) xavfsiz…, cmd+shift+4' → AppleScript. `(script, xato)` qaytaradi., test_as_str_escapes_quotes_and_backslashes(), test_hotkey_script_builder()

### Community 81 - "._finalize_user_turn"
Cohesion: 0.22
Nodes (3): UI dan matn buyrug'i. Sessiya yo'q bo'lsa False., Registry'ga foydalanuvchi navbatini bildiradi: og'zaki tasdiq (note_utterance)…, Suhbat rejimi: ismsiz erkin suhbat; jimlikdan keyin o'zi tugaydi (`tick`).

### Community 84 - "VideoTranslator"
Cohesion: 0.13
Nodes (11): AppleScript'ni `osascript` orqali bajaradi (stdin orqali, argument uzunligi…, run_applescript(), Process, `pos` dan `ahead` soniya oldinga tarjima tayyormi: ijroga qo'yilgan, yoki…, Video pauza, tarjima ovozi esa davom etadi — `seconds` dan keyin video qayta…, Buferlash: video pauzada turadi, oldinda `GATE_AHEAD_S` tarjima tayyor bo'lgach…, JS ni video ochilgan tabda bajaradi (faol tab emas — foydalanuvchi boshqa tabga…, Pleyer holatini kuzatadi; tab boshqa sahifaga o'tsa yoki video tugasa — tugaydi. (+3 more)

### Community 85 - "PlaybackClock"
Cohesion: 0.10
Nodes (14): find_binary(), is_junk_translation(), PlaybackClock, PATH + Homebrew papkalari (.app ichidan ishga tushganda PATH qisqa bo'ladi)., Model tarjima o'rniga yorliq/izoh aytdi (`(Uzbek translation: …)`, `<no…, Brauzer pleyeri holatidan joriy video vaqtini baholaydi (so'rovlar orasida…, s16le mono PCM ni ohangini saqlab `tempo` barobar tezlashtiradi (ffmpeg…, time_stretch() (+6 more)

### Community 88 - "AudioPlayer"
Cohesion: 0.10
Nodes (14): AudioPlayer, parse_latency(), EventBus, high"/"low" yoki sekund (str/float) → sounddevice `latency` argumenti., 24 kHz int16 mono ijro. `enqueue` istalgan thread/task'dan chaqirilishi mumkin.…, Buferdagi qolgan audioni (prebuffer to'lmagan bo'lsa ham) ijroga qo'yib…, Navbatni tozalaydi (interruption). Tashlangan chunklar sonini qaytaradi., test_parse_latency() (+6 more)

### Community 91 - "test_wake_dictation.py"
Cohesion: 0.16
Nodes (13): is_stop_phrase(), Butun gap faqat to'xtash iborasidan iboratmi?, Qisqa ism aniq mos kelishi kerak; uzunroq ism 2-3 xatoni ko'taradi., tolerance(), clock(), fixture, Wake (ism bilan chaqirish) va diktovka mantiqi testlari., test_is_stop_phrase() (+5 more)

### Community 93 - "._process_chunk"
Cohesion: 0.20
Nodes (6): gate_open(), Callback thread'da: darajani hisoblaydi, gate'ni yangilaydi, navbatga qo'yadi.…, Yordamchi buyruq ustida ishlayaptimi (o'ylayapti / tool bajaryapti /…, Yordamchi javobi paytida mikrofon to'liq bostirilsinmi?, Chunk Gemini'ga yuborilsinmi? (mute yoki PTT bosilmagan bo'lsa — yo'q)., should_forward()

### Community 94 - "Orb overlay page (orb.html)"
Cohesion: 0.21
Nodes (12): Desktop layer (pure pyobjc NSWindow + WKWebView, orb NSPanel, menu bar), Orb overlay (floating non-activating NSPanel), UI -> daemon commands (mute, ptt, confirm, kill_all, text, wake_mode, dictation...), UI event contract ({type, ts, data} over /ws), Old ui_overlay state colors, Orb overlay page (orb.html), Orb state COLORS/LABELS map, connect() WebSocket with exponential retry (+4 more)

### Community 97 - "TaintTracker"
Cohesion: 0.08
Nodes (24): Nexus Ovoz OS design mockup (dc.html), Design mockup Component (simulated PTT command flow), Local models concept (Whisper.cpp small.uz + Qwen 7B Q4), Navbat ichida tashqi matn o'qilganini eslab qoladi., TaintTracker, CommandGuard allow/deny/confirm tiers, Echo guard + playback prebuffer + low VAD start sensitivity, Gemini Live API (native audio, WebSocket) (+16 more)

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
- **15 isolated node(s):** `nexus-voice`, `Session resumption + context compression`, `EXTENSION_MODULES (TOOL_DECLARATIONS + HANDLERS)`, `macOS permissions (Microphone, Accessibility, Screen Recording, Automation)`, `Scripts: check_setup, benchmark_live, voice_picker` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 610 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Gemini Live API (native audio, WebSocket)` and `Local models concept (Whisper.cpp small.uz + Qwen 7B Q4)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `ToolRegistry` connect `ToolRegistry` to `TaintTracker`, `Result`, `run`, `LoopGuard`, `Nexus Ovoz OS README`, `._build_handlers`, `test_registry_loads_extension_modules`, `MacOSController`, `test_registry_no_confirmation_runs_immediately`, `desktop.py`, `test_tools.py`, `WindowsController`, `test_core.py`, `test_safety.py`, `test_video_translate.py`, `main.py`, `_registry`, `ConfirmationGate`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Why does `GeminiLiveClient` connect `GeminiLiveClient` to `AudioStreamer`, `TaintTracker`, `.tick`, `is_config_rejection`, `make_client`, `run`, `Nexus Ovoz OS README`, `._evaluate_addressed`, `FakeAudio`, `video_translate.py`, `Any`, `.run`, `._finalize_user_turn`, `._handle_message`, `test_core.py`, `WakeState`, `._handle_server_content`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `NexusDesktopApp` connect `NexusDesktopApp` to `._build_window`, `test_desktop.py`, `test_server.py`, `desktop.py`, `DesktopPrefs`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `GeminiLiveClient` (e.g. with `WakeState` and `run()`) actually correct?**
  _`GeminiLiveClient` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `ToolRegistry` (e.g. with `MacOSController` and `ConfirmationGate`) actually correct?**
  _`ToolRegistry` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `VideoTranslator` (e.g. with `AudioPlayer` and `BrowserController`) actually correct?**
  _`VideoTranslator` has 2 INFERRED edges - model-reasoned connections that need verification._