"""Test del testimone delle risposte di Claude, del filtro sul codice, di impronta, del diario
e delle note con da_risposta. Solo dati inventati."""

import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from hypomnema import configurazione, diario, risposte, sportello, testimone
from hypomnema.cli import main
from tests.esecutore import CONFIG_DI_PROVA, RADICE
from tests.test_chat import CONFIG_CHAT
from tests.test_regole import ADESSO, NOTA_BUONA
from tests.test_testimone import CONFIG_ACCESO

SEZIONE = '\n[risposte]\nattivo = true\nfile = "risposte.jsonl"\nometti_codice = true\n'
CONFIG_RISPOSTE = CONFIG_ACCESO + SEZIONE


def messaggio(testo, prompt_id=None):
    dati = {"hook_event_name": "UserPromptSubmit", "prompt": testo}
    if prompt_id is not None:
        dati["prompt_id"] = prompt_id
    return json.dumps(dati).encode("utf-8")


def risposta(testo, prompt_id=None):
    dati = {"hook_event_name": "Stop", "stop_hook_active": False, "last_assistant_message": testo}
    if prompt_id is not None:
        dati["prompt_id"] = prompt_id
    return json.dumps(dati).encode("utf-8")


def impronta_di(righe):
    return hashlib.sha256("".join(r + "\n" for r in righe).encode("utf-8")).hexdigest()[:12]


class ConQuaderno(unittest.TestCase):
    config_testo = CONFIG_RISPOSTE

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cartella = Path(self._tmp.name).resolve()
        self.file_config = self.cartella / "hypomnema.toml"
        self.scrivi_config(self.config_testo)
        self.minuti = 0

    def tearDown(self):
        self._tmp.cleanup()

    def scrivi_config(self, testo):
        self.file_config.write_text(testo, encoding="utf-8")
        self.config = configurazione.carica(str(self.file_config))

    def adesso(self):
        self.minuti += 1
        return ADESSO + timedelta(minutes=self.minuti)

    def dice(self, testo, prompt_id=None):
        testimone.registra(self.config, self.adesso(), messaggio(testo, prompt_id))

    def risponde(self, testo, prompt_id=None):
        return risposte.registra(self.config, self.adesso(), risposta(testo, prompt_id))

    def righe_risposte(self):
        return [json.loads(r) for r in self.config.file_risposte.read_text(encoding="utf-8").splitlines()]

    def comando(self, *argomenti):
        uscita = io.StringIO()
        codice = main(["--config", str(self.file_config), *argomenti], uscita=uscita, errori=uscita)
        return codice, uscita.getvalue()

    def proponi(self, **modifiche):
        nota = {k: v for k, v in dict(NOTA_BUONA, **modifiche).items() if v is not ...}
        return sportello.ricevi(json.dumps(nota).encode("utf-8"), "prova.json", self.config, self.adesso())


class TestConfigurazioneRisposte(ConQuaderno):
    def errore(self, testo, frammento):
        self.file_config.write_text(testo, encoding="utf-8")
        with self.assertRaisesRegex(configurazione.ErroreConfigurazione, frammento):
            configurazione.carica(str(self.file_config))

    def test_senza_sezione_spento(self):
        self.scrivi_config(CONFIG_ACCESO)
        self.assertFalse(self.config.sezione_risposte)
        self.assertFalse(self.config.risposte_attive)
        self.assertIsNone(self.config.file_risposte)

    def test_acceso(self):
        self.assertTrue(self.config.risposte_attive)
        self.assertTrue(self.config.ometti_codice)
        self.assertEqual(self.config.file_risposte, self.cartella / "quaderno" / "risposte.jsonl")

    def test_serve_anche_il_testimone_dell_utente(self):
        self.errore(CONFIG_DI_PROVA + SEZIONE, "le risposte si registrano solo insieme ai messaggi")

    def test_in_chat_non_esiste(self):
        self.errore(CONFIG_CHAT + SEZIONE, "nella chat di Claude non esiste")

    def test_valori_sbagliati(self):
        for vecchio, nuovo, frammento in (
            ("attivo = true\nfile", 'attivo = "sì"\nfile', "«attivo» della sezione \\[risposte\\]"),
            ("ometti_codice = true", "ometti_codice = 1", "«ometti_codice» della sezione \\[risposte\\]"),
            ('file = "risposte.jsonl"', 'file = "/tmp/risposte.jsonl"', "dentro la cartella del quaderno"),
            ('file = "risposte.jsonl"', 'file = "../risposte.jsonl"', "dentro la cartella del quaderno"),
            ('file = "risposte.jsonl"\n', "", "dentro la cartella del quaderno"),
        ):
            with self.subTest(nuovo=nuovo):
                testo = CONFIG_ACCESO + SEZIONE.replace(vecchio, nuovo)
                self.assertNotEqual(testo, CONFIG_RISPOSTE)
                self.errore(testo, frammento)

    def test_modelli(self):
        self.assertFalse(configurazione.carica(str(RADICE / "hypomnema.toml")).risposte_attive)
        uso = configurazione.carica(str(RADICE / "windows" / "hypomnema-uso.toml"))
        self.assertTrue(uso.risposte_attive and uso.ometti_codice)
        self.assertFalse(configurazione.carica(str(RADICE / "chat" / "hypomnema-chat.toml")).sezione_risposte)


class TestFiltroSulCodice(unittest.TestCase):
    def test_blocco_sostituito_con_impronta(self):
        testo = "Ecco:\n```python\nprint(1)\nprint(2)\n```\nFine."
        self.assertEqual(risposte.ometti_codice(testo),
                         f"Ecco:\n[blocco di codice di 2 righe omesso, impronta {impronta_di(['print(1)', 'print(2)'])}]\nFine.")

    def test_stesso_blocco_stessa_impronta(self):
        uno = risposte.ometti_codice("a\n```\nx = 1\n```")
        due = risposte.ometti_codice("b\n```js\nx = 1\n```\nc")
        self.assertEqual(uno.split("\n")[1], due.split("\n")[1])
        self.assertEqual(uno.split("\n")[1], f"[blocco di codice di 1 riga omesso, impronta {impronta_di(['x = 1'])}]")

    def test_piu_blocchi(self):
        uscita = risposte.ometti_codice("```\na\n```\nmezzo\n```\nb\n```")
        self.assertEqual(uscita.split("\n")[1], "mezzo")
        self.assertEqual(uscita.count("omesso"), 2)

    def test_quattro_apici_contengono_tre(self):
        righe = ["```", "dentro", "```"]
        testo = "````\n" + "\n".join(righe) + "\n````\nfuori"
        self.assertEqual(risposte.ometti_codice(testo),
                         f"[blocco di codice di 3 righe omesso, impronta {impronta_di(righe)}]\nfuori")

    def test_blocco_mai_chiuso_arriva_in_fondo(self):
        self.assertEqual(risposte.ometti_codice("a\n```\nx\ny"),
                         f"a\n[blocco di codice di 2 righe omesso, impronta {impronta_di(['x', 'y'])}]")

    def test_blocco_vuoto(self):
        self.assertEqual(risposte.ometti_codice("```\n```"),
                         f"[blocco di codice di 0 righe omesso, impronta {impronta_di([])}]")

    def test_senza_blocchi_testo_uguale(self):
        testo = "Niente codice, solo `apici` singoli e ``doppi``.\n  rientro"
        self.assertEqual(risposte.ometti_codice(testo), testo)

    def test_rientro_di_quattro_spazi_non_apre(self):
        testo = "a\n    ```\nb"
        self.assertEqual(risposte.ometti_codice(testo), testo)


class TestTestimoneDelleRisposte(ConQuaderno):
    def test_spento_non_registra(self):
        self.scrivi_config(CONFIG_ACCESO + SEZIONE.replace("attivo = true", "attivo = false"))
        self.dice("ciao")
        self.assertFalse(self.risponde("risposta"))
        self.assertFalse((self.cartella / "quaderno" / "risposte.jsonl").exists())

    def test_registra_con_codice_omesso(self):
        self.dice("domanda", "t1")
        self.assertTrue(self.risponde("Ecco:\n```\nx = 1\n```", "t1"))
        self.assertEqual(self.righe_risposte(), [{
            "quando": "2026-01-15T10:02:00+01:00",
            "testo": f"Ecco:\n[blocco di codice di 1 riga omesso, impronta {impronta_di(['x = 1'])}]",
            "prompt_id": "t1",
        }])

    def test_codice_intero_se_spento_il_filtro(self):
        self.scrivi_config(CONFIG_ACCESO + SEZIONE.replace("ometti_codice = true", "ometti_codice = false"))
        self.dice("domanda")
        self.risponde("Ecco:\n```\nx = 1\n```")
        self.assertEqual(self.righe_risposte()[0]["testo"], "Ecco:\n```\nx = 1\n```")

    def test_il_testimone_dell_utente_non_cambia(self):
        self.dice("Ecco:\n```\nx = 1\n```")
        voce = json.loads(self.config.file_testimone.read_text(encoding="utf-8"))
        self.assertEqual(voce["testo"], "Ecco:\n```\nx = 1\n```")

    def test_risposta_a_messaggio_privato(self):
        self.dice("#privato segreto", "t1")
        self.risponde("la risposta segreta", "t1")
        self.assertEqual(self.righe_risposte()[0]["privato"], "risposta a un messaggio privato, non registrata")
        self.assertNotIn("segreta", self.config.file_risposte.read_text(encoding="utf-8"))

    def test_privato_senza_prompt_id_usa_l_ultimo_messaggio(self):
        self.dice("normale")
        self.dice("#privato segreto")
        self.risponde("la risposta segreta")
        self.assertIn("privato", self.righe_risposte()[0])

    def test_prompt_id_lega_la_risposta_al_suo_messaggio(self):
        self.dice("#privato segreto", "t1")
        self.dice("normale", "t2")
        self.risponde("risposta al primo", "t1")
        self.risponde("risposta al secondo", "t2")
        righe = self.righe_risposte()
        self.assertIn("privato", righe[0])
        self.assertEqual(righe[1]["testo"], "risposta al secondo")

    def test_messaggio_non_trovato_per_prudenza_non_registra(self):
        self.dice("normale", "t1")
        self.risponde("risposta", "t9")
        self.assertEqual(self.righe_risposte()[0]["privato"],
                         "risposta a un messaggio non trovato nel testimone, non registrata")

    def test_nessun_messaggio_registrato(self):
        self.risponde("risposta")
        self.assertIn("non trovato nel testimone", self.righe_risposte()[0]["privato"])

    def test_solo_aggiunta(self):
        self.dice("uno")
        self.risponde("prima")
        prima = self.config.file_risposte.read_text(encoding="utf-8")
        self.dice("due")
        self.risponde("seconda")
        self.assertTrue(self.config.file_risposte.read_text(encoding="utf-8").startswith(prima))

    def test_risposta_non_valida(self):
        for contenuto in (b"non json", b"[1]", b'{"altro": 1}', b'{"last_assistant_message": 3}'):
            with self.subTest(contenuto=contenuto):
                with self.assertRaises(testimone.ErroreTestimone):
                    risposte.registra(self.config, ADESSO, contenuto)

    def test_prompt_id_nel_testimone_dell_utente(self):
        self.dice("ciao", "t1")
        self.dice("senza")
        messaggi = testimone.leggi_messaggi(self.config)
        self.assertEqual([m.prompt_id for m in messaggi], ["t1", None])

    def test_prompt_id_non_testo_rifiutato(self):
        self.config.cartella_quaderno.mkdir()
        self.config.file_testimone.write_text('{"quando": "x", "testo": "a", "prompt_id": 3}\n', encoding="utf-8")
        with self.assertRaises(testimone.ErroreTestimone):
            testimone.leggi_messaggi(self.config)


class TestComandoRisposte(ConQuaderno):
    """Come Claude Code lancia il comando: niente a schermo, mai il codice 2."""

    def lancia(self, ingresso, *argomenti, comando=("-m", "hypomnema")):
        ambiente = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
        ambiente.update(PYTHONPATH=str(RADICE), HYPOMNEMA_CONFIG=str(self.file_config))
        return subprocess.run([sys.executable, *comando, *argomenti], input=ingresso,
                              capture_output=True, env=ambiente, cwd=self.cartella)

    def test_registra_senza_scrivere_a_schermo(self):
        self.dice("domanda")
        risultato = self.lancia(risposta("dal vero"), "risposte")
        self.assertEqual(risultato.returncode, 0, risultato.stderr)
        self.assertEqual(risultato.stdout, b"")
        self.assertEqual(self.righe_risposte()[0]["testo"], "dal vero")

    def test_errori_mai_con_codice_2(self):
        for argomenti, ingresso in ((("risposte",), b"rotto"), (("risposte", "--sconosciuto"), b""),
                                    (("--config", "manca.toml", "risposte"), risposta("x"))):
            with self.subTest(argomenti=argomenti):
                risultato = self.lancia(ingresso, *argomenti)
                self.assertEqual(risultato.returncode, 1)
                self.assertEqual(risultato.stdout, b"")

    def test_errore_in_utf8(self):
        risultato = self.lancia(b"rotto", "risposte")
        self.assertIn("La risposta NON è stata registrata.", risultato.stderr.decode("utf-8"))

    def test_programma_del_plugin_con_risposte(self):
        self.dice("domanda")
        risultato = self.lancia(risposta("dall'aggancio"), "risposte", comando=(str(RADICE / "programma.py"),))
        self.assertEqual(risultato.returncode, 0, risultato.stderr)
        self.assertEqual(self.righe_risposte()[0]["testo"], "dall'aggancio")

    def test_programma_del_plugin_scritto_male_non_blocca(self):
        risultato = self.lancia(b"", "risposte", "--sconosciuto", comando=(str(RADICE / "programma.py"),))
        self.assertEqual(risultato.returncode, 1)

    def test_plugin_aggancia_stop(self):
        agganci = json.loads((RADICE / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        comandi = [h["command"] for g in agganci["Stop"] for h in g["hooks"]]
        self.assertEqual(len(comandi), 1)
        self.assertIn('programma.py" replies;', comandi[0])


class TestImpronta(unittest.TestCase):
    def test_file_e_testo(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "blocco.py"
            file.write_bytes(b"x = 1\n")
            uscita = io.StringIO()
            vecchia = os.getcwd()
            os.chdir(tmp)  # nessuna configurazione: non serve
            try:
                codice = main(["impronta", str(file)], uscita=uscita)
            finally:
                os.chdir(vecchia)
            self.assertEqual(codice, 0)
            self.assertEqual(uscita.getvalue(), f"Impronta di «{file}»: {impronta_di(['x = 1'])} (6 byte).\n")
            risultato = subprocess.run([sys.executable, "-m", "hypomnema", "impronta", "-"], input=b"x = 1\n",
                                       capture_output=True, cwd=tmp, env=dict(os.environ, PYTHONPATH=str(RADICE)))
            self.assertEqual(risultato.stdout.decode("utf-8").strip(),
                             f"Impronta di testo: {impronta_di(['x = 1'])} (6 byte).")

    def test_file_mancante(self):
        uscita = io.StringIO()
        self.assertEqual(main(["impronta", "non-esiste.py"], uscita=uscita), 2)


class TestDiario(ConQuaderno):
    def test_ordine_di_tempo_e_chi_parla(self):
        self.dice("Le fragole?")
        self.risponde("Le fragole vogliono sole.")
        self.dice("E il basilico?")
        tutte = diario.voci(self.config)
        self.assertEqual([(v.chi, v.testo) for v in tutte],
                         [("utente", "Le fragole?"), ("claude", "Le fragole vogliono sole."), ("utente", "E il basilico?")])

    def test_stessa_ora_prima_l_utente(self):
        self.dice("domanda")
        risposte.registra(self.config, ADESSO + timedelta(minutes=1), risposta("risposta"))
        self.assertEqual([v.chi for v in diario.voci(self.config)], ["utente", "claude"])

    def test_cerca_parola_esatta_senza_maiuscole(self):
        self.dice("Le FRAGOLE?")
        self.risponde("Il fragolone no.")
        codice, uscita = self.comando("diario", "fragole")
        self.assertEqual(codice, 0)
        self.assertIn("Trovato 1 messaggio con «fragole» nel diario", uscita)
        self.assertIn("· utente ---\n  Le FRAGOLE?", uscita)
        self.assertNotIn("fragolone", uscita)

    def test_intorno(self):
        for testo in ("uno", "due fragole", "tre"):
            self.dice(testo)
            self.risponde(f"risposta a {testo}")
        codice, uscita = self.comando("diario", "fragole", "--intorno")
        righe = [r for r in uscita.splitlines() if r.startswith("  ")]
        self.assertEqual(righe, ["  risposta a uno", "  due fragole", "  risposta a due fragole", "  tre"])
        self.assertIn("· utente (trovato) ---", uscita)

    def test_intorno_separa_i_gruppi(self):
        for testo in ("fragole", "a", "b", "c", "fragole"):
            self.dice(testo)
        _, uscita = self.comando("diario", "fragole", "--intorno")
        self.assertIn("\n[...]\n", uscita)

    def test_messaggi_privati_mostrati_come_tali(self):
        self.dice("#privato segreto")
        self.risponde("fragole segrete")
        self.dice("fragole")
        _, uscita = self.comando("diario", "fragole", "--intorno")
        self.assertIn("(risposta a un messaggio privato, non registrata)", uscita)
        self.assertNotIn("segret", uscita)

    def test_vuoto_e_non_trovato(self):
        self.assertEqual(self.comando("diario", "x"), (0, "Il diario è vuoto: non c'è nessun messaggio registrato.\n"))
        self.dice("ciao")
        self.assertEqual(self.comando("diario", "x"), (0, "Nessun messaggio del diario contiene «x».\n"))

    def test_solo_lettura(self):
        self.dice("fragole")
        self.risponde("fragole")
        prima = {p: p.read_bytes() for p in self.cartella.rglob("*") if p.is_file()}
        self.comando("diario", "fragole", "--intorno")
        self.assertEqual({p: p.read_bytes() for p in self.cartella.rglob("*") if p.is_file()}, prima)

    def test_data_non_valida(self):
        self.config.cartella_quaderno.mkdir()
        self.config.file_testimone.write_text('{"quando": "ieri", "testo": "a"}\n', encoding="utf-8")
        codice, uscita = self.comando("diario", "a")
        self.assertEqual(codice, 2)
        self.assertIn("data non valida", uscita)


class TestNoteDaRisposta(ConQuaderno):
    def riga_verifica(self, esito):
        return [r for r in esito.percorso.read_text(encoding="utf-8").splitlines() if r.startswith("- verifica")][0]

    def nota_claude(self, testo, **altro):
        return self.proponi(autore="claude", tipo="dedotta", natura="idea", da_risposta="sì", testo=testo, **altro)

    def test_trovata(self):
        self.dice("domanda")
        self.risponde("Conviene  una barriera\ndi cenere. E altro.")
        esito = self.nota_claude("Conviene una barriera di cenere.")
        self.assertTrue(esito.accettata, esito.motivi)
        self.assertEqual(self.riga_verifica(esito),
                         "- verification: text found in Claude's reply of 2026-01-15T10:02:00+01:00")
        self.assertIn("- from_reply: yes", esito.percorso.read_text(encoding="utf-8"))

    def test_mai_detta(self):
        self.dice("domanda")
        self.risponde("Conviene una barriera di cenere.")
        esito = self.nota_claude("Conviene il rame.")
        self.assertFalse(esito.accettata)
        self.assertIn("in any recorded reply of Claude", esito.motivi[0])

    def test_codice_omesso_non_si_trova(self):
        self.dice("domanda")
        self.risponde("Usa:\n```\nx = 1\n```")
        self.assertFalse(self.nota_claude("x = 1").accettata)

    def test_non_si_cerca_nei_messaggi_dell_utente(self):
        self.dice("Conviene il rame.")
        self.risponde("altro")
        self.assertFalse(self.nota_claude("Conviene il rame.").accettata)

    def test_risposte_spente(self):
        self.scrivi_config(CONFIG_ACCESO)
        esito = self.nota_claude("qualunque cosa")
        self.assertEqual(self.riga_verifica(esito), "- verification: reply not verified (replies witness off)")

    def test_in_chat(self):
        self.scrivi_config(CONFIG_CHAT)
        esito = self.nota_claude("qualunque cosa")
        self.assertEqual(self.riga_verifica(esito), "- verification: reply not verified (chat, no witness)")

    def test_regole_del_campo(self):
        self.dice("domanda")
        self.risponde("testo")
        for modifiche, frammento in (
            (dict(da_risposta="no"), "can only be «yes»"),
            (dict(autore="utente", tipo="dichiarata"), "is only for Claude's notes"),
            (dict(citazione="domanda"), "both «from_reply» and «quote»"),
        ):
            with self.subTest(modifiche=modifiche):
                nota = dict(autore="claude", tipo="dedotta", natura="idea", da_risposta="sì", testo="testo")
                nota.update(modifiche)
                esito = self.proponi(**nota)
                self.assertFalse(esito.accettata)
                self.assertTrue(any(frammento in m for m in esito.motivi), esito.motivi)

    def test_stato_mostra_le_risposte_solo_con_la_sezione(self):
        self.dice("domanda")
        self.risponde("risposta")
        _, uscita = self.comando("stato")
        self.assertIn("Testimone delle risposte: ACCESO (registra le risposte di Claude, con i blocchi di codice omessi).", uscita)
        self.assertIn("Risposte registrate: 1", uscita)
        self.scrivi_config(CONFIG_ACCESO)
        self.assertNotIn("risposte", self.comando("stato")[1])


class TestSkillDiario(unittest.TestCase):
    def test_skill(self):
        skill = (RADICE / "skills" / "hypomnema" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## 6. What we said: notebook and diary (Claude Code)", skill)
        self.assertIn("`P diary <word>`", skill)
        self.assertIn('`from_reply: "yes"`', skill)
        self.assertIn("**there are no witnesses**", skill)


if __name__ == "__main__":
    unittest.main()
