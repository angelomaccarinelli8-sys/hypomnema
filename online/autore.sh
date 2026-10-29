#!/bin/bash
# Mette la riga «autore» in cima al file dei taccuini, solo se manca (0.11.0, seconda parte). In cima perché in
# fondo finirebbe dentro l'ultimo [[taccuino]]. La lanciano installa.sh e aggiorna.sh.   $1 = l'autore
set -euo pipefail
autore="${1:-}"
file=/srv/hypomnema/taccuini/taccuini.toml
if [ -z "$autore" ] || [ ! -f "$file" ] || grep -q '^autore *=' "$file"; then exit 0; fi
if ! [[ "$autore" =~ ^[A-Za-z][A-Za-z\ \'.-]{0,59}$ ]]; then
  echo "ATTENZIONE: il nome dell'autore «$autore» non va (solo lettere, spazi, ' . -): riga non messa."
  exit 0
fi
sed -i "0,/^porta *=/s//autore = \"$autore\"\n&/" "$file"
echo "Riga aggiunta al file dei taccuini: autore = \"$autore\""
