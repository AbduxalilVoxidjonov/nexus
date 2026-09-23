#!/bin/zsh
# Nexus Ovoz OS — Finder'da ikki marta bosib ishga tushirish.
# Desktop rejim: o'z oynasi + ekranda doim tepada turadigan orb + menyu bar ikonkasi (brauzer OCHILMAYDI).
cd "$(dirname "$0")" || exit 1

pause() { echo; [[ -t 0 ]] && read "?Yopish uchun Enter bosing."; return 0; }

# Allaqachon ishlayaptimi? (faqat haqiqiy daemon jarayoni: `python -m nexus.main` yoki `.venv/bin/nexus`)
NEXUS_PGREP='(python[^ ]* -m nexus\.main|/bin/nexus(-desktop)?)( |$)'
running=$(pgrep -f "$NEXUS_PGREP" | head -1)
if [[ -n "$running" ]]; then
  echo "Nexus allaqachon ishlayapti (pid $running)."
  echo "To'xtatish: menyu bar → ◉ → Chiqish, yoki stop.command"
  pause
  exit 0
fi

# Virtual muhit
if [[ ! -x .venv/bin/python ]]; then
  if ! command -v uv >/dev/null 2>&1; then
    echo "XATO: 'uv' topilmadi. O'rnating: https://docs.astral.sh/uv/  (curl -LsSf https://astral.sh/uv/install.sh | sh)"
    pause
    exit 1
  fi
  echo "Virtual muhit yaratilmoqda (.venv, Python 3.13)..."
  uv venv --python 3.13 || { echo "XATO: uv venv muvaffaqiyatsiz."; pause; exit 1; }
  uv pip install -e . || { echo "XATO: paketlar o'rnatilmadi."; pause; exit 1; }
fi

# .env
if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    cp .env.example .env
    echo "DIQQAT: .env yaratildi — GEMINI_API_KEY ni yozing (https://aistudio.google.com/apikey),"
    echo "        so'ng start.command ni qayta ishga tushiring."
    echo "        Fayl: $(pwd)/.env"
    pause
    exit 0
  else
    echo "XATO: .env ham, .env.example ham topilmadi."
    pause
    exit 1
  fi
fi

# GEMINI_API_KEY: bo'sh yoki namunaviy (your_api_key_here, SIZNING_API_KEY, ...) bo'lsa — dastur ishga tushmaydi
api_key=$(grep -E '^[[:space:]]*(export[[:space:]]+)?GEMINI_API_KEY=' .env | tail -1 | sed -E 's/^[^=]*=//; s/^[[:space:]]+//; s/[[:space:]]+$//; s/^"(.*)"$/\1/; s/^'"'"'(.*)'"'"'$/\1/')
key_lc=$(printf '%s' "$api_key" | tr '[:upper:]' '[:lower:]')
case "$key_lc" in
  ""|your_api_key_here|sizning_api_key|sizning_api_kalitingiz|changeme|your_*|sizning_*)
    echo "XATO: .env faylida GEMINI_API_KEY yo'q yoki namunaviy qiymat (\"${api_key:-bo'sh}\")."
    echo "      Haqiqiy kalitni https://aistudio.google.com/apikey dan olib, .env fayliga yozing:"
    echo "        GEMINI_API_KEY=AIza..."
    echo "      Fayl: $(pwd)/.env"
    echo "      Kalit yozilgach start.command ni qayta ishga tushiring."
    pause
    exit 1
    ;;
esac

echo "Nexus Ovoz OS ishga tushmoqda..."
echo "To'xtatish: menyu bar → ◉ → Chiqish (yoki Cmd+Q, yoki stop.command)"
echo
exec .venv/bin/python -m nexus.main "$@"
