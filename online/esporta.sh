#!/bin/bash
# Prepara la copia di UN taccuino, per darla al suo tester (0.11.0, seconda parte): un archivio nuovo in
# /var/backups/hypomnema/esportazioni, leggibile dall'utente di amministrazione.   $1 = il nome del taccuino
set -euo pipefail
set -o noclobber
nome="$1"
if ! [[ "$nome" =~ ^[a-z0-9][a-z0-9-]{0,39}$ ]] || [ ! -d "/srv/hypomnema/taccuini/$nome" ]; then
  echo "ERRORE: non c'è un taccuino che si chiama «$nome»."
  exit 2
fi
cartella=/var/backups/hypomnema/esportazioni
install -d -m 750 -o root -g adm /var/backups/hypomnema "$cartella"
file="$cartella/$nome-$(date -u +%Y-%m-%d-%H%M%S).tar.gz"
umask 027
tar -czf - -C /srv/hypomnema/taccuini "$nome/quaderno" > "$file"
chgrp adm "$file"
echo "ESPORTATO: $file"
