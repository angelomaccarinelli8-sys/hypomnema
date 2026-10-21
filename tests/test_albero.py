"""Test della versione 0.10.0: l'albero delle etichette (pezzo 1), la regola dell'integrazione allo sportello (pezzo 2),
le proposte a catena (pezzo 3), il grafo ad albero (pezzo 4). Solo dati inventati."""

import unittest

from hypomnema import albero, etichette
from hypomnema.cercatore import leggi
from tests.test_etichette import ConEtichette

LISTA = """chi = ["Anna"]
cosa = ["orto", "bilancio"]

[rami.orto]
pomodori = ["pomodori", "pomodoro"]
irrigazione = ["irrigazione", "goccia"]
"""


class ConAlbero(ConEtichette):
    lista = LISTA

    def scrivi_lista(self, testo):
        (self.config.cartella_quaderno / "etichette.toml").write_text(testo, encoding="utf-8")

    def lista_letta(self):
        return etichette.leggi(self.config.cartella_quaderno)


class TestFileDeiRami(ConAlbero):
    def test_rami_letti_nell_ordine_del_file(self):
        lista = self.lista_letta()
        self.assertEqual(lista.cosa, ("orto", "bilancio"))
        self.assertEqual(lista.sotto_rami_di("orto"), (("pomodori", ("pomodori", "pomodoro")),
                                                       ("irrigazione", ("irrigazione", "goccia"))))
        self.assertEqual(lista.sotto_rami_di("bilancio"), ())

    def test_senza_rami_tutto_come_prima(self):
        self.scrivi_lista('chi = ["Anna"]\ncosa = ["orto"]\n')
        lista = self.lista_letta()
        self.assertEqual((lista.chi, lista.cosa, lista.rami), (("Anna",), ("orto",), ()))

    def test_scritti_male(self):
        casi = (
            ('cosa = ["orto"]\n[rami.giardino]\nrose = ["rose"]\n', "[rami.giardino] non corrisponde a nessuna COSA"),
            ('cosa = ["orto"]\n[rami.orto]\npomodori = []\n', "il sotto-ramo «pomodori» di [rami.orto] non ha parole"),
            ('cosa = ["orto"]\n[rami.orto]\npomodori = "pomodori"\n', "deve essere una lista di parole"),
            ('cosa = ["orto"]\nrami = ["orto"]\n', "«rami» deve essere una tabella"),
            ('cosa = ["orto"]\n[rami.orto]\na = ["goccia"]\nb = ["Goccia"]\n',
             "la parola «Goccia» del sotto-ramo «b» di [rami.orto] è anche nel sotto-ramo «a»"),
            ('cosa = ["orto"]\n[rami.orto]\na = ["goccia", "goccia"]\n', "«goccia» del sotto-ramo «a» di [rami.orto] è "
                                                                        "ripetuta"),
            ('cosa = ["orto"]\n[rami.orto]\na = [" goccia"]\n', "ha spazi all'inizio o alla fine"),
            ('cosa = ["orto"]\nalberi = 1\n', "non prevede «alberi»"),
        )
        for testo, atteso in casi:
            with self.subTest(atteso=atteso):
                self.scrivi_lista(testo)
                with self.assertRaises(etichette.ErroreEtichette) as errore:
                    self.lista_letta()
                self.assertIn(atteso, str(errore.exception))
                self.assertIn("Non ho scritto niente.", str(errore.exception))

    def test_stessa_parola_in_due_rami_va_bene(self):
        self.scrivi_lista('cosa = ["orto", "bilancio"]\n[rami.orto]\nacqua = ["acqua"]\n[rami.bilancio]\n'
                          'bollette = ["acqua"]\n')
        self.assertEqual(len(self.lista_letta().rami), 2)


class TestSottoRami(ConAlbero):
    def test_serve_la_cosa_del_ramo(self):
        lista = self.lista_letta()
        self.assertEqual(etichette.sotto_rami("I pomodori.", None, lista), ())
        self.assertEqual(etichette.sotto_rami("I pomodori.", ("orto",), lista), (("orto", "pomodori"),))
        self.assertEqual(etichette.sotto_rami("Pomodoro e goccia.", ("orto",), lista),
                         (("orto", "pomodori"), ("orto", "irrigazione")))

    def test_il_nome_non_conta_come_parola(self):
        self.scrivi_lista('cosa = ["orto"]\n[rami.orto]\nsemina = ["seminare"]\n')
        lista = self.lista_letta()
        self.assertEqual(etichette.sotto_rami("La semina dell'orto.", ("orto",), lista), ())
        self.assertEqual(etichette.sotto_rami("Seminare l'orto.", ("orto",), lista), (("orto", "semina"),))

    def test_parola_intera(self):
        lista = self.lista_letta()
        self.assertEqual(etichette.sotto_rami("Gocciolare nell'orto.", ("orto",), lista), ())

    def test_si_calcolano_alla_lettura(self):
        self.scrivi_lista('cosa = ["orto"]\n')
        self.accettata(kind="idea", text="Nell'orto i pomodori vicino al muro.")
        prima = self.file_nota("0001")
        self.scrivi_lista(LISTA)
        storia = leggi(self.config).storie["0001"]
        self.assertEqual(albero.sotto_rami_visti(storia, self.lista_letta()), (("orto", "pomodori"),))
        self.assertEqual(self.file_nota("0001"), prima)


class TestTestoProprio(ConAlbero):
    def test_le_integrazioni_non_allargano_il_testo_proprio(self):
        self.accettata(kind="idea", text="Nell'orto i pomodori vicino al muro.")
        self.accettata(kind="idea", text="Nell'orto la goccia sotto il pacciame.")
        self.accettata(integrates="0001", from_note="0002")
        self.accettata(integrates="0001", text="Anche l'irrigazione la sera.")
        quaderno = leggi(self.config)
        storia, lista = quaderno.storie["0001"], self.lista_letta()
        self.assertEqual(albero.testo_proprio(storia), "Nell'orto i pomodori vicino al muro.")
        self.assertEqual(albero.sotto_rami_propri(storia, lista), (("orto", "pomodori"),))
        self.assertEqual(albero.sotto_rami_visti(storia, lista), (("orto", "pomodori"), ("orto", "irrigazione")))

    def test_una_correzione_conta(self):
        self.accettata(kind="idea", text="Nell'orto i pomodori vicino al muro.")
        self.accettata(corrects="0001", text="Nell'orto la goccia vicino al muro.")
        storia = leggi(self.config).storie["0001"]
        self.assertEqual(albero.sotto_rami_propri(storia, self.lista_letta()), (("orto", "irrigazione"),))


class TestComandoTree(ConAlbero):
    def test_catene_e_senza_argomento(self):
        self.accettata(kind="idea", text="Nell'orto i pomodori vicino al muro.")   # 0001
        self.accettata(kind="fact", text="Nell'orto i pomodori sono dodici.")      # 0002
        self.accettata(kind="idea", text="Nell'orto una panchina.")                # 0003
        self.accettata(kind="idea", text="Nell'orto i pomodori sotto la rete.")    # 0004 (prima della regola I0213)
        self.accettata(integrates="0001", from_note="0004")
        self.accettata(kind="todo", text="Chiudere il bilancio.")                 # 0005
        self.accettata(done="0005", text="fatto")
        codice, uscita = self.comando("tree")
        self.assertEqual(codice, 0)
        self.assertIn("orto · 3 note\n  pomodori · 2\n    F0002  Nell'orto i pomodori sono dodici.\n"
                      "    I0001.1 ← I0004  Nell'orto i pomodori vicino al muro. …\n"
                      "  irrigazione · nessuna nota\n  senza argomento · 1\n    I0003  Nell'orto una panchina.\n",
                      uscita)
        self.assertIn("bilancio · 0 note\n", uscita)
        self.assertIn("(1 nota chiusa o annullata non mostrata: aggiungi --all per vederle.)", uscita)
        uscita = self.comando("tree", "--all", "--cosa", "bilancio")[1]
        self.assertIn("bilancio · 1 nota\n  senza argomento · 1\n    ✓T0005.1  Chiudere il bilancio.\n", uscita)
        self.assertNotIn("orto", uscita)

    def test_catena_in_piu_passaggi(self):
        for testo in ("Nell'orto i pomodori A.", "Nell'orto i pomodori B.", "Nell'orto i pomodori C."):
            self.accettata(kind="idea", text=testo)
        self.accettata(integrates="0002", from_note="0001")
        self.accettata(integrates="0003", from_note="0002")
        self.assertIn("    I0003.1 ← I0002.1 ← I0001  Nell'orto i pomodori C. …\n", self.comando("tree")[1])

    def test_senza_lista(self):
        (self.config.cartella_quaderno / "etichette.toml").unlink()
        self.accettata(kind="idea", text="Nell'orto.")
        codice, uscita = self.comando("albero")
        self.assertEqual(codice, 0)
        self.assertIn("L'albero è vuoto", uscita)

    def test_solo_lettura(self):
        self.accettata(kind="idea", text="Nell'orto i pomodori.")
        prima = {p: p.read_bytes() for p in self.config.cartella_quaderno.rglob("*") if p.is_file()}
        self.comando("tree")
        self.assertEqual({p: p.read_bytes() for p in self.config.cartella_quaderno.rglob("*") if p.is_file()}, prima)


if __name__ == "__main__":
    unittest.main()
