#!/bin/bash
# Carica la lista delle etichette in un taccuino online (0.11.0, seconda parte). Lo lancia carica-etichette.ps1 con
# «az vm run-command». La lista la scrive l'utente; il programma la ricontrolla qui, con le stesse regole dello
# sportello, e non scrive mai sopra una lista con dentro qualcosa senza la conferma: la lista di prima resta accanto.
#   $1 = il nome del taccuino   $2 = la lista, in base64   $3 = «sostituisci» per confermare, altrimenti «no»
set -euo pipefail
cd /srv/hypomnema
temporaneo=$(sudo -u hypomnema mktemp -p /srv/hypomnema/casa etichette-XXXXXX.toml)
trap 'rm -f "$temporaneo"' EXIT
printf '%s' "$2" | base64 -d | sudo -u hypomnema tee "$temporaneo" >/dev/null
opzione=()
if [ "${3:-no}" = "sostituisci" ]; then opzione=(--replace); fi
sudo -u hypomnema HOME=/srv/hypomnema/casa python3 /opt/hypomnema/programma.py notebook-labels \
  --labels "$temporaneo" --file /srv/hypomnema/taccuini/taccuini.toml --name "$1" "${opzione[@]}"
