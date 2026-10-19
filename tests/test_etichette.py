"""Test della versione 0.7.0: le etichette CHI e COSA (1), il recap per data (2), il contesto nelle chiusure (3).
Solo dati inventati."""

import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from hypomnema import configurazione, controllo, etichette, versioni
from hypomnema.cercatore import leggi
from hypomnema.nota import da_markdown
from hypomnema.revisione import rivedi
from tests.esecutore import RADICE, modello_chat
from tests.test_versioni import ConQuaderno

LISTA = 'chi = ["Anna", "Marco", "Code"]\ncosa = ["orto", "bilancio", "gioco"]\n'


class ConEtichette(ConQuaderno):
    lista: str | None = LISTA

    def setUp(self):
        super().setUp()
        self.config.cartella_quaderno.mkdir(parents=True, exist_ok=True)
        if self.lista is not None:
            (self.config.cartella_quaderno / "etichette.toml").write_text(self.lista, encoding="utf-8")

    def claude(self, **campi):
        return {"author": "claude", "knowledge": "inferred", **campi}


class TestEtichetteNelleProposte(ConEtichette):
    def test_nota_con_etichette(self):  # E1
        self.assertEqual(self.accettata(kind="todo", who="Anna", about="orto", text="Seminare il basilico."), "0001")
        testo = self.file_nota("0001")
        self.assertIn("- kind: todo\n- who: Anna\n- about: orto\n- verification:", testo)
        nota = da_markdown("0001", testo)
        self.assertEqual((nota.chi, nota.cosa), (("Anna",), ("orto",)))
        self.accettata(kind="fact", who="Anna, Marco", about="orto, gioco", text="Due e due.")
        self.assertIn("- who: Anna, Marco\n- about: orto, gioco\n", self.file_nota("0002"))

    def test_etichetta_fuori_lista(self):  # E2
        self.assertIn("the label «giardino» is not in the list of «about» labels: the allowed ones are orto, "
                      "bilancio, gioco.", self.motivi(kind="fact", about="giardino", text="Rose."))
        self.assertIn("the label «orto» is not in the list of «who» labels",
                      self.motivi(kind="fact", who="orto", text="Scambiata."))
        # Il confronto è esatto.
        self.assertIn("«Orto» is not in the list", self.motivi(kind="fact", about="Orto", text="Maiuscola."))

    def test_al_massimo_due(self):  # E3
        self.assertIn("at most 2 «who» labels: «Anna, Marco, Code» has 3",
                      self.motivi(kind="fact", who="Anna, Marco, Code", text="Tre."))

    def test_ripetuta_e_vuota(self):  # E4
        self.assertIn("the label «orto» is repeated in «about»", self.motivi(kind="fact", about="orto, orto", text="x"))
        self.assertIn("«about» has an empty label", self.motivi(kind="fact", about="orto,", text="x"))
        self.assertIn("the field «who» is empty", self.motivi(kind="fact", who=" ", text="x"))

    def test_nomi_italiani(self):  # E12
        self.assertEqual(self.accettata(kind="fact", chi="Marco", cosa="bilancio", text="Conti."), "0001")
        self.assertIn("- who: Marco\n- about: bilancio\n", self.file_nota("0001"))

    def test_le_etichette_si_cambiano_solo_con_updates(self):
        self.accettata(kind="todo", text="Uno.")
        for campo in ("done", "corrects", "reopens"):
            self.assertIn(f"change only with «updates», not with «{campo}»",
                          self.motivi(**{campo: "0001"}, about="orto", text="Fatto."))

    def test_versioni_copiano_le_etichette(self):
        self.accettata(kind="todo", who="Anna", text="Uno.")
        self.accettata(updates="0001", priority="high", text="Urgente.")
        self.accettata(corrects="0001", text="Uno, corretto.")
        self.accettata(done="0001", text="Fatto.")
        for versione in ("0001.1", "0001.2", "0001.3"):
            self.assertIn("- who: Anna\n", self.file_nota(versione))


class TestSenzaLista(ConEtichette):
    lista = None

    def test_senza_file_nessuna_etichetta(self):  # E5
        self.assertIn("there are no labels in this notebook, so «about» cannot be used: the user lists them in the "
                      "file etichette.toml inside the notebook folder.",
                      self.motivi(kind="fact", about="orto", text="x"))
        # Senza etichette tutto resta come prima.
        self.assertEqual(self.accettata(kind="fact", text="Senza etichette."), "0001")
        codice, uscita = self.comando("labels")
        self.assertEqual(codice, 0)
        self.assertTrue(uscita.startswith("Nessuna etichetta: nella cartella del quaderno non c'è il file "
                                          "etichette.toml"))
        codice, uscita = self.comando("search", "--about", "orto")
        self.assertEqual(codice, 2)
        self.assertIn("in questo quaderno non ci sono etichette", uscita)


class TestListaScrittaMale(ConEtichette):
    lista = 'cosa = "orto"\n'

    def test_errore_chiaro_e_niente_scritto(self):  # E14
        prima = sorted(p.name for p in self.config.cartella_quaderno.iterdir())
        file = self.cartella / "p.json"
        file.write_text('{"date": "2026-01-15", "source": "s", "author": "user", "knowledge": "stated", '
                        '"kind": "fact", "about": "orto", "text": "x"}', encoding="utf-8")
        codice, uscita = self.comando("propose", str(file))
        self.assertEqual(codice, 2)
        self.assertIn("«cosa» deve essere una lista di testi tra virgolette", uscita)
        self.assertIn("Non ho scritto niente.", uscita)
        self.assertEqual(sorted(p.name for p in self.config.cartella_quaderno.iterdir()), prima)
        self.assertEqual(self.comando("labels")[0], 2)

    def test_altri_errori_del_file(self):
        cartella = self.config.cartella_quaderno
        for testo, atteso in (('chi = ["Anna", "Anna"]\n', "è ripetuta"), ('chi = ["Anna, Marco"]\n', "virgola"),
                              ('chi = [" Anna"]\n', "spazi"), ('chi = [""]\n', "è vuota"),
                              ('persone = ["Anna"]\n', "non prevede «persone»"), ('chi = [\n', "non è scritto")):
            with self.subTest(testo=testo):
                (cartella / "etichette.toml").write_text(testo, encoding="utf-8")
                with self.assertRaisesRegex(etichette.ErroreEtichette, atteso):
                    etichette.leggi(cartella)


class TestPermessi(ConEtichette):
    def test_claude_etichetta_le_note_vecchie_dell_utente(self):  # E6, E7
        self.accettata(kind="fact", text="Il basilico vuole il sole pieno.")
        self.assertEqual(self.accettata(**self.claude(updates="0001", about="orto", text="Etichetta messa dopo.")),
                         "0001.1")
        self.assertIn("- change: about → orto\n", self.file_nota("0001.1"))
        self.assertIn("only the user can change the labels of one of the user's notes once they are set",
                      self.motivi(**self.claude(updates="0001", about="orto, gioco", text="Anche il gioco.")))
        self.assertIn("only the user can change the labels",
                      self.motivi(**self.claude(updates="0001", who="Anna", text="Aggiungo chi.")))
        # L'utente può sempre.
        self.assertEqual(self.accettata(updates="0001", about="orto, gioco", text="Anche il gioco."), "0001.2")
        self.assertIn("- change: about orto → orto, gioco\n", self.file_nota("0001.2"))

    def test_claude_sulle_sue_note_sempre(self):
        self.accettata(**self.claude(kind="idea", about="orto", text="Un'idea."))
        self.assertEqual(self.accettata(**self.claude(updates="0001", about="gioco", who="Code", text="Meglio.")),
                         "0001.1")

    def test_cambiamento_che_non_cambia_niente(self):
        self.accettata(kind="fact", about="orto", text="Uno.")
        self.assertIn("changes nothing: write in «kind», «priority», «remind», «who» or «about» the new value.",
                      self.motivi(updates="0001", about="orto", text="Uguale."))

    def test_una_nota_utente_con_etichette_proposte_da_claude(self):
        # Nelle note dell'utente le etichette le propone Claude: la nota è dell'utente, autore user.
        self.assertEqual(self.accettata(kind="todo", who="Marco", about="bilancio", text="Pagare la luce."), "0001")


class TestDueConfigurazioni(ConEtichette):
    def test_la_chat_e_claude_code_leggono_la_stessa_lista(self):  # E13
        chat = configurazione.carica(str(modello_chat(self.cartella)))
        self.assertEqual(chat.cartella_quaderno, self.config.cartella_quaderno)
        self.assertEqual(etichette.leggi(chat.cartella_quaderno), etichette.leggi(self.config.cartella_quaderno))
        # Nessuna sezione [etichette] nei modelli di configurazione: la lista sta solo nel quaderno.
        for modello in (RADICE / "chat" / "hypomnema-chat.toml", RADICE / "windows" / "hypomnema-uso.toml",
                        RADICE / "hypomnema.toml"):
            self.assertNotIn("[etichette]", modello.read_text(encoding="utf-8"))

    def test_il_modello_negli_esempi(self):
        modello = RADICE / "esempi" / "etichette.toml"
        testo = modello.read_text(encoding="utf-8")
        self.assertIn("MODELLO da copiare", testo)
        self.assertIn("Claude non lo scrive mai", testo)
        cartella = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, cartella)
        shutil.copy(modello, cartella / "etichette.toml")
        lista = etichette.leggi(cartella)
        self.assertTrue(lista.chi and lista.cosa)

    def test_claude_non_puo_scrivere_la_lista(self):
        from hypomnema import avvio
        self.assertTrue(avvio.protetto(self.file_config, str(self.config.cartella_quaderno / "etichette.toml")))

    def test_check_ignora_la_lista(self):
        self.accettata(kind="fact", about="orto", text="x")
        self.assertTrue(controllo.controlla(self.config).in_ordine)


class TestFiltri(ConEtichette):
    def setUp(self):
        super().setUp()
        self.accettata(kind="todo", who="Anna", about="orto", text="Seminare il basilico con Anna.")
        self.accettata(kind="todo", who="Marco", about="orto", text="Annaffiare il basilico.")
        self.accettata(kind="fact", who="Anna", about="bilancio", text="Anna tiene i conti.")
        self.accettata(kind="todo", text="Il basilico senza etichette.")

    def test_ricerca(self):  # E8, E9
        codice, uscita = self.comando("search", "--about", "orto")
        self.assertEqual(codice, 0)
        self.assertTrue(uscita.startswith("Trovate 2 note con le etichette cosa: orto (dalla più recente)."))
        self.assertIn("--- Nota T0002 ---", uscita)
        self.assertIn("chi: Anna\ncosa: orto\n", uscita)
        codice, uscita = self.comando("search", "basilico", "--who", "Anna", "--about", "orto")
        self.assertTrue(uscita.startswith("Trovata 1 nota con «basilico» e le etichette chi: Anna e cosa: orto."))
        self.assertNotIn("T0002", uscita)
        self.assertNotIn("T0004", uscita)
        codice, uscita = self.comando("search", "--chi", "Anna", "--chi", "Marco")
        self.assertEqual(uscita.splitlines()[0], "Nessuna nota con le etichette chi: Anna e chi: Marco.")
        self.assertEqual(self.comando("search")[0], 2)

    def test_ricerca_delle_chiuse(self):
        self.accettata(done="0001", text="Fatto.")
        _, uscita = self.comando("search", "--who", "Anna")
        self.assertIn("(1 nota chiusa non mostrata: aggiungi --all per vederla.)", uscita)

    def test_recap(self):  # E10
        codice, uscita = self.comando("recap", "--about", "orto")
        self.assertEqual(codice, 0)
        righe = uscita.splitlines()
        self.assertEqual(righe[0], "Dove eravamo rimasti (recap del 2026-01-15, solo le note con le etichette cosa: orto).")
        self.assertIn("- [T0002] 2026-01-15: Annaffiare il basilico. · chi: Marco · cosa: orto", righe)
        self.assertNotIn("Il basilico senza etichette.", uscita)
        self.assertIn("Ultime voci del diario: non mostrate (il diario non ha etichette).", righe)
        # Senza filtro le note senza etichette si vedono come prima.
        _, uscita = self.comando("recap")
        self.assertIn("- [T0004] 2026-01-15: Il basilico senza etichette.\n", uscita)

    def test_etichette(self):  # E11
        self.accettata(done="0002", text="Fatto.")
        codice, uscita = self.comando("labels")
        self.assertEqual(codice, 0)
        self.assertEqual(uscita.splitlines()[:9], [
            "Etichette CHI:", "- Anna: 2 note (1 aperta)", "- Marco: 1 nota (0 aperte)", "- Code: 0 note",
            "Etichette COSA:", "- orto: 2 note (1 aperta)", "- bilancio: 1 nota (0 aperte)", "- gioco: 0 note",
            "Etichette usate in qualche nota ma non nella lista: nessuna.",
        ])

    def test_etichetta_tolta_dalla_lista(self):
        (self.config.cartella_quaderno / "etichette.toml").write_text('chi = ["Anna"]\ncosa = ["orto"]\n',
                                                                      encoding="utf-8")
        _, uscita = self.comando("labels")
        self.assertIn("Etichette usate in qualche nota ma non nella lista: CHI «Marco», COSA «bilancio».", uscita)
        # Il filtro per un'etichetta tolta funziona ancora: le note la hanno.
        codice, uscita = self.comando("search", "--who", "Marco")
        self.assertEqual(codice, 0)
        self.assertIn("T0002", uscita)
        codice, uscita = self.comando("recap", "--who", "Luca")
        self.assertEqual(codice, 2)
        self.assertIn("l'etichetta CHI «Luca» non è nella lista (le etichette CHI sono: Anna)", uscita)


class TestRecapPerData(ConEtichette):
    def test_r1_ultima_versione_prima(self):
        self.accettata(date="2026-01-02", kind="todo", text="Comprare il terriccio.")
        self.accettata(date="2026-01-10", kind="todo", text="Rinvasare il limone.")
        _, uscita = self.comando("recap")
        self.assertLess(uscita.index("T0002"), uscita.index("T0001"))
        self.accettata(date="2026-01-15", corrects="0001", text="Comprare il terriccio universale.")
        _, uscita = self.comando("recap")
        self.assertLess(uscita.index("[T0001.1] 2026-01-15"), uscita.index("[T0002] 2026-01-10"))

    def test_r2_chiusa_come_decisione_oggi(self):
        self.accettata(date="2026-01-12", kind="decision", text="Il limone resta sul balcone.")
        self.accettata(date="2026-01-03", kind="open", text="Dove mettere la compostiera?")
        self.accettata(date="2026-01-14", done="0002", kind="decision", text="Sotto il fico.")
        _, uscita = self.comando("recap")
        decisioni = uscita[uscita.index("Ultime decisioni"):]
        self.assertLess(decisioni.index("✓D0002.1"), decisioni.index("D0001"))

    def test_stesso_giorno_numero_piu_alto_e_priorita_prima(self):
        self.accettata(date="2026-01-10", kind="todo", text="Uno.")
        self.accettata(date="2026-01-10", kind="todo", text="Due.")
        self.accettata(date="2026-01-01", kind="todo", priority="high", text="Tre, urgente.")
        _, uscita = self.comando("recap")
        self.assertLess(uscita.index("T0003"), uscita.index("T0002"))
        self.assertLess(uscita.index("T0002"), uscita.index("T0001"))

    def test_le_etichette_non_spostano_la_nota(self):
        self.accettata(date="2026-01-02", kind="todo", text="Pulire la serra.")
        self.accettata(date="2026-01-10", kind="todo", text="Rinvasare il limone.")
        self.accettata(**self.claude(date="2026-01-15", updates="0001", about="orto", text="Etichetta."))
        _, uscita = self.comando("recap")
        self.assertLess(uscita.index("T0002"), uscita.index("T0001.1"))
        self.assertIn("- [T0001.1] 2026-01-02: Pulire la serra. · cosa: orto", uscita)
        storia = leggi(self.config).storie["0001"]
        self.assertTrue(storia.ultima.solo_etichette)
        self.assertEqual(storia.data_del_contenuto, "2026-01-02")

    def test_le_etichette_non_riazzerano_la_revisione(self):
        self.accettata(date="2025-11-01", kind="todo", text="Pulire la serra.")
        self.accettata(**self.claude(date="2026-01-15", updates="0001", about="orto", text="Etichetta."))
        segnalazioni = rivedi(leggi(self.config), date(2026, 1, 15), 30, versioni.SEGNO_CHIUSA)
        self.assertTrue(any("da fare da 75 giorni (ultima versione del 2025-11-01)" in s.testo for s in segnalazioni))

    def test_i_promemoria_restano_per_scadenza(self):
        self.accettata(date="2026-01-14", kind="todo", remind="2026-01-05", text="Più recente, scade prima.")
        self.accettata(date="2026-01-01", kind="todo", remind="2026-01-10", text="Più vecchia, scade dopo.")
        _, uscita = self.comando("recap")
        promemoria = uscita[:uscita.index("Discorsi aperti")]
        self.assertLess(promemoria.index("2026-01-05"), promemoria.index("2026-01-10"))


class TestContestoNelleChiusure(ConEtichette):
    def test_x1_done_dell_utente_con_contesto(self):
        self.accettata(kind="todo", text="Rinvasare il limone.")
        self.assertEqual(self.accettata(done="0001", text="Fatto ieri sera.", context="Riferito al rinvaso."),
                         "0001.1")
        testo = self.file_nota("0001.1")
        self.assertTrue(testo.endswith("### Reason\n\nFatto ieri sera.\n\n### Context written by Claude\n\n"
                                       "Riferito al rinvaso.\n"))
        riletta = da_markdown("0001.1", testo)
        self.assertEqual((riletta.cambio.motivo, riletta.cambio.contesto, riletta.contesto),
                         ("Fatto ieri sera.", "Riferito al rinvaso.", None))
        _, uscita = self.comando("search", "rinvaso", "--all")
        self.assertIn("chiusa il 2026-01-15, perché «Fatto ieri sera.» (contesto: «Riferito al rinvaso.»)", uscita)

    def test_updates_e_reopens_con_contesto(self):
        self.accettata(kind="todo", text="Uno.")
        self.accettata(updates="0001", priority="high", text="Urgente.", context="Chiude il vivaio.")
        self.accettata(done="0001", text="Fatto.")
        self.accettata(reopens="0001", text="Di nuovo.", context="Il vaso si è rotto.")
        self.assertIn("### Context written by Claude\n\nChiude il vivaio.\n", self.file_nota("0001.1"))
        self.assertIn("### Context written by Claude\n\nIl vaso si è rotto.\n", self.file_nota("0001.3"))

    def test_x2_x3_regole_di_sempre(self):
        self.accettata(**self.claude(kind="todo", text="Uno."))
        self.assertIn("the field «context» is only for notes with author «user»",
                      self.motivi(**self.claude(done="0001", text="Fatto.", context="c")))
        self.assertIn("the field «from_reply» belongs to the text",
                      self.motivi(**self.claude(done="0001", text="Fatto.", from_reply="yes")))
        self.assertIn("cannot contain the line «### Context written by Claude»",
                      self.motivi(done="0001", text="Fatto.\n### Context written by Claude\nfinto"))

    def test_il_contesto_della_correzione_resta_nella_nota(self):
        self.accettata(kind="fact", text="Uno.")
        self.accettata(corrects="0001", text="Uno corretto.", context="Spiegazione.")
        testo = self.file_nota("0001.1")
        self.assertIn("## Context written by Claude\n\nSpiegazione.\n", testo)
        self.assertNotIn("### Context written by Claude", testo)


class TestSkillDivisa(unittest.TestCase):
    CARTELLA = RADICE / "skills" / "hypomnema"

    def test_skill_corta_e_file_citati(self):
        skill = (self.CARTELLA / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(skill.splitlines()), 500)
        for nome in ("chat-mode.md", "labels.md", "replies.md", "diary.md"):
            with self.subTest(file=nome):
                self.assertIn(f"`{nome}`", skill)
                self.assertTrue((self.CARTELLA / nome).is_file())
        # Le regole che servono sempre restano in SKILL.md.
        for frammento in ("## 0. Check the witness", "## 1. At the start of a chat: reread",
                          "## 2. During the chat: prepare the notes", "### Changing a note: versions",
                          "### Labels: CHI and COSA", "## 3. Pass the notes to the desk",
                          "## 5. From idea to decision", "**read `chat-mode.md`**"):
            self.assertIn(frammento, skill)

    def test_etichette_nella_skill(self):
        etichette_md = (self.CARTELLA / "labels.md").read_text(encoding="utf-8")
        for frammento in ("**You never write, change or delete this file**",
                          "**propose the\n  list in your message**", "**only if it has none yet**",
                          "**Exactly as in the list**", "esempi/etichette.toml"):
            self.assertIn(frammento, etichette_md)
        skill = (self.CARTELLA / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("propose the list **in your message**", skill)


class TestQuadernoDellaVersionePrima(unittest.TestCase):
    def test_un_quaderno_0_6_1_si_legge_uguale(self):
        """Il quaderno dell'esempio 53 dopo i suoi passi (scritto dalla 0.6.1): check pulito, file intatti."""
        cartella = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, cartella)
        shutil.copytree(RADICE / "esempi" / "53-versioni" / "atteso" / "quaderno", cartella / "quaderno")
        (cartella / "quaderno" / ".sportello.lock").write_bytes(b"")  # come lo lasciava la 0.6.1
        prima = {p: p.read_bytes() for p in (cartella / "quaderno").rglob("*") if p.is_file()}
        config_file = cartella / "hypomnema.toml"
        config_file.write_text((RADICE / "tests" / "esecutore.py").read_text(encoding="utf-8")
                               .split('CONFIG_DI_PROVA = """\\\n')[1].split('"""')[0], encoding="utf-8")
        config = configurazione.carica(str(config_file))
        self.assertTrue(controllo.controlla(config).in_ordine)
        quaderno = leggi(config)
        self.assertTrue(all(s.ultima.contenuto.chi is None for s in quaderno.elenco()))
        self.assertEqual({p: p.read_bytes() for p in (cartella / "quaderno").rglob("*") if p.is_file()}, prima)


if __name__ == "__main__":
    unittest.main()
