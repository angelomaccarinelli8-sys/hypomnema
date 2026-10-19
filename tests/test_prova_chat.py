"""Test delle correzioni nate dalla prova dal vero in chat (11/10/2026). Solo dati inventati."""

import io
import os
import tempfile
import unittest
from pathlib import Path

from hypomnema import registro, sportello
from hypomnema.cli import main
from hypomnema.registro import INTESTAZIONE
from tests.esecutore import RADICE, testo_della_skill
from tests.test_chat import ConQuaderno
from tests.test_regole import ADESSO

RIGA_VERA = "- 2026-01-15T10:00:00+01:00 | ACCETTATA | nota 0001 | da: proposta.json\n"


def fotografia(cartella: Path) -> dict:
    return {p: p.read_bytes() for p in cartella.rglob("*") if p.is_file()}


class TestSportelloRegistroToccato(ConQuaderno):
    """Punto 2: se il registro non finisce con un a capo, lo sportello non scrive niente."""

    def tocca_registro(self, testo: str):
        self.config.cartella_quaderno.mkdir(parents=True, exist_ok=True)
        self.config.file_registro.write_bytes(testo.encode("utf-8"))

    def test_nota_valida_non_scritta(self):
        self.proponi()
        with open(self.config.file_registro, "ab") as f:
            f.write("riga scritta a mano".encode("utf-8"))
        prima = fotografia(self.cartella)
        with self.assertRaises(registro.RegistroToccato):
            self.proponi(testo="seconda")
        self.assertEqual(fotografia(self.cartella), prima)
        self.assertFalse((self.config.cartella_note / "0002.md").exists())

    def test_proposta_non_valida_non_annotata(self):
        self.tocca_registro(INTESTAZIONE + "riga scritta a mano")
        prima = fotografia(self.cartella)
        with self.assertRaises(registro.RegistroToccato):
            sportello.ricevi(b"{}", "prova.json", self.config, ADESSO)
        self.assertEqual(fotografia(self.cartella), prima)

    def test_registro_vuoto(self):
        self.tocca_registro("")
        with self.assertRaises(registro.RegistroToccato):
            self.proponi()

    def test_dalla_riga_di_comando(self):
        self.tocca_registro(INTESTAZIONE + "riga scritta a mano")
        proposta = self.cartella / "nota.json"
        proposta.write_text('{"data": "2026-01-15"}', encoding="utf-8")
        codice, uscita = self.comando("proponi", str(proposta))
        self.assertEqual(codice, 2)
        self.assertTrue(uscita.startswith("ERRORE: il registro è stato toccato a mano: non finisce con un a capo"))
        self.assertIn("Non ho scritto niente, né la nota né la riga nel registro.", uscita)

    def test_registro_in_ordine_si_scrive(self):
        self.tocca_registro(INTESTAZIONE + RIGA_VERA)
        self.assertTrue(self.proponi().accettata)


class TestCambiatiInizioRiga(ConQuaderno):
    """Punto 2: il pezzo aggiunto al registro deve cominciare all'inizio di una riga."""

    def test_pezzo_attaccato_a_una_riga_scritta_a_mano(self):
        self.proponi()
        with open(self.config.file_registro, "ab") as f:
            f.write("riga scritta a mano".encode("utf-8"))
        prima = self.istantanea()
        # Come faceva lo sportello prima della correzione: la sua riga in fondo, attaccata.
        with open(self.config.file_registro, "ab") as f:
            f.write("- 2026-01-15T10:01:00+01:00 | RIFIUTATA | da: x.json | motivi: y\n".encode("utf-8"))
        codice, uscita = self.comando("cambiati", str(prima))
        self.assertEqual(codice, 2)
        self.assertIn("non comincia all'inizio di una riga", uscita)


class TestControllaRigheEstranee(ConQuaderno):
    """Punto 3: «controlla» segnala le righe che non sono dello sportello, con il numero."""

    def scrivi_registro(self, testo: str):
        self.config.cartella_quaderno.mkdir(parents=True, exist_ok=True)
        self.config.file_registro.write_bytes(testo.encode("utf-8"))  # byte esatti, anche su Windows

    def test_riga_estranea_in_mezzo(self):
        self.proponi()
        with open(self.config.file_registro, "ab") as f:
            f.write("riga scritta a mano\n".encode("utf-8"))
        self.proponi(fonte=...)
        codice, uscita = self.comando("controlla")
        self.assertEqual(codice, 1)
        self.assertIn("- registro, riga 6: «riga scritta a mano» non è una riga dello sportello.", uscita)
        self.assertNotIn("riga 7", uscita)

    def test_il_caso_della_prova(self):
        self.proponi()
        (self.config.cartella_note / "0002.md").write_text("# Note 0002\n", encoding="utf-8")
        with open(self.config.file_registro, "ab") as f:
            f.write("riga scritta a mano- 2026-10-11T18:47:33+02:00 | ACCETTATA | nota 0002 | da: proposta.json\n"
                    .encode("utf-8"))
        codice, uscita = self.comando("controlla")
        self.assertEqual(codice, 1)
        self.assertIn("- registro, riga 6: «riga scritta a mano- 2026-10-11T18:47:33+02:00", uscita)
        self.assertIn("- nota 0002: la nota c'è, ma nel registro manca la sua riga ACCETTATA.", uscita)

    def test_senza_a_capo_finale(self):
        self.scrivi_registro(INTESTAZIONE + RIGA_VERA.rstrip("\n"))
        self.config.cartella_note.mkdir()
        (self.config.cartella_note / "0001.md").write_text("# Note 0001\n", encoding="utf-8")
        codice, uscita = self.comando("controlla")
        self.assertEqual(codice, 1)
        self.assertIn("- il registro non finisce con un a capo", uscita)
        self.assertNotIn("non è una riga dello sportello", uscita)  # la riga in sé è giusta

    def test_senza_intestazione(self):
        self.scrivi_registro("titolo cambiato\n" + RIGA_VERA)
        self.config.cartella_note.mkdir()
        (self.config.cartella_note / "0001.md").write_text("# Note 0001\n", encoding="utf-8")
        codice, uscita = self.comando("controlla")
        self.assertEqual(codice, 1)
        self.assertIn("- il registro non comincia con la sua intestazione.", uscita)
        self.assertIn("- registro, riga 1: «titolo cambiato»", uscita)

    def test_registro_vero_in_ordine(self):
        self.proponi()
        self.proponi(fonte=...)
        self.assertEqual(self.comando("controlla")[0], 0)


class TestConfronta(unittest.TestCase):
    """Punto 1: due file identici byte per byte? Solo lettura, senza configurazione."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cartella = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def file(self, nome, dati: bytes):
        percorso = self.cartella / nome
        percorso.write_bytes(dati)
        return str(percorso)

    def confronta(self, a, b):
        uscita = io.StringIO()
        vecchia = os.getcwd()
        os.chdir(self.cartella)  # qui non c'è nessun hypomnema.toml
        try:
            codice = main(["confronta", a, b], uscita=uscita)
        finally:
            os.chdir(vecchia)
        return codice, uscita.getvalue()

    def test_uguali(self):
        a, b = self.file("a", b"stesso testo\n"), self.file("b", b"stesso testo\n")
        self.assertEqual(self.confronta(a, b),
                         (0, f"UGUALI: «{a}» e «{b}» sono identici byte per byte (13 byte).\n"))

    def test_diversi(self):
        a, b = self.file("a", b"nota 0001\n"), self.file("b", b"nota 0002\n")
        codice, uscita = self.confronta(a, b)
        self.assertEqual(codice, 1)
        self.assertIn("la prima differenza è al byte 9.", uscita)

    def test_uno_e_l_inizio_dell_altro(self):
        a, b = self.file("a", b"riga\n"), self.file("b", b"riga\naltra\n")
        codice, uscita = self.confronta(a, b)
        self.assertEqual(codice, 1)
        self.assertIn("(5 byte)", uscita)
        self.assertIn("(11 byte)", uscita)
        self.assertIn("la prima differenza è al byte 6.", uscita)

    def test_copia_vecchia_della_prova(self):
        """Il caso della prova: sul computer è arrivata la versione precedente del registro."""
        nuovo = INTESTAZIONE + RIGA_VERA + "- 2026-01-15T10:01:00+01:00 | RIFIUTATA | da: x | motivi: y\n"
        a, b = self.file("lavoro.md", nuovo.encode("utf-8")), self.file("computer.md", (INTESTAZIONE + RIGA_VERA).encode("utf-8"))
        self.assertEqual(self.confronta(a, b)[0], 1)

    def test_file_mancante(self):
        a = self.file("a", b"x")
        codice, uscita = self.confronta(a, str(self.cartella / "manca"))
        self.assertEqual(codice, 2)
        self.assertIn("non trovo il file", uscita)

    def test_solo_lettura(self):
        a, b = self.file("a", b"x"), self.file("b", b"y")
        prima = fotografia(self.cartella)
        self.confronta(a, b)
        self.assertEqual(fotografia(self.cartella), prima)


class TestSkill(unittest.TestCase):
    def setUp(self):
        self.skill = testo_della_skill()

    def test_riporto_da_cartella_nuova_e_verifica(self):
        self.assertIn("copy it into a **new folder** of the work computer, never used before in this chat", self.skill)
        self.assertIn("H compare ", self.skill)
        self.assertIn("**stop, do not write other files**", self.skill)

    def test_salvare_le_risposte_di_claude(self):
        self.assertIn("**«Salva questa risposta di Claude»**", self.skill)
        self.assertIn("**«Questa risposta la faccio mia»**", self.skill)
        self.assertIn("**only the piece that matters**", self.skill)


if __name__ == "__main__":
    unittest.main()
