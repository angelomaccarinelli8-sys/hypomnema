#!/bin/bash
# Aggiorna il programma sul server e riavvia (0.11.0, seconda parte). I taccuini stanno in /srv/hypomnema:
# l'aggiornamento non li tocca.   $1 = il ramo (di solito main)
set -euo pipefail
ramo="${1:-main}"
git -C /opt/hypomnema fetch -q origin "$ramo"
git -C /opt/hypomnema checkout -q -B "$ramo" "origin/$ramo"
git -C /opt/hypomnema log -1 --format='Programma aggiornato a: %h %s'
if systemctl is-enabled -q hypomnema 2>/dev/null; then
  systemctl restart hypomnema
  sleep 2
  systemctl is-active hypomnema
fi
