#!/bin/zsh
# Nexus Ovoz OS — Finder'da ikki marta bosib to'xtatish.
cd "$(dirname "$0")" || exit 1

NEXUS_PGREP='(python[^ ]* -m nexus\.main|/bin/nexus(-desktop)?)( |$)'
pids=$(pgrep -f "$NEXUS_PGREP")
if [[ -z "$pids" ]]; then
  echo "Nexus ishlamayapti."
else
  echo "To'xtatilmoqda (pid: ${pids//$'\n'/ })..."
  echo "$pids" | while read -r pid; do kill -INT "$pid" 2>/dev/null; done   # SIGINT → toza yopilish
  for _ in 1 2 3 4 5 6; do
    sleep 0.5
    [[ -z "$(pgrep -f "$NEXUS_PGREP")" ]] && break
  done
  left=$(pgrep -f "$NEXUS_PGREP")
  if [[ -n "$left" ]]; then
    echo "3 s ichida tugamadi — majburan to'xtatilmoqda (SIGKILL)."
    echo "$left" | while read -r pid; do kill -9 "$pid" 2>/dev/null; done
  fi
  echo "To'xtatildi."
fi
echo
[[ -t 0 ]] && read "?Yopish uchun Enter bosing."
exit 0
