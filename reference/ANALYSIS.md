# reference/AI tahlili — eski "Voice Assistant" (Gemini Live, ~7100 qator)

Sana: 2026-09-21. Manba: `reference/AI/`. (Tahlilchi agent hisoboti, PM tomonidan saqlangan.)

## 1. Arxitektura
Oqim: main.py → LiveSession (gemini_live.py) → mic/screen `send_realtime_input` → `receive()` → tool dispatch (tool_handlers.py, 30 tool): loop guard → CommandGate (decisions.py) → WakeState (wake.py) → taint guard → ConfirmationGate (safety.py) → handler. PyQt orb (ui_overlay.py), admin panel, roles.json, secrets_store (.env).

## 2. Gemini Live API — muhim topilmalar
- LiveConnectConfig: AUDIO modality; `input_audio_transcription(language_codes=["uz-UZ","ru-RU","en-US"])`; VAD: `RealtimeInputConfig(automatic_activity_detection(start=LOW, end=HIGH, prefix_padding_ms=150, silence_duration_ms=500))` (HIGH start o'z ovozini eshitadi); `session_resumption(handle)`; `context_window_compression(sliding_window)`; `media_resolution HIGH`; `enable_affective_dialog` → 1007/1011 xato, O'CHIQ; TEXT modality → 1007.
- `session.receive()` HAR navbat tugaganda to'xtaydi — bu uzilish EMAS. `while not stop: received=False; async for ...; if not received: break`.
- `generation_complete` → play_out (prebuffer). `interrupted` → speaker.clear().
- Ephemeral token: `client.aio.auth_tokens.create(...)`, `http_options api_version=v1alpha`.
- Reconnect: mic ulanishdan oldin mute, ulangach drain+unmute; sessiya <5s yashasa resume handle tashlanadi.
- Tool bilan tugagan navbatdan keyin model reaksiyasi KEYINGI receive() iteratsiyasida keladi.

## 3. Eski toollar (Nexus'da yo'q bo'lganlar)
write_note, append_spreadsheet_row, set_spreadsheet_cell, read_spreadsheet, write_file, read_file, list_directory, delete_file, list_applications, click/scroll/move_mouse/drag (koordinata), list_ui_elements, click_ui_element, read_screen_text, list_menus, menu_command, start/stop_dictation, look_at_screen.
Registry qoidalari: CHANGES_THE_SCREEN, NEEDS_TO_BE_ADDRESSED, INGESTS_EXTERNAL_CONTENT → tainted, EXFIL_OR_EXECUTE, MAX_CALLS_PER_TURN=15, MAX_IDENTICAL_CALLS=3.

## 4. Qo'shimcha modullar
- wake.py — transkriptda ismni Levenshtein bilan qidirish (ALWAYS/NAME/SMART, 25s follow-up). P1.
- screen_stream.py — screencapture→grid+AX belgi→JPEG→video Blob (ondemand/continuous). P2.
- dictation.py — diktovka rejimi, stop iboralar. P1.
- decisions.py — tashqi SaaS qaror qatlami. P2 (kerak emas).
- safety.py — ConfirmationGate (og'zaki "ha", token TTL 60s, AFFIRMATIVE/NEGATIVE regex), DANGEROUS_SHELL, looks_read_only, path_is_sensitive, redact_secrets. P0.
- ui_elements.py — macOS AX API (AXManualAccessibility, MAX_DEPTH 40). P1.
- ui_overlay.py — holat ranglari: connecting #6b7280, listening #22c55e, thinking #f59e0b, speaking #06b6d4, dictating #a855f7, error #ef4444.
- benchmark.py (24 o'zbekcha buyruq), check_setup.py, voice_picker.py (Autonoe tanlangan).

## 5. Mahsulot talablari
Hands-free, o'zbekcha javob (uz/ru/en kirish), iliq qisqa uslub, barge-in, to'liq kompyuter boshqaruvi (allowlist = tez yo'l, qolgani tasdiq bilan), Excel/eslatma/fayl, diktovka, ism bilan chaqirish, orb overlay.
Bo'lgan muammolar: echo (VAD LOW + echo guard + prebuffer 220ms), har 10s reconnect (receive semantikasi), 10 min uzilish (resumption/compression), pyautogui o'zbekni buzadi (clipboard+Cmd+V), model bir joyni qayta bosadi (loop guard), Chrome AX bo'sh (AXManualAccessibility).

## 6. Eski koddagi xatolar (takrorlamaslik)
Tool receive loop'ni bloklaydi; read_file redakt/yo'l cheklovsiz; ikki koordinata fazosi; taint klik toollarini qamramaydi; AFFIRMATIVE juda keng (`ok`, `ha`); diktovka model navbatidan keyin teriladi; run_shell killpg yo'q; check_setup kalitni chop etadi.

## 7. Reja
P0: session_resumption+go_away+compression; VAD+language_codes; receive() semantikasi; echo guard+prebuffer+pre-connect mute; type_text clipboard; loop guard; ConfirmationGate; CommandGuard kengaytmasi; taint guard; system instruction qoidalari.
P1: AX toollar; fayl/Excel toollar; ism (wake); diktovka; fuzzy launch_app; UI holatlari; benchmark; check_setup; interrupted→tool cancel.
P2: ekran ko'rish; ephemeral token; sozlamalar paneli; voice_picker.
