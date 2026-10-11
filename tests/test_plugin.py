"""Test del plugin installabile: catalogo, agganci dal percorso del plugin, configurazione creata
la prima volta fuori dal plugin, protezione del quaderno, pausa e ripresa. Solo dati inventati."""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from hypomnema import avvio, configurazione, risposte, sportello, testimone
from hypomnema.cli import main
from tests.esecutore import RADICE
from tests.test_regole import ADESSO, NOTA_BUONA
from tests.test_risposte import CONFIG_RISPOSTE, messaggio, risposta
from tests.test_testimone import CONFIG_ACCESO, _bash

# I file che servono al plugin installato (quelli che Claude Code copia nella sua cache).
FILE_DEL_PLUGIN = ("programma.py", "hypomnema", "windows", "hooks", "skills", "commands", ".claude-plugin")


def copia_del_plugin(destinazione: Path) -> Path:
    destinazione.mkdir(parents=True)
    for nome in FILE_DEL_PLUGIN:
        sorgente = RADICE / nome
        if sorgente.is_dir():
            shutil.copytree(sorgente, destinazione / nome, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy(sorgente, destinazione / nome)
    return destinazione


class TestCatalogoEManifesto(unittest.TestCase):
    def test_catalogo(self):
        catalogo = json.loads((RADICE / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(catalogo["name"], "hypomnema")
        self.assertEqual([(p["name"], p["source"]) for p in catalogo["plugins"]], [("hypomnema", "./")])
        manifesto = json.loads((RADICE / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifesto["name"], "hypomnema")
        self.assertNotIn("version", manifesto)  # così ogni aggiornamento di main arriva con l'update

    def test_agganci_usano_il_percorso_del_plugin(self):
        agganci = json.loads((RADICE / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        attesi = {"SessionStart": "avvio", "UserPromptSubmit": "testimone", "Stop": "risposte",
                  "PreToolUse": "protezione"}
        self.assertEqual(set(agganci), set(attesi))
        for evento, comando in attesi.items():
            with self.subTest(evento=evento):
                testo = agganci[evento][0]["hooks"][0]["command"]
                self.assertIn(f'"${{CLAUDE_PLUGIN_ROOT}}/programma.py" {comando};', testo)
                self.assertNotIn("..", testo)
        self.assertEqual(agganci["PreToolUse"][0]["matcher"], "Edit|Write|MultiEdit|NotebookEdit")

    def test_comandi_con_la_barra(self):
        for nome in ("pausa", "riprendi"):
            with self.subTest(nome=nome):
                testo = (RADICE / "commands" / f"{nome}.md").read_text(encoding="utf-8")
                self.assertIn("disable-model-invocation: true", testo)  # Claude non può lanciarli
                self.assertIn(f"/hypomnema:{nome}", testo)
        self.assertEqual(testimone.COMANDO_PAUSA, "/hypomnema:pausa")
        self.assertEqual(testimone.COMANDO_RIPRESA, "/hypomnema:riprendi")


class ConCasa(unittest.TestCase):
    """Una casa dell'utente temporanea: la configurazione di base è <casa>/Hypomnema/hypomnema.toml."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.casa = Path(self._tmp.name).resolve()
        self.config = self.casa / "Hypomnema" / "hypomnema.toml"

    def tearDown(self):
        self._tmp.cleanup()

    def ambiente(self, **altro):
        ambiente = {k: v for k, v in os.environ.items()
                    if k not in ("HYPOMNEMA_CONFIG", "PYTHONIOENCODING", "PYTHONUTF8", "OneDrive",
                                 "OneDriveConsumer", "OneDriveCommercial")}
        ambiente.update(HOME=str(self.casa), USERPROFILE=str(self.casa), **altro)
        return ambiente

    def programma(self, *argomenti, ingresso=b"", plugin=RADICE, **altro):
        return subprocess.run([sys.executable, str(plugin / "programma.py"), *argomenti], input=ingresso,
                              capture_output=True, env=self.ambiente(**altro), cwd=self.casa)


class TestPrimaVolta(ConCasa):
    def test_crea_la_configurazione_fuori_dal_plugin_e_avvisa(self):
        risultato = self.programma("avvio")
        self.assertEqual(risultato.returncode, 0, risultato.stderr)
        self.assertEqual(self.config.read_bytes(), (RADICE / "windows" / "hypomnema-uso.toml").read_bytes())
        uscita = json.loads(risultato.stdout.decode("utf-8"))
        self.assertIn("è la prima volta", uscita["systemMessage"])
        self.assertIn("ACCESI", uscita["systemMessage"])
        self.assertEqual(uscita["hookSpecificOutput"]["hookEventName"], "SessionStart")
        config = configurazione.carica(str(self.config))
        self.assertTrue(config.testimone_attivo and config.risposte_attive)
        self.assertEqual(config.cartella_quaderno, self.casa / "Hypomnema" / "quaderno")

    def test_la_seconda_volta_niente_e_niente_sovrascritto(self):
        self.config.parent.mkdir()
        mia = CONFIG_ACCESO.replace("cifre_numero_nota = 4", "cifre_numero_nota = 5")
        self.config.write_text(mia, encoding="utf-8")
        risultato = self.programma("avvio")
        self.assertEqual((risultato.returncode, risultato.stdout), (0, b""))
        self.assertEqual(self.config.read_text(encoding="utf-8"), mia)

    def test_quaderno_dentro_il_plugin(self):
        self.config.parent.mkdir()
        dentro = (RADICE / "quaderno-di-prova").as_posix()
        self.config.write_text(CONFIG_ACCESO.replace('cartella = "quaderno"', f'cartella = "{dentro}"'),
                               encoding="utf-8")
        uscita = json.loads(self.programma("avvio").stdout.decode("utf-8"))
        self.assertIn("è dentro la cartella del programma", uscita["systemMessage"])
        risultato = self.programma("testimone", ingresso=messaggio("ciao"))
        self.assertEqual(risultato.returncode, 1)
        self.assertIn("non registro niente", risultato.stderr.decode("utf-8"))
        self.assertFalse((RADICE / "quaderno-di-prova").exists())

    def test_quaderno_in_onedrive(self):
        self.programma("avvio")
        risultato = self.programma("avvio", OneDrive=str(self.casa))
        self.assertIn("è dentro OneDrive", json.loads(risultato.stdout.decode("utf-8"))["systemMessage"])

    def test_configurazione_sbagliata_avvisa_senza_bloccare(self):
        self.config.parent.mkdir()
        self.config.write_text("non è toml", encoding="utf-8")
        risultato = self.programma("avvio")
        self.assertEqual(risultato.returncode, 0)
        self.assertIn("la configurazione non va bene", json.loads(risultato.stdout.decode("utf-8"))["systemMessage"])

    def test_la_variabile_vince_sulla_cartella_di_base(self):
        altrove = self.casa / "altrove" / "hypomnema.toml"
        self.programma("avvio", HYPOMNEMA_CONFIG=str(altrove))
        self.assertTrue(altrove.exists())
        self.assertFalse(self.config.exists())


class TestDallaCopiaDelPlugin(ConCasa):
    """Gli agganci trovano i programmi dal percorso del plugin, anche da una copia altrove."""

    def setUp(self):
        super().setUp()
        self.plugin = copia_del_plugin(self.casa / "cache" / "hypomnema" / "abc123")

    def test_testimone_e_risposte_dalla_copia(self):
        self.programma("avvio", plugin=self.plugin)
        self.assertEqual(self.programma("testimone", ingresso=messaggio("dalla copia"), plugin=self.plugin).returncode, 0)
        self.assertEqual(self.programma("risposte", ingresso=risposta("risposta dalla copia"), plugin=self.plugin).returncode, 0)
        quaderno = self.casa / "Hypomnema" / "quaderno"
        self.assertIn("dalla copia", (quaderno / "testimone.jsonl").read_text(encoding="utf-8"))
        self.assertIn("risposta dalla copia", (quaderno / "risposte.jsonl").read_text(encoding="utf-8"))

    @unittest.skipIf(_bash() is None, "serve bash (su Windows: Git Bash)")
    def test_comandi_degli_agganci_veri(self):
        agganci = json.loads((self.plugin / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]

        def lancia(evento, ingresso):
            comando = agganci[evento][0]["hooks"][0]["command"]
            # Come Claude Code: sostituisce ${CLAUDE_PLUGIN_ROOT}, con le barre "/" anche su Windows.
            comando = comando.replace("${CLAUDE_PLUGIN_ROOT}", self.plugin.as_posix())
            return subprocess.run([_bash(), "-c", comando], input=ingresso, capture_output=True,
                                  env=self.ambiente(CLAUDE_PLUGIN_ROOT=self.plugin.as_posix()), cwd=self.casa)

        avviato = lancia("SessionStart", b"{}")
        self.assertEqual(avviato.returncode, 0, avviato.stderr)
        self.assertIn("prima volta", avviato.stdout.decode("utf-8"))
        self.assertEqual(lancia("UserPromptSubmit", messaggio("dal vero", "t1")).returncode, 0)
        self.assertEqual(lancia("Stop", risposta("risposta vera", "t1")).returncode, 0)
        quaderno = self.casa / "Hypomnema" / "quaderno"
        self.assertIn("dal vero", (quaderno / "testimone.jsonl").read_text(encoding="utf-8"))
        self.assertIn("risposta vera", (quaderno / "risposte.jsonl").read_text(encoding="utf-8"))
        bloccato = lancia("PreToolUse", json.dumps({"tool_name": "Write", "tool_input": {
            "file_path": str(quaderno / "note" / "0001.md"), "content": "x"}}).encode("utf-8"))
        self.assertEqual(bloccato.returncode, 2)


class TestProtezione(ConCasa):
    def setUp(self):
        super().setUp()
        self.programma("avvio")
        self.quaderno = self.casa / "Hypomnema" / "quaderno"

    def protezione(self, strumento, **ingresso):
        return self.programma("protezione", ingresso=json.dumps(
            {"tool_name": strumento, "tool_input": ingresso}).encode("utf-8"))

    def test_blocca_quaderno_e_configurazione(self):
        for strumento, ingresso in (
            ("Write", {"file_path": str(self.quaderno / "note" / "0009.md")}),
            ("Edit", {"file_path": str(self.quaderno / "registro.md")}),
            ("Edit", {"file_path": str(self.quaderno / "testimone.jsonl")}),
            ("Write", {"file_path": str(self.config)}),
            ("NotebookEdit", {"notebook_path": str(self.quaderno / "x.ipynb")}),
        ):
            with self.subTest(ingresso=ingresso):
                risultato = self.protezione(strumento, **ingresso)
                self.assertEqual(risultato.returncode, 2)
                self.assertIn("Claude non lo modifica mai con i suoi strumenti", risultato.stderr.decode("utf-8"))

    def test_lascia_passare_il_resto(self):
        for percorso in (self.casa / "progetto" / "main.py", self.casa / "Hypomnema" / "appunti.txt",
                         self.casa / "Hypomnema-quaderno" / "x.md"):
            with self.subTest(percorso=percorso):
                self.assertEqual(self.protezione("Write", file_path=str(percorso)).returncode, 0)

    def test_maiuscole_diverse_su_windows(self):
        if os.name != "nt":
            self.skipTest("solo su Windows i percorsi non distinguono le maiuscole")
        self.assertEqual(self.protezione("Write", file_path=str(self.quaderno).upper() + "\\X.MD").returncode, 2)

    def test_ingresso_strano_non_blocca(self):
        for ingresso in (b"non json", b"[]", b'{"tool_input": "x"}', b'{"tool_input": {}}'):
            with self.subTest(ingresso=ingresso):
                self.assertEqual(self.programma("protezione", ingresso=ingresso).returncode, 0)

    def test_senza_configurazione_non_blocca(self):
        self.config.unlink()
        self.assertEqual(self.protezione("Write", file_path=str(self.quaderno / "registro.md")).returncode, 0)


class TestPausa(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cartella = Path(self._tmp.name).resolve()
        self.file_config = self.cartella / "hypomnema.toml"
        self.file_config.write_text(CONFIG_RISPOSTE, encoding="utf-8")
        self.config = configurazione.carica(str(self.file_config))
        self.minuti = 0

    def tearDown(self):
        self._tmp.cleanup()

    def adesso(self):
        self.minuti += 1
        return ADESSO + timedelta(minutes=self.minuti)

    def dice(self, testo, turno=None):
        testimone.registra(self.config, self.adesso(), messaggio(testo, turno))

    def risponde(self, testo, turno=None):
        risposte.registra(self.config, self.adesso(), risposta(testo, turno))

    def ultimo(self, file):
        return json.loads(file.read_text(encoding="utf-8").splitlines()[-1])

    def stato(self):
        uscita = io.StringIO()
        main(["--config", str(self.file_config), "stato"], uscita=uscita)
        return uscita.getvalue()

    def test_pausa_e_ripresa(self):
        self.dice("prima", "t1")
        self.dice("/hypomnema:pausa", "t2")
        self.assertEqual(self.ultimo(self.config.file_testimone)["privato"], testimone.DICITURA_PAUSA)
        self.dice("segreto in pausa", "t3")
        self.assertEqual(self.ultimo(self.config.file_testimone)["privato"], testimone.DICITURA_IN_PAUSA)
        self.risponde("risposta segreta", "t3")
        self.assertEqual(self.ultimo(self.config.file_risposte)["privato"], risposte.DICITURA_IN_PAUSA)
        self.dice("  /hypomnema:riprendi  ", "t4")
        self.assertEqual(self.ultimo(self.config.file_testimone)["privato"], testimone.DICITURA_RIPRESA)
        self.dice("dopo", "t5")
        self.assertEqual(self.ultimo(self.config.file_testimone)["testo"], "dopo")
        self.assertNotIn("segret", self.config.file_testimone.read_text(encoding="utf-8")
                         + self.config.file_risposte.read_text(encoding="utf-8"))

    def test_risposta_al_comando_non_registrata(self):
        self.dice("/hypomnema:pausa", "t1")
        self.risponde("ok, in pausa", "t1")
        self.assertEqual(self.ultimo(self.config.file_risposte)["privato"], risposte.DICITURA_COMANDO)

    def test_comando_con_altro_testo_e_testo_che_lo_cita(self):
        self.dice("/hypomnema:pausa adesso basta")
        self.assertEqual(self.ultimo(self.config.file_testimone)["privato"], testimone.DICITURA_PAUSA)
        self.dice("/hypomnema:riprendi")
        self.dice("come funziona /hypomnema:pausa?")
        self.assertEqual(self.ultimo(self.config.file_testimone)["testo"], "come funziona /hypomnema:pausa?")
        self.dice("/hypomnema:pausaccia")
        self.assertIn("testo", self.ultimo(self.config.file_testimone))

    def test_privato_dopo_la_ripresa(self):
        self.dice("/hypomnema:pausa")
        self.dice("/hypomnema:riprendi")
        self.dice("#privato segreto")
        self.assertEqual(self.ultimo(self.config.file_testimone)["privato"], testimone.DICITURA_PRIVATO)

    def test_stato_in_pausa(self):
        self.dice("/hypomnema:pausa")
        stato = self.stato()
        self.assertIn("Testimone: IN PAUSA dal 2026-01-15T10:01:00+01:00 (comando /hypomnema:pausa)", stato)
        self.assertIn("Per riprendere: /hypomnema:riprendi.", stato)
        self.dice("/hypomnema:riprendi")
        self.assertIn("Testimone: ACCESO", self.stato())

    def test_note_in_pausa_come_con_il_testimone_spento(self):
        self.dice("Una nota di prova.")
        self.risponde("Una risposta di prova.")
        self.dice("/hypomnema:pausa")
        esito = sportello.ricevi(json.dumps(NOTA_BUONA).encode("utf-8"), "prova.json", self.config, self.adesso())
        self.assertTrue(esito.accettata)
        self.assertIn("- verifica: autore non verificato (testimoni in pausa)", esito.percorso.read_text(encoding="utf-8"))
        nota = dict(NOTA_BUONA, autore="claude", tipo="dedotta", natura="idea", da_risposta="sì",
                    testo="Una risposta di prova.")
        esito = sportello.ricevi(json.dumps(nota).encode("utf-8"), "prova.json", self.config, self.adesso())
        self.assertIn("risposta non verificata (testimoni in pausa)", esito.percorso.read_text(encoding="utf-8"))
        nota = dict(NOTA_BUONA, autore="claude", tipo="dedotta", natura="idea", citazione="Una nota di prova.")
        esito = sportello.ricevi(json.dumps(nota).encode("utf-8"), "prova.json", self.config, self.adesso())
        self.assertIn("citazione non verificata (testimoni in pausa)", esito.percorso.read_text(encoding="utf-8"))

    def test_dopo_la_ripresa_si_verifica_di_nuovo(self):
        self.dice("/hypomnema:pausa")
        self.dice("/hypomnema:riprendi")
        self.dice("Una nota di prova.")
        esito = sportello.ricevi(json.dumps(NOTA_BUONA).encode("utf-8"), "prova.json", self.config, self.adesso())
        self.assertIn("- verifica: testo trovato nel messaggio del", esito.percorso.read_text(encoding="utf-8"))

    def test_avviso_di_pausa_a_inizio_sessione(self):
        self.dice("/hypomnema:pausa")
        avvisi = avvio.prepara(self.file_config)
        self.assertTrue(any("i testimoni sono in pausa dal" in a for a in avvisi))


class TestSkillPlugin(unittest.TestCase):
    def test_skill(self):
        skill = (RADICE / "skills" / "hypomnema" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("**La pausa la decide solo l'utente**", skill)
        self.assertIn("`~/Hypomnema/hypomnema.toml`", skill)
        self.assertNotIn("avviabile", skill.split("## Modalità chat")[0])


if __name__ == "__main__":
    unittest.main()
