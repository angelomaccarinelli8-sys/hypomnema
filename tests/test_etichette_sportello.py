"""Test della versione 0.8.0: le etichette COSA messe dallo sportello, trovate nel testo della nota.
Solo dati inventati."""

import shutil
import tempfile
import unittest
from pathlib import Path

from hypomnema import configurazione, controllo, etichette
from hypomnema.cercatore import leggi
from hypomnema.nota import da_markdown
from tests.esecutore import CONFIG_DI_PROVA, RADICE
from tests.test_etichette import ConEtichette

LISTA = 'chi = ["Anna", "Marco", "Luca"]\ncosa = ["orto", "bilancio", "gioco", "Famiglia", "orto botanico", "caffè"]\n'


class ConLista(ConEtichette):
    lista = LISTA

    def etichette_di(self, numero):
        nota = da_markdown(numero, self.file_nota(numero))
        return nota.chi, nota.cosa, nota.cosa_dal_testo

    def cosa_dal_testo(self, testo):
        return etichette.trova_nel_testo(testo, etichette.leggi(self.config.cartella_quaderno))


class TestParolaIntera(ConLista):
    def test_casi_a(self):
        for caso, testo, attese in (
            ("A1", "Seminare l'orto", ("orto",)),
            ("A2", "ORTO in ordine", ("orto",)),
            ("A3", "Pagare il bilancio. Rifare il bilancio.", ("bilancio",)),
            ("A4", "Ortografia da ripassare", ()),
            ("A5", "Un gioco giocoso", ("gioco",)),
            ("A6", "Visita all'orto\nbotanico", ("orto", "orto botanico")),
            ("A7", "i bilanci di casa", ()),
            ("A9", "è in gioco la scadenza", ("gioco",)),
            ("A10", "la famiglia del vicino", ("Famiglia",)),
            ("A11", "Spesa da Orto-Frutta", ("orto",)),
            ("A12", "un caffe al bar", ()),
            ("A13", "orto-giardino da rifare", ("orto",)),
        ):
            with self.subTest(caso=caso):
                self.assertEqual(self.cosa_dal_testo(testo), attese)

    def test_a8_chi_non_si_cerca_nel_testo(self):
        self.accettata(kind="fact", text="Seminare l'orto con Anna.")
        self.assertEqual(self.etichette_di("0001"), (None, ("orto",), ("orto",)))

    def test_senza_lista_niente(self):
        self.assertEqual(etichette.trova_nel_testo("l'orto", None), ())


class TestDoveSiCerca(ConLista):
    def test_b1_solo_nel_testo(self):
        self.accettata(kind="todo", text="Fatto!", context="riferito all'orto")
        self.assertEqual(self.etichette_di("0001"), (None, None, None))
        self.accettata(author="claude", knowledge="inferred", kind="idea", text="Un'idea.", quote="l'orto")
        self.assertEqual(self.etichette_di("0002"), (None, None, None))


class TestNellaNota(ConLista):
    def test_c1_c4(self):
        self.accettata(kind="fact", text="Seminare l'orto con Anna.")
        testo = self.file_nota("0001")
        self.assertIn("- kind: fact\n- about: orto\n- labels from text: about orto\n- verification:", testo)
        self.assertNotIn("- who:", testo)
        self.accettata(kind="todo", about="bilancio", text="Seminare l'orto entro marzo.")
        self.assertIn("- about: bilancio, orto\n- labels from text: about orto\n", self.file_nota("0002"))
        self.accettata(kind="fact", about="orto", text="L'orto è esposto a sud.")
        self.assertEqual(self.etichette_di("0003"), (None, ("orto",), None))
        self.assertNotIn("labels from text", self.file_nota("0003"))
        self.accettata(kind="todo", text="Comprare il pane.")
        self.assertNotIn("- about:", self.file_nota("0004"))

    def test_c5_c6_limiti_a_mano(self):
        self.assertIn("at most 2 «who» labels", self.motivi(kind="fact", who="Anna, Marco, Luca", text="x"))
        self.assertIn("at most 2 «about» labels", self.motivi(kind="fact", about="orto, bilancio, gioco", text="x"))

    def test_c7_nessun_limite_per_lo_sportello(self):
        self.accettata(kind="todo", text="Rivedere orto, bilancio, gioco e Famiglia.")
        self.assertEqual(self.etichette_di("0001")[1], ("orto", "bilancio", "gioco", "Famiglia"))

    def test_il_tipo_non_si_tocca(self):
        self.accettata(kind="idea", text="Un gioco per l'orto.")
        self.assertIn("- kind: idea\n", self.file_nota("0001"))

    def test_ricerca_e_filtri_sulle_etichette_finali(self):
        self.accettata(kind="todo", text="Seminare l'orto.")
        codice, uscita = self.comando("search", "--about", "orto")
        self.assertEqual(codice, 0)
        self.assertIn("cosa: orto\netichette dal testo (messe dallo sportello): cosa orto\n", uscita)
        self.assertIn("· cosa: orto", self.comando("recap", "--cosa", "orto")[1])


class TestVersioni(ConLista):
    def test_d1_le_etichette_seguono_il_testo(self):
        self.accettata(kind="todo", text="Comprare semi per l'orto.")
        self.accettata(corrects="0001", text="Comprare semi per il bilancio.")
        self.assertEqual(self.etichette_di("0001.1"), (None, ("bilancio",), ("bilancio",)))
        self.assertIn("- change: text corrected; about orto → bilancio\n", self.file_nota("0001.1"))

    def test_d2_quelle_a_mano_restano(self):
        self.accettata(kind="fact", about="orto", text="Annaffiare l'orto la sera.")
        self.accettata(corrects="0001", text="Annaffiare il prato la sera.")
        self.assertEqual(self.etichette_di("0001.1"), (None, ("orto",), None))

    def test_d3_lista_cambiata_e_chiusura(self):
        (self.config.cartella_quaderno / "etichette.toml").write_text('cosa = ["orto"]\n', encoding="utf-8")
        self.accettata(kind="todo", text="Rifare il gioco.")
        self.assertEqual(self.etichette_di("0001"), (None, None, None))
        (self.config.cartella_quaderno / "etichette.toml").write_text('cosa = ["orto", "gioco"]\n', encoding="utf-8")
        self.accettata(done="0001", text="Fatto.")
        self.assertEqual(self.etichette_di("0001.1"), (None, ("gioco",), ("gioco",)))
        self.assertIn("- change: closed; about → gioco\n", self.file_nota("0001.1"))

    def test_d4_d5_d6_permessi(self):
        self.accettata(kind="todo", text="Pulire l'orto.")
        claude = dict(author="claude", knowledge="inferred")
        self.assertEqual(self.accettata(updates="0001", about="Famiglia", text="Insieme.", **claude), "0001.1")
        self.assertEqual(self.etichette_di("0001.1"), (None, ("Famiglia", "orto"), ("orto",)))
        self.assertIn("only the user can change the labels",
                      self.motivi(updates="0001", about="Famiglia, bilancio", text="Costa.", **claude))
        self.accettata(kind="todo", text="Rifare il bilancio.")
        self.assertEqual(self.accettata(updates="0002", who="Anna", text="Lo fa Anna.", **claude), "0002.1")
        self.assertEqual(self.etichette_di("0002.1"), (("Anna",), ("bilancio",), ("bilancio",)))

    def test_la_correzione_dell_utente_resta_dell_utente(self):
        self.accettata(kind="todo", text="Seminare l'orto.")
        self.assertIn("only the user can correct it",
                      self.motivi(author="claude", knowledge="inferred", corrects="0001", text="Seminare il prato."))


class TestComandi(ConLista):
    def test_labels(self):
        self.accettata(kind="todo", text="Seminare l'orto.")
        self.accettata(kind="fact", about="orto", text="Il prato.")
        _, uscita = self.comando("labels")
        self.assertIn("- orto: 2 note (1 aperta): 1 dal testo, 1 proposta\n", uscita)
        self.assertIn("- Anna: 0 note\n", uscita)

    def test_status(self):
        self.assertIn("\nEtichette: etichette.toml letto bene: 3 CHI, 6 COSA. Lo sportello aggiunge da solo le COSA che "
                      "trova nel testo; le CHI si propongono a mano.\n", self.comando("status")[1])
        (self.config.cartella_quaderno / "etichette.toml").write_text('cosa = "orto"\n', encoding="utf-8")
        codice, uscita = self.comando("status")
        self.assertEqual(codice, 0)
        self.assertIn("\nEtichette: ERRORE in etichette.toml: nel file delle etichette", uscita)
        self.assertIn("Finché non è corretto lo sportello non salva niente.", uscita)
        # E lo sportello si ferma senza scrivere niente, nemmeno per una proposta senza etichette.
        file = self.cartella / "p.json"
        file.write_text('{"date": "2026-01-15", "source": "s", "author": "user", "knowledge": "stated", '
                        '"kind": "fact", "text": "x"}', encoding="utf-8")
        self.assertEqual(self.comando("propose", str(file))[0], 2)
        self.assertFalse((self.config.cartella_quaderno / "registro.md").exists())

    def test_matches(self):
        self.accettata(kind="todo", text="Domani mattina presto vado a seminare l'orto con Anna e poi pranzo.")
        self.accettata(kind="fact", about="bilancio", text="Il prato.")
        self.accettata(kind="todo", text="È in gioco la scadenza.")
        codice, uscita = self.comando("matches")
        self.assertEqual(codice, 0)
        self.assertEqual(uscita.splitlines()[2:], [
            "- T0001 · orto · dal testo: «… presto vado a seminare l'[orto] con Anna e poi …»",
            "- F0002 · bilancio · a mano, non nel testo",
            "- T0003 · gioco · dal testo: «È in [gioco] la scadenza.»",
        ])
        self.assertEqual(self.comando("riscontri", "--cosa", "gioco")[1].splitlines()[2:],
                         ["- T0003 · gioco · dal testo: «È in [gioco] la scadenza.»"])
        self.assertEqual(self.comando("matches", "--about", "Gioco")[0], 2)
        prima = {p: p.read_bytes() for p in self.config.cartella_quaderno.rglob("*") if p.is_file()}
        self.comando("matches")
        self.assertEqual({p: p.read_bytes() for p in self.config.cartella_quaderno.rglob("*") if p.is_file()}, prima)


class TestQuadernoDella070(unittest.TestCase):
    def test_note_e_lista_della_0_7_0(self):
        """Il quaderno dell'esempio 60 (scritto dalla 0.7.0): check pulito, file identici, tutte le etichette a mano."""
        cartella = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, cartella)
        shutil.copytree(RADICE / "esempi" / "60-etichette" / "atteso" / "quaderno", cartella / "quaderno")
        prima = {p: p.read_bytes() for p in (cartella / "quaderno").rglob("*") if p.is_file()}
        (cartella / "hypomnema.toml").write_text(CONFIG_DI_PROVA, encoding="utf-8")
        config = configurazione.carica(str(cartella / "hypomnema.toml"))
        self.assertTrue(controllo.controlla(config).in_ordine)
        self.assertIsNotNone(etichette.leggi(config.cartella_quaderno))  # la lista della 0.7.0 va bene così
        quaderno = leggi(config)
        self.assertTrue(all(s.ultima.contenuto.cosa_dal_testo is None for s in quaderno.elenco()))
        self.assertEqual({p: p.read_bytes() for p in (cartella / "quaderno").rglob("*") if p.is_file()}, prima)


if __name__ == "__main__":
    unittest.main()
