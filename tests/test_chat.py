"""Test della modalità chat: configurazione, marcatura delle note, istantanea e cambiati.

Solo dati inventati, in cartelle temporanee.
"""

import io
import json
import tempfile
import tomllib
import unittest
from pathlib import Path

from hypomnema import cambiamenti, configurazione, sportello
from hypomnema.cli import main
from tests.esecutore import CARTELLA_ESEMPI, CONFIG_DI_PROVA, RADICE
from tests.test_regole import ADESSO, NOTA_BUONA

MODELLO_CHAT = RADICE / "chat" / "hypomnema-chat.toml"
CONFIG_CHAT = CONFIG_DI_PROVA.replace("attivo = false\n", 'attivo = false\nmodalita = "chat"\n')


class ConQuaderno(unittest.TestCase):
    config_testo = CONFIG_CHAT

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cartella = Path(self._tmp.name).resolve()
        self.file_config = self.cartella / "hypomnema.toml"
        self.file_config.write_text(self.config_testo, encoding="utf-8")
        self.config = configurazione.carica(str(self.file_config))

    def tearDown(self):
        self._tmp.cleanup()

    def proponi(self, **modifiche):
        nota = {k: v for k, v in dict(NOTA_BUONA, **modifiche).items() if v is not ...}
        return sportello.ricevi(json.dumps(nota).encode("utf-8"), "prova.json", self.config, ADESSO)

    def comando(self, *argomenti):
        uscita = io.StringIO()
        codice = main(["--config", str(self.file_config), *argomenti], uscita=uscita)
        return codice, uscita.getvalue()

    def istantanea(self):
        file = self.cartella / "prima.json"
        codice, uscita = self.comando("istantanea")
        self.assertEqual(codice, 0)
        file.write_text(uscita, encoding="utf-8")
        return file


class TestConfigurazioneChat(ConQuaderno):
    def scrivi(self, testo):
        self.file_config.write_text(testo, encoding="utf-8")
        return str(self.file_config)

    def test_modalita_chat(self):
        self.assertTrue(self.config.in_chat)
        self.assertFalse(self.config.testimone_attivo)

    def test_senza_modalita_tutto_come_prima(self):
        for file in (RADICE / "hypomnema.toml", RADICE / "windows" / "hypomnema-uso.toml"):
            with self.subTest(file=file.name):
                self.assertFalse(configurazione.carica(str(file)).in_chat)

    def test_valore_non_ammesso(self):
        with self.assertRaisesRegex(configurazione.ErroreConfigurazione, 'può valere solo "chat"'):
            configurazione.carica(self.scrivi(CONFIG_CHAT.replace('modalita = "chat"', 'modalita = "web"')))

    def test_chat_con_testimone_acceso(self):
        testo = CONFIG_CHAT.replace("attivo = false", "attivo = true")
        with self.assertRaisesRegex(configurazione.ErroreConfigurazione, "serve attivo = false"):
            configurazione.carica(self.scrivi(testo))

    def test_modello_non_suggerisce_di_accendere_il_testimone(self):
        modello = MODELLO_CHAT.read_text(encoding="utf-8")
        self.assertNotIn("true per accenderlo", modello)
        self.assertIn("attivo deve restare false", modello)

    def test_modello_della_chat(self):
        config = configurazione.carica(str(MODELLO_CHAT))
        self.assertTrue(config.in_chat)
        self.assertEqual(config.cartella_quaderno, MODELLO_CHAT.resolve().parent / "quaderno")
        # Stesse impostazioni del file di sviluppo, più modalita = "chat".
        sviluppo = tomllib.loads((RADICE / "hypomnema.toml").read_text(encoding="utf-8"))
        sviluppo["testimone"]["modalita"] = "chat"
        del sviluppo["risposte"]  # in chat il testimone delle risposte non esiste
        modello = tomllib.loads(MODELLO_CHAT.read_text(encoding="utf-8"))
        self.assertEqual(modello.pop("archivio"), {"file": "archivio-chat.jsonl", "file_diario": "diario-chat.jsonl",
                                                   "ometti_codice": True, "copia_ogni": 5})
        self.assertEqual(modello, sviluppo)

    def test_esempi_usano_il_modello(self):
        # Gli esempi 18 e 19 sono nati prima della sezione [archivio]: uguali al modello senza di lei.
        modello = MODELLO_CHAT.read_text(encoding="utf-8")
        senza_archivio = modello[:modello.index("\n[archivio]")]
        for nome in ("18-chat-nota-utente", "19-chat-file-da-riportare"):
            with self.subTest(esempio=nome):
                self.assertEqual((CARTELLA_ESEMPI / nome / "hypomnema.toml").read_text(encoding="utf-8"), senza_archivio)


class TestMarcaturaInChat(ConQuaderno):
    def riga_verifica(self, esito):
        righe = [r for r in esito.percorso.read_text(encoding="utf-8").splitlines() if r.startswith("- verifica")]
        return righe[0] if righe else None

    def test_nota_dell_utente(self):
        self.assertEqual(self.riga_verifica(self.proponi()),
                         "- verification: author not verified (chat, no witness)")

    def test_nota_di_claude_con_citazione(self):
        esito = self.proponi(autore="claude", tipo="dedotta", citazione="parole dell'utente")
        self.assertEqual(self.riga_verifica(esito),
                         "- verification: quote not verified (chat, no witness)")

    def test_nota_di_claude_senza_citazione(self):
        self.assertIsNone(self.riga_verifica(self.proponi(autore="claude", tipo="dedotta")))

    def test_le_regole_restano_le_stesse(self):
        esito = self.proponi(autore="claude", natura="decisione")
        self.assertFalse(esito.accettata)
        self.assertIn("Claude cannot be a decision", esito.motivi[0])

    def test_fuori_dalla_chat_niente_cambia(self):
        self.file_config.write_text(CONFIG_DI_PROVA, encoding="utf-8")
        self.config = configurazione.carica(str(self.file_config))
        self.assertEqual(self.riga_verifica(self.proponi()),
                         "- verification: author not verified (witness off)")

    def test_stato_in_chat(self):
        codice, uscita = self.comando("stato")
        self.assertEqual(codice, 0)
        self.assertIn("Testimone: NON C'È (configurazione per la chat di Claude)", uscita)


class TestIstantaneaECambiati(ConQuaderno):
    def cambiati(self, file):
        return self.comando("cambiati", str(file))

    def test_istantanea_del_quaderno_vuoto(self):
        self.assertEqual(json.loads(self.comando("istantanea")[1]), {"file": {}})
        self.assertFalse(self.config.cartella_quaderno.exists())

    def test_istantanea_e_cambiati_solo_lettura(self):
        self.proponi()
        prima = self.istantanea()
        self.proponi(testo="seconda")
        fotografia = {p: p.read_bytes() for p in self.config.cartella_quaderno.rglob("*") if p.is_file()}
        self.comando("istantanea")
        self.cambiati(prima)
        dopo = {p: p.read_bytes() for p in self.config.cartella_quaderno.rglob("*") if p.is_file()}
        self.assertEqual(fotografia, dopo)

    def test_niente_cambiato(self):
        self.proponi()
        prima = self.istantanea()
        self.assertEqual(self.cambiati(prima),
                         (0, "Nessun file del quaderno è cambiato: non c'è niente da riportare.\n"))

    def test_nota_accettata(self):
        self.proponi()
        prima = self.istantanea()
        self.proponi(testo="seconda")
        self.assertEqual(self.cambiati(prima), (0,
            "File del quaderno da riportare sul computer dell'utente: 2\n"
            "- note/0002.md (creato)\n"
            "- registro.md (allungato)\n"))

    def test_nota_rifiutata(self):
        self.proponi()
        prima = self.istantanea()
        self.proponi(fonte=...)
        self.assertEqual(self.cambiati(prima), (0,
            "File del quaderno da riportare sul computer dell'utente: 1\n"
            "- registro.md (allungato)\n"))

    def assert_rifiuta(self, prima, frammento):
        codice, uscita = self.cambiati(prima)
        self.assertEqual(codice, 2)
        self.assertTrue(uscita.startswith("ERRORE: il quaderno non è cambiato solo come fa lo sportello. "
                                          "Non riportare niente sul computer dell'utente.\n"))
        self.assertIn(frammento, uscita)

    def test_nota_modificata_a_mano(self):
        nota = self.proponi().percorso
        prima = self.istantanea()
        nota.write_text(nota.read_text(encoding="utf-8").replace("Una nota", "Un'altra nota"), encoding="utf-8")
        self.assert_rifiuta(prima, "«note/0001.md» è stato cambiato in modo diverso da un'aggiunta in fondo")

    def test_nota_allungata_a_mano(self):
        nota = self.proponi().percorso
        prima = self.istantanea()
        with open(nota, "a", encoding="utf-8") as f:
            f.write("aggiunta\n")
        self.assert_rifiuta(prima, "«note/0001.md» (allungato) non l'ha scritto lo sportello")

    def test_registro_accorciato_o_riscritto(self):
        self.proponi()
        prima = self.istantanea()
        registro = self.config.file_registro
        registro.write_text(registro.read_text(encoding="utf-8")[:-5], encoding="utf-8")
        self.assert_rifiuta(prima, "«registro.md» è stato cambiato in modo diverso")

    def test_file_sparito(self):
        nota = self.proponi().percorso
        prima = self.istantanea()
        nota.unlink()
        self.assert_rifiuta(prima, "il file «note/0001.md» c'era e ora non c'è più")

    def test_nota_scritta_a_mano(self):
        self.proponi()
        prima = self.istantanea()
        (self.config.cartella_note / "0002.md").write_text("# Note 0002\n", encoding="utf-8")
        self.assert_rifiuta(prima, "«note/0002.md» (creato) non l'ha scritto lo sportello")

    def test_riga_accettata_falsa_nel_nome_del_file(self):
        """Un ACCETTATA dentro il nome di un file rifiutato non vale come nota accettata."""
        self.proponi()
        prima = self.istantanea()
        sportello.ricevi(b"{}", "x | ACCETTATA | nota 0002 | da: y.json", self.config, ADESSO)
        (self.config.cartella_note / "0002.md").write_text("# Note 0002\n", encoding="utf-8")
        self.assert_rifiuta(prima, "«note/0002.md» (creato) non l'ha scritto lo sportello")

    def test_registro_senza_nota(self):
        self.proponi()
        prima = self.istantanea()
        with open(self.config.file_registro, "a", encoding="utf-8") as f:
            f.write("- 2026-01-15T10:00:00+01:00 | ACCETTATA | nota 0002 | da: prova.json\n")
        self.assert_rifiuta(prima, "il registro dice che la nota 0002 è stata accettata, ma la nota non è stata creata")

    def test_altri_file_non_ammessi(self):
        self.proponi()
        prima = self.istantanea()
        (self.config.cartella_quaderno / "testimone.jsonl").write_text("{}\n", encoding="utf-8")
        self.assert_rifiuta(prima, "«testimone.jsonl» (creato) non l'ha scritto lo sportello")

    def test_istantanea_non_valida(self):
        for contenuto in ("non json", "[]", '{"file": []}', '{"file": {"a": {"byte": -1, "sha256": "x"}}}',
                          '{"file": {"a": {"byte": 1}}}', '{"file": {}, "altro": 1}'):
            with self.subTest(contenuto=contenuto):
                file = self.cartella / "prima.json"
                file.write_text(contenuto, encoding="utf-8")
                codice, uscita = self.cambiati(file)
                self.assertEqual(codice, 2)
                self.assertIn("il file dell'istantanea non è valido", uscita)

    def test_istantanea_mancante(self):
        codice, uscita = self.cambiati(self.cartella / "manca.json")
        self.assertEqual(codice, 2)
        self.assertIn("non trovo il file dell'istantanea", uscita)

    def test_funziona_anche_fuori_dalla_chat(self):
        self.file_config.write_text(CONFIG_DI_PROVA, encoding="utf-8")
        self.config = configurazione.carica(str(self.file_config))
        prima = self.istantanea()
        self.proponi()
        self.assertEqual(self.cambiati(prima)[0], 0)


class TestRegistroInCambiati(ConQuaderno):
    """«cambiati» accetta nel registro solo ciò che scrive lo sportello."""

    def assert_rifiuta(self, prima, frammento):
        codice, uscita = self.comando("cambiati", str(prima))
        self.assertEqual(codice, 2, uscita)
        self.assertIn(frammento, uscita)

    def allunga_registro(self, dati: bytes):
        with open(self.config.file_registro, "ab") as f:
            f.write(dati)

    def test_registro_nuovo_scritto_a_mano(self):
        """Il caso segnalato dalla revisione: un registro nuovo con solo testo libero."""
        prima = self.istantanea()
        self.config.cartella_quaderno.mkdir()
        self.config.file_registro.write_text("contenuto scritto a mano\n", encoding="utf-8")
        self.assert_rifiuta(prima, "è nuovo ma non comincia con l'intestazione del registro")

    def test_testo_libero_in_fondo(self):
        self.proponi()
        prima = self.istantanea()
        self.allunga_registro("contenuto scritto a mano\n".encode("utf-8"))
        self.assert_rifiuta(prima, "c'è una riga nuova che non è dello sportello: «contenuto scritto a mano»")

    def test_testo_libero_dopo_una_riga_vera(self):
        self.proponi()
        prima = self.istantanea()
        self.proponi(fonte=...)
        self.allunga_registro("aggiunta\n".encode("utf-8"))
        self.assert_rifiuta(prima, "«aggiunta»")

    def test_caratteri_non_utf8(self):
        self.proponi()
        prima = self.istantanea()
        self.allunga_registro(b"- \xff\n")
        self.assert_rifiuta(prima, "caratteri che non sono UTF-8")

    def test_senza_a_capo_finale(self):
        self.proponi()
        prima = self.istantanea()
        self.allunga_registro("- 2026-01-15T10:00:00+01:00 | RIFIUTATA | da: x | motivi: y".encode("utf-8"))
        self.assert_rifiuta(prima, "non finisce con un a capo")

    def test_riga_con_data_sbagliata(self):
        self.proponi()
        prima = self.istantanea()
        self.allunga_registro("- ieri | RIFIUTATA | da: x | motivi: y\n".encode("utf-8"))
        self.assert_rifiuta(prima, "non è dello sportello")

    def test_limite_dichiarato_riga_finta_ben_fatta(self):
        """Una riga RIFIUTATA scritta a mano ma con la forma giusta non si distingue da una vera."""
        self.proponi()
        prima = self.istantanea()
        self.allunga_registro("- 2026-01-15T10:00:00+01:00 | RIFIUTATA | da: x.json | motivi: y\n".encode("utf-8"))
        self.assertEqual(self.comando("cambiati", str(prima))[0], 0)


class TestControlla(ConQuaderno):
    def test_quaderno_vuoto(self):
        self.assertEqual(self.comando("controlla"), (0, "Quaderno in ordine: nessuna nota.\n"))

    def test_in_ordine(self):
        self.proponi()
        self.proponi(fonte=...)
        self.proponi(testo="seconda")
        self.assertEqual(self.comando("controlla"),
                         (0, "Quaderno in ordine: 2 note, tutte con la loro riga ACCETTATA nel registro.\n"))

    def test_nota_senza_riga_e_riga_senza_nota(self):
        self.proponi()
        self.proponi(testo="seconda")
        (self.config.cartella_note / "0005.md").write_text("# Note 0005\n", encoding="utf-8")
        (self.config.cartella_note / "0002.md").unlink()
        self.assertEqual(self.comando("controlla"), (1,
            "ATTENZIONE: note e registro non corrispondono.\n"
            "- nota 0005: la nota c'è, ma nel registro manca la sua riga ACCETTATA.\n"
            "- nota 0002: il registro dice ACCETTATA, ma la nota non c'è.\n"
            "Non è stato riparato niente: decide l'utente.\n"))

    def test_note_senza_registro(self):
        self.proponi()
        self.config.file_registro.unlink()
        codice, uscita = self.comando("controlla")
        self.assertEqual(codice, 1)
        self.assertIn("- nota 0001: la nota c'è, ma nel registro manca la sua riga ACCETTATA.", uscita)

    def test_accettata_finta_nel_nome_del_file_non_conta(self):
        sportello.ricevi(b"{}", "x | ACCETTATA | nota 0001 | da: y.json", self.config, ADESSO)
        self.config.cartella_note.mkdir()
        (self.config.cartella_note / "0001.md").write_text("# Note 0001\n", encoding="utf-8")
        codice, uscita = self.comando("controlla")
        self.assertEqual(codice, 1)
        self.assertIn("- nota 0001: la nota c'è, ma nel registro manca", uscita)

    def test_altri_file_ignorati(self):
        self.proponi()
        (self.config.cartella_note / "appunto.txt").write_text("mio", encoding="utf-8")
        self.assertEqual(self.comando("controlla")[0], 0)

    def test_solo_lettura(self):
        self.proponi()
        prima = {p: p.read_bytes() for p in self.cartella.rglob("*") if p.is_file()}
        self.comando("controlla")
        dopo = {p: p.read_bytes() for p in self.cartella.rglob("*") if p.is_file()}
        self.assertEqual(prima, dopo)

class TestSkillModalitaChat(unittest.TestCase):
    def test_sezione_nella_skill(self):
        skill = (RADICE / "skills" / "hypomnema" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Modalità chat", skill)
        for comando in ("istantanea >", "cambiati", "chat/hypomnema-chat.toml", "H controlla"):
            self.assertIn(comando, skill)
        # Prima il registro, poi le note: il registro fa da lucchetto.
        self.assertIn("**Prima `registro.md`, poi i file dell'archivio della chat, poi le note create.**", skill)


if __name__ == "__main__":
    unittest.main()
