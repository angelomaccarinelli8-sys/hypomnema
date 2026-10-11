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

    def test_modello_della_chat(self):
        config = configurazione.carica(str(MODELLO_CHAT))
        self.assertTrue(config.in_chat)
        self.assertEqual(config.cartella_quaderno, MODELLO_CHAT.resolve().parent / "quaderno")
        # Stesse impostazioni del file di sviluppo, più modalita = "chat".
        sviluppo = tomllib.loads((RADICE / "hypomnema.toml").read_text(encoding="utf-8"))
        sviluppo["testimone"]["modalita"] = "chat"
        self.assertEqual(tomllib.loads(MODELLO_CHAT.read_text(encoding="utf-8")), sviluppo)

    def test_esempi_usano_il_modello(self):
        modello = MODELLO_CHAT.read_text(encoding="utf-8")
        for nome in ("18-chat-nota-utente", "19-chat-file-da-riportare"):
            with self.subTest(esempio=nome):
                self.assertEqual((CARTELLA_ESEMPI / nome / "hypomnema.toml").read_text(encoding="utf-8"), modello)


class TestMarcaturaInChat(ConQuaderno):
    def riga_verifica(self, esito):
        righe = [r for r in esito.percorso.read_text(encoding="utf-8").splitlines() if r.startswith("- verifica")]
        return righe[0] if righe else None

    def test_nota_dell_utente(self):
        self.assertEqual(self.riga_verifica(self.proponi()),
                         "- verifica: autore non verificato (chat, senza testimone)")

    def test_nota_di_claude_con_citazione(self):
        esito = self.proponi(autore="claude", tipo="dedotta", citazione="parole dell'utente")
        self.assertEqual(self.riga_verifica(esito),
                         "- verifica: citazione non verificata (chat, senza testimone)")

    def test_nota_di_claude_senza_citazione(self):
        self.assertIsNone(self.riga_verifica(self.proponi(autore="claude", tipo="dedotta")))

    def test_le_regole_restano_le_stesse(self):
        esito = self.proponi(autore="claude", natura="decisione")
        self.assertFalse(esito.accettata)
        self.assertIn("Claude non può essere una decisione", esito.motivi[0])

    def test_fuori_dalla_chat_niente_cambia(self):
        self.file_config.write_text(CONFIG_DI_PROVA, encoding="utf-8")
        self.config = configurazione.carica(str(self.file_config))
        self.assertEqual(self.riga_verifica(self.proponi()),
                         "- verifica: autore non verificato (testimone spento)")

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
        (self.config.cartella_note / "0002.md").write_text("# Nota 0002\n", encoding="utf-8")
        self.assert_rifiuta(prima, "«note/0002.md» (creato) non l'ha scritto lo sportello")

    def test_riga_accettata_falsa_nel_nome_del_file(self):
        """Un ACCETTATA dentro il nome di un file rifiutato non vale come nota accettata."""
        self.proponi()
        prima = self.istantanea()
        sportello.ricevi(b"{}", "x | ACCETTATA | nota 0002 | da: y.json", self.config, ADESSO)
        (self.config.cartella_note / "0002.md").write_text("# Nota 0002\n", encoding="utf-8")
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


class TestSkillModalitaChat(unittest.TestCase):
    def test_sezione_nella_skill(self):
        skill = (RADICE / "plugin" / "skills" / "hypomnema" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Modalità chat", skill)
        for comando in ("istantanea >", "cambiati", "chat/hypomnema-chat.toml"):
            self.assertIn(comando, skill)


if __name__ == "__main__":
    unittest.main()
