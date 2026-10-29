#!/bin/bash
# La copia dei taccuini online: un archivio nuovo, mai sopra uno che c'è già (noclobber). La cartella è
# leggibile dal gruppo adm, cioè dall'utente di amministrazione, per scaricarla sul PC (scarica-copie.ps1).
set -euo pipefail
set -o noclobber
cartella=/var/backups/hypomnema
install -d -m 750 -o root -g adm "$cartella"
file="$cartella/taccuini-$(date -u +%Y-%m-%d-%H%M%S).tar.gz"
umask 027
tar -czf - -C /srv/hypomnema taccuini > "$file"
chgrp adm "$file"
echo "Copia fatta: $file"
