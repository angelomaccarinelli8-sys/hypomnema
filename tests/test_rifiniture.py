"""Test delle rifiniture nate dall'uso (v0.4.0): correzioni che viaggiano insieme (A), prima le note
più recenti (B), parole composte (C), promemoria con «done» (D), recap (E), segni dell'archivio e
skill (F). Solo dati inventati."""

import io
import json
import shutil
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from hypomnema import __version__, archivio, cercatore, configurazione, promemoria, quaderno, sportello
from hypomnema.cli import main
from hypomnema.nota import da_markdown
from tests.esecutore import CONFIG_DI_PROVA, RADICE, testo_della_skill
from tests.test_archivio import CONFIG_ARCHIVIO, copia_json
from tests.test_testimone import CONFIG_ACCESO, messaggio

ADESSO = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone(timedelta(hours=1)))
OGGI = ADESSO.date()


class ConQuaderno(unittest.TestCase):
    config_testo = CONFIG_DI_PROVA

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cartella = Path(self._tmp.name).resolve()
        self.file_config = self.cartella / "hypomnema.toml"
        self.scrivi_config(self.config_testo)

    def tearDown(self):
        self._tmp.cleanup()

    def scrivi_config(self, testo):
        self.file_config.write_text(testo, encoding="utf-8")
        self.config = configurazione.carica(str(self.file_config))

    def proponi(self, testo="Una nota.", **campi):
        nota = {"data": "2026-01-15", "fonte": "prova", "autore": "claude", "tipo": "dedotta",
                "natura": "idea", "testo": testo, **campi}
        # natura=... toglie il campo: in un cambiamento (dalla 0.6.0) la natura è facoltativa.
        nota = {k: v for k, v in nota.items() if v is not ...}
        esito = sportello.ricevi(json.dumps(nota, ensure_ascii=False).encode("utf-8"), "prova.json",
                                 self.config, ADESSO)
        return esito

    def nota(self, testo="Una nota.", **campi):
        esito = self.proponi(testo, **campi)
        self.assertTrue(esito.accettata, esito.motivi)
        return esito.id_nota

    def comando(self, *argomenti, adesso=ADESSO):
        uscita = io.StringIO()
        codice = main(["--config", str(self.file_config), *argomenti], adesso=adesso, uscita=uscita)
        return codice, uscita.getvalue()


class TestCampiNuovi(ConQuaderno):
    def test_corregge_una_nota_che_esiste(self):
        self.nota()
        self.assertEqual(self.proponi("Una nota corretta.", corregge="0001").id_nota, "0001.1")
        self.assertEqual(self.proponi(corregge="0099").motivi,
                         ["note «0099» named in «corrects» does not exist in the notebook."])

    def test_riprendere_il_solo_giorno_valido(self):
        for giorno, valida in (("2026-01-20", True), ("2026-02-30", False), ("2026-01-20T10:00", False),
                               ("20/01/2026", False), ("domani", False)):
            with self.subTest(giorno=giorno):
                self.assertEqual(self.proponi(riprendere_il=giorno).accettata, valida)

    def test_done_solo_su_un_promemoria_che_esiste(self):
        self.nota(riprendere_il="2026-01-10")
        self.nota()
        self.assertTrue(self.proponi(natura=..., done="0001").accettata)
        self.assertIn("«done» closes only open, todo and reminder notes", self.proponi(done="0002").motivi[0])
        self.assertIn("does not exist in the notebook", self.proponi(done="0099").motivi[0])

    def test_campi_scritti_e_riletti(self):
        self.nota(riprendere_il="2026-01-10")
        numero = self.nota("Una nota corretta.", corregge="0001", riprendere_il="2026-02-01")
        chiusa = self.nota("Fatto.", natura=..., done="0001")
        testo = (self.config.cartella_note / f"{numero}.md").read_text(encoding="utf-8")
        self.assertIn("- remind: 2026-02-01\n", testo)
        self.assertIn("- change: text corrected; remind 2026-01-10 → 2026-02-01\n", testo)
        rilette = quaderno.leggi_note(self.config)
        self.assertEqual([n.id for n in rilette], ["0001", numero, chiusa])
        self.assertEqual((rilette[1].riprendere_il, rilette[2].stato, rilette[2].cambio.motivo),
                         ("2026-02-01", "closed", "Fatto."))

    def test_nota_vecchia_senza_campi_nuovi(self):
        vecchia = ("# Note 0001\n\n- data: 2026-01-10\n- fonte: f\n- autore: utente\n- tipo: dichiarata\n"
                   "- natura: fatto\n\n## Text\n\nVecchia.\n")
        nota = da_markdown("0001", vecchia)
        self.assertEqual((nota.corregge, nota.done, nota.riprendere_il), (None, None, None))


class TestCercatore(ConQuaderno):
    def test_dalla_piu_recente(self):
        for _ in range(3):
            self.nota("Il caffè.")
        self.assertEqual([n.id for n in cercatore.cerca(self.config, "caffè")], ["0003", "0002", "0001"])

    def test_parole_composte(self):
        self.nota("ho aggiornato orto_balcone.py e semi-orto/vasi.txt")
        self.nota("il caffèlatte e l'orto2")
        for parola, trovate in (("orto", ["0001"]), ("balcone", ["0001"]), ("py", ["0001"]), ("vasi", ["0001"]),
                                ("txt", ["0001"]), ("orto_balcone", ["0001"]), ("caffè", []), ("orto2", ["0002"]),
                                ("semi-orto/vasi", ["0001"])):
            with self.subTest(parola=parola):
                self.assertEqual([n.id for n in cercatore.cerca(self.config, parola)], trovate)

    def test_correzioni_e_conferme_anche_senza_la_parola(self):
        self.nota("Il pomodoro va annaffiato ogni giorno.", natura="idea")
        self.nota("No, a giorni alterni.", natura=..., corregge="0001")
        self.nota("Ancora: due volte a settimana.", natura=..., corregge="0001")
        self.nota("Confermo.", autore="utente", tipo="dichiarata", natura="decisione", conferma_di="0001")
        codice, uscita = self.comando("cerca", "pomodoro")
        self.assertEqual(codice, 0)
        self.assertIn("Trovata 1 nota con «pomodoro».", uscita)
        self.assertIn("--- Nota I0001.2 ---\n", uscita)
        self.assertIn("confermata da: nota D0002\n", uscita)
        self.assertIn("  I0001.1 2026-01-15 · claude: testo corretto (prima: «Il pomodoro va annaffiato ogni giorno.»)\n"
                      "  I0001.2 2026-01-15 · claude: testo corretto (prima: «No, a giorni alterni.»)\n", uscita)
        self.assertIn("    --- Nota D0002 (conferma la nota 0001) ---", uscita)
        self.assertIn("    conferma di: nota I0001.2\n", uscita)

    def test_collegata_gia_mostrata(self):
        self.nota("pomodoro uno", natura="idea")
        self.nota("pomodoro due", autore="utente", tipo="dichiarata", natura="decisione", conferma_di="0001")
        _, uscita = self.comando("cerca", "pomodoro")
        self.assertEqual(uscita.count("--- Nota D0002"), 1)
        self.assertIn("    (nota D0002, che conferma la nota 0001: già mostrata sopra)", uscita)

    def test_done_mostrato_sotto_il_promemoria(self):
        self.nota("comprare i semi", riprendere_il="2026-01-10")
        self.nota("fatto", natura=..., done="0001")
        _, uscita = self.comando("cerca", "semi", "--all")
        self.assertIn("--- Nota ✓I0001.1 ---", uscita)
        self.assertIn("stato: chiusa (2026-01-15)", uscita)
        self.assertIn("✓I0001.1 2026-01-15 · claude: chiusa il 2026-01-15, perché «fatto»", uscita)


class TestDiarioParoleComposte(ConQuaderno):
    config_testo = CONFIG_ACCESO

    def test_diario(self):
        from hypomnema import testimone
        testimone.registra(self.config, ADESSO, messaggio("guarda orto_balcone.py"))
        _, uscita = self.comando("diario", "balcone")
        self.assertIn("Trovato 1 messaggio con «balcone»", uscita)


class TestPromemoria(ConQuaderno):
    def scaduti(self, oggi=OGGI):
        return [(p.storia.base, p.giorno, p.storia.ultima.id)
                for p in promemoria.scaduti(cercatore.leggi(self.config), oggi)]

    def test_ordine_e_data_arrivata(self):
        self.nota(riprendere_il="2026-01-20")
        self.nota(riprendere_il="2026-01-01")
        self.nota(riprendere_il="2026-01-15")
        self.nota(riprendere_il="2026-01-01")
        self.assertEqual(self.scaduti(), [("0002", "2026-01-01", "0002"), ("0004", "2026-01-01", "0004"),
                                          ("0003", "2026-01-15", "0003")])
        self.assertEqual(promemoria.in_arrivo(cercatore.leggi(self.config), OGGI), 1)
        self.assertEqual(self.scaduti(date(2026, 1, 20))[-1], ("0001", "2026-01-20", "0001"))

    def test_done_lo_toglie(self):
        self.nota(riprendere_il="2026-01-10")
        self.nota(natura=..., done="0001")
        self.assertEqual(self.scaduti(), [])

    def test_correzione_senza_data_lo_lascia(self):
        self.nota(riprendere_il="2026-01-10")
        self.nota("Corretta.", corregge="0001")
        self.assertEqual(self.scaduti(), [("0001", "2026-01-10", "0001.1")])

    def test_correzione_con_data_la_sposta(self):
        self.nota(riprendere_il="2026-01-10")
        self.nota(natura=..., aggiorna="0001", riprendere_il="2026-03-01")
        self.assertEqual(self.scaduti(), [])
        self.nota(natura=..., aggiorna="0001", riprendere_il="2026-01-12")
        self.assertEqual(self.scaduti(), [("0001", "2026-01-12", "0001.2")])

    def test_done_dopo_una_correzione_chiude_la_nota(self):
        self.nota(riprendere_il="2026-01-10")
        self.nota("Corretta.", corregge="0001", riprendere_il="2026-01-12")
        self.nota(natura=..., done="0001")
        self.assertEqual(self.scaduti(), [])

    def test_versione_che_aggiunge_la_data(self):
        self.nota("un fatto qualsiasi")
        self.nota(natura=..., aggiorna="0001", riprendere_il="2026-01-12")
        self.assertEqual(self.scaduti(), [("0001", "2026-01-12", "0001.1")])

    def test_giro_di_correzioni_fatto_a_mano(self):
        self.nota(riprendere_il="2026-01-10")
        self.nota("Un'altra nota.")
        # Due note vecchie che si correggono a vicenda, scritte a mano.
        for numero, altra in (("0001", "0002"), ("0002", "0001")):
            file = self.config.cartella_note / f"{numero}.md"
            file.write_text(file.read_text(encoding="utf-8").replace("- kind:", f"- corrects: {altra}\n- kind:"),
                            encoding="utf-8")
        self.assertEqual(len(self.scaduti()), 1)  # finisce, non gira all'infinito
        codice, _ = self.comando("cerca", "nota")
        self.assertEqual(codice, 0)

    def test_comando(self):
        codice, uscita = self.comando("promemoria")
        self.assertEqual((codice, uscita), (0, "Nessun promemoria scaduto al 2026-01-15.\n"))
        self.nota("comprare i semi", riprendere_il="2026-01-10")
        self.nota("e il terriccio", riprendere_il="2026-02-10")
        _, uscita = self.comando("promemoria")
        self.assertTrue(uscita.startswith("1 promemoria scaduto al 2026-01-15 (dal più vecchio).\n\n"
                                          "=== Da riprendere il 2026-01-10 ===\n"))
        self.assertTrue(uscita.endswith("(1 promemoria ha una data non ancora arrivata.)\n"))


class TestRecap(ConQuaderno):
    def test_quaderno_vuoto(self):
        codice, uscita = self.comando("recap")
        self.assertEqual(codice, 0)
        self.assertEqual(uscita, "Dove eravamo rimasti (recap del 2026-01-15).\n\nPromemoria scaduti: nessuno.\n\n"
                                 "Discorsi aperti: nessuno.\n\nCose da fare: nessuna.\n\nUltime decisioni: nessuna.\n\n"
                                 "Ultime voci del diario: nessuna.\n\n"
                                 "Legenda: F fatto · I idea · D decisione · O aperta · T da fare · ✓ chiusa\n")

    def test_numeri_di_base_senza_sezione(self):
        for _ in range(7):
            self.nota(natura="discorso aperto")
        _, uscita = self.comando("recap")
        self.assertIn("Discorsi aperti: 5 di 7 (prima la priorità alta, poi dal più recente)\n- [O0007]", uscita)
        self.assertIn("(2 discorsi aperti più vecchi non mostrati)", uscita)
        self.assertNotIn("[O0002]", uscita)

    def test_sezione_recap(self):
        self.scrivi_config(CONFIG_DI_PROVA + "\n[recap]\ndecisioni = 1\n")
        self.assertEqual((self.config.recap_decisioni, self.config.recap_discorsi_aperti,
                          self.config.recap_voci_diario), (1, 5, 10))
        for _ in range(2):
            self.nota(autore="utente", tipo="dichiarata", natura="decisione")
        _, uscita = self.comando("recap")
        self.assertIn("Ultime decisioni: 1 di 2 (prima la priorità alta, poi dal più recente)\n- [D0002] 2026-01-15: Una nota.\n"
                      "(1 decisione più vecchia non mostrata)", uscita)

    def test_sezione_recap_sbagliata(self):
        for aggiunta in ("[recap]\ndecisioni = 0\n", "[recap]\ndecisioni = \"tre\"\n", "[recap]\nidee = 3\n",
                         "[recap]\nvoci_diario = true\n"):
            with self.subTest(aggiunta=aggiunta):
                self.file_config.write_text(CONFIG_DI_PROVA + "\n" + aggiunta, encoding="utf-8")
                with self.assertRaises(configurazione.ErroreConfigurazione):
                    configurazione.carica(str(self.file_config))

    def test_prima_riga_e_collegate(self):
        self.nota("Resta da capire\ndove mettere la compostiera.", natura="discorso aperto")
        self.nota("Resta da capire\nse la compostiera va all'ombra.", natura=..., corregge="0001")
        self.nota("Controllare le fragole.", riprendere_il="2026-01-10")
        _, uscita = self.comando("recap")
        self.assertIn("Promemoria scaduti: 1 (prima la priorità alta, poi dal più vecchio)\n- [I0002] da riprendere il "
                      "2026-01-10: Controllare le fragole.\n", uscita)
        self.assertIn("- [O0001.1] 2026-01-15: Resta da capire …\n"
                      "    ↳ O0001.1 2026-01-15 · claude: testo corretto\n", uscita)


class TestRecapDiario(ConQuaderno):
    config_testo = CONFIG_ACCESO + "\n[recap]\nvoci_diario = 2\n"

    def test_ultime_voci(self):
        from hypomnema import testimone
        for i, testo in enumerate(("primo", "secondo\ncon due righe", "#privato terzo")):
            testimone.registra(self.config, ADESSO + timedelta(minutes=i), messaggio(testo))
        _, uscita = self.comando("recap")
        self.assertIn("Ultime voci del diario: 2 di 3 (la conversazione registrata, non le note)\n"
                      "- 2026-01-15T10:01:00+01:00 · utente: secondo …\n"
                      "- 2026-01-15T10:02:00+01:00 · utente: (messaggio privato, non registrato)\n"
                      "(per leggerle intere: diary --last 2)\n", uscita)


class TestSegniDellArchivio(ConQuaderno):
    config_testo = CONFIG_ARCHIVIO

    def test_segni_veri(self):
        for scritto, vero in (("a &lt; b &gt; c", "a < b > c"), ("x &amp; y", "x & y"), ("&amp;lt;", "&lt;"),
                              ("niente da cambiare <ok>", "niente da cambiare <ok>"), ("&lt&gt;", "&lt>")):
            with self.subTest(scritto=scritto):
                self.assertEqual(archivio.segni_veri(scritto), vero)

    def copia(self, testo):
        file = self.cartella / "copia.json"
        file.write_bytes(copia_json((0, "Thu 2026-01-15 09:00", "utente", testo)))
        return self.comando("archivio", str(file))

    def test_avviso_scritto_con_i_segni_html(self):
        codice, uscita = self.copia("umidità &lt; 30%\n&lt;system-reminder&gt;\navviso\n&lt;/system-reminder&gt;")
        self.assertEqual(codice, 0)
        self.assertIn("Avvisi tecnici <system-reminder> tolti dai messaggi dell'utente: 1.", uscita)
        self.assertEqual(archivio.leggi_messaggi(self.config)[0].testo, "umidità < 30%")
        esito = sportello.ricevi(json.dumps({
            "data": "2026-01-15", "fonte": "prova", "autore": "utente", "tipo": "dichiarata", "natura": "fatto",
            "testo": "umidità < 30%"}).encode("utf-8"), "prova.json", self.config, ADESSO)
        self.assertIn("- verification: text matched in the chat archive",
                      esito.percorso.read_text(encoding="utf-8"))

    def test_avviso_html_senza_chiusura_rifiutato(self):
        codice, uscita = self.copia("ciao &lt;system-reminder&gt; senza chiusura")
        self.assertEqual(codice, 2)
        self.assertFalse(self.config.file_archivio.exists())


class TestQuadernoVecchio(unittest.TestCase):
    """Un quaderno di prima della 0.4.0, con la configurazione di prima: tutto funziona senza modifiche."""

    def test_tutti_i_comandi(self):
        with tempfile.TemporaryDirectory() as tmp:
            cartella = Path(tmp)
            shutil.copytree(RADICE / "esempi" / "05-ricerca" / "atteso" / "quaderno", cartella / "quaderno")
            file_config = cartella / "hypomnema.toml"
            file_config.write_text(CONFIG_DI_PROVA, encoding="utf-8")
            prima = {p: p.read_bytes() for p in (cartella / "quaderno").rglob("*") if p.is_file()}
            for comando in (["cerca", "caffè"], ["promemoria"], ["recap"], ["controlla"], ["stato"]):
                with self.subTest(comando=comando):
                    codice = main(["--config", str(file_config), *comando], adesso=ADESSO, uscita=io.StringIO())
                    self.assertEqual(codice, 0)
            dopo = {p: p.read_bytes() for p in (cartella / "quaderno").rglob("*") if p.is_file()}
            self.assertEqual(prima, dopo)  # sono tutti comandi di sola lettura


class TestVersioneEDocumenti(unittest.TestCase):
    def test_versione(self):
        self.assertEqual(__version__, "0.6.1")
        self.assertIn('version = "0.6.1"', (RADICE / "pyproject.toml").read_text(encoding="utf-8"))

    def test_comando_recap_del_plugin(self):
        testo = (RADICE / "commands" / "recap.md").read_text(encoding="utf-8")
        self.assertIn("/hypomnema:recap", testo)
        self.assertIn('programma.py" recap', testo)

    def test_skill(self):
        skill = testo_della_skill()
        self.assertIn("P recap", skill)
        self.assertIn("H recap", skill)
        self.assertIn("riporto-<AAAAMMGG>-<hhmm>-<lettera>", skill)
        self.assertNotIn("riporto-<numero", skill)
        self.assertIn("**cannot also have `quote`**", skill)
        self.assertIn("&lt;", skill)
        # Le note riscontrate sull'archivio non si chiamano mai «verificate».
        for frase in ("verificata sull'archivio", "verificate sull'archivio", "verificato sull'archivio",
                      "verificata dall'archivio", "verified against the chat archive", "verified in the chat archive"):
            self.assertNotIn(frase, skill)

    def test_storia_delle_versioni(self):
        storia = (RADICE / "STORIA.md").read_text(encoding="utf-8")
        for versione in ("0.1", "0.2", "0.3", "0.4"):
            self.assertIn(f"## {versione}", storia)


if __name__ == "__main__":
    unittest.main()
