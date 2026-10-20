"""Test del comando stato, delle regole per l'avviabile, del plugin e dell'avviabile di Windows.

Solo dati inventati, in cartelle temporanee.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path, PurePosixPath, PureWindowsPath

from hypomnema import avvio, configurazione, testimone
from hypomnema.cli import main
from tests.esecutore import CONFIG_DI_PROVA, RADICE, testo_della_skill
from tests.test_regole import ADESSO
from tests.test_testimone import CONFIG_ACCESO, messaggio


class ConCartella(unittest.TestCase):
    config_testo = CONFIG_ACCESO

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cartella = Path(self._tmp.name).resolve()
        self.file_config = self.cartella / "hypomnema.toml"
        self.file_config.write_text(self.config_testo, encoding="utf-8")
        self.config = configurazione.carica(str(self.file_config))

    def tearDown(self):
        self._tmp.cleanup()

    def comando(self, *argomenti):
        uscita = io.StringIO()
        codice = main(["--config", str(self.file_config), *argomenti], uscita=uscita)
        return codice, uscita.getvalue()

    def dice(self, testo, minuti=0):
        testimone.registra(self.config, ADESSO + timedelta(minutes=minuti), messaggio(testo))


class TestStato(ConCartella):
    def test_acceso_senza_messaggi(self):
        codice, uscita = self.comando("stato")
        self.assertEqual(codice, 0)
        self.assertEqual(uscita.splitlines(), [
            f"Configurazione: {self.file_config}",
            f"Quaderno: {self.cartella / 'quaderno'}",
            "Fuso orario: UTC, quello di questa macchina: il quaderno non ha ancora il file fuso-del-sistema.jsonl, "
            "che nasce la prima volta che usi Hypomnema sul tuo computer.",
            "Etichette: nessun file etichette.toml (nessuna etichetta).",
            "Testimone: ACCESO (registra le parole esatte di ogni messaggio dell'utente).",
            f"File del testimone: {self.cartella / 'quaderno' / 'testimone.jsonl'}",
            "Messaggi registrati: 0",
            "Ultimo messaggio registrato: nessuno.",
        ])

    def test_acceso_ultimo_messaggio_con_testo(self):
        self.dice("primo")
        self.dice("secondo,\n\ncon una riga vuota", minuti=1)
        codice, uscita = self.comando("stato")
        self.assertEqual(codice, 0)
        self.assertTrue(uscita.endswith(
            "Messaggi registrati: 2\n"
            "Ultimo messaggio registrato: 2026-01-15T10:01:00+01:00\n"
            "Testo dell'ultimo messaggio:\n"
            "  secondo,\n"
            "\n"
            "  con una riga vuota\n"))

    def test_acceso_ultimo_messaggio_privato(self):
        self.dice("normale")
        self.dice("#privato segreto", minuti=1)
        codice, uscita = self.comando("stato")
        self.assertTrue(uscita.endswith(
            "Ultimo messaggio registrato: 2026-01-15T10:01:00+01:00 (messaggio privato, non registrato).\n"))
        self.assertNotIn("segreto", uscita)

    def test_spento(self):
        self.file_config.write_text(CONFIG_DI_PROVA, encoding="utf-8")
        codice, uscita = self.comando("stato")
        self.assertEqual(codice, 0)
        self.assertIn("Testimone: SPENTO (nella configurazione attivo = false)", uscita)
        self.assertIn("Messaggi registrati: 0", uscita)

    def test_spento_con_messaggi_di_prima(self):
        self.dice("registrato quando era acceso")
        self.file_config.write_text(CONFIG_DI_PROVA, encoding="utf-8")
        _, uscita = self.comando("stato")
        self.assertIn("Testimone: SPENTO", uscita)
        self.assertIn("  registrato quando era acceso\n", uscita)

    def test_solo_lettura(self):
        self.comando("stato")
        self.assertFalse((self.cartella / "quaderno").exists())
        self.dice("ciao")
        prima = {p: p.read_bytes() for p in self.cartella.rglob("*") if p.is_file()}
        self.comando("stato")
        dopo = {p: p.read_bytes() for p in self.cartella.rglob("*") if p.is_file()}
        self.assertEqual(prima, dopo)

    def test_testimone_rovinato(self):
        self.dice("ciao")
        with open(self.config.file_testimone, "a", encoding="utf-8") as f:
            f.write("rovinata\n")
        codice, uscita = self.comando("stato")
        self.assertEqual(codice, 2)
        self.assertIn("la riga 2 del file del testimone non è valida", uscita)

    def test_configurazione_dalla_variabile(self):
        ambiente = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
        ambiente.update(HYPOMNEMA_CONFIG=str(self.file_config), PYTHONPATH=str(RADICE))
        risultato = subprocess.run([sys.executable, "-m", "hypomnema", "stato"], capture_output=True,
                                   env=ambiente, cwd=RADICE)
        self.assertEqual(risultato.returncode, 0)
        self.assertIn(f"Configurazione: {self.file_config}", risultato.stdout.decode("utf-8"))


class TestImpostazioniClaude(ConCartella):
    def test_percorsi_nella_forma_delle_regole(self):
        self.assertEqual(avvio.percorso_per_le_regole(PureWindowsPath("C:/Users/nome/Hypomnema/quaderno")),
                         "//c/Users/nome/Hypomnema/quaderno")
        self.assertEqual(avvio.percorso_per_le_regole(PureWindowsPath(r"D:\Appunti")), "//d/Appunti")
        self.assertEqual(avvio.percorso_per_le_regole(PurePosixPath("/home/nome/quaderno")),
                         "//home/nome/quaderno")

    def test_divieti_su_quaderno_e_configurazione(self):
        codice, uscita = self.comando("impostazioni-claude")
        self.assertEqual(codice, 0)
        self.assertTrue(uscita.isascii())
        quaderno = avvio.percorso_per_le_regole(self.cartella / "quaderno")
        config = avvio.percorso_per_le_regole(self.file_config)
        self.assertEqual(json.loads(uscita), {
            "permissions": {"deny": [f"Edit({quaderno}/**)", f"Edit({config})"]}})

    def test_quaderno_dentro_il_programma_rifiutato(self):
        dentro = (RADICE / "quaderno-di-prova").as_posix()
        self.file_config.write_text(
            CONFIG_ACCESO.replace('cartella = "quaderno"', f'cartella = "{dentro}"'), encoding="utf-8")
        codice, uscita = self.comando("impostazioni-claude")
        self.assertEqual(codice, 2)
        self.assertIn("è dentro la cartella del programma", uscita)
        self.assertFalse((RADICE / "quaderno-di-prova").exists())


class TestPluginEModello(unittest.TestCase):
    def test_plugin(self):
        manifesto = json.loads((RADICE / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifesto["name"], "hypomnema")
        skill = testo_della_skill()
        self.assertTrue(skill.startswith("---\nname: hypomnema\n"))
        self.assertIn('py "${CLAUDE_PLUGIN_ROOT}/programma.py" status', skill)
        self.assertIn("Il testimone non è attivo: le note che salvi ora saranno marcate come non\n"
                      "  verificate. Per accenderlo serve attivo = true nella configurazione di Hypomnema.", skill)

    def test_modello_della_configurazione_in_uso(self):
        modello = RADICE / "windows" / "hypomnema-uso.toml"
        config = configurazione.carica(str(modello))
        self.assertTrue(config.testimone_attivo)
        self.assertEqual(config.cartella_quaderno, modello.resolve().parent / "quaderno")
        # Stesse impostazioni del file di sviluppo: cambia solo il testimone acceso.
        sviluppo = configurazione.tomllib.loads((RADICE / "hypomnema.toml").read_text(encoding="utf-8"))
        uso = configurazione.tomllib.loads(modello.read_text(encoding="utf-8"))
        sviluppo["testimone"]["attivo"] = True
        sviluppo["risposte"]["attivo"] = True
        self.assertEqual(uso, sviluppo)

    def test_file_cmd_ascii_e_crlf(self):
        for nome in ("Hypomnema.cmd", "aggiorna-hypomnema.cmd"):
            with self.subTest(nome=nome):
                contenuto = (RADICE / "windows" / nome).read_bytes()
                self.assertTrue(contenuto.isascii())
                self.assertEqual(contenuto.count(b"\n"), contenuto.count(b"\r\n"))

    def test_avviabile_con_bom(self):
        self.assertTrue((RADICE / "windows" / "avvia-hypomnema.ps1").read_bytes().startswith(b"\xef\xbb\xbf"))


FINTO_CLAUDE = """\
import json, os, sys
from pathlib import Path
Path(os.environ["FINTO_CLAUDE_USCITA"]).write_text(json.dumps({
    "argomenti": sys.argv[1:], "cartella": os.getcwd(),
    "HYPOMNEMA_CONFIG": os.environ.get("HYPOMNEMA_CONFIG")}), encoding="utf-8")
"""


@unittest.skipIf(os.name != "nt" or shutil.which("powershell.exe") is None or shutil.which("py") is None,
                 "l'avviabile si prova solo su Windows, con PowerShell e py")
class TestAvviabileWindows(unittest.TestCase):
    """L'avviabile vero, con un Claude Code finto che annota cosa riceve."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cartella = Path(self._tmp.name).resolve()
        self.dati = self.cartella / "dati"
        self.finto = self.cartella / "finto_claude.py"
        self.finto.write_text(FINTO_CLAUDE, encoding="utf-8")
        self.ricevuto = self.cartella / "ricevuto.json"

    def tearDown(self):
        self._tmp.cleanup()

    def avvia(self):
        def tra_apici(testo):
            return "'" + str(testo).replace("'", "''") + "'"
        script = RADICE / "windows" / "avvia-hypomnema.ps1"
        comando = (f"& {tra_apici(script)} -CartellaDati {tra_apici(self.dati)} "
                   f"-Claude {tra_apici(sys.executable)},{tra_apici(self.finto)}")
        ambiente = {k: v for k, v in os.environ.items() if k != "HYPOMNEMA_CONFIG"}
        ambiente["FINTO_CLAUDE_USCITA"] = str(self.ricevuto)
        return subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", comando],
            capture_output=True, env=ambiente, cwd=self.cartella)

    def test_prima_volta_crea_la_configurazione_e_avvia_claude(self):
        risultato = self.avvia()
        self.assertEqual(risultato.returncode, 0, risultato.stdout + risultato.stderr)
        config = self.dati / "hypomnema.toml"
        self.assertEqual(config.read_bytes(), (RADICE / "windows" / "hypomnema-uso.toml").read_bytes())
        self.assertFalse((self.dati / "quaderno").exists())  # lo crea il testimone al primo messaggio
        ricevuto = json.loads(self.ricevuto.read_text(encoding="utf-8"))
        self.assertEqual(Path(ricevuto["cartella"]), RADICE)
        self.assertEqual(Path(ricevuto["HYPOMNEMA_CONFIG"]), config)
        argomenti = ricevuto["argomenti"]
        self.assertEqual(argomenti[:3], ["--plugin-dir", str(RADICE), "--settings"])
        impostazioni = json.loads(argomenti[3])  # il JSON arriva intatto
        self.assertEqual(impostazioni["permissions"]["deny"], [
            f"Edit({avvio.percorso_per_le_regole(self.dati / 'quaderno')}/**)",
            f"Edit({avvio.percorso_per_le_regole(config)})",
        ])

    def test_configurazione_esistente_mai_sovrascritta(self):
        self.dati.mkdir()
        mia = CONFIG_ACCESO.replace("cifre_numero_nota = 4", "cifre_numero_nota = 5")
        (self.dati / "hypomnema.toml").write_text(mia, encoding="utf-8")
        risultato = self.avvia()
        self.assertEqual(risultato.returncode, 0, risultato.stdout + risultato.stderr)
        self.assertEqual((self.dati / "hypomnema.toml").read_text(encoding="utf-8"), mia)

    def test_quaderno_dentro_il_programma_ferma_l_avvio(self):
        self.dati.mkdir()
        dentro = (RADICE / "quaderno-di-prova").as_posix()
        (self.dati / "hypomnema.toml").write_text(
            CONFIG_ACCESO.replace('cartella = "quaderno"', f'cartella = "{dentro}"'), encoding="utf-8")
        risultato = self.avvia()
        self.assertEqual(risultato.returncode, 1)
        self.assertIn("dentro la cartella del programma", risultato.stdout.decode("utf-8", errors="replace"))
        self.assertFalse(self.ricevuto.exists())  # Claude Code non è partito
        self.assertFalse((RADICE / "quaderno-di-prova").exists())



# Un git e un py finti, come file .cmd: annotano cosa ricevono e da quale cartella.
FINTO_GIT = r"""@echo off
echo git %* @ %CD%>>"%FINTI_REGISTRO%"
if "%1"=="rev-parse" (echo %FINTO_RAMO%& exit /b 0)
if "%1"=="pull" exit /b %FINTO_ESITO_PULL%
exit /b 0
"""
FINTO_PY = r"""@echo off
echo py %* @ %CD%>>"%FINTI_REGISTRO%"
exit /b 0
"""


@unittest.skipIf(os.name != "nt", "l'aggiornamento è un comando di Windows")
class TestAggiornamentoWindows(unittest.TestCase):
    """aggiorna-hypomnema.cmd vero, su una copia in una cartella temporanea, con git e py finti."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        cartella = Path(self._tmp.name).resolve()
        self.programma = cartella / "programma"
        (self.programma / "windows").mkdir(parents=True)
        self.script = self.programma / "windows" / "aggiorna-hypomnema.cmd"
        shutil.copy(RADICE / "windows" / "aggiorna-hypomnema.cmd", self.script)
        self.finti = cartella / "finti"
        self.finti.mkdir()
        for nome, testo in (("git.cmd", FINTO_GIT), ("py.cmd", FINTO_PY)):
            (self.finti / nome).write_bytes(testo.replace("\n", "\r\n").encode("ascii"))
        self.registro = cartella / "registro.txt"

    def tearDown(self):
        self._tmp.cleanup()

    def aggiorna(self, ramo, esito_pull=0):
        ambiente = dict(os.environ, FINTI_REGISTRO=str(self.registro), FINTO_RAMO=ramo,
                        FINTO_ESITO_PULL=str(esito_pull))
        ambiente["PATH"] = f"{self.finti}{os.pathsep}{os.environ['PATH']}"
        # L'invio risponde al "pause" finale.
        risultato = subprocess.run(["cmd", "/c", str(self.script)], input=b"\r\n",
                                   capture_output=True, env=ambiente, cwd=self._tmp.name)
        chiamate = self.registro.read_text(encoding="ascii").splitlines() if self.registro.exists() else []
        return risultato.stdout.decode("ascii", errors="replace"), chiamate

    def test_ramo_diverso_da_main_non_aggiorna(self):
        uscita, chiamate = self.aggiorna("prova")
        self.assertIn('Questa copia non e\' sulla versione principale (main) ma su "prova".', uscita)
        self.assertIn("non aggiorno niente", uscita)
        self.assertEqual(chiamate, [f"git rev-parse --abbrev-ref HEAD @ {self.programma}"])

    def test_download_fallito_si_ferma(self):
        uscita, chiamate = self.aggiorna("main", esito_pull=1)
        self.assertIn("Aggiornamento NON riuscito", uscita)
        self.assertEqual(chiamate, [
            f"git rev-parse --abbrev-ref HEAD @ {self.programma}",
            f"git pull --ff-only origin main @ {self.programma}",
        ])

    def test_download_riuscito_lancia_i_test(self):
        uscita, chiamate = self.aggiorna("main")
        self.assertNotIn("NON riuscito", uscita)
        self.assertEqual(chiamate, [
            f"git rev-parse --abbrev-ref HEAD @ {self.programma}",
            f"git pull --ff-only origin main @ {self.programma}",
            f"py -m unittest -q @ {self.programma}",
        ])


if __name__ == "__main__":
    unittest.main()
