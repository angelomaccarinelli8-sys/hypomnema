"""Test delle regole dello sportello, del registro e del cercatore."""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from hypomnema import cercatore, configurazione, sportello
from hypomnema.cli import main
from tests.esecutore import CONFIG_DI_PROVA, RADICE

ADESSO = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone(timedelta(hours=1)))

NOTA_BUONA = {
    "data": "2026-01-15",
    "fonte": "chat di prova",
    "autore": "utente",
    "tipo": "dichiarata",
    "natura": "fatto",
    "testo": "Una nota di prova.",
}


class ConQuaderno(unittest.TestCase):
    """Ogni test ha un quaderno vuoto in una cartella temporanea."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cartella = Path(self._tmp.name)
        self.file_config = self.cartella / "hypomnema.toml"
        self.file_config.write_text(CONFIG_DI_PROVA, encoding="utf-8")
        self.config = configurazione.carica(str(self.file_config))

    def tearDown(self):
        self._tmp.cleanup()

    def proponi(self, nota, adesso=ADESSO):
        contenuto = nota if isinstance(nota, bytes) else json.dumps(nota, ensure_ascii=False).encode("utf-8")
        return sportello.ricevi(contenuto, "prova.json", self.config, adesso)

    def con(self, **modifiche):
        nota = dict(NOTA_BUONA, **modifiche)
        return {k: v for k, v in nota.items() if v is not ...}


class TestSportello(ConQuaderno):
    def test_nota_completa_accettata(self):
        esito = self.proponi(NOTA_BUONA)
        self.assertTrue(esito.accettata)
        self.assertEqual(esito.id_nota, "0001")
        self.assertTrue((self.config.cartella_note / "0001.md").is_file())

    def test_ogni_campo_obbligatorio_mancante_rifiutato(self):
        for campo in NOTA_BUONA:
            with self.subTest(campo=campo):
                esito = self.proponi(self.con(**{campo: ...}))
                self.assertFalse(esito.accettata)
                self.assertEqual(len(esito.motivi), 1)
                self.assertIn(f"manca il campo «{campo}»", esito.motivi[0])

    def test_campo_vuoto_rifiutato(self):
        esito = self.proponi(self.con(fonte="   "))
        self.assertFalse(esito.accettata)
        self.assertIn("«fonte» è vuoto", esito.motivi[0])

    def test_valori_non_ammessi(self):
        for campo, valore in (("autore", "Mario"), ("tipo", "certa"), ("natura", "opinione")):
            with self.subTest(campo=campo):
                esito = self.proponi(self.con(**{campo: valore}))
                self.assertFalse(esito.accettata)
                self.assertIn(f"«{valore}» non è ammesso per «{campo}»", esito.motivi[0])

    def test_maiuscole_non_ammesse_nei_valori(self):
        self.assertFalse(self.proponi(self.con(autore="Utente")).accettata)

    def test_campo_sconosciuto_rifiutato(self):
        esito = self.proponi(self.con(fnte="refuso"))
        self.assertFalse(esito.accettata)
        self.assertIn("«fnte» non è previsto", esito.motivi[0])

    def test_campo_doppio_rifiutato(self):
        testo = b'{"data": "2026-01-15", "data": "2026-01-16"}'
        esito = self.proponi(testo)
        self.assertEqual(esito.motivi, ["il campo «data» compare due volte: deve comparire una volta sola."])

    def test_campo_non_testo_rifiutato(self):
        esito = self.proponi(self.con(testo=42))
        self.assertIn("«testo» deve essere un testo", esito.motivi[0])

    def test_date(self):
        for data, valida in (
            ("2026-01-15", True),
            ("2026-01-15T10:30", True),
            ("2026-01-15T10:30:15", True),
            ("15/01/2026", False),
            ("2026-02-30", False),
            ("2026-1-5", False),
            ("ieri", False),
        ):
            with self.subTest(data=data):
                self.assertEqual(self.proponi(self.con(data=data)).accettata, valida)

    def test_fonte_su_piu_righe_rifiutata(self):
        esito = self.proponi(self.con(fonte="riga uno\nriga due"))
        self.assertIn("«fonte» deve stare su una riga sola", esito.motivi[0])

    def test_testo_su_piu_righe_accettato(self):
        self.assertTrue(self.proponi(self.con(testo="riga uno\nriga due")).accettata)

    def test_json_rotto_rifiutato(self):
        esito = self.proponi(b'{"data": "2026-01-15",')
        self.assertIn("formato JSON corretto", esito.motivi[0])

    def test_json_non_oggetto_rifiutato(self):
        esito = self.proponi(b'[1, 2]')
        self.assertIn("una sola nota", esito.motivi[0])

    def test_file_non_utf8_rifiutato(self):
        esito = self.proponi('{"testo": "caffè"}'.encode("latin-1"))
        self.assertIn("UTF-8", esito.motivi[0])

    def test_file_utf8_con_bom_accettato(self):
        contenuto = b"\xef\xbb\xbf" + json.dumps(NOTA_BUONA).encode("utf-8")
        self.assertTrue(self.proponi(contenuto).accettata)

    def test_nota_rifiutata_non_lascia_file(self):
        self.proponi(self.con(fonte=...))
        self.assertFalse(self.config.cartella_note.exists())

    def test_numeri_progressivi(self):
        ids = [self.proponi(NOTA_BUONA).id_nota for _ in range(3)]
        self.assertEqual(ids, ["0001", "0002", "0003"])

    def test_nota_esistente_mai_sovrascritta(self):
        self.config.cartella_note.mkdir(parents=True)
        # Un file con nome non numerico non conta come nota e non viene toccato.
        estraneo = self.config.cartella_note / "appunto.md"
        estraneo.write_text("mio", encoding="utf-8")
        self.proponi(NOTA_BUONA)
        prima = (self.config.cartella_note / "0001.md").read_text(encoding="utf-8")
        self.proponi(self.con(testo="altra"))
        self.assertEqual((self.config.cartella_note / "0001.md").read_text(encoding="utf-8"), prima)
        self.assertEqual(estraneo.read_text(encoding="utf-8"), "mio")


class TestDecisioni(ConQuaderno):
    def test_decisione_di_claude_rifiutata(self):
        esito = self.proponi(self.con(autore="claude", natura="decisione"))
        self.assertFalse(esito.accettata)
        self.assertIn("Claude non può essere una decisione", esito.motivi[0])

    def test_decisione_non_dichiarata_rifiutata(self):
        for tipo in ("osservata", "dedotta"):
            with self.subTest(tipo=tipo):
                esito = self.proponi(self.con(natura="decisione", tipo=tipo))
                self.assertFalse(esito.accettata)
                self.assertIn("deve essere dichiarata", esito.motivi[0])

    def test_decisione_diretta_dell_utente_accettata(self):
        self.assertTrue(self.proponi(self.con(natura="decisione")).accettata)

    def test_conferma_di_idea_accettata(self):
        self.proponi(self.con(autore="claude", tipo="dedotta", natura="idea"))
        esito = self.proponi(self.con(natura="decisione", conferma_di="0001"))
        self.assertTrue(esito.accettata)
        # L'idea originale resta com'era.
        idea = (self.config.cartella_note / "0001.md").read_text(encoding="utf-8")
        self.assertIn("- natura: idea", idea)

    def test_conferma_di_nota_inesistente_rifiutata(self):
        esito = self.proponi(self.con(natura="decisione", conferma_di="0099"))
        self.assertIn("«0099» indicata in «conferma_di» non esiste", esito.motivi[0])

    def test_conferma_di_nota_che_non_e_idea_rifiutata(self):
        self.proponi(NOTA_BUONA)
        esito = self.proponi(self.con(natura="decisione", conferma_di="0001"))
        self.assertIn("non è un'idea", esito.motivi[0])

    def test_conferma_di_solo_per_decisioni(self):
        self.proponi(self.con(natura="idea"))
        esito = self.proponi(self.con(natura="fatto", conferma_di="0001"))
        self.assertIn("si usa solo per le decisioni", esito.motivi[0])


class TestRegistro(ConQuaderno):
    def test_ogni_passaggio_annotato_solo_in_aggiunta(self):
        self.proponi(NOTA_BUONA)
        prima = self.config.file_registro.read_text(encoding="utf-8")
        self.proponi(self.con(fonte=...), adesso=ADESSO + timedelta(minutes=1))
        dopo = self.config.file_registro.read_text(encoding="utf-8")
        self.assertTrue(dopo.startswith(prima))
        nuove = dopo[len(prima):].splitlines()
        self.assertEqual(len(nuove), 1)
        self.assertIn("2026-01-15T10:01:00+01:00 | RIFIUTATA", nuove[0])
        self.assertIn("manca il campo «fonte»", nuove[0])


class TestCercatore(ConQuaderno):
    def test_parola_esatta_senza_maiuscole(self):
        self.proponi(self.con(testo="Bevo un Caffè."))
        self.proponi(self.con(testo="Il caffèlatte no."))
        self.proponi(self.con(testo="Solo tè."))
        self.assertEqual([n.id for n in cercatore.cerca(self.config, "caffè")], ["0001"])

    def test_piu_parole_cercate_insieme(self):
        self.proponi(self.con(testo="annaffio l'orto la mattina"))
        self.proponi(self.con(testo="la mattina presto"))
        self.assertEqual([n.id for n in cercatore.cerca(self.config, "orto la mattina")], ["0001"])

    def test_caratteri_speciali_cercati_come_sono(self):
        self.proponi(self.con(testo="costa 3.5 euro"))
        self.proponi(self.con(testo="costa 315 euro"))
        self.assertEqual([n.id for n in cercatore.cerca(self.config, "3.5")], ["0001"])

    def test_nota_modificata_a_mano_segnalata(self):
        self.proponi(NOTA_BUONA)
        (self.config.cartella_note / "0001.md").write_text("rovinata", encoding="utf-8")
        uscita = io.StringIO()
        codice = main(["--config", str(self.file_config), "cerca", "prova"], uscita=uscita)
        self.assertEqual(codice, 2)
        self.assertIn("manca la sezione «## Testo»", uscita.getvalue())

    def test_quaderno_vuoto(self):
        self.assertEqual(cercatore.cerca(self.config, "niente"), [])

    def test_cerca_non_cambia_nulla(self):
        self.proponi(NOTA_BUONA)
        prima = {p: p.read_bytes() for p in self.cartella.rglob("*") if p.is_file()}
        cercatore.cerca(self.config, "prova")
        dopo = {p: p.read_bytes() for p in self.cartella.rglob("*") if p.is_file()}
        self.assertEqual(prima, dopo)


class TestConfigurazione(unittest.TestCase):
    def test_file_mancante(self):
        with self.assertRaises(configurazione.ErroreConfigurazione):
            configurazione.carica(str(Path(tempfile.gettempdir()) / "non-esiste" / "hypomnema.toml"))

    def test_impostazione_mancante(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "hypomnema.toml"
            file.write_text('[quaderno]\ncartella = "q"\n', encoding="utf-8")
            with self.assertRaises(configurazione.ErroreConfigurazione):
                configurazione.carica(str(file))

    def test_file_del_repository_valido(self):
        config = configurazione.carica(str(RADICE / "hypomnema.toml"))
        self.assertEqual(config.cifre_numero_nota, 4)

    def test_errore_di_configurazione_da_riga_di_comando(self):
        uscita = io.StringIO()
        codice = main(["--config", "non-esiste.toml", "cerca", "x"], uscita=uscita)
        self.assertEqual(codice, 2)
        self.assertTrue(uscita.getvalue().startswith("ERRORE: non trovo il file di configurazione"))


class TestRigaDiComando(ConQuaderno):
    """Lancia davvero il programma come farebbe l'utente."""

    def lancia(self, *argomenti, ingresso=None):
        ambiente = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONPATH=str(RADICE))
        return subprocess.run(
            [sys.executable, "-m", "hypomnema", "--config", str(self.file_config), *argomenti],
            input=ingresso, capture_output=True, env=ambiente, cwd=self.cartella,
        )

    def test_proponi_da_file_e_cerca(self):
        file = self.cartella / "proposta.json"
        file.write_text(json.dumps(NOTA_BUONA, ensure_ascii=False), encoding="utf-8")
        risultato = self.lancia("proponi", str(file))
        self.assertEqual(risultato.returncode, 0, risultato.stdout.decode("utf-8"))
        risultato = self.lancia("cerca", "prova")
        self.assertIn("Trovata 1 nota con «prova».", risultato.stdout.decode("utf-8"))

    def test_proponi_da_ingresso_standard(self):
        dati = json.dumps(self.con(fonte=...)).encode("utf-8")
        risultato = self.lancia("proponi", "-", ingresso=dati)
        self.assertEqual(risultato.returncode, 1)
        self.assertIn("(ingresso diretto)", self.config.file_registro.read_text(encoding="utf-8"))

    def test_file_inesistente(self):
        risultato = self.lancia("proponi", "manca.json")
        self.assertEqual(risultato.returncode, 2)


if __name__ == "__main__":
    unittest.main()
