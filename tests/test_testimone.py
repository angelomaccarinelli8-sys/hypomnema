"""Test del testimone e della regola della citazione. Solo messaggi inventati."""

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

from hypomnema import configurazione, sportello, testimone
from hypomnema.cli import main
from tests.esecutore import CONFIG_DI_PROVA, RADICE
from tests.test_regole import ADESSO, NOTA_BUONA

CONFIG_ACCESO = CONFIG_DI_PROVA.replace("attivo = false", "attivo = true")


def _bash() -> str | None:
    """La bash con cui Claude Code lancia gli agganci: su Windows quella di Git (Git Bash)."""
    if os.name != "nt":
        return shutil.which("bash")
    git = shutil.which("git")
    if git is None:
        return None
    # git.exe sta in Git\cmd oppure in Git\mingw64\bin: si risale fino a Git\bin\bash.exe.
    for cartella in Path(git).resolve().parents:
        candidata = cartella / "bin" / "bash.exe"
        if candidata.is_file():
            return str(candidata)
    return None


def messaggio(testo: str) -> bytes:
    """Un messaggio come lo manda Claude Code all'aggancio UserPromptSubmit."""
    return json.dumps({
        "session_id": "prova",
        "hook_event_name": "UserPromptSubmit",
        "prompt": testo,
    }).encode("utf-8")


class ConTestimone(unittest.TestCase):
    config_testo = CONFIG_ACCESO

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cartella = Path(self._tmp.name)
        self.file_config = self.cartella / "hypomnema.toml"
        self.file_config.write_text(self.config_testo, encoding="utf-8")
        self.config = configurazione.carica(str(self.file_config))
        self.minuti = 0

    def tearDown(self):
        self._tmp.cleanup()

    def adesso(self):
        self.minuti += 1
        return ADESSO + timedelta(minutes=self.minuti)

    def dice(self, testo):
        return testimone.registra(self.config, self.adesso(), messaggio(testo))

    def proponi(self, **modifiche):
        nota = {k: v for k, v in dict(NOTA_BUONA, **modifiche).items() if v is not ...}
        contenuto = json.dumps(nota, ensure_ascii=False).encode("utf-8")
        return sportello.ricevi(contenuto, "prova.json", self.config, self.adesso())

    def righe_testimone(self):
        return [json.loads(r) for r in self.config.file_testimone.read_text(encoding="utf-8").splitlines()]


class TestRegistrazione(ConTestimone):
    def test_registra_testo_esatto_con_data_e_ora(self):
        self.dice("Ciao,  ecco il  testo\ncon a capo e accenti: è già così.")
        self.assertEqual(self.righe_testimone(), [{
            "quando": "2026-01-15T10:01:00+01:00",
            "testo": "Ciao,  ecco il  testo\ncon a capo e accenti: è già così.",
        }])

    def test_solo_aggiunta(self):
        self.dice("primo")
        prima = self.config.file_testimone.read_text(encoding="utf-8")
        self.dice("secondo")
        dopo = self.config.file_testimone.read_text(encoding="utf-8")
        self.assertTrue(dopo.startswith(prima))
        self.assertEqual([r["testo"] for r in self.righe_testimone()], ["primo", "secondo"])

    def test_messaggio_privato_non_registrato(self):
        self.dice("#privato una cosa mia")
        self.dice("   #privato anche con spazi davanti")
        righe = self.righe_testimone()
        self.assertEqual(righe[0], {"quando": "2026-01-15T10:01:00+01:00",
                                    "privato": "messaggio privato, non registrato"})
        self.assertNotIn("cosa mia", self.config.file_testimone.read_text(encoding="utf-8"))
        self.assertEqual(righe[1]["privato"], "messaggio privato, non registrato")

    def test_prefisso_solo_all_inizio(self):
        self.dice("questo non è #privato")
        self.assertEqual(self.righe_testimone()[0]["testo"], "questo non è #privato")

    def test_prefisso_regolabile(self):
        self.file_config.write_text(
            CONFIG_ACCESO.replace('prefisso_privato = "#privato"', 'prefisso_privato = "!!"'),
            encoding="utf-8")
        self.config = configurazione.carica(str(self.file_config))
        self.dice("!! segreto")
        self.dice("#privato ora si registra")
        righe = self.righe_testimone()
        self.assertIn("privato", righe[0])
        self.assertEqual(righe[1]["testo"], "#privato ora si registra")

    def test_messaggio_in_arrivo_non_valido(self):
        for contenuto in (b"non json", b"[1]", b'{"altro": 1}', b'{"prompt": 3}'):
            with self.subTest(contenuto=contenuto):
                with self.assertRaises(testimone.ErroreTestimone):
                    testimone.registra(self.config, ADESSO, contenuto)

    def test_righe_rovinate_segnalate(self):
        for riga in (
            "rovinata",
            "[1, 2]",
            '{"testo": "manca quando"}',
            '{"quando": 1, "testo": "quando non è testo"}',
            '{"quando": "2026-01-15T10:00:00+01:00", "testo": []}',
            '{"quando": "2026-01-15T10:00:00+01:00"}',
            '{"quando": "2026-01-15T10:00:00+01:00", "testo": "a", "privato": "b"}',
            '{"quando": "2026-01-15T10:00:00+01:00", "privato": 3}',
            '{"quando": "2026-01-15T10:00:00+01:00", "testo": "a", "altro": "b"}',
        ):
            with self.subTest(riga=riga):
                self.config.file_testimone.parent.mkdir(parents=True, exist_ok=True)
                self.config.file_testimone.write_text(riga + "\n", encoding="utf-8")
                with self.assertRaises(testimone.ErroreTestimone):
                    testimone.leggi_messaggi(self.config)

    def test_file_non_utf8_segnalato_dallo_sportello(self):
        self.config.file_testimone.parent.mkdir(parents=True, exist_ok=True)
        self.config.file_testimone.write_bytes('{"quando": "x", "testo": "caffè"}\n'.encode("latin-1"))
        uscita = io.StringIO()
        file = self.cartella / "nota.json"
        file.write_text(json.dumps(NOTA_BUONA), encoding="utf-8")
        codice = main(["--config", str(self.file_config), "proponi", str(file)], uscita=uscita)
        self.assertEqual(codice, 2)
        self.assertIn("non è in UTF-8", uscita.getvalue())


class TestTestimoneSpento(ConTestimone):
    config_testo = CONFIG_DI_PROVA

    def test_spento_non_registra_niente(self):
        self.assertFalse(self.dice("ciao"))
        self.assertFalse(self.config.file_testimone.exists())

    def test_nota_utente_accettata_e_marcata(self):
        esito = self.proponi()
        self.assertTrue(esito.accettata)
        self.assertIn("- verifica: autore non verificato (testimone spento)",
                      esito.percorso.read_text(encoding="utf-8"))

    def test_nota_di_claude_senza_marcatura(self):
        esito = self.proponi(autore="claude", tipo="dedotta")
        self.assertNotIn("verifica", esito.percorso.read_text(encoding="utf-8"))

    def test_citazione_di_claude_non_verificata(self):
        esito = self.proponi(autore="claude", tipo="dedotta", citazione="qualcosa")
        self.assertIn("- verifica: citazione non verificata (testimone spento)",
                      esito.percorso.read_text(encoding="utf-8"))


class TestRegolaTesto(ConTestimone):
    """Con il testimone acceso, il testo di una nota dell'utente sono le sue parole esatte."""

    def test_testo_trovato(self):
        self.dice("Domani pianto i fagioli nel vaso grande.")
        esito = self.proponi(testo="pianto i fagioli")
        self.assertTrue(esito.accettata, esito.motivi)
        contenuto = esito.percorso.read_text(encoding="utf-8")
        self.assertIn("- verifica: testo trovato nel messaggio del 2026-01-15T10:01:00+01:00", contenuto)
        self.assertNotIn("citazione", contenuto)

    def test_testo_non_detto(self):
        self.dice("qualcosa")
        esito = self.proponi(testo="tutt'altro")
        self.assertEqual(len(esito.motivi), 1)
        self.assertIn("il testo non si trova", esito.motivi[0])
        self.assertIn("«contesto»", esito.motivi[0])

    def test_vale_anche_per_le_decisioni(self):
        self.dice("Ho deciso: niente pesticidi.")
        self.assertTrue(self.proponi(natura="decisione", testo="niente pesticidi").accettata)
        self.assertFalse(self.proponi(natura="decisione", testo="niente concimi").accettata)

    def test_nessun_messaggio_registrato(self):
        self.assertIn("il testo non si trova", self.proponi(testo="qualunque cosa").motivi[0])

    def test_confronti(self):
        self.dice("Le Zucchine  vanno\n\nraccolte piccole, mi raccomando!")
        for testo, trovato in (
            ("Le Zucchine vanno raccolte piccole", True),          # spazi e a capo ridotti
            ("  vanno   raccolte  ", True),                         # spazi ai bordi
            ("raccolte piccole, mi raccomando!", True),            # punteggiatura identica
            ("le zucchine vanno", False),                           # maiuscola diversa
            ("Le Zucchine vanno raccolte grandi", False),          # una parola cambiata
            ("raccolte piccole mi raccomando", False),             # punteggiatura tolta
            ("ucchine vanno", False),                               # pezzo di parola
            ("vanno raccolte piccole, mi raccomando! Grazie", False),  # parola in più
        ):
            with self.subTest(testo=testo):
                self.assertEqual(self.proponi(testo=testo).accettata, trovato)

    def test_dentro_un_solo_messaggio(self):
        self.dice("prima frase")
        self.dice("seconda frase")
        self.assertFalse(self.proponi(testo="prima frase seconda frase").accettata)

    def test_messaggio_privato_non_citabile(self):
        self.dice("#privato parole segrete")
        self.assertFalse(self.proponi(testo="parole segrete").accettata)

    def test_testo_su_piu_righe_salvato_com_e(self):
        self.dice("riga uno\nriga due")
        esito = self.proponi(testo="riga uno\nriga due")
        self.assertIn("## Testo\n\nriga uno\nriga due\n", esito.percorso.read_text(encoding="utf-8"))

    def test_claude_non_puo_scrivere_la_verifica(self):
        self.dice("ciao")
        esito = self.proponi(testo="ciao", verifica="verificata")
        self.assertIn("«verifica» non è previsto", esito.motivi[0])


class TestContesto(ConTestimone):
    """Parole dell'utente e parole di Claude non si mescolano."""

    def test_contesto_separato(self):
        self.dice("Il melo va potato a febbraio.")
        esito = self.proponi(testo="Il melo va potato a febbraio.",
                             contesto="Detto parlando degli alberi\nda frutto del giardino.")
        self.assertTrue(esito.accettata, esito.motivi)
        contenuto = esito.percorso.read_text(encoding="utf-8")
        self.assertTrue(contenuto.endswith(
            "## Testo\n\nIl melo va potato a febbraio.\n\n"
            "## Contesto scritto da Claude\n\nDetto parlando degli alberi\nda frutto del giardino.\n"))

    def test_contesto_non_verificato_dal_testimone(self):
        self.dice("Il melo va potato a febbraio.")
        self.assertTrue(self.proponi(testo="Il melo va potato a febbraio.",
                                     contesto="parole mai dette dall'utente").accettata)

    def test_contesto_solo_per_note_dell_utente(self):
        esito = self.proponi(autore="claude", tipo="dedotta", contesto="spiegazione")
        self.assertIn("«contesto» si usa solo nelle note con autore «utente»", esito.motivi[0])

    def test_citazione_non_ammessa_per_note_dell_utente(self):
        self.dice("ciao")
        esito = self.proponi(testo="ciao", citazione="ciao")
        self.assertIn("le sue parole vanno nel campo «testo»", esito.motivi[0])

    def test_riga_riservata(self):
        for campo in ("testo", "contesto"):
            with self.subTest(campo=campo):
                valori = {"testo": "ciao", campo: "a\r\n## Contesto scritto da Claude\r\nb"}
                esito = self.proponi(**valori)
                self.assertTrue(any("è riservata al formato della nota" in m for m in esito.motivi))

    def test_cercatore_mostra_e_cerca_il_contesto(self):
        self.dice("Il melo va potato a febbraio.")
        self.proponi(testo="Il melo va potato a febbraio.", contesto="Alberi da frutto.")
        uscita = io.StringIO()
        main(["--config", str(self.file_config), "cerca", "frutto"], uscita=uscita)
        self.assertIn("testo:\n  Il melo va potato a febbraio.\n"
                      "contesto scritto da Claude:\n  Alberi da frutto.\n", uscita.getvalue())
        self.assertIn("verifica: testo trovato nel messaggio del", uscita.getvalue())

    def test_testimone_spento_contesto_salvato(self):
        self.file_config.write_text(CONFIG_DI_PROVA, encoding="utf-8")
        self.config = configurazione.carica(str(self.file_config))
        esito = self.proponi(contesto="spiegazione")
        self.assertIn("## Contesto scritto da Claude\n\nspiegazione\n", esito.percorso.read_text(encoding="utf-8"))


class TestCitazioneDiClaude(ConTestimone):
    def proponi_claude(self, **modifiche):
        return self.proponi(autore="claude", tipo="dedotta", **modifiche)

    def test_citazione_verificata(self):
        self.dice("forse cambio vaso")
        esito = self.proponi_claude(citazione="forse cambio vaso")
        self.assertTrue(esito.accettata)
        self.assertIn("- citazione: forse cambio vaso\n- verifica: citazione trovata nel messaggio del",
                      esito.percorso.read_text(encoding="utf-8"))
        self.assertIn("la citazione non si trova", self.proponi_claude(citazione="cambio vaso sicuro").motivi[0])

    def test_senza_citazione_accettata(self):
        self.assertTrue(self.proponi_claude().accettata)

    def test_citazione_su_piu_righe_salvata_su_una(self):
        self.dice("riga uno\nriga due")
        esito = self.proponi_claude(citazione="riga uno\nriga due")
        self.assertIn("- citazione: riga uno riga due", esito.percorso.read_text(encoding="utf-8"))


class TestSegnoCitazione(ConTestimone):
    MESSAGGIO = ("Ho letto questo passo:\n"
                 "> Chi semina con pazienza\n"
                 ">raccoglie con gioia.\n"
                 "Mi sembra vero anche per l'orto.\n"
                 "> Seconda frase riportata.")

    def test_righe_marcate_annotate_testo_identico(self):
        self.dice(self.MESSAGGIO)
        self.assertEqual(self.righe_testimone()[0],
                         {"quando": "2026-01-15T10:01:00+01:00", "testo": self.MESSAGGIO,
                          "righe_citate": [2, 3, 5]})

    def test_senza_segno_nessuna_annotazione(self):
        self.dice("niente > qui\nné qui")
        self.assertNotIn("righe_citate", self.righe_testimone()[0])

    def test_segno_con_spazi_davanti(self):
        self.dice("a\n   > b")
        self.assertEqual(self.righe_testimone()[0]["righe_citate"], [2])

    def leggi_verifica(self, testo):
        esito = self.proponi(testo=testo, fonte="dal libro Il quaderno dell'ortolano")
        self.assertTrue(esito.accettata, (testo, esito.motivi))
        return [r for r in esito.percorso.read_text(encoding="utf-8").splitlines() if r.startswith("- verifica")][0]

    def test_citazione_tutta_da_righe_marcate(self):
        self.dice(self.MESSAGGIO)
        for testo in ("Chi semina con pazienza raccoglie con gioia.", "con pazienza",
                      "Seconda frase riportata.", "> Chi semina con pazienza"):
            with self.subTest(testo=testo):
                self.assertEqual(self.leggi_verifica(testo),
                                 "- verifica: citazione riportata dall'utente, trovata nel messaggio "
                                 "del 2026-01-15T10:01:00+01:00")

    def test_citazione_mista(self):
        self.dice(self.MESSAGGIO)
        for testo in ("raccoglie con gioia. Mi sembra vero", "Ho letto questo passo: Chi semina"):
            with self.subTest(testo=testo):
                self.assertEqual(self.leggi_verifica(testo),
                                 "- verifica: testo trovato nel messaggio del 2026-01-15T10:01:00+01:00")

    def test_blocchi_separati_non_si_uniscono(self):
        self.dice(self.MESSAGGIO)
        # Le righe 3 e 5 sono marcate ma non consecutive: insieme non sono "riportate".
        self.assertFalse(self.proponi(testo="raccoglie con gioia. Seconda frase").accettata)

    def test_segno_regolabile(self):
        self.file_config.write_text(CONFIG_ACCESO.replace('segno_citazione = ">"', 'segno_citazione = "|"'),
                                    encoding="utf-8")
        self.config = configurazione.carica(str(self.file_config))
        self.dice("| riga riportata\n> non marcata")
        self.assertEqual(self.righe_testimone()[0]["righe_citate"], [1])
        self.assertIn("citazione riportata", self.leggi_verifica("riga riportata"))

    def test_citazione_di_claude_da_righe_marcate(self):
        self.dice(self.MESSAGGIO)
        esito = self.proponi(autore="claude", tipo="dedotta", citazione="Seconda frase riportata.")
        self.assertIn("- verifica: citazione riportata dall'utente", esito.percorso.read_text(encoding="utf-8"))

    def test_righe_citate_non_valide_segnalate(self):
        for citate in ("[0]", "[3]", "[2, 1]", "[1, 1]", "[]", '["1"]', "[true]", "1"):
            with self.subTest(citate=citate):
                self.config.file_testimone.parent.mkdir(parents=True, exist_ok=True)
                self.config.file_testimone.write_text(
                    '{"quando": "x", "testo": "a\\nb", "righe_citate": ' + citate + '}\n', encoding="utf-8")
                with self.assertRaises(testimone.ErroreTestimone):
                    testimone.leggi_messaggi(self.config)


class TestComandoTestimone(ConTestimone):
    """Il comando come lo lancia Claude Code: niente a schermo, mai il codice 2."""

    def lancia(self, ingresso, *argomenti):
        ambiente = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONPATH=str(RADICE))
        return subprocess.run(
            [sys.executable, "-m", "hypomnema", *argomenti, "testimone"],
            input=ingresso, capture_output=True, env=ambiente, cwd=self.cartella,
        )

    def test_registra_senza_scrivere_a_schermo(self):
        risultato = self.lancia(messaggio("dal vero"))
        self.assertEqual(risultato.returncode, 0, risultato.stderr)
        self.assertEqual(risultato.stdout, b"")
        self.assertEqual(self.righe_testimone()[0]["testo"], "dal vero")

    def test_errore_non_blocca_il_messaggio(self):
        risultato = self.lancia(b"rotto")
        self.assertEqual(risultato.returncode, 1)
        self.assertEqual(risultato.stdout, b"")
        self.assertIn("NON è stato registrato", risultato.stderr.decode("utf-8"))

    def test_comando_scritto_male_non_blocca(self):
        self.assertEqual(main(["testimone", "--sconosciuto"], errori=io.StringIO()), 1)
        self.assertEqual(main(["testimone", "a", "b"], errori=io.StringIO()), 1)

    def test_configurazione_mancante_non_blocca(self):
        risultato = self.lancia(messaggio("x"), "--config", "manca.toml")
        self.assertEqual(risultato.returncode, 1)

    def test_errore_sempre_in_utf8(self):
        # Senza impostazioni particolari: su Windows Python userebbe la vecchia codifica di sistema.
        ambiente = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
        ambiente["PYTHONPATH"] = str(RADICE)
        risultato = subprocess.run(
            [sys.executable, "-m", "hypomnema", "--config", "manca.toml", "testimone"],
            input=messaggio("x"), capture_output=True, env=ambiente, cwd=self.cartella,
        )
        self.assertEqual(risultato.returncode, 1)
        errore = risultato.stderr.decode("utf-8")
        self.assertIn("non trovo il file di configurazione «manca.toml»", errore)
        self.assertIn("Il messaggio NON è stato registrato.", errore)


class TestImpostazioniClaudeCode(unittest.TestCase):
    def comando_aggancio(self):
        aggancio = json.loads((RADICE / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        comandi = [h["command"] for g in aggancio["hooks"]["UserPromptSubmit"] for h in g["hooks"]]
        self.assertEqual(len(comandi), 1)
        return comandi[0]

    def test_progetto_senza_aggancio_e_con_divieto(self):
        """Fuori dall'avviabile non c'è nessun aggancio: il testimone vive solo nel plugin."""
        impostazioni = json.loads((RADICE / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertNotIn("hooks", impostazioni)
        self.assertEqual(impostazioni["permissions"]["deny"], ["Edit(/quaderno/**)"])

    @unittest.skipIf(_bash() is None, "serve bash (su Windows: Git Bash)")
    def test_aggancio_vero_con_py(self):
        """Windows: c'è il lanciatore py."""
        self.lancia_aggancio("py")

    @unittest.skipIf(_bash() is None, "serve bash (su Windows: Git Bash)")
    def test_aggancio_vero_con_python3(self):
        """macOS e Linux: py non c'è, si usa python3."""
        self.lancia_aggancio("python3")

    def lancia_aggancio(self, lanciatore):
        """Lancia il comando dell'aggancio come farebbe Claude Code, da una cartella qualunque.

        Nel PATH c'è solo un lanciatore finto (py o python3) che rimanda all'interprete dei test:
        così si controlla quale dei due rami del comando viene usato.
        """
        with tempfile.TemporaryDirectory() as progetto, tempfile.TemporaryDirectory() as altrove:
            # Una copia del plugin (come quella che Claude Code tiene nella cache) e i dati altrove.
            shutil.copytree(RADICE / "hypomnema", Path(progetto) / "hypomnema",
                            ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copy(RADICE / "programma.py", progetto)
            dati = Path(altrove) / "Hypomnema"
            dati.mkdir()
            (dati / "hypomnema.toml").write_text(CONFIG_ACCESO, encoding="utf-8")
            finti = Path(altrove) / "bin"
            finti.mkdir()
            finto = finti / lanciatore
            finto.write_text(
                f'#!/bin/sh\necho {lanciatore} > "{(finti / "usato").as_posix()}"\n'
                f'exec "{Path(sys.executable).as_posix()}" "$@"\n',
                encoding="utf-8", newline="\n")
            finto.chmod(0o755)
            ambiente = {k: v for k, v in os.environ.items() if k != "HYPOMNEMA_CONFIG"}
            # La configurazione di base è ~/Hypomnema: la casa dell'utente è la cartella temporanea.
            ambiente.update(CLAUDE_PLUGIN_ROOT=progetto, PATH=str(finti), HOME=altrove, USERPROFILE=altrove)
            risultato = subprocess.run([_bash(), "-c", self.comando_aggancio()], input=messaggio("dal vero"),
                                       capture_output=True, env=ambiente, cwd=altrove)
            self.assertEqual(risultato.returncode, 0, risultato.stderr)
            self.assertEqual(risultato.stdout, b"")
            self.assertEqual((finti / "usato").read_text(encoding="utf-8").strip(), lanciatore)
            registrato = (dati / "quaderno" / "testimone.jsonl").read_text(encoding="utf-8")
            self.assertIn('"testo": "dal vero"', registrato)

    def test_testimone_spento_di_base(self):
        self.assertFalse(configurazione.carica(str(RADICE / "hypomnema.toml")).testimone_attivo)

    def test_configurazione_senza_testimone(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "hypomnema.toml"
            file.write_text(CONFIG_DI_PROVA.split("[testimone]")[0], encoding="utf-8")
            with self.assertRaises(configurazione.ErroreConfigurazione):
                configurazione.carica(str(file))

    def test_attivo_deve_essere_vero_o_falso(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "hypomnema.toml"
            file.write_text(CONFIG_DI_PROVA.replace("attivo = false", 'attivo = "sì"'), encoding="utf-8")
            with self.assertRaises(configurazione.ErroreConfigurazione):
                configurazione.carica(str(file))


if __name__ == "__main__":
    unittest.main()
