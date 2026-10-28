"""Test della 0.11.0, seconda parte: i file del server online (cartella online/) e il guardiano. Niente rete:
si leggono i file, non si lancia niente su Azure."""

import re
import subprocess
import unittest

from hypomnema import configurazione, mcp_http
from tests.esecutore import RADICE

ONLINE = RADICE / "online"


def testo(nome: str) -> str:
    return (ONLINE / nome).read_bytes().decode("utf-8-sig")


def file_del_repository() -> list:
    try:
        nomi = subprocess.run(["git", "ls-files"], cwd=RADICE, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        raise unittest.SkipTest("git non c'è: il guardiano delle chiavi gira dove c'è il repository")
    return [RADICE / nome for nome in nomi.splitlines()]


class TestGuardianoPorte(unittest.TestCase):
    """Niente porte aperte oltre quelle decise: nel firewall di Azure solo la 443 per tutti; la 22 solo per l'IP del
    PC, solo per il tempo di un lavoro, e richiusa in un finally."""

    def regole(self):
        for file in sorted(ONLINE.glob("*.ps1")):
            for blocco in re.findall(r"az network nsg rule create.*?--output none", file.read_bytes().decode("utf-8-sig"),
                                     re.S):
                yield file.name, blocco

    def test_solo_443_e_22_temporanea(self):
        trovate = sorted((nome, re.search(r"--destination-port-ranges (\S+)", blocco).group(1))
                         for nome, blocco in self.regole())
        self.assertEqual(trovate, [("crea-macchina.ps1", "443"), ("porta-ssh.ps1", "22")])
        for nome, blocco in self.regole():
            self.assertIn("--access Allow", blocco)
            self.assertIn("--direction Inbound", blocco)
            if nome == "porta-ssh.ps1":
                self.assertIn('--source-address-prefixes "$mio/32"', blocco)
            else:
                self.assertNotIn("--source-address-prefixes", blocco)

    def test_la_22_si_richiude_sempre(self):
        porta = testo("porta-ssh.ps1")
        self.assertRegex(porta, r"(?s)try \{.*& \$Lavoro.*\} finally \{.*az network nsg rule delete [^\n]*"
                                r"--name ssh-temporanea")

    def test_macchina_senza_ssh_aperta(self):
        macchina = testo("crea-macchina.ps1")
        self.assertIn("--nsg-rule NONE", macchina)
        # Le risorse dei servizi gratuiti: la taglia, il disco P6 (64 GB Premium), Ubuntu LTS, la regione europea.
        for pezzo in ("--size Standard_B2ats_v2", "--storage-sku Premium_LRS --os-disk-size-gb 64",
                      "Canonical:ubuntu-24_04-lts:server:latest"):
            self.assertIn(pezzo, macchina)
        self.assertIn('$Regione = "swedencentral"', testo("impostazioni.ps1"))

    def test_caddy_e_servizio(self):
        caddy = testo("Caddyfile")
        righe = [r.strip() for r in caddy.splitlines() if r.strip() and not r.strip().startswith("#")]
        self.assertEqual(righe, ["DOMINIO {", "request_body {", "max_size 4MB", "}",
                                 "reverse_proxy 127.0.0.1:8765", "}"])
        self.assertIn("porta = 8765", testo("installa.sh"))
        servizio = testo("hypomnema.service")
        self.assertIn("ExecStart=/usr/bin/python3 /opt/hypomnema/programma.py serve --http "
                      "/srv/hypomnema/taccuini/taccuini.toml", servizio)
        self.assertIn("User=hypomnema", servizio)
        self.assertEqual(mcp_http.INDIRIZZO, "127.0.0.1")

    def test_niente_log_delle_richieste(self):
        # Le richieste contengono le note e a volte la chiave nell'indirizzo: Caddy non le scrive.
        self.assertNotRegex(testo("Caddyfile"), r"(?m)^\s*log\b")


class TestGuardianoChiavi(unittest.TestCase):
    """Niente chiavi nel repository; la chiave nata sul PC non va mai a schermo né in un file."""

    def test_nessuna_chiave_nel_repository(self):
        sospette = []
        for file in file_del_repository():
            relativo = file.relative_to(RADICE).as_posix()
            if relativo.startswith(("tests/", "hypomnema/_tomli/", "hypomnema/_cldr/")) or not file.is_file():
                continue
            try:
                contenuto = file.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                continue
            # Una chiave come quelle create (token_urlsafe, 32 byte o più): 40 o più caratteri di fila tra lettere,
            # cifre, - e _, con maiuscole, minuscole e cifre insieme.
            for pezzo in re.findall(r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{40,}(?![A-Za-z0-9_-])", contenuto):
                if re.search(r"[A-Z]", pezzo) and re.search(r"[a-z]", pezzo) and re.search(r"[0-9]", pezzo):
                    sospette.append(relativo)
            # Una riga del file dei taccuini con una chiave o un'impronta vera (non un segnaposto come «incolla qui»).
            for riga in re.findall(r'(?m)^\s*(?:chiave\s*=\s*"[A-Za-z0-9_-]{32,}"|impronta\s*=\s*"[0-9a-f]{64}")',
                                   contenuto):
                sospette.append(f"{relativo}: {riga.strip()[:12]}…")
        self.assertEqual(sospette, [])

    def test_chiave_mai_a_schermo_ne_in_un_file(self):
        script = testo("crea-taccuino-online.ps1")
        for riga in script.splitlines():
            if "$chiave" in riga and not riga.lstrip().startswith("#"):
                with self.subTest(riga=riga):
                    self.assertNotRegex(riga, r"Write-|Out-|Set-Content|Add-Content|echo|Tee-")
        # Al server va solo l'impronta; negli appunti la chiave, poi gli appunti si svuotano.
        self.assertIn('SulServer "nuovo-taccuino.sh" @($Nome, $impronta)', script)
        self.assertIn("Set-Clipboard -Value $chiave", script)
        self.assertIn('Set-Clipboard -Value " "', script)
        self.assertIn("RandomNumberGenerator", script)

    def test_impronta_uguale_a_quella_del_server(self):
        # Lo script calcola SHA-256 dei byte UTF-8 della chiave, in esadecimale minuscolo: come mcp_http.impronta.
        script = testo("crea-taccuino-online.ps1")
        self.assertIn('[Security.Cryptography.SHA256]::Create()', script)
        self.assertIn('ComputeHash([Text.Encoding]::UTF8.GetBytes($chiave))', script)
        self.assertIn('ToString("x2")', script)


class TestFileOnline(unittest.TestCase):
    def test_modello_online(self):
        config = configurazione.carica(str(ONLINE / "hypomnema-online.toml"))
        self.assertTrue(config.online and config.in_chat)
        self.assertFalse(config.testimone_attivo)

    def test_formati_dei_file(self):
        for file in ONLINE.glob("*.ps1"):
            with self.subTest(file=file.name):
                self.assertTrue(file.read_bytes().startswith(b"\xef\xbb\xbf"), "i .ps1 sono UTF-8 con BOM")
        for file in [*ONLINE.glob("*.sh"), ONLINE / "Caddyfile", *ONLINE.glob("hypomnema*.service"),
                     ONLINE / "hypomnema-copia.timer"]:
            with self.subTest(file=file.name):
                self.assertNotIn(b"\r", file.read_bytes(), "i file per Linux hanno il fine riga LF")
        for file in ONLINE.glob("*.sh"):
            with self.subTest(file=file.name):
                self.assertTrue(testo(file.name).startswith("#!/bin/bash\n"))
                self.assertIn("set -euo pipefail", testo(file.name))

    def test_copie_mai_cancellate(self):
        for nome in ("copia.sh", "esporta.sh"):
            with self.subTest(nome=nome):
                self.assertIn("set -o noclobber", testo(nome))
                self.assertNotRegex(testo(nome), r"\brm\b|find .*-delete")


if __name__ == "__main__":
    unittest.main()
