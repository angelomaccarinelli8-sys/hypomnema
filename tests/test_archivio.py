"""Test del testimone dell'archivio della chat: copia, privati, doppioni, i tre livelli delle note,
il diario, cambiati e controlla. Solo dati e indirizzi inventati."""

import io
import json
import tempfile
import unittest
from pathlib import Path

from hypomnema import archivio, configurazione, sportello
from hypomnema.cli import main
from tests.esecutore import RADICE, modello_chat
from tests.test_chat import CONFIG_CHAT
from tests.test_regole import ADESSO, NOTA_BUONA
from tests.test_testimone import CONFIG_ACCESO

CHAT = "https://claude.ai/chat/00000000-prova"
SEZIONE = ('\n[archivio]\nfile = "archivio-chat.jsonl"\nfile_diario = "diario-chat.jsonl"\n'
           'ometti_codice = true\ncopia_ogni = 5\n')
CONFIG_ARCHIVIO = CONFIG_CHAT + SEZIONE


def copia_json(*messaggi, chat=CHAT, fuso="UTC+01:00") -> bytes:
    """Una copia come la dà lo strumento dell'archivio: ora al minuto, fuso a parte, numero del turno."""
    return json.dumps({"chat": chat, "fuso": fuso, "messaggi": [
        {"turno": t, "quando": q, "chi": chi, "testo": testo} for t, q, chi, testo in messaggi]}).encode("utf-8")


UTENTE = (0, "Thu 2026-01-15 09:00", "utente", "Voglio provare i peperoncini sul balcone.")
CLAUDE = (1, "Thu 2026-01-15 09:00", "claude", "Bella idea:\n```\nx = 1\n```\nmettili al sole.")


class ConArchivio(unittest.TestCase):
    config_testo = CONFIG_ARCHIVIO

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

    def righe(self, file):
        return [json.loads(r) for r in file.read_text(encoding="utf-8").splitlines()]

    def comando(self, *argomenti):
        uscita = io.StringIO()
        codice = main(["--config", str(self.file_config), *argomenti], uscita=uscita)
        return codice, uscita.getvalue()

    def copia_da_file(self, contenuto: bytes):
        file = self.cartella / "copia.json"
        file.write_bytes(contenuto)
        return self.comando("archivio", str(file))

    def proponi(self, **modifiche):
        nota = {k: v for k, v in dict(NOTA_BUONA, **modifiche).items() if v is not ...}
        return sportello.ricevi(json.dumps(nota).encode("utf-8"), "prova.json", self.config, ADESSO)

    def riga_verifica(self, esito):
        return [r for r in esito.percorso.read_text(encoding="utf-8").splitlines() if r.startswith("- verifica")][0]


class TestConfigurazioneArchivio(ConArchivio):
    def test_sezione(self):
        self.assertEqual(self.config.file_archivio, self.cartella / "quaderno" / "archivio-chat.jsonl")
        self.assertEqual(self.config.file_diario_chat, self.cartella / "quaderno" / "diario-chat.jsonl")
        self.assertEqual(self.config.copia_ogni, 5)

    def test_solo_nella_chat(self):
        self.file_config.write_text(CONFIG_ACCESO + SEZIONE, encoding="utf-8")
        with self.assertRaisesRegex(configurazione.ErroreConfigurazione, "serve solo nella chat di Claude"):
            configurazione.carica(str(self.file_config))

    def test_valori_sbagliati(self):
        for vecchio, nuovo, frammento in (
            ('file = "archivio-chat.jsonl"', 'file = "../a.jsonl"', "«file» della sezione"),
            ('file_diario = "diario-chat.jsonl"', 'file_diario = "/tmp/d.jsonl"', "«file_diario» della sezione"),
            ("ometti_codice = true", 'ometti_codice = "sì"', "«ometti_codice»"),
            ("copia_ogni = 5", "copia_ogni = 0", "«copia_ogni»"),
        ):
            with self.subTest(nuovo=nuovo):
                self.file_config.write_text(CONFIG_CHAT + SEZIONE.replace(vecchio, nuovo), encoding="utf-8")
                with self.assertRaisesRegex(configurazione.ErroreConfigurazione, frammento):
                    configurazione.carica(str(self.file_config))

    def test_modello_della_chat_ha_l_archivio(self):
        with tempfile.TemporaryDirectory() as cartella:
            config = configurazione.carica(str(modello_chat(Path(cartella))))
        self.assertTrue(config.in_chat)
        self.assertEqual(config.file_archivio.name, "archivio-chat.jsonl")


class TestCopia(ConArchivio):
    def test_copia_messaggi_e_risposte_con_il_codice_omesso(self):
        codice, uscita = self.copia_da_file(copia_json(UTENTE, CLAUDE))
        self.assertEqual(codice, 0)
        self.assertIn("1 messaggio dell'utente, 1 risposta di Claude", uscita)
        self.assertEqual(self.righe(self.config.file_archivio), [{
            "quando": "2026-01-15T09:00:00+01:00", "chat": CHAT, "turno": 0,
            "testo": "Voglio provare i peperoncini sul balcone.", "origine": archivio.ORIGINE}])
        testo = self.righe(self.config.file_diario_chat)[0]["testo"]
        self.assertTrue(testo.startswith("Bella idea:\n[blocco di codice di 1 riga omesso, impronta "))

    def test_privati(self):
        # Tutto nello stesso minuto: a dire chi risponde a chi è il numero del turno.
        self.copia_da_file(copia_json((0, "Thu 2026-01-15 09:00", "utente", "#privato segreto"),
                                      (1, "Thu 2026-01-15 09:00", "claude", "risposta segreta"),
                                      (2, "Thu 2026-01-15 09:00", "utente", "normale"),
                                      (3, "Thu 2026-01-15 09:00", "claude", "risposta normale")))
        self.assertEqual([r.get("privato") for r in self.righe(self.config.file_archivio)],
                         [archivio.DICITURA_PRIVATO, None])
        self.assertEqual([r.get("privato") for r in self.righe(self.config.file_diario_chat)],
                         [archivio.DICITURA_RISPOSTA_PRIVATA, None])
        tutto = self.config.file_archivio.read_text(encoding="utf-8") + self.config.file_diario_chat.read_text(encoding="utf-8")
        self.assertNotIn("segret", tutto)

    def test_risposta_a_un_privato_copiato_prima(self):
        self.copia_da_file(copia_json((0, "Thu 2026-01-15 09:00", "utente", "#privato segreto")))
        self.copia_da_file(copia_json((1, "Thu 2026-01-15 09:00", "claude", "risposta segreta")))
        self.assertEqual(self.righe(self.config.file_diario_chat)[0]["privato"], archivio.DICITURA_RISPOSTA_PRIVATA)

    def test_niente_doppioni_e_testo_diverso_segnalato(self):
        self.copia_da_file(copia_json(UTENTE, CLAUDE))
        prima = self.config.file_archivio.read_text(encoding="utf-8")
        codice, uscita = self.copia_da_file(copia_json(UTENTE, (1, "Thu 2026-01-15 09:00", "claude", "cambiata")))
        self.assertEqual(codice, 0)
        self.assertEqual(self.config.file_archivio.read_text(encoding="utf-8"), prima)
        self.assertIn("Già presenti (stessa chat, stesso turno), non duplicati: 2.", uscita)
        self.assertIn("ATTENZIONE: 1 già presente ha un testo diverso", uscita)
        self.assertEqual(len(self.righe(self.config.file_diario_chat)), 1)

    def test_doppioni_per_turno_non_per_ora(self):
        self.copia_da_file(copia_json(UTENTE))
        # Stesso minuto, turno diverso: è un messaggio nuovo. Stesso turno, minuto diverso: è lo stesso.
        self.copia_da_file(copia_json((2, "Thu 2026-01-15 09:00", "utente", "nuovo nello stesso minuto"),
                                      (0, "Thu 2026-01-15 09:03", "utente", UTENTE[3])))
        self.assertEqual([r["turno"] for r in self.righe(self.config.file_archivio)], [0, 2])

    def test_stesso_turno_in_due_chat(self):
        self.copia_da_file(copia_json(UTENTE))
        self.copia_da_file(copia_json(UTENTE, chat="https://claude.ai/chat/altra"))
        self.assertEqual(len(self.righe(self.config.file_archivio)), 2)

    def test_ora_e_fuso_dello_strumento(self):
        self.copia_da_file(copia_json((0, "Fri 2026-10-09 17:46", "utente", "a"), fuso="UTC+02:00"))
        self.copia_da_file(copia_json((0, "2026-10-09 17:46", "utente", "b"), fuso="UTC-05:30",
                                      chat="https://claude.ai/chat/altra"))
        self.assertEqual([r["quando"] for r in self.righe(self.config.file_archivio)],
                         ["2026-10-09T17:46:00+02:00", "2026-10-09T17:46:00-05:30"])

    def test_avvisi_tecnici_tolti_dai_messaggi_dell_utente(self):
        testo = "<system-reminder>\navviso\n</system-reminder>\n#privato segreto"
        codice, uscita = self.copia_da_file(copia_json(
            (0, "Thu 2026-01-15 09:00", "utente", testo),
            (1, "Thu 2026-01-15 09:00", "claude", "risposta"),
            (2, "Thu 2026-01-15 09:01", "utente", "prima <system-reminder>x</system-reminder> dopo"),
            (3, "Thu 2026-01-15 09:01", "claude", "parlo di <system-reminder>x</system-reminder>")))
        self.assertEqual(codice, 0)
        self.assertIn("Avvisi tecnici <system-reminder> tolti dai messaggi dell'utente: 2.", uscita)
        utente = self.righe(self.config.file_archivio)
        self.assertEqual(utente[0]["privato"], archivio.DICITURA_PRIVATO)  # il #privato dopo l'avviso vale
        self.assertEqual(utente[1]["testo"], "prima  dopo")
        # Le risposte di Claude restano come sono.
        self.assertEqual(self.righe(self.config.file_diario_chat)[1]["testo"],
                         "parlo di <system-reminder>x</system-reminder>")

    def test_avviso_non_chiuso_ferma_la_copia(self):
        codice, uscita = self.copia_da_file(copia_json((0, "Thu 2026-01-15 09:00", "utente", "a <system-reminder> b")))
        self.assertEqual(codice, 2)
        self.assertIn("senza la sua chiusura", uscita)
        self.assertFalse(self.config.cartella_quaderno.exists())

    def test_solo_aggiunta(self):
        self.copia_da_file(copia_json(UTENTE))
        prima = self.config.file_archivio.read_text(encoding="utf-8")
        self.copia_da_file(copia_json((2, "Thu 2026-01-15 09:05", "utente", "dopo")))
        self.assertTrue(self.config.file_archivio.read_text(encoding="utf-8").startswith(prima))

    def test_copia_non_valida_non_scrive_niente(self):
        for contenuto, frammento in (
            (b"non json", "non è in formato JSON"),
            (json.dumps({"chat": CHAT}).encode(), "solo i campi «chat», «fuso» e «messaggi»"),
            (copia_json(UTENTE, chat="claude.ai/chat/x"), "comincia con https://"),
            (copia_json(UTENTE, chat="https://claude.ai/chat/ con spazio"), "comincia con https://"),
            (copia_json(UTENTE, fuso="+02:00"), "il campo «fuso»"),
            (json.dumps({"chat": CHAT, "fuso": "UTC+01:00", "messaggi": []}).encode(), "almeno un messaggio"),
            (copia_json((0, "2026-01-15T09:00:00+01:00", "utente", "x")), "la forma dell'archivio"),
            (copia_json((0, "Thu 2026-02-30 09:00", "utente", "x")), "una data che non esiste"),
            (copia_json((-1, "Thu 2026-01-15 09:00", "utente", "x")), "numero del turno"),
            (copia_json(UTENTE, UTENTE), "ripete un turno"),
            (copia_json((0, "Thu 2026-01-15 09:00", "altro", "x")), "«utente» oppure «claude»"),
            (copia_json((0, "Thu 2026-01-15 09:00", "utente", 3)), "deve essere un testo"),
        ):
            with self.subTest(frammento=frammento):
                codice, uscita = self.copia_da_file(contenuto)
                self.assertEqual(codice, 2)
                self.assertIn(frammento, uscita)
                self.assertFalse(self.config.cartella_quaderno.exists())

    def test_senza_sezione_archivio(self):
        self.scrivi_config(CONFIG_CHAT)
        codice, uscita = self.copia_da_file(copia_json(UTENTE))
        self.assertEqual(codice, 2)
        self.assertIn("non ha la sezione [archivio]", uscita)


class TestTreLivelli(ConArchivio):
    def test_nota_dell_utente_riscontrata(self):
        self.copia_da_file(copia_json(UTENTE))
        self.assertEqual(self.riga_verifica(self.proponi(testo="provare i peperoncini")),
                         f"- verification: text matched in the chat archive {CHAT}, message of turn 0 "
                         "(2026-01-15T09:00:00+01:00, copied by Claude)")

    def test_testo_assente_non_verificato_e_non_rifiutato(self):
        self.copia_da_file(copia_json(UTENTE))
        esito = self.proponi(testo="i peperoni dolci")
        self.assertTrue(esito.accettata)
        self.assertEqual(self.riga_verifica(esito), "- verification: author not verified (chat, no witness)")

    def test_non_si_cerca_nelle_risposte_di_claude(self):
        self.copia_da_file(copia_json(UTENTE, CLAUDE))
        self.assertIn("not verified", self.riga_verifica(self.proponi(testo="mettili al sole.")))

    def test_messaggio_privato_non_riscontrabile(self):
        self.copia_da_file(copia_json((0, "Thu 2026-01-15 09:00", "utente", "#privato parole segrete")))
        self.assertIn("not verified", self.riga_verifica(self.proponi(testo="parole segrete")))

    def test_citazione_di_claude_riscontrata(self):
        self.copia_da_file(copia_json(UTENTE))
        esito = self.proponi(autore="claude", tipo="dedotta", natura="idea", citazione="i peperoncini sul balcone")
        self.assertIn("- verification: quote matched in the chat archive", esito.percorso.read_text(encoding="utf-8"))

    def test_risposta_di_claude_riscontrata_sul_diario_della_chat(self):
        self.copia_da_file(copia_json(UTENTE, CLAUDE))
        esito = self.proponi(autore="claude", tipo="dedotta", natura="idea", da_risposta="sì", testo="mettili al sole.")
        self.assertEqual(self.riga_verifica(esito),
                         f"- verification: text matched in the chat archive {CHAT}, reply of turn 1 "
                         "(2026-01-15T09:00:00+01:00, copied by Claude)")
        esito = self.proponi(autore="claude", tipo="dedotta", natura="idea", da_risposta="sì", testo="mai detto")
        self.assertEqual(self.riga_verifica(esito), "- verification: reply not verified (chat, no witness)")

    def test_senza_sezione_come_prima(self):
        self.scrivi_config(CONFIG_CHAT)
        self.assertEqual(self.riga_verifica(self.proponi()), "- verification: author not verified (chat, no witness)")


class TestDiarioEStato(ConArchivio):
    def test_diario_dice_da_dove_viene(self):
        self.copia_da_file(copia_json(UTENTE, CLAUDE))
        codice, uscita = self.comando("diario", "peperoncini")
        self.assertEqual(codice, 0)
        self.assertIn(f"--- 2026-01-15T09:00:00+01:00 · utente · archivio della chat {CHAT}, turno 0, copiato da Claude ---", uscita)

    def test_ultimi(self):
        self.copia_da_file(copia_json(UTENTE, CLAUDE, (2, "Thu 2026-01-15 09:05", "utente", "terzo")))
        codice, uscita = self.comando("diario", "--ultimi", "2")
        self.assertEqual(codice, 0)
        self.assertTrue(uscita.startswith("Gli ultimi 2 messaggi del diario"))
        self.assertIn("  terzo", uscita)
        self.assertNotIn("peperoncini", uscita)
        self.assertEqual(self.comando("diario")[0], 2)
        self.assertEqual(self.comando("diario", "--ultimi", "0")[0], 2)

    def test_stato(self):
        self.copia_da_file(copia_json(UTENTE, CLAUDE))
        _, uscita = self.comando("stato")
        self.assertIn("Archivio della chat: 1 messaggi dell'utente e 1 risposte di Claude copiati da Claude "
                      "(da copiare ogni 5 scambi e alla chiusura).", uscita)
        self.assertIn(f"Ultimo copiato: 2026-01-15T09:00:00+01:00 (chat {CHAT})", uscita)


class TestCambiatiEControlla(ConArchivio):
    def istantanea(self):
        file = self.cartella / "prima.json"
        file.write_text(self.comando("istantanea")[1], encoding="utf-8")
        return file

    def test_cambiati_elenca_i_file_dell_archivio(self):
        prima = self.istantanea()
        self.copia_da_file(copia_json(UTENTE, CLAUDE))
        self.proponi(testo="provare i peperoncini")
        codice, uscita = self.comando("cambiati", str(prima))
        self.assertEqual(codice, 0, uscita)
        for riga in ("- archivio-chat.jsonl (creato)", "- diario-chat.jsonl (creato)", "- registro.md (creato)",
                     "- note/0001.md (creato)"):
            self.assertIn(riga, uscita)

    def test_cambiati_rifiuta_righe_scritte_a_mano(self):
        self.copia_da_file(copia_json(UTENTE))
        prima = self.istantanea()
        with open(self.config.file_archivio, "ab") as f:
            f.write(b'{"quando": "2026-01-15T10:00:00+01:00", "turno": 9, "testo": "scritto a mano"}\n')
        codice, uscita = self.comando("cambiati", str(prima))
        self.assertEqual(codice, 2)
        self.assertIn("non è del comando archivio", uscita)

    def test_controlla_doppioni_e_righe_rovinate(self):
        self.copia_da_file(copia_json(UTENTE))
        riga = self.config.file_archivio.read_bytes()
        with open(self.config.file_archivio, "ab") as f:
            f.write(riga + b"rovinata\n")
        codice, uscita = self.comando("controlla")
        self.assertEqual(codice, 1)
        self.assertIn("- archivio-chat.jsonl, riga 2: stessa chat e stesso turno della riga 1 (doppione).", uscita)
        self.assertIn("- archivio-chat.jsonl, riga 3: non ha la forma di una riga dell'archivio della chat.", uscita)

    def test_controlla_in_ordine(self):
        self.copia_da_file(copia_json(UTENTE, CLAUDE))
        self.assertEqual(self.comando("controlla"), (0, "Quaderno in ordine: nessuna nota.\n"))


class TestSkillArchivio(unittest.TestCase):
    def test_skill(self):
        skill = (RADICE / "skills" / "hypomnema" / "SKILL.md").read_text(encoding="utf-8")
        for frammento in ("H archive", "Where we left off", "H recap", "copia_ogni",
                          "**Never copy the user's words from memory**", "50 turni", "segnalino",
                          '"fuso": "UTC+02:00"', '"turno"'):
            with self.subTest(frammento=frammento):
                self.assertIn(frammento, skill)


if __name__ == "__main__":
    unittest.main()
