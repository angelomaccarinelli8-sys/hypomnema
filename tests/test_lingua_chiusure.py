"""Test della versione 0.5.0: lingua per ruolo (1), che cos'è una nota (2), chiudere open e todo (3),
priorità (4), il quaderno vecchio in italiano. Solo dati inventati."""

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from hypomnema import __version__, cercatore, configurazione, quaderno, sportello, testimone
from hypomnema.cli import INGLESE, main
from hypomnema.nota import da_markdown
from tests.esecutore import CONFIG_DI_PROVA, RADICE, testo_della_skill
from tests.test_testimone import CONFIG_ACCESO, messaggio

ADESSO = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone(timedelta(hours=1)))


class ConQuaderno(unittest.TestCase):
    config_testo = CONFIG_DI_PROVA

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cartella = Path(self._tmp.name).resolve()
        self.file_config = self.cartella / "hypomnema.toml"
        self.file_config.write_text(self.config_testo, encoding="utf-8")
        self.config = configurazione.carica(str(self.file_config))

    def tearDown(self):
        self._tmp.cleanup()

    def proponi(self, **campi):
        nota = {"date": "2026-01-15", "source": "prova", "author": "user", "knowledge": "stated",
                "kind": "fact", "text": "Una nota.", **campi}
        nota = {k: v for k, v in nota.items() if v is not ...}
        return sportello.ricevi(json.dumps(nota, ensure_ascii=False).encode("utf-8"), "prova.json",
                                self.config, ADESSO)

    def nota(self, **campi):
        esito = self.proponi(**campi)
        self.assertTrue(esito.accettata, esito.motivi)
        return esito.id_nota

    def comando(self, *argomenti):
        uscita = io.StringIO()
        codice = main(["--config", str(self.file_config), *argomenti], adesso=ADESSO, uscita=uscita,
                      errori=io.StringIO())
        return codice, uscita.getvalue()

    def file_nota(self, numero):
        return (self.config.cartella_note / f"{numero}.md").read_text(encoding="utf-8")


ITALIANA = {"data": "2026-01-15", "fonte": "prova", "autore": "utente", "tipo": "dichiarata",
            "natura": "discorso aperto", "testo": "Dove mettere la compostiera?"}
INGLESE_NOTA = {"date": "2026-01-15", "source": "prova", "author": "user", "knowledge": "stated",
                "kind": "open", "text": "Dove mettere la compostiera?"}


class TestLingua(ConQuaderno):
    def test_proposta_italiana_e_inglese_scritte_uguali(self):
        prima = sportello.ricevi(json.dumps(ITALIANA).encode("utf-8"), "a.json", self.config, ADESSO)
        seconda = sportello.ricevi(json.dumps(INGLESE_NOTA).encode("utf-8"), "b.json", self.config, ADESSO)
        self.assertEqual(self.file_nota(prima.id_nota).replace("0001", "X"),
                         self.file_nota(seconda.id_nota).replace("0002", "X"))
        self.assertEqual(self.file_nota("0001"),
                         "# Note 0001\n\n- date: 2026-01-15\n- source: prova\n- author: user\n- knowledge: stated\n"
                         "- kind: open\n- verification: author not verified (witness off)\n\n## Text\n\n"
                         "Dove mettere la compostiera?\n")

    def test_valori_italiani(self):
        for campo, italiano, inglese in (("knowledge", "osservata", "observed"), ("knowledge", "dedotta", "inferred"),
                                         ("kind", "fatto", "fact"), ("kind", "idea", "idea"),
                                         ("priority", "alta", "high"), ("priority", "bassa", "low")):
            with self.subTest(italiano=italiano):
                numero = self.nota(**{campo: italiano})
                self.assertIn(f"- {campo}: {inglese}\n", self.file_nota(numero))

    def test_stesso_campo_due_volte(self):
        esito = self.proponi(fonte="altra")
        self.assertEqual(esito.motivi, ["the field «source» appears twice (as «source» and as «fonte»): "
                                        "it must appear only once."])

    def test_motivi_in_inglese(self):
        self.assertEqual(self.proponi(source=...).motivi,
                         ["the field «source» is missing: every note must say where it comes from."])

    def test_contesto_e_citazione(self):
        numero = self.nota(context="Detto parlando del balcone.")
        self.assertTrue(self.file_nota(numero).endswith("## Context written by Claude\n\nDetto parlando del balcone.\n"))
        numero = self.nota(author="claude", knowledge="inferred", kind="idea", quote="parole")
        self.assertIn("- quote: parole\n- verification: quote not verified (witness off)\n", self.file_nota(numero))

    def test_nota_vecchia_letta_in_inglese(self):
        vecchia = ("# Nota 0001\n\n- data: 2026-01-10\n- fonte: f\n- autore: utente\n- tipo: dedotta\n"
                   "- natura: discorso aperto\n- riprendere_il: 2026-01-12\n- verifica: autore non verificato\n\n"
                   "## Testo\n\nRiga.\n## Context written by Claude\nResta testo.\n\n"
                   "## Contesto scritto da Claude\n\nIl contesto.\n")
        nota = da_markdown("0001", vecchia)
        self.assertEqual((nota.autore, nota.tipo, nota.natura, nota.riprendere_il, nota.verifica),
                         ("user", "inferred", "open", "2026-01-12", "autore non verificato"))
        self.assertEqual((nota.testo, nota.contesto), ("Riga.\n## Context written by Claude\nResta testo.", "Il contesto."))

    def test_comandi_con_i_due_nomi(self):
        self.nota(text="Il fico va potato a febbraio.")
        for italiano, inglese in INGLESE.items():
            if italiano in ("testimone", "risposte", "avvio", "protezione", "impronta", "confronta",
                            "cambiati", "archivio", "proponi", "impostazioni-claude", "istantanea",
                            "grafo",  # grafo scrive un file: test_riordino.TestGrafo
                            "servizio",  # il server legge l'ingresso standard: test_servizio
                            "taccuino-nuovo",  # crea cartelle: test_http.TestTaccuinoNuovo
                            "taccuino-etichette"):  # ha argomenti obbligatori: test_http.TestEtichetteDelTaccuino
                continue
            argomenti = ["fico"] if inglese == "search" else ["--last", "1"] if inglese == "diary" else []
            with self.subTest(comando=italiano):
                self.assertEqual(self.comando(italiano, *argomenti), self.comando(inglese, *argomenti))
        self.assertEqual(self.comando("cerca", "fico", "--tutte"), self.comando("search", "fico", "--all"))

    def test_tutti_i_nomi_inglesi_e_italiani_esistono(self):
        for italiano, inglese in INGLESE.items():
            for nome in (italiano, inglese):
                with self.subTest(comando=nome), self.assertRaises(SystemExit) as uscita, \
                        contextlib.redirect_stdout(io.StringIO()):
                    main([nome, "--help"], uscita=io.StringIO(), errori=io.StringIO())
                self.assertEqual(uscita.exception.code, 0)  # --help esiste: il comando c'è
        with self.assertRaises(SystemExit) as uscita, contextlib.redirect_stderr(io.StringIO()):
            main(["inesistente"], uscita=io.StringIO(), errori=io.StringIO())
        self.assertEqual(uscita.exception.code, 2)

    def test_agganci_e_comandi_del_plugin(self):
        agganci = (RADICE / "hooks" / "hooks.json").read_text(encoding="utf-8")
        for nome in ("start", "witness", "replies", "protect"):
            self.assertIn(f'programma.py\\" {nome};', agganci)
        for nome in ("pause", "resume", "pausa", "riprendi"):
            with self.subTest(nome=nome):
                testo = (RADICE / "commands" / f"{nome}.md").read_text(encoding="utf-8")
                self.assertIn("disable-model-invocation: true", testo)
                self.assertIn(f"/hypomnema:{nome}", testo)

    def test_versione(self):
        self.assertEqual(__version__, "0.11.0")


class TestPausaInInglese(ConQuaderno):
    config_testo = CONFIG_ACCESO

    def test_pause_e_resume(self):
        testimone.registra(self.config, ADESSO, messaggio("/hypomnema:pause"))
        self.assertIsNotNone(testimone.in_pausa(testimone.leggi_messaggi(self.config)))
        testimone.registra(self.config, ADESSO, messaggio("/hypomnema:resume"))
        self.assertIsNone(testimone.in_pausa(testimone.leggi_messaggi(self.config)))
        testimone.registra(self.config, ADESSO, messaggio("/hypomnema:pausa"))
        self.assertIsNotNone(testimone.in_pausa(testimone.leggi_messaggi(self.config)))
        testimone.registra(self.config, ADESSO, messaggio("/hypomnema:riprendi"))
        self.assertIsNone(testimone.in_pausa(testimone.leggi_messaggi(self.config)))


class TestKind(ConQuaderno):
    def test_cinque_valori(self):
        for kind in ("fact", "idea", "open", "todo"):
            with self.subTest(kind=kind):
                self.assertTrue(self.proponi(author="claude", knowledge="inferred", kind=kind).accettata)
        self.assertTrue(self.proponi(kind="decision").accettata)
        self.assertIn("cannot be a decision", self.proponi(author="claude", knowledge="inferred",
                                                           kind="decision").motivi[0])
        self.assertIn("«choice» is not allowed for «kind»", self.proponi(kind="choice").motivi[0])


class TestChiusure(ConQuaderno):
    """Dalla 0.6.0 una chiusura è una versione chiusa della nota (vedi anche test_versioni)."""

    def test_chiudere_un_open(self):
        aperta = self.nota(author="claude", knowledge="inferred", kind="open")
        self.assertIn("only the user can close an open note",
                      self.proponi(author="claude", knowledge="inferred", kind=..., done=aperta).motivi[0])
        self.assertIn("closing cannot turn note «0001» into «todo»", self.proponi(kind="todo", done=aperta).motivi[0])
        chiusa = self.nota(kind="decision", done=aperta)
        self.assertEqual(chiusa, "0001.1")
        self.assertEqual(self.proponi(kind="decision", done=aperta).motivi,
                         [f"note «{aperta}» is already closed (✓D0001.1): to reopen it use «reopens»."])

    def test_todo_e_promemoria_li_chiude_anche_claude(self):
        da_fare = self.nota(author="claude", knowledge="inferred", kind="todo")
        promemoria = self.nota(author="claude", knowledge="inferred", kind="idea", remind="2026-01-10")
        esito = self.proponi(author="claude", knowledge="observed", kind=..., done=f"{da_fare}, {promemoria}")
        self.assertEqual([numero for numero, _ in esito.scritte], ["0001.1", "0002.1"])
        self.assertIn("- status: closed\n", self.file_nota("0001.1"))
        self.assertIn("- change: closed\n", self.file_nota("0002.1"))

    def test_cosa_non_si_chiude(self):
        fatto = self.nota()
        idea = self.nota(author="claude", knowledge="inferred", kind="idea")
        decisione = self.nota(kind="decision")
        for numero in (fatto, idea, decisione):
            with self.subTest(numero=numero):
                motivo = self.proponi(kind=..., done=numero).motivi[0]
                self.assertIn("«done» closes only open, todo and reminder notes", motivo)
                self.assertTrue(motivo.endswith("correct it with «corrects» or change it with «updates»."), motivo)

    def test_elenco_di_numeri(self):
        da_fare = self.nota(kind="todo")
        for valore, motivo in (("0001, 0001", "listed twice"), ("0099", "does not exist"),
                               ("uno", "must contain a note number"), ("0001,", "must contain a note number")):
            with self.subTest(valore=valore):
                self.assertIn(motivo, " ".join(self.proponi(kind=..., done=valore).motivi))
        self.assertEqual(da_fare, "0001")

    def test_ricerca_e_recap_senza_le_chiuse(self):
        self.nota(text="Comprare il terriccio.", kind="todo")
        self.nota(text="Il terriccio è arrivato.", kind=..., done="0001")
        _, uscita = self.comando("search", "terriccio")
        self.assertIn("Nessuna nota aperta contiene «terriccio».\n(1 nota chiusa non mostrata: aggiungi --all per "
                      "vederla.)", uscita)
        self.assertNotIn("--- Nota", uscita)
        _, tutte = self.comando("search", "terriccio", "--all")
        self.assertIn("--- Nota ✓T0001.1 ---", tutte)
        self.assertIn("✓T0001.1 2026-01-15 · user: chiusa il 2026-01-15, perché «Il terriccio è arrivato.»", tutte)
        _, recap = self.comando("recap")
        self.assertIn("Cose da fare: nessuna.", recap)
        self.assertEqual(cercatore.cerca(self.config, "terriccio"), [])

    def test_nessuna_aperta(self):
        self.nota(text="Comprare il terriccio.", kind="todo")
        self.nota(text="Fatto.", kind=..., done="0001")
        _, uscita = self.comando("search", "terriccio")
        self.assertEqual(uscita, "Nessuna nota aperta contiene «terriccio».\n"
                                 "(1 nota chiusa non mostrata: aggiungi --all per vederla.)\n")

    def test_blocco_cose_da_fare(self):
        for i in range(7):
            self.nota(text=f"Cosa {i}.", kind="todo")
        _, recap = self.comando("recap")
        self.assertIn("Cose da fare: 5 di 7 (prima la priorità alta, poi dal più recente)\n- [T0007]", recap)
        self.assertIn("(2 cose da fare più vecchie non mostrate)", recap)

    def test_sezione_recap_todo(self):
        self.file_config.write_text(CONFIG_DI_PROVA + "\n[recap]\ntodo = 1\n", encoding="utf-8")
        self.config = configurazione.carica(str(self.file_config))
        self.assertEqual(self.config.recap_todo, 1)


class TestPriorita(ConQuaderno):
    def test_solo_dell_utente(self):
        self.assertIn("only the user can set «priority»",
                      self.proponi(author="claude", knowledge="inferred", kind="idea", priority="high").motivi[0])
        self.assertIn("«urgent» is not allowed for «priority»", self.proponi(priority="urgent").motivi[0])

    def test_priorita_in_vigore(self):
        prima = self.nota(kind="todo")
        seconda = self.nota(kind="todo", priority="low")
        storie = cercatore.leggi(self.config).elenco()
        self.assertEqual([cercatore.priorita_in_vigore(s) for s in storie], ["normal", "low"])
        self.assertEqual(self.nota(kind=..., updates=seconda, priority="high"), "0002.1")
        self.assertEqual(cercatore.priorita_in_vigore(cercatore.leggi(self.config).storie["0002"]), "high")
        self.assertIn("changes nothing", self.proponi(kind=..., updates=seconda, priority="high").motivi[0])
        self.assertEqual(prima, "0001")

    def test_ordine_nel_recap(self):
        self.nota(text="Normale.", kind="todo")
        self.nota(text="Bassa.", kind="todo", priority="low")
        self.nota(text="Alta.", kind="todo", priority="high")
        self.nota(text="Promemoria basso.", kind="todo", priority="low", remind="2026-01-01")
        self.nota(text="Promemoria alto.", kind="todo", priority="high", remind="2026-01-10")
        _, recap = self.comando("recap")
        self.assertIn("- [T0005] [alta] da riprendere il 2026-01-10: Promemoria alto.\n"
                      "- [T0004] [bassa] da riprendere il 2026-01-01: Promemoria basso.\n", recap)
        self.assertIn("- [T0005] [alta] 2026-01-15: Promemoria alto.\n- [T0003] [alta] 2026-01-15: Alta.\n"
                      "- [T0001] 2026-01-15: Normale.\n- [T0004] [bassa] 2026-01-15: Promemoria basso.\n"
                      "- [T0002] [bassa] 2026-01-15: Bassa.\n", recap)


class TestDocumenti(unittest.TestCase):
    def test_skill_in_inglese_con_le_novita(self):
        skill = testo_della_skill()
        self.assertIn("description: Permanent memory", skill)
        for frammento in ("**Language by role.**", "**only the user** closes, reopens or changes the kind of an `open`", "### Priority",
                          "Da questa nota in poi", "`todo`: something to do", "P search <word> --all",
                          "/hypomnema:pause", "**you always talk to the user\nin Italian**"):
            with self.subTest(frammento=frammento):
                self.assertIn(frammento, skill)

    def test_readme(self):
        readme = (RADICE / "README.md").read_text(encoding="utf-8")
        for frammento in ("### Lingua per ruolo", "### Ogni cambiamento è una versione nuova",
                          "### La priorità", "### Quando cambiano le regole del quaderno: la nota-regola",
                          "Da questa nota in poi", "**Gli `open` li chiudi e li riapri solo tu**"):
            with self.subTest(frammento=frammento):
                self.assertIn(frammento, readme)

    def test_storia(self):
        self.assertIn("## 0.5.0", (RADICE / "STORIA.md").read_text(encoding="utf-8"))


class TestQuadernoVecchioItaliano(unittest.TestCase):
    """Il quaderno dell'esempio 52 (note della 0.4.0, in italiano): tutti i comandi, nei due nomi."""

    def test_tutti_i_comandi_e_niente_toccato(self):
        esempio = RADICE / "esempi" / "52-quaderno-vecchio-italiano"
        with tempfile.TemporaryDirectory() as tmp:
            cartella = Path(tmp)
            shutil.copytree(esempio / "quaderno-iniziale", cartella / "quaderno")
            file_config = cartella / "hypomnema.toml"
            shutil.copy(esempio / "hypomnema.toml", file_config)
            prima = {p: p.read_bytes() for p in (cartella / "quaderno").rglob("*") if p.is_file()}
            for comando in (["cerca", "compostiera"], ["search", "compostiera", "--all"], ["promemoria"],
                            ["reminders"], ["recap"], ["controlla"], ["check"], ["stato"], ["status"],
                            ["diario", "--ultimi", "2"], ["diary", "--last", "2"], ["istantanea"], ["snapshot"]):
                with self.subTest(comando=comando):
                    codice = main(["--config", str(file_config), *comando], adesso=ADESSO, uscita=io.StringIO())
                    self.assertEqual(codice, 0)
            dopo = {p: p.read_bytes() for p in (cartella / "quaderno").rglob("*") if p.is_file()}
            self.assertEqual(prima, dopo)
            note = quaderno.leggi_note(configurazione.carica(str(file_config)))
            self.assertEqual([n.natura for n in note], ["decision", "decision", "decision", "open", "open", "idea", "fact"])


if __name__ == "__main__":
    unittest.main()
