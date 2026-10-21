"""Test della versione 0.9.0: il riordino del taccuino. Etichette retroattive (pezzo 2, E), integrare una nota
(pezzo 3, G), annullare una nota (pezzo 4, K). Solo dati inventati."""

import shutil
import tempfile
import unittest
from pathlib import Path

from hypomnema import configurazione, controllo
from hypomnema.cercatore import leggi
from tests.esecutore import CONFIG_DI_PROVA, RADICE
from tests.test_etichette import ConEtichette

LISTA = 'chi = ["Anna", "Marco"]\ncosa = ["orto", "gioco"]\n'


class ConLista(ConEtichette):
    lista = LISTA

    def scrivi_lista(self, testo):
        (self.config.cartella_quaderno / "etichette.toml").write_text(testo, encoding="utf-8")

    def file_del_quaderno(self):
        return {p: p.read_bytes() for p in self.config.cartella_quaderno.rglob("*") if p.is_file()}


class TestEtichetteRetroattive(ConLista):
    def setUp(self):
        super().setUp()
        # Note «vecchie»: scritte senza lista, quindi senza COSA dal testo nel file.
        (self.config.cartella_quaderno / "etichette.toml").unlink()
        self.accettata(kind="todo", text="Seminare l'orto.")
        self.accettata(kind="fact", text="Il bilancio di casa è in ordine.")
        self.scrivi_lista(LISTA)

    def test_e1_le_note_vecchie_prendono_le_cosa(self):
        self.assertNotIn("- about:", self.file_nota("0001"))
        codice, uscita = self.comando("search", "--about", "orto")
        self.assertEqual(codice, 0)
        self.assertIn("--- Nota T0001 ---", uscita)
        self.assertIn("etichette dal testo (messe dallo sportello): cosa orto", uscita)
        self.assertIn("- orto: 1 nota (1 aperta): 1 dal testo, 0 proposte", self.comando("labels")[1])
        self.assertIn("· cosa: orto", self.comando("recap")[1])
        self.assertIn("- T0001 · orto · dal testo: «Seminare l'[orto].»", self.comando("matches")[1])

    def test_e2_un_etichetta_nuova_vale_subito_e_i_file_non_cambiano(self):
        prima = self.file_del_quaderno()
        self.scrivi_lista('cosa = ["orto", "bilancio"]\n')
        self.assertIn("--- Nota F0002 ---", self.comando("search", "--about", "bilancio")[1])
        dopo = self.file_del_quaderno()
        dopo.pop(self.config.cartella_quaderno / "etichette.toml")
        prima.pop(self.config.cartella_quaderno / "etichette.toml")
        self.assertEqual(dopo, prima)

    def test_e3_quelle_a_mano_restano(self):
        self.accettata(kind="fact", about="gioco", text="Il prato.")
        storia = leggi(self.config).storie["0003"]
        self.assertEqual((storia.ultima.contenuto.cosa, storia.ultima.contenuto.cosa_dal_testo), (("gioco",), None))

    def test_e4_lista_scritta_male(self):
        self.scrivi_lista('cosa = "orto"\n')
        codice, uscita = self.comando("recap")
        self.assertEqual(codice, 0)
        self.assertTrue(uscita.startswith("Attenzione: etichette.toml è scritto male ("))
        self.assertIn("le COSA dal testo non sono calcolate.\nDove eravamo rimasti", uscita)
        file = self.cartella / "p.json"
        file.write_text('{"date": "2026-01-15", "source": "s", "author": "user", "knowledge": "stated", '
                        '"kind": "fact", "text": "x"}', encoding="utf-8")
        self.assertEqual(self.comando("propose", str(file))[0], 2)  # lo sportello si ferma, come nella 0.8.0

    def test_e5_quaderno_della_0_8_0(self):
        cartella = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, cartella)
        shutil.copytree(RADICE / "esempi" / "65-etichette-e-versioni" / "atteso" / "quaderno", cartella / "quaderno")
        prima = {p: p.read_bytes() for p in (cartella / "quaderno").rglob("*") if p.is_file()}
        (cartella / "hypomnema.toml").write_text(CONFIG_DI_PROVA, encoding="utf-8")
        config = configurazione.carica(str(cartella / "hypomnema.toml"))
        self.assertTrue(controllo.controlla(config).in_ordine)
        leggi(config)
        self.assertEqual({p: p.read_bytes() for p in (cartella / "quaderno").rglob("*") if p.is_file()}, prima)


if __name__ == "__main__":
    unittest.main()
