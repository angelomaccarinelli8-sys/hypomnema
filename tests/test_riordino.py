"""Test della versione 0.9.0: il riordino del taccuino. Etichette retroattive (pezzo 2, E), integrare una nota
(pezzo 3, G), annullare una nota (pezzo 4, K). Solo dati inventati."""

import shutil
import tempfile
import unittest
from pathlib import Path

from hypomnema import configurazione, controllo
from hypomnema.cercatore import leggi
from hypomnema.nota import da_markdown
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


class TestIntegrare(ConLista):
    def setUp(self):
        super().setUp()
        self.accettata(kind="idea", text="Un pozzo per l'orto.")                    # 0001
        self.accettata(kind="idea", text="Il pozzo dell'orto con la pompa a mano.")  # 0002
        self.accettata(kind="idea", text="Un gioco per i bambini.")                 # 0003
        self.claude = dict(author="claude", knowledge="inferred")

    def test_g1_integrare_una_nota(self):
        self.assertEqual(self.accettata(integrates="0001", from_note="0002"), "0001.1")
        testo = self.file_nota("0001.1")
        self.assertIn("## Text\n\nUn pozzo per l'orto.\n\nIl pozzo dell'orto con la pompa a mano.\n", testo)
        self.assertIn("- change: integrated 0002\n", testo)
        self.assertIn("### From note 0002\n\n- date: 2026-01-15\n- source: prova\n- author: user\n"
                      "- verification: author not verified (witness off)\n", testo)
        self.assertNotIn("### Reason", testo)
        riletta = da_markdown("0001.1", testo)
        self.assertEqual(riletta.cambio.da_nota, ("0002", "2026-01-15", "prova", "user",
                                                  "author not verified (witness off)"))
        # La nota integrata: fuori dal recap e dalla ricerca di base, con --all la riga «integrata nella nota».
        _, base = self.comando("search", "pompa")
        self.assertIn("  I0001.1 2026-01-15 · user: integrata in fondo la nota 0002\n", base)
        self.assertIn("--- Nota I0001.1 ---", base)
        self.assertNotIn("--- Nota I0002 ---", base)
        self.assertIn("(1 nota chiusa non mostrata", base)
        _, tutte = self.comando("search", "pompa", "--all")
        self.assertIn("stato: integrata nella nota I0001.1 (2026-01-15): il suo testo è in fondo a quella nota", tutte)
        self.assertTrue(controllo.controlla(self.config).in_ordine)
        self.assertFalse((self.config.cartella_note / "0002.1.md").exists())  # la nota integrata non si tocca

    def test_g1_fuori_dal_recap(self):
        self.accettata(kind="todo", text="Scavare il pozzo nell'orto.")  # 0004
        self.accettata(kind="todo", text="Comprare la pompa per l'orto.")  # 0005
        self.accettata(integrates="0004", from_note="0005")
        recap = self.comando("recap")[1]
        self.assertNotIn("T0005", recap)
        self.assertIn("- [T0004.1] 2026-01-15: Scavare il pozzo nell'orto. …", recap)
        self.assertIn("    ↳ T0004.1 2026-01-15 · user: integrata in fondo la nota 0005", recap)
        self.assertEqual(self.comando("review")[0], 0)

    def test_g2_senza_cosa_in_comune(self):
        self.assertIn("have no COSA label in common", self.motivi(integrates="0001", from_note="0003"))

    def test_g3_claude_non_integra_le_note_dell_utente(self):
        self.assertIn("only the user can integrate it", self.motivi(integrates="0001", from_note="0002", **self.claude))

    def test_g4_niente_testo_con_from_note(self):
        self.assertIn("remove «text»", self.motivi(integrates="0001", from_note="0002", text="Altro."))

    def test_g5_gia_integrata_o_autori_diversi(self):
        self.accettata(integrates="0001", from_note="0002")
        self.accettata(kind="idea", text="Ancora l'orto.")  # 0004
        self.assertIn("already integrated", self.motivi(integrates="0004", from_note="0002"))
        self.accettata(kind="idea", text="L'orto di Claude.", **self.claude)  # 0005
        self.assertIn("have different authors", self.motivi(integrates="0004", from_note="0005"))
        self.assertIn("same note", self.motivi(integrates="0004", from_note="0004"))
        self.assertIn("«from_note» goes only with «integrates»", self.motivi(kind="idea", from_note="0004", text="x"))

    def test_g6_parole_nuove(self):
        self.assertEqual(self.accettata(integrates="0003", text="Con le corde e le palline."), "0003.1")
        testo = self.file_nota("0003.1")
        self.assertIn("## Text\n\nUn gioco per i bambini.\n\nCon le corde e le palline.\n", testo)
        self.assertIn("- change: text added\n", testo)
        self.assertIn("- change: text added\n- verification: author not verified (witness off)\n", testo)

    def test_g7_niente_tipo_e_non_le_chiuse(self):
        self.assertIn("«kind» is not allowed", self.motivi(integrates="0003", kind="todo", text="x"))
        self.accettata(kind="todo", text="Annaffiare l'orto.")  # 0004
        self.accettata(done="0004", text="Fatto.")
        self.assertIn("is closed or integrated", self.motivi(integrates="0004", text="Anche le aiuole."))

    def test_g8_claude_non_aggiunge_parole_alle_note_dell_utente(self):
        self.assertIn("only «user» can add words to it", self.motivi(integrates="0003", text="Idea mia.", **self.claude))
        self.accettata(kind="idea", text="Un'aiuola.", **self.claude)  # 0004
        self.assertEqual(self.accettata(integrates="0004", text="Con le margherite.", **self.claude), "0004.1")

    def test_g6_con_il_testimone(self):
        from hypomnema import configurazione as conf
        self.file_config.write_text(self.file_config.read_text(encoding="utf-8").replace("attivo = false",
                                                                                       "attivo = true"),
                                    encoding="utf-8")
        self.config = conf.carica(str(self.file_config))
        self.assertIn("is not found, word for word", self.motivi(integrates="0003", text="Parole mai dette."))


if __name__ == "__main__":
    unittest.main()
