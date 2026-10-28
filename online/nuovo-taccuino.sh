#!/bin/bash
# Crea un taccuino online e riavvia il server (0.11.0, seconda parte). Lo lancia crea-taccuino-online.ps1 con
# «az vm run-command». Riceve solo il nome e l'IMPRONTA della chiave: la chiave non arriva mai qui.
#   $1 = il nome del taccuino   $2 = l'impronta SHA-256 della chiave
set -euo pipefail
cd /srv/hypomnema
sudo -u hypomnema HOME=/srv/hypomnema/casa python3 /opt/hypomnema/programma.py notebook-new \
  --file /srv/hypomnema/taccuini/taccuini.toml --name "$1" --fingerprint "$2"
systemctl enable -q hypomnema
systemctl restart hypomnema
sleep 2
systemctl is-active hypomnema
