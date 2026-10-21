"""Test della versione 0.6.0: versioni delle note (1), chiusura e riapertura (2), codici (3), note vecchie
lette come versioni (4), revisione (6). Solo dati inventati."""

import io
import json
import shutil
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from hypomnema import cambiamenti, configurazione, controllo, quaderno, sportello, versioni
from hypomnema.cli import main
from hypomnema.nota import da_markdown
from hypomnema.revisione import rivedi
from tests.esecutore import CONFIG_DI_PROVA, RADICE, testo_della_skill

ADESSO = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone(timedelta(hours=1)))
QUADERNO_DI_PROVA = RADICE / "esempi" / "53-versioni" / "quaderno-iniziale"


class ConQuaderno(unittest.TestCase):
    config_testo = CONFIG_DI_PROVA
    iniziale: Path | None = None

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cartella = Path(self._tmp.name).resolve()
        self.file_config = self.cartella / "hypomnema.toml"
        self.file_config.write_text(self.config_testo, encoding="utf-8")
        if self.iniziale is not None:
            shutil.copytree(self.iniziale, self.cartella / "quaderno")
        self.config = configurazione.carica(str(self.file_config))

    def tearDown(self):
        self._tmp.cleanup()

    def proponi(self, **campi):
        nota = {"date": "2026-01-15", "source": "prova", "author": "user", "knowledge": "stated", **campi}
        return sportello.ricevi(json.dumps(nota, ensure_ascii=False).encode("utf-8"), "prova.json",
                                self.config, ADESSO)

    def accettata(self, **campi):
        esito = self.proponi(**campi)
        self.assertTrue(esito.accettata, esito.motivi)
        return esito.id_nota

    def motivi(self, **campi):
        esito = self.proponi(**campi)
        self.assertFalse(esito.accettata)
        return " / ".join(esito.motivi)

    def comando(self, *argomenti, adesso=ADESSO):
        uscita = io.StringIO()
        codice = main(["--config", str(self.file_config), *argomenti], adesso=adesso, uscita=uscita,
                      errori=io.StringIO())
        return codice, uscita.getvalue()

    def file_nota(self, numero):
        return (self.config.cartella_note / f"{numero}.md").read_text(encoding="utf-8")


class TestFileDelleVersioni(ConQuaderno):
    def test_versione_con_tutto_dentro(self):
        self.accettata(kind="todo", text="Seminare il basilico.", remind="2026-01-20")
        self.assertEqual(self.accettata(updates="0001", priority="high", text="È urgente."), "0001.1")
        testo = self.file_nota("0001.1")
        self.assertTrue(testo.startswith("# Note 0001.1\n\n- date: 2026-01-15\n"))
        self.assertIn("- kind: todo\n- priority: high\n- remind: 2026-01-20\n", testo)
        self.assertIn("## Text\n\nSeminare il basilico.\n\n## Change\n\n- date: 2026-01-15\n- source: prova\n"
                      "- author: user\n- knowledge: stated\n- change: priority normal → high\n"
                      "- verification: author not verified (witness off)\n\n### Reason\n\nÈ urgente.\n", testo)
        riletta = da_markdown("0001.1", testo)
        self.assertEqual((riletta.priorita, riletta.cambio.motivo, riletta.cambio.cambio),
                         ("high", "È urgente.", "priority normal → high"))

    def test_registro_e_contatore(self):
        self.accettata(kind="todo", text="Uno.")
        self.accettata(updates="0001", priority="low", text="Non è urgente.")
        self.assertEqual(self.accettata(kind="fact", text="Due."), "0002")
        registro = self.config.file_registro.read_text(encoding="utf-8")
        self.assertIn("| ACCETTATA | nota 0001.1 | da: prova.json\n", registro)
        (self.config.cartella_note / "0007.md").write_text(self.file_nota("0002").replace("0002", "0007"),
                                                          encoding="utf-8")
        self.assertEqual(quaderno.prossimo_id(quaderno.leggi_note(self.config), 4), "0008")

    def test_riga_cambio_nel_testo_di_una_nota_vecchia(self):
        vecchia = "# Note 0001\n\n- date: 2026-01-10\n- source: s\n- author: user\n- knowledge: stated\n" \
                  "- kind: fact\n\n## Text\n\nPrima\n## Change\ndopo\n"
        self.assertEqual(da_markdown("0001", vecchia).testo, "Prima\n## Change\ndopo")
        self.assertIsNone(da_markdown("0001", vecchia).cambio)
        self.assertIn("cannot contain the line «## Change»", self.motivi(kind="fact", text="Uno\n## Change\ndue"))

    def test_correzione_del_testo(self):
        self.accettata(author="claude", knowledge="inferred", kind="idea", text="Il fico va potato a febbraio.",
                       quote="potare il fico")
        self.accettata(author="user", corrects="0001", text="Il fico va potato a marzo.")
        testo = self.file_nota("0001.1")
        self.assertIn("- author: user\n", testo)
        self.assertNotIn("- quote:", testo)
        self.assertIn("- change: text corrected\n", testo)
        self.assertNotIn("### Reason", testo)
        self.assertIn("changes nothing: the new text is the same",
                      self.motivi(corrects="0001", text="Il fico va potato a marzo."))
        self.assertIn("only the user can correct it",
                      self.motivi(author="claude", knowledge="inferred", corrects="0001", text="Ad aprile."))

    def test_un_cambiamento_per_proposta_e_campi_estranei(self):
        self.accettata(kind="todo", text="Uno.")
        self.assertIn("only one change", self.motivi(updates="0001", done="0001", text="x"))
        self.assertIn("«confirms» makes a new decision note", self.motivi(confirms="0001", done="0001", text="x"))
        # Dalla 0.7.0 il contesto si può mettere in un cambiamento dell'utente (test_etichette); from_reply no.
        self.assertIn("the field «from_reply» belongs to the text",
                      self.motivi(author="claude", knowledge="inferred", done="0001", text="x", from_reply="yes"))
        self.assertIn("to change «priority» use «updates»", self.motivi(done="0001", text="x", priority="high"))
        self.assertIn("names only one note", self.motivi(updates="0001, 0002", priority="high", text="x"))
        self.assertIn("the field «kind» is missing", self.motivi(text="Senza natura."))

    def test_nomi_italiani(self):
        self.accettata(kind="todo", text="Uno.")
        self.assertEqual(self.accettata(aggiorna="0001", priority="high", text="Urgente."), "0001.1")
        self.assertEqual(self.accettata(done="0001", text="Fatto."), "0001.2")
        self.assertEqual(self.accettata(riapre="0001", text="Di nuovo."), "0001.3")


class TestPermessi(ConQuaderno):
    def test_natura(self):
        self.accettata(kind="todo", text="Della persona.")
        self.accettata(author="claude", knowledge="inferred", kind="idea", text="Di Claude.")
        self.accettata(kind="decision", text="Deciso.")
        self.assertIn("only the user can change the kind of one of the user's notes",
                      self.motivi(author="claude", knowledge="inferred", updates="0001", kind="fact", text="x"))
        self.assertIn("only with a new note that has «confirms»", self.motivi(updates="0002", kind="decision", text="x"))
        self.assertIn("only the user can change the kind of a decision",
                      self.motivi(author="claude", knowledge="inferred", updates="0003", kind="fact", text="x"))
        self.assertEqual(self.accettata(author="claude", knowledge="inferred", updates="0002", kind="todo",
                                        text="È una cosa da fare."), "0002.1")
        self.assertEqual(self.accettata(updates="0001", kind="decision", text="Lo decido io."), "0001.1")

    def test_open(self):
        self.accettata(author="claude", knowledge="inferred", kind="open", text="Dove?")
        self.assertIn("only the user can change an open note",
                      self.motivi(author="claude", knowledge="inferred", updates="0001", kind="todo", text="x"))
        self.assertIn("only the user can close an open note",
                      self.motivi(author="claude", knowledge="inferred", done="0001", text="x"))
        self.accettata(done="0001", text="Qui.")
        self.assertIn("only the user can reopen an open note",
                      self.motivi(author="claude", knowledge="inferred", reopens="0001", text="x"))
        self.assertEqual(self.accettata(reopens="0001", text="Ci ripenso."), "0001.2")
        self.assertIn("- kind: open\n", self.file_nota("0001.2"))
        self.assertNotIn("- status:", self.file_nota("0001.2"))

    def test_chiusure(self):
        self.accettata(kind="todo", text="Uno.")
        self.accettata(kind="todo", text="Due.")
        self.assertIn("closing cannot turn note «0001» into «open»", self.motivi(done="0001", kind="open", text="x"))
        self.accettata(updates="0001", priority="high", text="Urgente.")
        self.assertIn("are the same note (0001): list it once", self.motivi(done="0001, 0001.1", text="x"))
        esito = self.proponi(author="claude", knowledge="observed", done="0001, 0002", kind="fact", text="Fatti.")
        self.assertEqual([n for n, _ in esito.scritte], ["0001.2", "0002.1"])
        self.assertIn("- change: closed; kind todo → fact\n", self.file_nota("0002.1"))
        self.accettata(kind="todo", text="Tre.")
        self.assertEqual(self.motivi(reopens="0003", text="x"),
                         "note «0003» is not closed (T0003): only a closed or cancelled note can be reopened.")
        self.assertEqual(self.accettata(reopens="0002.1", text="Non era fatto."), "0002.2")

    def test_si_cambia_solo_l_ultima_versione(self):
        self.accettata(kind="todo", text="Uno.")
        self.accettata(updates="0001", priority="high", text="Urgente.")
        self.assertEqual(self.motivi(updates="0001.0", priority="low", text="x"),
                         "note «0001.0» named in «updates» does not exist in the notebook.")
        self.assertEqual(self.accettata(updates="0001.1", priority="low", text="Non più."), "0001.2")
        self.assertIn("0001.1 is not the last version of 0001: the last is T0001.2",
                      self.motivi(updates="0001.1", priority="high", text="x"))

    def test_lettera_nel_rimando(self):
        self.accettata(kind="todo", text="Uno.")
        for rimando in ("T0001", "✓T0001.1", "x0001"):
            with self.subTest(rimando=rimando):
                self.assertIn(f"write only the number in «done»: «{rimando.lstrip('✓Tx')}», not «{rimando}»",
                              self.motivi(done=rimando, text="x"))

    def test_proposta_scritta_mentre_un_altro_cambia_la_stessa_nota(self):
        self.accettata(kind="todo", text="Uno.")
        vecchie = quaderno.leggi_note(self.config)
        self.accettata(updates="0001", priority="high", text="Urgente.")
        with mock.patch.object(quaderno, "leggi_note", return_value=vecchie):
            esito = self.proponi(updates="0001", priority="low", text="Non urgente.")
        self.assertFalse(esito.accettata)
        self.assertIn("version 0001.1 was written by another passage", esito.motivi[0])
        self.assertIn("- priority: high\n", self.file_nota("0001.1"))


class TestQuadernoDiProva(ConQuaderno):
    iniziale = QUADERNO_DI_PROVA

    def test_caso_richiesto_nota_correzione_chiusura(self):
        """Nota, sua correzione, terza nota che con done chiude entrambe: una storia sola, nascosta nel recap."""
        storia = versioni.Quaderno(quaderno.leggi_note(self.config)).storie["0001"]
        self.assertEqual([v.etichetta() for v in storia.versioni],
                         ["T0001", "T0001.1 (nota 0002)", "✓F0001.2 (nota 0003)"])
        _, recap = self.comando("recap")
        self.assertNotIn("terriccio", recap)
        _, tutte = self.comando("search", "terriccio", "--all")
        self.assertIn("Trovata 1 nota con «terriccio».", tutte)
        self.assertEqual(tutte.count("--- Nota"), 1)

    def test_numeri_vecchi_nei_rimandi(self):
        self.assertIn("0001.1 (note 0002) is not the last version of 0001: the last is ✓F0001.2",
                      self.motivi(corrects="0002", text="x"))
        self.assertEqual(self.accettata(reopens="0003", text="Il terriccio è finito."), "0001.3")
        self.assertIn("- kind: todo\n", self.file_nota("0001.3"))

    def test_note_vecchie_mai_toccate(self):
        prima = {p.name: p.read_bytes() for p in self.config.cartella_note.iterdir()}
        for comando in (("recap",), ("search", "terriccio", "--all"), ("reminders",), ("review",), ("check",)):
            self.comando(*comando)
        self.accettata(updates="0006", priority="high", text="Urgente.")
        self.accettata(done="0004", kind="decision", text="Nell'angolo nord.")
        dopo = {p.name: p.read_bytes() for p in self.config.cartella_note.iterdir()}
        self.assertEqual({n: dopo[n] for n in prima}, prima)
        self.assertEqual(sorted(set(dopo) - set(prima)), ["0004.1.md", "0006.1.md"])

    def test_istantanea_cambiati_e_controllo_con_le_versioni(self):
        istantanea = json.dumps(cambiamenti.istantanea(self.config)).encode("utf-8")
        self.accettata(done="0004, 0006", text="Fatto tutto.")
        elenco = cambiamenti.cambiati(self.config, cambiamenti.leggi_istantanea(istantanea))
        self.assertEqual([(c.percorso, c.tipo) for c in elenco],
                         [("note/0004.1.md", "creato"), ("note/0006.1.md", "creato"), ("registro.md", "allungato")])
        esito = controllo.controlla(self.config)
        self.assertTrue(esito.in_ordine)
        self.assertEqual((esito.note, esito.versioni), (7, 2))
        (self.config.cartella_note / "0006.2.md").write_text(self.file_nota("0006.1"), encoding="utf-8")
        self.assertEqual(controllo.controlla(self.config).senza_riga, ["0006.2"])
        with self.assertRaises(cambiamenti.ErroreCambiamenti):
            cambiamenti.cambiati(self.config, cambiamenti.leggi_istantanea(istantanea))


class ConNoteVecchie(ConQuaderno):
    """Un quaderno con note scritte a mano nel formato di prima delle versioni."""

    def scrivi(self, numero, testo):
        self.config.cartella_note.mkdir(parents=True, exist_ok=True)
        (self.config.cartella_note / f"{numero}.md").write_text(testo, encoding="utf-8")

    def vecchia(self, numero, kind, text, extra="", author="user"):
        self.scrivi(numero, f"# Note {numero}\n\n- date: 2026-01-1{int(numero) % 10}\n- source: s\n- author: {author}\n"
                            f"- knowledge: stated\n- kind: {kind}\n{extra}\n## Text\n\n{text}\n")

    def storie(self):
        return versioni.Quaderno(quaderno.leggi_note(self.config))


class TestNoteVecchie(ConNoteVecchie):
    def test_chiusura_vecchia_che_e_un_todo_resta_visibile(self):
        self.vecchia("0001", "open", "Chi chiamare?")
        self.vecchia("0002", "todo", "Chiamare l'idraulico.", "- done: 0001\n")
        storie = self.storie()
        self.assertEqual(sorted(storie.storie), ["0001", "0002"])
        self.assertEqual(storie.storie["0001"].ultima.etichetta(), "✓O0001.1 (nota 0002)")
        _, recap = self.comando("recap")
        self.assertIn("- [T0002] 2026-01-12: Chiamare l'idraulico.", recap)
        self.assertIn("Discorsi aperti: nessuno.", recap)

    def test_chiusura_vecchia_di_due_note_diverse(self):
        self.vecchia("0001", "todo", "Uno.")
        self.vecchia("0002", "todo", "Due.")
        self.vecchia("0003", "fact", "Fatti tutti e due.", "- done: 0001, 0002\n")
        storie = self.storie()
        self.assertEqual(sorted(storie.storie), ["0001", "0002"])
        self.assertIn("is an old closing note: it is version 0001.1 and 0002.1",
                      self.motivi(reopens="0003", text="x"))
        self.assertEqual(self.accettata(reopens="0002", text="Non era fatto."), "0002.2")

    def test_ramo(self):
        self.vecchia("0001", "fact", "Il rubinetto perde.")
        self.vecchia("0002", "fact", "Perde dal tubo.", "- corrects: 0001\n")
        self.vecchia("0003", "fact", "Perde dalla guarnizione.", "- corrects: 0001\n")
        storie = self.storie()
        self.assertEqual([(v.id, [n.id for n in note]) for v, note in storie.rami], [("0001", ["0002", "0003"])])
        self.assertEqual(storie.storie["0001"].ultima.etichetta(), "F0001.2 (nota 0003)")

    def test_priorita_e_promemoria_delle_catene_vecchie(self):
        self.vecchia("0001", "todo", "Uno.", "- priority: low\n- remind: 2026-01-10\n")
        self.vecchia("0002", "todo", "Uno, corretto.", "- corrects: 0001\n")
        ultima = self.storie().storie["0001"].ultima
        self.assertEqual((ultima.contenuto.priorita, ultima.contenuto.riprendere_il), ("low", "2026-01-10"))
        self.assertEqual(ultima.cambi, ("text corrected",))

    def test_quaderno_misto_come_quello_in_inglese(self):
        """Le note con i campi italiani si mostrano esattamente come quelle in inglese."""
        italiane = {
            "0001": "- data: 2026-01-11\n- fonte: s\n- autore: utente\n- tipo: dichiarata\n- natura: todo\n"
                    "- priorità: alta\n- riprendere_il: 2026-01-12\n- verifica: v\n\n## Testo\n\nSeminare.\n",
            "0002": "- data: 2026-01-12\n- fonte: s\n- autore: utente\n- tipo: dichiarata\n- natura: discorso aperto\n"
                    "\n## Testo\n\nDove? La 0001 è fatta.\n\n## Contesto scritto da Claude\n\nSpiegazione.\n",
            "0003": "- data: 2026-01-13\n- fonte: s\n- autore: claude\n- tipo: dedotta\n- natura: idea\n"
                    "- corregge: 0002\n- citazione: Dove?\n\n## Testo\n\nNell'angolo.\n",
            "0004": "- data: 2026-01-14\n- fonte: s\n- autore: utente\n- tipo: dichiarata\n- natura: decisione\n"
                    "- conferma_di: 0003\n- done: 0001\n\n## Testo\n\nSì.\n",
        }
        inglesi = {
            "0001": "- date: 2026-01-11\n- source: s\n- author: user\n- knowledge: stated\n- kind: todo\n"
                    "- priority: high\n- remind: 2026-01-12\n- verification: v\n\n## Text\n\nSeminare.\n",
            "0002": "- date: 2026-01-12\n- source: s\n- author: user\n- knowledge: stated\n- kind: open\n"
                    "\n## Text\n\nDove? La 0001 è fatta.\n\n## Context written by Claude\n\nSpiegazione.\n",
            "0003": "- date: 2026-01-13\n- source: s\n- author: claude\n- knowledge: inferred\n- kind: idea\n"
                    "- corrects: 0002\n- quote: Dove?\n\n## Text\n\nNell'angolo.\n",
            "0004": "- date: 2026-01-14\n- source: s\n- author: user\n- knowledge: stated\n- kind: decision\n"
                    "- confirms: 0003\n- done: 0001\n\n## Text\n\nSì.\n",
        }
        uscite = []
        for titolo, note in (("Nota", {**inglesi, "0001": italiane["0001"], "0003": italiane["0003"]}),
                             ("Note", inglesi)):
            shutil.rmtree(self.config.cartella_note, ignore_errors=True)
            for numero, testo in note.items():
                self.scrivi(numero, f"# {titolo} {numero}\n\n{testo}")
            uscite.append([self.comando(*c) for c in (("recap",), ("search", "Dove", "--all"), ("search", "Sì"),
                                                      ("reminders",), ("review",))])
        self.assertEqual(uscite[0], uscite[1])
        # La 0003 di Claude non può cambiare il testo né la natura della questione aperta dell'utente.
        self.assertIn("--- Nota O0002.1 (nota 0003) ---", uscite[0][1][1])
        self.assertIn("conferma di: nota O0002.1 (nota 0003)", uscite[0][2][1])

    def test_giro_scritto_a_mano(self):
        self.vecchia("0001", "fact", "Uno.", "- corrects: 0002\n")
        self.vecchia("0002", "fact", "Due.", "- corrects: 0001\n")
        storie = self.storie()
        self.assertEqual([v.etichetta() for v in storie.storie["0001"].versioni], ["F0001", "F0001.1 (nota 0002)"])


class TestRevisione(ConQuaderno):
    def segnalazioni(self, oggi=date(2026, 1, 15), giorni=30):
        storie = versioni.Quaderno(quaderno.leggi_note(self.config))
        return [f"{s.storia.ultima.etichetta()}: {s.testo}" for s in rivedi(storie, oggi, giorni, "✓")]

    def test_niente_da_segnalare(self):
        codice, uscita = self.comando("review")
        self.assertEqual((codice, uscita), (0, "Revisione del quaderno (2026-01-15): niente da segnalare.\n"))
        self.assertEqual(self.comando("revisione")[0], 0)

    def test_ferme_da_troppo(self):
        self.accettata(date="2025-12-15", kind="todo", text="Ferma.")
        self.accettata(date="2025-12-16", kind="open", text="Quasi ferma?")
        self.assertEqual(len(self.segnalazioni()), 1)
        self.assertIn("T0001: da fare da 31 giorni", self.segnalazioni()[0])
        self.assertEqual(len(self.segnalazioni(giorni=10)), 2)
        self.accettata(updates="0001", priority="high", text="Ancora da fare.")
        self.assertEqual(self.segnalazioni(), [])

    def test_nominate(self):
        self.accettata(kind="todo", text="Rinvasare il limone.")
        self.accettata(kind="fact", text="Il 2026-01-15 ho visto il vaso 0001-bis e la data 15/01/0001.")
        self.assertEqual(self.segnalazioni(), [])
        self.accettata(kind="fact", text="La T0001 è fatta.")
        self.accettata(kind="fact", text="Vedi anche la 0001.")
        self.assertEqual([s[:40] for s in self.segnalazioni()],
                         ["T0001: nominata nella nota F0003 (2026-0", "T0001: nominata nella nota F0004 (2026-0"])
        self.accettata(done="0001", text="Fatto.")
        self.assertEqual(self.segnalazioni(), [])

    def test_senza_data(self):
        for testo in ("Ricordamelo domani.", "Potare tra tre giorni.", "Remind me later.", "Fra due settimane.",
                      "Water it in two days.", "Una cosa normale."):
            self.accettata(kind="todo", text=testo)
        self.accettata(kind="fact", text="Ricordamelo, ma è un fatto.")
        self.accettata(kind="todo", text="Ricordami di innaffiare.", remind="2026-01-20")
        self.assertEqual([s.split(":")[0] for s in self.segnalazioni()], ["T0001", "T0002", "T0003", "T0004", "T0005"])

    def test_impostazioni(self):
        self.file_config.write_text(CONFIG_DI_PROVA + '\n[revisione]\ngiorni = 7\n\n[codici]\nchiusa = "x"\n',
                                    encoding="utf-8")
        config = configurazione.carica(str(self.file_config))
        self.assertEqual((config.giorni_revisione, config.segno_chiusa), (7, "x"))
        for aggiunta in ("[revisione]\ngiorni = 0\n", "[revisione]\nsoglia = 3\n", '[codici]\nchiusa = ""\n',
                         '[codici]\nchiusa = "a b"\n', '[codici]\nchiusa = "1"\n', "[codici]\naperta = \"o\"\n"):
            with self.subTest(aggiunta=aggiunta):
                self.file_config.write_text(CONFIG_DI_PROVA + "\n" + aggiunta, encoding="utf-8")
                with self.assertRaises(configurazione.ErroreConfigurazione):
                    configurazione.carica(str(self.file_config))
        self.file_config.write_text(CONFIG_DI_PROVA, encoding="utf-8")
        config = configurazione.carica(str(self.file_config))
        self.assertEqual((config.giorni_revisione, config.segno_chiusa), (30, "✓"))


class TestRecapPerQuelloCheENotaAdesso(ConQuaderno):
    """Correzioni chieste da Angelo dopo la prova sul quaderno vero (PR #15)."""

    def test_open_chiusa_come_decisione_tra_le_decisioni(self):
        self.accettata(kind="open", text="Dove mettiamo la compostiera?")
        self.accettata(done="0001", kind="decision", text="nell'angolo nord")
        _, recap = self.comando("recap")
        self.assertIn("Discorsi aperti: nessuno.", recap)
        self.assertIn("Ultime decisioni: 1 di 1 (prima la priorità alta, poi dal più recente)\n"
                      "- [✓D0001.1] 2026-01-15: Dove mettiamo la compostiera?\n"
                      "    ↳ ✓D0001.1 2026-01-15 · user: chiusa il 2026-01-15, perché «nell'angolo nord», "
                      "natura open → decision\n", recap)
        _, ricerca = self.comando("search", "compostiera")
        self.assertIn("--- Nota ✓D0001.1 ---", ricerca)

    def test_chiuse_che_non_sono_decisioni_restano_nascoste(self):
        self.accettata(kind="todo", text="Comprare il terriccio.")
        self.accettata(kind="todo", text="Pulire i vasi.")
        self.accettata(done="0001", text="Comprato.")
        self.accettata(done="0002", kind="fact", text="Puliti.")
        _, recap = self.comando("recap")
        self.assertIn("Cose da fare: nessuna.", recap)
        self.assertIn("Ultime decisioni: nessuna.", recap)
        _, ricerca = self.comando("search", "vasi")
        self.assertIn("Nessuna nota aperta contiene «vasi».", ricerca)

    def test_storia_nel_recap_dalla_piu_recente(self):
        self.accettata(kind="todo", text="Seminare il basilico.")
        self.accettata(updates="0001", priority="high", text="Urgente.")
        self.accettata(done="0001", text="Seminato.")
        self.accettata(reopens="0001", text="Il gelo l'ha bruciato.")
        _, recap = self.comando("recap")
        self.assertIn("- [T0001.3] [alta] 2026-01-15: Seminare il basilico.\n"
                      "    ↳ T0001.3 2026-01-15 · user: riaperta il 2026-01-15, perché «Il gelo l'ha bruciato.»\n"
                      "    ↳ ✓T0001.2 2026-01-15 · user: chiusa il 2026-01-15, perché «Seminato.»\n"
                      "    ↳ T0001.1 2026-01-15 · user: priorità normal → high\n", recap)


class TestCateneVecchieNonPermesseOggi(ConNoteVecchie):
    def test_claude_non_cambia_il_testo_dell_utente(self):
        self.vecchia("0001", "fact", "Il rubinetto perde dal tubo.")
        self.vecchia("0002", "fact", "Perde dalla guarnizione.", "- corrects: 0001\n", author="claude")
        storia = self.storie().storie["0001"]
        ultima = storia.ultima
        self.assertEqual((ultima.etichetta(), ultima.contenuto.testo, ultima.contenuto.autore),
                         ("F0001.1 (nota 0002)", "Il rubinetto perde dal tubo.", "user"))
        self.assertEqual((ultima.cambi, ultima.bloccati), ((), ("text corrected",)))
        _, ricerca = self.comando("search", "rubinetto")
        self.assertIn("non applicato (catena vecchia non permessa oggi): testo corretto («Perde dalla guarnizione.»)",
                      ricerca)
        codice, revisione = self.comando("review")
        self.assertEqual(codice, 1)
        self.assertIn("- F0001.1 (nota 0002): catena vecchia non permessa oggi: nella nota 0002 (claude, 2026-01-12) "
                      "non vale «testo corretto». Resta nella storia; se il cambiamento va fatto, lo decide l'utente "
                      "(corrects: 0001).", revisione)

    def test_un_open_resta_open(self):
        self.vecchia("0001", "open", "Serve un vaso più grande?", author="claude")
        self.vecchia("0002", "fact", "Il vaso grande è arrivato.", "- corrects: 0001\n", author="claude")
        self.vecchia("0003", "open", "Chi chiama l'idraulico?")
        self.vecchia("0004", "fact", "Ha chiamato il vicino.", "- done: 0003\n", author="claude")
        storie = self.storie()
        prima, seconda = storie.storie["0001"].ultima, storie.storie["0003"].ultima
        self.assertEqual((prima.contenuto.natura, prima.cambi, prima.bloccati),
                         ("open", ("text corrected",), ("kind open → fact",)))
        self.assertEqual((seconda.etichetta(), seconda.chiusa, seconda.bloccati),
                         ("O0003.1 (nota 0004)", False, ("closed", "kind open → fact")))
        _, recap = self.comando("recap")
        self.assertIn("Discorsi aperti: 2 di 2", recap)
        self.assertIn("    ↳ O0003.1 (nota 0004) 2026-01-14 · claude: non applicato (catena vecchia non permessa "
                      "oggi): chiusa, perché «Ha chiamato il vicino.», natura open → fact\n", recap)
        _, revisione = self.comando("review")
        self.assertEqual(revisione.count("catena vecchia non permessa oggi"), 2)
        # La chiusura che non vale non conta: l'utente può chiudere la questione con le sue parole.
        self.assertEqual(self.accettata(done="0003", text="La chiamo io."), "0003.2")

    def test_le_catene_permesse_valgono_come_prima(self):
        self.vecchia("0001", "fact", "Il rubinetto perde dal tubo.")
        self.vecchia("0002", "fact", "Perde dalla guarnizione.", "- corrects: 0001\n")
        self.vecchia("0003", "todo", "Comprare la guarnizione.", author="claude")
        self.vecchia("0004", "fact", "Comprata.", "- done: 0003\n", author="claude")
        storie = self.storie()
        self.assertEqual(storie.storie["0001"].ultima.contenuto.testo, "Perde dalla guarnizione.")
        self.assertEqual(storie.storie["0003"].ultima.etichetta(), "✓F0003.1 (nota 0004)")
        self.assertFalse(any(v.bloccati for s in storie.elenco() for v in s.versioni))
        self.assertIn("niente da segnalare", self.comando("review")[1])


class TestDocumenti(unittest.TestCase):
    def test_formato_con_tutte_le_regole(self):
        formato = (RADICE / "FORMATO.md").read_text(encoding="utf-8")
        regole = formato[formato.index("## Le regole del quaderno"):]
        titoli = [r for r in regole.splitlines() if r.startswith("### ")]
        self.assertEqual(len(titoli), 25)  # dalla 0.7.0 anche «Le etichette vengono dalla lista dell'utente»
        for titolo in titoli:
            blocco = regole[regole.index(titolo):].split("\n### ")[0]
            with self.subTest(regola=titolo):
                for parte in ("- **Dice:**", "- **Chi:**", "- **Effetto:**", "- ✔", "- ✘"):
                    self.assertIn(parte, blocco)
        for frammento in ("## Le versioni", "## Il codice della nota", "## Le note di prima delle versioni",
                          "## La revisione", "`updates`", "`reopens`"):
            self.assertIn(frammento, formato)

    def test_skill_readme_storia_comandi(self):
        skill = testo_della_skill()
        for frammento in ("run `P review` (in chat `H review`)", "### Changing a note: versions", "**A correction does not close**",
                          "### The rules of the notebook, in short", "`note/0049.1.md`", "Then run\n   `H review`"):
            with self.subTest(frammento=frammento):
                self.assertIn(frammento, skill)
        readme = (RADICE / "README.md").read_text(encoding="utf-8")
        for frammento in ("### Ogni cambiamento è una versione nuova", "### Il codice della nota", "### La revisione"):
            self.assertIn(frammento, readme)
        self.assertIn("## 0.6.0 (prototipo) — versioni e regole", (RADICE / "STORIA.md").read_text(encoding="utf-8"))
        for nome in ("review", "revisione"):
            testo = (RADICE / "commands" / f"{nome}.md").read_text(encoding="utf-8")
            self.assertIn(f"/hypomnema:{nome}", testo)
            self.assertIn("programma.py\" review", testo)


if __name__ == "__main__":
    unittest.main()
