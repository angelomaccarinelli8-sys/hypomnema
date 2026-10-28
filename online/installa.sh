#!/bin/bash
# Prepara la macchina online di Hypomnema (0.11.0, seconda parte). Lo lancia crea-macchina.ps1 con
# «az vm run-command», come root, senza porte aperte. Si può rilanciare: rifà solo ciò che manca.
#   $1 = il nome della macchina su internet (per esempio hypomnema-tester.swedencentral.cloudapp.azure.com)
#   $2 = il ramo del repository da usare (di solito main)
#   $3 = l'utente di amministrazione (può leggere le copie, gruppo adm)
set -euo pipefail
dominio="$1"
ramo="${2:-main}"
amministratore="${3:-}"
export DEBIAN_FRONTEND=noninteractive

echo "1/6 Programmi: python3, git, caddy, aggiornamenti automatici"
# Alla prima accensione Ubuntu finisce di prepararsi e si aggiorna da solo: si aspetta, invece di litigare per apt.
cloud-init status --wait >/dev/null 2>&1 || true
apt-get() { command apt-get -o DPkg::Lock::Timeout=900 "$@"; }
apt-get update -q
apt-get install -y -q python3 git unattended-upgrades tzdata
if ! apt-get install -y -q caddy; then
  # Se Ubuntu non ha Caddy, dal deposito ufficiale di Caddy (https://caddyserver.com/docs/install).
  apt-get install -y -q debian-keyring debian-archive-keyring apt-transport-https curl gnupg
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key | gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt > /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -q
  apt-get install -y -q caddy
fi

echo "2/6 Aggiornamenti di sicurezza automatici, con riavvio alle 4 (UTC) se servono"
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'FINE'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
FINE
cat > /etc/apt/apt.conf.d/52hypomnema <<'FINE'
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "04:00";
FINE

echo "3/6 Il programma in /opt/hypomnema (ramo $ramo)"
if [ ! -d /opt/hypomnema/.git ]; then
  git clone -q --branch "$ramo" https://github.com/angelomaccarinelli8-sys/hypomnema /opt/hypomnema
else
  git -C /opt/hypomnema fetch -q origin "$ramo"
  git -C /opt/hypomnema checkout -q -B "$ramo" "origin/$ramo"
fi

echo "4/6 L'utente hypomnema e la cartella dei taccuini"
id hypomnema >/dev/null 2>&1 || useradd --system --home-dir /srv/hypomnema/casa --shell /usr/sbin/nologin hypomnema
install -d -m 750 -o hypomnema -g hypomnema /srv/hypomnema /srv/hypomnema/casa /srv/hypomnema/taccuini
if [ ! -f /srv/hypomnema/taccuini/taccuini.toml ]; then
  install -m 640 -o hypomnema -g hypomnema /dev/null /srv/hypomnema/taccuini/taccuini.toml
  cat > /srv/hypomnema/taccuini/taccuini.toml <<'FINE'
# Il file dei taccuini del server online. Le voci [[taccuino]] le aggiunge  notebook-new  (crea-taccuino-online.ps1),
# con la sola impronta della chiave: la chiave qui non c'è.
porta = 8765
richieste_al_minuto = 30
proposte_al_minuto = 10
FINE
fi

echo "5/6 Caddy (HTTPS) e il servizio di Hypomnema"
sed "s/^DOMINIO {/$dominio {/" /opt/hypomnema/online/Caddyfile > /etc/caddy/Caddyfile
install -m 644 /opt/hypomnema/online/hypomnema.service /etc/systemd/system/hypomnema.service
install -m 644 /opt/hypomnema/online/hypomnema-copia.service /etc/systemd/system/hypomnema-copia.service
install -m 644 /opt/hypomnema/online/hypomnema-copia.timer /etc/systemd/system/hypomnema-copia.timer
systemctl daemon-reload
systemctl enable -q caddy hypomnema-copia.timer
systemctl restart caddy
systemctl start hypomnema-copia.timer
# Il server parte solo quando c'è almeno un taccuino.
if grep -q '^\[\[taccuino\]\]' /srv/hypomnema/taccuini/taccuini.toml; then
  systemctl enable -q hypomnema
  systemctl restart hypomnema
fi

if [ -n "$amministratore" ]; then usermod -aG adm "$amministratore"; fi
systemctl start hypomnema-copia.service

echo "6/6 Controllo"
python3 --version
systemctl is-active caddy
echo "PRONTO: https://$dominio"
