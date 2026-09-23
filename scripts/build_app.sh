#!/bin/zsh
# "dist/Nexus Ovoz OS.app" — PyInstaller bilan mustaqil .app (ixtiyoriy; asosiy yo'l — start.command).
#   .venv/bin/python -m pip install pyinstaller   yoki   uv pip install -e ".[dev]"
#   zsh scripts/build_app.sh
# Muhit: NEXUS_HIDE_DOCK=true → Info.plist'ga LSUIElement (faqat menyu bar, Dock'da ko'rinmaydi).
set -euo pipefail
cd "$(dirname "$0")/.."

APP_NAME="Nexus Ovoz OS"
PY=.venv/bin/python
if ! "$PY" -c "import PyInstaller" 2>/dev/null; then
  echo "pyinstaller yo'q — o'rnatilmoqda (dev dependency)..."
  uv pip install --python "$PY" pyinstaller
fi

ICON_ARGS=()
if [[ -f assets/nexus.icns ]]; then
  ICON_ARGS=(--icon assets/nexus.icns)
fi

rm -rf build "dist/$APP_NAME.app" "$APP_NAME.spec"
"$PY" -m PyInstaller \
  --noconfirm --windowed --name "$APP_NAME" \
  --add-data "ui:ui" \
  --add-data ".env.example:." \
  --collect-submodules nexus \
  --collect-submodules google.genai \
  --hidden-import nexus.desktop \
  --hidden-import AppKit --hidden-import WebKit --hidden-import Foundation --hidden-import Quartz \
  --hidden-import objc --hidden-import PyObjCTools.MachSignals \
  --hidden-import sounddevice --hidden-import _sounddevice_data \
  --hidden-import uvicorn.loops.asyncio --hidden-import uvicorn.protocols.http.h11_impl \
  --hidden-import uvicorn.protocols.websockets.websockets_impl --hidden-import uvicorn.lifespan.off \
  "${ICON_ARGS[@]}" \
  nexus/main.py

PLIST="dist/$APP_NAME.app/Contents/Info.plist"
PB=/usr/libexec/PlistBuddy
"$PB" -c "Add :NSMicrophoneUsageDescription string 'Nexus ovozli buyruqlarni eshitish uchun mikrofonga muhtoj.'" "$PLIST" 2>/dev/null || \
"$PB" -c "Set :NSMicrophoneUsageDescription 'Nexus ovozli buyruqlarni eshitish uchun mikrofonga muhtoj.'" "$PLIST"
"$PB" -c "Add :NSAppleEventsUsageDescription string 'Nexus ilovalarni boshqarish uchun Automation (AppleScript) ruxsatiga muhtoj.'" "$PLIST" 2>/dev/null || \
"$PB" -c "Set :NSAppleEventsUsageDescription 'Nexus ilovalarni boshqarish uchun Automation (AppleScript) ruxsatiga muhtoj.'" "$PLIST"
"$PB" -c "Add :NSAppleMusicUsageDescription string 'Media boshqaruvi.'" "$PLIST" 2>/dev/null || true
"$PB" -c "Add :NSHighResolutionCapable bool true" "$PLIST" 2>/dev/null || true
"$PB" -c "Add :CFBundleDisplayName string '$APP_NAME'" "$PLIST" 2>/dev/null || true
if [[ "${NEXUS_HIDE_DOCK:-}" == "true" ]]; then
  "$PB" -c "Add :LSUIElement bool true" "$PLIST" 2>/dev/null || "$PB" -c "Set :LSUIElement true" "$PLIST"
fi

# Ad-hoc imzo (Gatekeeper uchun emas — TCC ruxsatlari barqaror bo'lishi uchun)
codesign --force --deep --sign - "dist/$APP_NAME.app" 2>/dev/null || echo "codesign o'tkazib yuborildi"

echo
echo "Tayyor: dist/$APP_NAME.app"
echo "Eslatma: .app o'z ichida .env o'qiydi — ishga tushirishdan oldin loyiha papkasidagi .env ni"
echo "         ~/.nexus/.env yoki dist/$APP_NAME.app/Contents/Resources/.env ga nusxalang."
