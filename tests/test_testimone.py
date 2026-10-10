"""Test del testimone e della regola della citazione. Solo messaggi inventati."""

import io
import json
import os
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


class TestRegolaCitazione(ConTestimone):
    def test_citazione_trovata(self):
        self.dice("Domani pianto i fagioli nel vaso grande.")
        esito = self.proponi(citazione="pianto i fagioli")
        self.assertTrue(esito.accettata, esito.motivi)
        contenuto = esito.percorso.read_text(encoding="utf-8")
        self.assertIn("- citazione: pianto i fagioli", contenuto)
        self.assertIn("- verifica: citazione trovata nel messaggio del 2026-01-15T10:01:00+01:00", contenuto)

    def test_citazione_mancante(self):
        self.dice("qualcosa")
        esito = self.proponi()
        self.assertEqual(len(esito.motivi), 1)
        self.assertIn("manca il campo «citazione»", esito.motivi[0])

    def test_citazione_nulla_conta_come_mancante(self):
        esito = self.proponi(citazione=None)
        self.assertIn("manca il campo «citazione»", esito.motivi[0])

    def test_vale_anche_per_le_decisioni(self):
        esito = self.proponi(natura="decisione")
        self.assertIn("manca il campo «citazione»", esito.motivi[0])

    def test_nessun_messaggio_registrato(self):
        esito = self.proponi(citazione="qualunque cosa")
        self.assertIn("non si trova", esito.motivi[0])

    def test_confronti(self):
        self.dice("Le Zucchine  vanno\n\nraccolte piccole, mi raccomando!")
        for citazione, trovata in (
            ("Le Zucchine vanno raccolte piccole", True),          # spazi e a capo ridotti
            ("  vanno   raccolte  ", True),                         # spazi ai bordi
            ("raccolte piccole, mi raccomando!", True),            # punteggiatura identica
            ("le zucchine vanno", False),                           # maiuscola diversa
            ("Le Zucchine vanno raccolte grandi", False),          # una parola cambiata
            ("raccolte piccole mi raccomando", False),             # punteggiatura tolta
            ("ucchine vanno", False),                               # pezzo di parola
            ("vanno raccolte piccole, mi raccomando! Grazie", False),  # parola in più
        ):
            with self.subTest(citazione=citazione):
                self.assertEqual(self.proponi(citazione=citazione).accettata, trovata)

    def test_citazione_dentro_un_solo_messaggio(self):
        self.dice("prima frase")
        self.dice("seconda frase")
        self.assertFalse(self.proponi(citazione="prima frase seconda frase").accettata)

    def test_messaggio_privato_non_citabile(self):
        self.dice("#privato parole segrete")
        self.assertFalse(self.proponi(citazione="parole segrete").accettata)

    def test_citazione_su_piu_righe_salvata_su_una(self):
        self.dice("riga uno\nriga due")
        esito = self.proponi(citazione="riga uno\nriga due")
        self.assertIn("- citazione: riga uno riga due", esito.percorso.read_text(encoding="utf-8"))

    def test_citazione_di_claude_verificata(self):
        self.dice("forse cambio vaso")
        self.assertTrue(self.proponi(autore="claude", tipo="dedotta", citazione="forse cambio vaso").accettata)
        self.assertFalse(self.proponi(autore="claude", tipo="dedotta", citazione="cambio vaso sicuro").accettata)

    def test_nota_di_claude_senza_citazione_accettata(self):
        self.assertTrue(self.proponi(autore="claude", tipo="dedotta").accettata)

    def test_claude_non_puo_scrivere_la_verifica(self):
        self.dice("ciao")
        esito = self.proponi(citazione="ciao", verifica="verificata")
        self.assertIn("«verifica» non è previsto", esito.motivi[0])

    def test_cercatore_mostra_citazione_e_verifica(self):
        self.dice("Il melo va potato a febbraio.")
        self.proponi(citazione="Il melo va potato a febbraio.", testo="Potatura del melo a febbraio.")
        uscita = io.StringIO()
        main(["--config", str(self.file_config), "cerca", "melo"], uscita=uscita)
        self.assertIn("citazione: Il melo va potato a febbraio.", uscita.getvalue())
        self.assertIn("verifica: citazione trovata nel messaggio del", uscita.getvalue())


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


class TestImpostazioniClaudeCode(unittest.TestCase):
    def test_aggancio_e_divieto(self):
        impostazioni = json.loads((RADICE / ".claude" / "settings.json").read_text(encoding="utf-8"))
        comandi = [h["command"] for g in impostazioni["hooks"]["UserPromptSubmit"] for h in g["hooks"]]
        self.assertEqual(comandi, ['cd "$CLAUDE_PROJECT_DIR" && python -m hypomnema testimone'])
        self.assertIn("Edit(/quaderno/**)", impostazioni["permissions"]["deny"])

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
