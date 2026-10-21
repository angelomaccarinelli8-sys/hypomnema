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

    def senza_rami(self):
        """Un quaderno della 0.9.0: la lista senza sotto-rami (la regola dell'integrazione non c'è)."""
        self.scrivi_lista(LISTA.split("[rami")[0])

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
        self.senza_rami()
        self.accettata(kind="idea", text="Nell'orto i pomodori vicino al muro.")
        self.accettata(kind="idea", text="Nell'orto la goccia sotto il pacciame.")
        self.accettata(integrates="0001", from_note="0002")
        self.accettata(integrates="0001", text="Anche l'irrigazione la sera.")
        self.scrivi_lista(LISTA)
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
        self.senza_rami()
        self.accettata(kind="idea", text="Nell'orto i pomodori vicino al muro.")   # 0001
        self.accettata(kind="fact", text="Nell'orto i pomodori sono dodici.")      # 0002
        self.accettata(kind="idea", text="Nell'orto una panchina.")                # 0003
        self.accettata(kind="idea", text="Nell'orto i pomodori sotto la rete.")    # 0004 (senza i sotto-rami)
        self.accettata(integrates="0001", from_note="0004")
        self.accettata(kind="todo", text="Chiudere il bilancio.")                 # 0005
        self.accettata(done="0005", text="fatto")
        self.scrivi_lista(LISTA)
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
        self.senza_rami()
        for testo in ("Nell'orto i pomodori A.", "Nell'orto i pomodori B.", "Nell'orto i pomodori C."):
            self.accettata(kind="idea", text=testo)
        self.accettata(integrates="0002", from_note="0001")
        self.accettata(integrates="0003", from_note="0002")
        self.scrivi_lista(LISTA)
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



class TestRegolaDellIntegrazione(ConAlbero):
    """Pezzo 2 (I0213): un'idea nuova nel sotto-ramo di un'idea viva dello stesso autore si integra in quella."""

    def test_idea_rifiutata_con_il_numero_e_il_sotto_ramo(self):
        self.accettata(kind="idea", text="Nell'orto i pomodori vicino al muro.")
        motivi = self.motivi(kind="idea", text="Nell'orto i pomodori sotto la rete.")
        self.assertEqual(motivi, "this idea already has its note (0001, sub-branch orto/pomodori): propose it as an "
                                 "integration of 0001 («integrates»: «0001», with only the new words in «text», no "
                                 "«kind» and no «about»). If they are really different ideas, the sub-branches in "
                                 "etichette.toml need more precise words: only the user writes them.")
        # La proposta giusta passa: le parole nuove in fondo alla 0001.
        self.assertEqual(self.accettata(integrates="0001", text="Nell'orto i pomodori sotto la rete."), "0001.1")

    def test_la_cosa_a_mano_conta(self):
        self.accettata(kind="idea", text="Nell'orto i pomodori vicino al muro.")
        self.assertIn("sub-branch orto/pomodori", self.motivi(kind="idea", about="orto", text="I pomodori in vaso."))
        # Senza la COSA del ramo (né a mano né nel testo) il sotto-ramo non c'è.
        self.assertEqual(self.accettata(kind="idea", text="I pomodori in vaso."), "0002")

    def test_quando_non_vale(self):
        self.accettata(kind="idea", text="Nell'orto i pomodori vicino al muro.")   # 0001
        casi = (
            dict(kind="idea", text="Nell'orto la goccia sotto il pacciame."),       # altro sotto-ramo
            dict(kind="idea", text="Nell'orto una panchina."),                      # nessun sotto-ramo
            dict(kind="decision", text="Nell'orto i pomodori vanno al muro."),      # decisione
            dict(kind="todo", text="Comprare i tutori per i pomodori dell'orto."),  # da fare
            dict(kind="open", text="Quanti pomodori nell'orto?"),                   # aperta
            dict(author="claude", knowledge="inferred", kind="idea",                # altro autore
                 text="Proposta: nell'orto i pomodori in fila."),
        )
        for numero, caso in enumerate(casi, start=2):
            with self.subTest(caso=caso):
                self.assertEqual(self.accettata(**caso), f"{numero:04d}")

    def test_una_nota_non_viva_non_conta(self):
        self.accettata(kind="idea", text="Nell'orto i pomodori vicino al muro.")   # 0001
        self.accettata(cancels="0001", text="non vale più")
        self.assertEqual(self.accettata(kind="idea", text="Nell'orto i pomodori sotto la rete."), "0002")

    def test_vale_il_testo_proprio_non_le_integrazioni(self):
        self.accettata(kind="idea", text="Nell'orto i pomodori vicino al muro.")   # 0001
        self.accettata(integrates="0001", text="E la goccia per l'irrigazione.")
        # La 0001 ha preso «irrigazione» solo con l'integrazione: un'idea sull'irrigazione passa.
        self.assertEqual(self.accettata(kind="idea", text="Nell'orto la goccia sotto il pacciame."), "0002")
        self.assertIn("(0001, sub-branch orto/pomodori)", self.motivi(kind="idea", text="Pomodori nell'orto."))

    def test_nomina_la_piu_recente_e_le_altre(self):
        self.senza_rami()
        self.accettata(kind="idea", text="Nell'orto i pomodori A.")
        self.accettata(kind="idea", text="Nell'orto i pomodori B.")
        self.scrivi_lista(LISTA)
        motivi = self.motivi(kind="idea", text="Nell'orto i pomodori C.")
        self.assertIn("this idea already has its note (0002, sub-branch orto/pomodori)", motivi)
        self.assertIn("Also in this sub-branch: 0001.", motivi)

    def test_senza_rami_come_nella_0_9_0(self):
        self.senza_rami()
        self.accettata(kind="idea", text="Nell'orto i pomodori A.")
        self.assertEqual(self.accettata(kind="idea", text="Nell'orto i pomodori B."), "0002")

    def test_i_fatti_hanno_solo_il_suggerimento(self):
        self.accettata(kind="fact", text="Nell'orto i pomodori sono dodici.")
        esito = self.proponi(kind="fact", text="Nell'orto i pomodori sono San Marzano.")
        self.assertTrue(esito.accettata)
        self.assertEqual(esito.integrazione, ("0001", "orto/pomodori"))
        file = self.cartella / "p.json"
        file.write_text('{"date": "2026-01-15", "source": "s", "author": "user", "knowledge": "stated", '
                        '"kind": "fact", "text": "Nell\'orto i pomodori rossi."}', encoding="utf-8")
        codice, uscita = self.comando("propose", str(file))
        self.assertEqual(codice, 0)
        self.assertIn("ACCETTATA: la nota 0003", uscita)
        self.assertIn("SUGGERIMENTO (non cambia niente): there is already fact 0002 in this sub-branch "
                      "(orto/pomodori): is this an integration? («integrates»: «0002»)", uscita)
        # Un fatto in un altro sotto-ramo, o un'idea accanto a un fatto: niente suggerimento.
        self.assertIsNone(self.proponi(kind="fact", text="Nell'orto la goccia alle sei.").integrazione)
        self.assertEqual(self.accettata(kind="idea", text="Nell'orto i pomodori in fila."), "0005")



class TestProposteACatena(ConAlbero):
    """Pezzo 3: review --proposte propone catene, non coppie."""

    def proposte(self):
        from datetime import date
        from hypomnema.revisione import rivedi
        return [v.proposta for v in rivedi(leggi(self.config), date(2026, 1, 15), 30, "✓", self.lista_letta())
                if v.proposta is not None and "integrates" in v.proposta]

    def coppie(self):
        return [(p["integrates"], p["from_note"]) for p in self.proposte()]

    def test_un_sotto_ramo_una_catena_verso_la_piu_recente(self):
        self.senza_rami()
        self.accettata(kind="idea", text="Nell'orto i pomodori A.")              # 0001
        self.accettata(kind="idea", text="Nell'orto i pomodori B.")              # 0002
        self.accettata(kind="fact", text="Nell'orto i pomodori sono dodici.")    # 0003: altro tipo
        self.accettata(kind="idea", text="Nell'orto i pomodori C.")              # 0004
        self.accettata(kind="idea", text="Nell'orto i pomodori D.", author="claude", knowledge="inferred")  # 0005
        self.scrivi_lista(LISTA)
        self.assertEqual(self.coppie(), [("0004", "0001"), ("0004", "0002")])
        # Le proposte della catena passano tutte, una dopo l'altra.
        for proposta in self.proposte():
            self.accettata(**{k: v for k, v in proposta.items() if k not in ("date", "author", "knowledge")
                              and v != ""}, source="chat inventata")
        self.assertEqual(self.coppie(), [])
        self.assertIn("    I0004.2 ← I0002 ← I0001  Nell'orto i pomodori C. …\n", self.comando("tree")[1])

    def test_una_nota_in_due_sotto_rami_va_nel_primo(self):
        self.senza_rami()
        self.accettata(kind="idea", text="Nell'orto la goccia per i pomodori.")  # 0001: pomodori e irrigazione
        self.accettata(kind="idea", text="Nell'orto i pomodori B.")              # 0002
        self.accettata(kind="idea", text="Nell'orto la goccia C.")               # 0003
        self.scrivi_lista(LISTA)
        self.assertEqual(self.coppie(), [("0002", "0001")])

    def test_il_contesto_non_basta(self):
        self.accettata(kind="idea", text="Il bilancio di gennaio.")                             # 0001
        self.accettata(kind="idea", text="Il bilancio di febbraio.", context="Come la 0001.")  # 0002
        self.assertEqual(self.coppie(), [])

    def test_senza_sotto_rami_a_catena_nel_testo(self):
        self.accettata(kind="idea", text="Il bilancio di gennaio.")                       # 0001
        self.accettata(kind="todo", text="Il bilancio di febbraio, dopo la nota 0001.")  # 0002
        self.accettata(kind="idea", text="Il bilancio di marzo, come la 0002.")          # 0003
        self.accettata(kind="idea", text="Il bilancio di aprile.")                        # 0004: non nomina nessuno
        self.assertEqual(self.coppie(), [("0003", "0001"), ("0003", "0002")])

    def test_le_cosa_con_sotto_rami_non_usano_la_regola_vecchia(self):
        self.senza_rami()
        self.accettata(kind="idea", text="Nell'orto una panchina.")                    # 0001: senza argomento
        self.accettata(kind="todo", text="Nell'orto la panchina della nota 0001.")     # 0002
        self.scrivi_lista(LISTA)
        self.assertEqual(self.coppie(), [])



class TestGrafoAdAlbero(ConAlbero):
    """Pezzo 4: graph --albero, in sola lettura e fuori dal quaderno; senza l'opzione il grafo della 0.9.0."""

    def setUp(self):
        super().setUp()
        self.senza_rami()
        self.accettata(kind="idea", text="Nell'orto i pomodori A.", who="Anna")   # 0001
        self.accettata(kind="idea", text="Nell'orto i pomodori B.")               # 0002
        self.accettata(integrates="0002", from_note="0001")
        self.accettata(kind="fact", text="Nell'orto la goccia per i pomodori.")   # 0003: due sotto-rami
        self.accettata(kind="todo", text="Comprare il pane.")                     # 0004: senza COSA
        self.scrivi_lista(LISTA)
        self.cartella_fuori = self.cartella / "fuori"
        self.cartella_fuori.mkdir()

    def disegna(self, *opzioni, nome="albero.html"):
        pagina = self.cartella_fuori / nome
        codice, uscita = self.comando("graph", str(pagina), *opzioni)
        self.assertEqual(codice, 0, uscita)
        return pagina.read_text(encoding="utf-8")

    def test_pagina_ad_albero(self):
        prima = {p: p.read_bytes() for p in self.config.cartella_quaderno.rglob("*") if p.is_file()}
        testo = self.disegna("--albero")
        self.assertTrue(testo.startswith("<!doctype html>\n<!-- Hypomnema: grafo del taccuino -->"))
        self.assertIn('aria-label="Albero delle etichette: rami, sotto-rami e note"', testo)
        self.assertIn("4 note, 2 rami, 2 sotto-rami", testo)
        for nome in (">orto</text>", ">bilancio</text>", ">pomodori</text>", ">irrigazione</text>",
                     ">senza COSA</text>"):
            self.assertIn(nome, testo)
        self.assertNotIn(">Anna</text>", testo)  # le CHI non si disegnano
        self.assertIn('class="legame altro"', testo)  # la 0003 ha anche il sotto-ramo irrigazione
        self.assertIn("<title>0002 integra 0001</title>", testo)
        self.assertNotIn("http", testo.replace('xmlns="http', ""))
        self.assertEqual({p: p.read_bytes() for p in self.config.cartella_quaderno.rglob("*") if p.is_file()}, prima)

    def test_sempre_uguale_e_senza_opzione_come_prima(self):
        self.assertEqual(self.disegna("--tree"), self.disegna("--albero", nome="altra.html"))
        from hypomnema import grafo
        quaderno = leggi(self.config)
        self.assertEqual(self.disegna(), grafo.pagina(quaderno, self.lista_letta(), "✓"))
        self.assertNotIn("sotto-rami", self.disegna())

    def test_ogni_nota_una_volta_sola(self):
        from hypomnema import grafo
        nodi, dove_nota = grafo.posizioni_albero(leggi(self.config), self.lista_letta())
        self.assertEqual(sorted(dove_nota), ["0001", "0002", "0003", "0004"])
        self.assertEqual([n[1] for n in nodi if n[0] == "ramo"], ["orto", "bilancio", "senza COSA"])
        posizioni = list(dove_nota.values())
        self.assertEqual(len(set(posizioni)), len(posizioni))



class TestModelli(ConAlbero):
    """Pezzo 6 a): template stampa per ogni mossa la proposta vuota con solo i campi ammessi."""

    def compila(self, mossa, forma=0, **valori):
        """Il modello con i valori dati; i campi lasciati vuoti si tolgono, come farebbe Claude."""
        from datetime import date
        from hypomnema import modelli
        proposta = {**modelli.modelli(mossa, date(2026, 1, 15))[forma][1], "source": "chat inventata", **valori}
        return {k: v for k, v in proposta.items() if v != ""}

    def proponi_modello(self, mossa, forma=0, **valori):
        from hypomnema import sportello
        from tests.test_versioni import ADESSO
        import json
        proposta = self.compila(mossa, forma, **valori)
        return sportello.ricevi(json.dumps(proposta, ensure_ascii=False).encode("utf-8"), "p.json", self.config,
                                ADESSO)

    def test_ogni_modello_compilato_passa(self):
        casi = (
            ("new", 0, dict(kind="todo", text="Seminare il basilico nell'orto.")),          # 0001
            ("new", 0, dict(kind="idea", text="Il bilancio di gennaio.")),                   # 0002
            ("new", 0, dict(kind="idea", text="Il bilancio di febbraio.")),                  # 0003
            ("integrates", 0, dict(integrates="0002", text="E anche quello di marzo.")),    # 0002.1
            ("integrates", 1, dict(integrates="0002", from_note="0003")),                   # 0002.2
            ("updates", 0, dict(updates="0001", priority="high", text="è urgente")),         # 0001.1
            ("done", 0, dict(done="0001", text="fatto")),                                    # 0001.2
            ("new", 0, dict(kind="idea", text="Una panchina nell'orto.")),                   # 0004
            ("cancels", 0, dict(cancels="0004", text="non serve più")),                      # 0004.1
        )
        for mossa, forma, valori in casi:
            with self.subTest(mossa=mossa, valori=valori):
                esito = self.proponi_modello(mossa, forma, **valori)
                self.assertTrue(esito.accettata, esito.motivi)

    def test_vuoto_e_rifiutato(self):
        from datetime import date
        from hypomnema import modelli
        from hypomnema import sportello
        from tests.test_versioni import ADESSO
        import json
        for mossa in modelli.MOSSE:
            for _, proposta in modelli.modelli(mossa, date(2026, 1, 15)):
                with self.subTest(mossa=mossa):
                    esito = sportello.ricevi(json.dumps(proposta).encode("utf-8"), "p.json", self.config, ADESSO)
                    self.assertFalse(esito.accettata)

    def test_integrazione_senza_kind_ne_about(self):
        from datetime import date
        from hypomnema import modelli
        for _, proposta in modelli.modelli("integrates", date(2026, 1, 15)):
            for campo in ("kind", "about", "who", "priority", "remind", "context"):
                self.assertNotIn(campo, proposta)

    def test_comando_senza_configurazione(self):
        import io
        from hypomnema.cli import main
        from tests.test_versioni import ADESSO
        uscita = io.StringIO()
        self.assertEqual(main(["--config", str(self.cartella / "non-c-e.toml"), "modello", "integra"], adesso=ADESSO,
                              uscita=uscita, errori=io.StringIO()), 0)
        testo = uscita.getvalue()
        self.assertIn('{"date": "2026-01-15", "source": "", "author": "user", "knowledge": "stated", "integrates": "", '
                      '"text": ""}', testo)
        self.assertIn('"integrates": "", "from_note": ""}', testo)
        uscita = io.StringIO()
        main(["template"], adesso=ADESSO, uscita=uscita, errori=io.StringIO())
        self.assertIn("- cancels: annullare una nota che non vale più", uscita.getvalue())



class TestSkill(unittest.TestCase):
    """Pezzi 5 e 6: la skill dice di guardare il sotto-ramo, i modelli delle mosse, l'inizio leggero."""

    def test_regole_nella_skill(self):
        from tests.esecutore import RADICE, testo_della_skill
        skill = testo_della_skill()
        for frammento in ("**Before proposing an idea or a fact, look at its sub-branch**",
                          "**without `kind` and without `about`**", "run `P tree --cosa <COSA>`",
                          "`P template <move>`", "never put `who` or\n  `about` in a proposal",
                          "H tree --cosa <COSA>", "Since 0.10.0 the start is **light**"):
            with self.subTest(frammento=frammento):
                self.assertIn(frammento, skill)
        self.assertLess(len((RADICE / "skills" / "hypomnema" / "SKILL.md").read_text(encoding="utf-8").splitlines()),
                        500)

    def test_i_modelli_della_skill_sono_json_con_i_campi_giusti(self):
        import json
        import re
        from tests.esecutore import RADICE
        testo = (RADICE / "skills" / "hypomnema" / "moves.md").read_text(encoding="utf-8")
        modelli = [json.loads(b) for b in re.findall(r"```json\n(.*?)\n```", testo, re.DOTALL)]
        self.assertEqual(len(modelli), 6)
        for modello in modelli:
            self.assertTrue({"date", "source", "author", "knowledge", "text"} <= set(modello) or "from_note" in modello)
            if "integrates" in modello:
                self.assertFalse({"kind", "about", "who", "priority", "remind", "context"} & set(modello))


if __name__ == "__main__":
    unittest.main()
