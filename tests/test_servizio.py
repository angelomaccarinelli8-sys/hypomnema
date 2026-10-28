"""Test della 0.11.0, prima parte: il server MCP su stdio (il cuore, il trasporto, le proposte, il guardiano, due
scrittori insieme). Solo quaderni inventati."""

import io
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

from hypomnema import mcp_stdio, servizio
from hypomnema.cli import main
from tests.esecutore import RADICE, modello_chat
from tests.test_regole import ADESSO

NOTA = {"date": "2026-01-15", "source": "chat di prova sull'orto", "author": "user", "knowledge": "stated",
        "kind": "fact", "text": "L'orto è sul balcone esposto a sud."}
ETICHETTE = 'chi = ["Marta"]\ncosa = ["orto"]\n'


def chiamata(numero: int, nome: str, argomenti=None) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": numero, "method": "tools/call",
                       "params": {"name": nome, "arguments": argomenti or {}}}, ensure_ascii=False)


class ConTaccuino(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cartella = Path(self._tmp.name)
        self.config = modello_chat(self.cartella)
        (self.cartella / "quaderno").mkdir()
        (self.cartella / "quaderno" / "etichette.toml").write_text(ETICHETTE, encoding="utf-8")
        self.taccuino = servizio.Taccuino("prova", self.config, orologio=lambda: ADESSO)

    def tearDown(self):
        self._tmp.cleanup()

    def comando(self, *riga: str) -> str:
        uscita = io.StringIO()
        main(["--config", str(self.config), *riga], adesso=ADESSO, uscita=uscita, errori=uscita)
        return uscita.getvalue()

    def strumento(self, nome: str, argomenti=None) -> str:
        testo, errore = servizio.chiama(self.taccuino, nome, argomenti)
        self.assertFalse(errore, testo)
        return testo


class TestCuore(ConTaccuino):
    def test_gli_strumenti(self):
        nomi = [s["name"] for s in servizio.elenco_strumenti()]
        self.assertEqual(nomi, ["status", "check", "recap", "review", "tree", "search", "labels", "template",
                                "propose", "archive"])

    def test_nessuno_strumento_accetta_un_altro_taccuino(self):
        for strumento in servizio.elenco_strumenti():
            schema = strumento["inputSchema"]
            self.assertFalse(schema["additionalProperties"])
            for chiave in schema["properties"]:
                self.assertNotIn(chiave, ("config", "folder", "path", "file", "notebook", "cartella"))

    def test_stessi_messaggi_dei_comandi(self):
        self.strumento("propose", {"proposal": dict(NOTA, who="Marta")})
        coppie = [
            ("status", {}, ["status"]), ("check", {}, ["check"]), ("recap", {}, ["recap"]),
            ("recap", {"about": ["orto"]}, ["recap", "--about", "orto"]),
            ("review", {"proposals": True}, ["review", "--proposals"]),
            ("tree", {"about": ["orto"], "all": True}, ["tree", "--cosa", "orto", "--all"]),
            ("search", {"word": "balcone"}, ["search", "balcone"]),
            ("search", {"word": "balcone", "all": True, "who": ["Marta"]}, ["search", "balcone", "--all", "--chi", "Marta"]),
            ("search", {"about": ["orto"]}, ["search", "--about", "orto"]),
            ("labels", {}, ["labels"]), ("template", {}, ["template"]), ("template", {"move": "done"}, ["template", "done"]),
        ]
        for nome, argomenti, riga in coppie:
            with self.subTest(strumento=nome, argomenti=argomenti):
                self.assertEqual(self.strumento(nome, argomenti), self.comando(*riga))

    def test_argomenti_sbagliati(self):
        sbagliati = [
            ("search", {"word": "orto", "config": "altro.toml"}), ("search", {"word": 3}),
            ("search", {"about": "orto"}), ("search", {"all": "sì"}), ("template", {"move": "cancella"}),
            ("propose", {}), ("propose", {"proposal": "testo"}), ("recap", ["orto"]),
        ]
        for nome, argomenti in sbagliati:
            with self.subTest(strumento=nome, argomenti=argomenti), self.assertRaises(servizio.ErroreArgomenti):
                servizio.chiama(self.taccuino, nome, argomenti)

    def test_un_valore_non_diventa_un_opzione(self):
        altra = self.cartella / "altra"
        altra.mkdir()
        (altra / "hypomnema.toml").write_text(self.config.read_text(encoding="utf-8"), encoding="utf-8")
        for argomenti in ({"word": f"--config={altra / 'hypomnema.toml'}"}, {"word": "--all"},
                          {"about": [f"--config={altra}"]}):
            with self.subTest(argomenti=argomenti):
                testo, _ = servizio.chiama(self.taccuino, "search", argomenti)
                self.assertNotIn("Trovat", testo)
        self.assertFalse((altra / "quaderno").exists())

    def test_proposta_con_il_controllo(self):
        testo = self.strumento("propose", {"proposal": NOTA})
        self.assertTrue(testo.startswith("ACCETTATA: la nota 0001"))
        self.assertIn("Controllo dopo il passaggio (check):\nQuaderno in ordine: 1 nota", testo)
        self.assertIn("| da: (strumento MCP)", (self.cartella / "quaderno" / "registro.md").read_text(encoding="utf-8"))
        rifiutata = self.strumento("propose", {"proposal": dict(NOTA, author="claude", kind="decision")})
        self.assertIn("RIFIUTATA", rifiutata)
        self.assertIn("Controllo dopo il passaggio (check)", rifiutata)

    def test_la_nota_dell_utente_resta_non_verificata(self):
        self.strumento("propose", {"proposal": NOTA})
        self.assertIn("author not verified (chat, no witness)",
                      (self.cartella / "quaderno" / "note" / "0001.md").read_text(encoding="utf-8"))

    def test_archivio_e_nota_riscontrata(self):
        archivio = {"chat": "https://claude.ai/chat/00000000-0000-0000-0000-000000000001", "fuso": "UTC+01:00",
                    "messaggi": [{"turno": 1, "quando": "Thu 2026-01-15 10:00", "chi": "utente",
                                  "testo": "L'orto è sul balcone esposto a sud."}]}
        testo = self.strumento("archive", {"archive": archivio})
        self.assertIn("Copiati dall'archivio della chat: 1 messaggio dell'utente", testo)
        self.assertIn("Controllo dopo il passaggio (check)", testo)
        self.strumento("propose", {"proposal": NOTA})
        self.assertIn("text matched in the chat archive",
                      (self.cartella / "quaderno" / "note" / "0001.md").read_text(encoding="utf-8"))

    def test_errore_della_configurazione_all_avvio(self):
        with self.assertRaises(Exception):
            servizio.Taccuino("prova", self.cartella / "non-c-e.toml")


class TestProtocollo(ConTaccuino):
    def rispondi(self, messaggio):
        return servizio.rispondi(self.taccuino, messaggio)

    def test_initialize(self):
        risposta = self.rispondi({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                  "params": {"protocolVersion": "2025-03-26"}})["result"]
        self.assertEqual(risposta["protocolVersion"], "2025-03-26")
        self.assertEqual(risposta["serverInfo"]["name"], "hypomnema")
        self.assertIn("You never write its files", risposta["instructions"])
        sconosciuta = self.rispondi({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                     "params": {"protocolVersion": "1999-01-01"}})["result"]
        self.assertEqual(sconosciuta["protocolVersion"], servizio.VERSIONI_PROTOCOLLO[0])

    def test_notifiche_senza_risposta(self):
        self.assertIsNone(self.rispondi({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_errori(self):
        self.assertEqual(self.rispondi({"jsonrpc": "2.0", "id": 1, "method": "boh"})["error"]["code"], -32601)
        self.assertEqual(self.rispondi({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                        "params": {"name": "delete"}})["error"]["code"], -32602)
        self.assertEqual(self.rispondi([{"jsonrpc": "2.0", "id": 1, "method": "ping"}])["error"]["code"], -32600)
        self.assertEqual(servizio.rispondi_al_testo(self.taccuino, "{non json")["error"]["code"], -32700)
        sbagliato = self.rispondi(json.loads(chiamata(1, "search", {"cartella": "x"})))["result"]
        self.assertTrue(sbagliato["isError"])

    def test_istruzioni_corte(self):
        # La scheda corta sta al posto della skill lunga: deve restare corta.
        self.assertLess(len(servizio.ISTRUZIONI), 3000)


class TestStdio(ConTaccuino):
    def test_processo_vero(self):
        righe = [
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}}),
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
            chiamata(3, "propose", {"proposal": NOTA}),
            chiamata(4, "search", {"word": "balcone"}),
        ]
        processo = subprocess.run([sys.executable, str(RADICE / "programma.py"), "--config", str(self.config), "serve"],
                                  input="\n".join(righe) + "\n", capture_output=True, encoding="utf-8", timeout=60)
        self.assertEqual(processo.returncode, 0, processo.stderr)
        risposte = [json.loads(r) for r in processo.stdout.splitlines()]
        self.assertEqual([r["id"] for r in risposte], [1, 2, 3, 4])
        self.assertEqual(len(risposte[1]["result"]["tools"]), 10)
        self.assertIn("ACCETTATA", risposte[2]["result"]["content"][0]["text"])
        self.assertIn("Trovata 1 nota", risposte[3]["result"]["content"][0]["text"])

    def test_configurazione_sbagliata(self):
        processo = subprocess.run([sys.executable, str(RADICE / "programma.py"), "--config",
                                   str(self.cartella / "non-c-e.toml"), "serve"],
                                  input="", capture_output=True, encoding="utf-8", timeout=60)
        self.assertEqual(processo.returncode, 2)
        self.assertEqual(processo.stdout, "")  # l'uscita è del protocollo: l'errore va altrove
        self.assertIn("ERRORE", processo.stderr)


# Il guardiano: in un processo nuovo, ogni socket fa fallire; il server su stdio lavora lo stesso (anche una proposta)
# e alla fine nessun modulo di rete è stato caricato.
GUARDIANO = r"""
import json, socket, sys
def trappola(*a, **k):
    raise SystemExit("GUARDIANO: il server su stdio ha aperto un socket")
socket.socket = trappola
socket.create_connection = trappola
socket.create_server = trappola
sys.path.insert(0, sys.argv[1])
from hypomnema.cli import main
codice = main(["--config", sys.argv[2], "serve"])
caricati = sorted(m for m in ("http.server", "socketserver", "http.client", "urllib.request") if m in sys.modules)
print(json.dumps({"guardiano": caricati}), file=sys.stderr)
sys.exit(codice)
"""


class TestGuardiano(ConTaccuino):
    def test_stdio_non_apre_porte(self):
        righe = [json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
                 chiamata(2, "propose", {"proposal": NOTA}), chiamata(3, "recap"), chiamata(4, "search", {"word": "orto"})]
        processo = subprocess.run([sys.executable, "-c", GUARDIANO, str(RADICE), str(self.config)],
                                  input="\n".join(righe) + "\n", capture_output=True, encoding="utf-8", timeout=60)
        self.assertEqual(processo.returncode, 0, processo.stderr)
        self.assertIn('{"guardiano": []}', processo.stderr)
        self.assertEqual(len(processo.stdout.splitlines()), 4)
        self.assertIn("ACCETTATA", processo.stdout)

    def test_il_trasporto_stdio_non_importa_la_rete(self):
        testo = (RADICE / "hypomnema" / "mcp_stdio.py").read_text(encoding="utf-8")
        testo += (RADICE / "hypomnema" / "servizio.py").read_text(encoding="utf-8")
        for modulo in ("socket", "http", "urllib", "socketserver"):
            self.assertNotIn(f"import {modulo}", testo)
            self.assertNotIn(f"from {modulo}", testo)


class TestDueScrittoriSulloStessoPC(ConTaccuino):
    """Code e l'app desktop sullo stesso PC: due server, lo stesso quaderno, il blocco dello sportello li mette in fila."""

    def test_due_server_propongono_insieme(self):
        quante = 10

        def server(chi: str, risultati: list):
            righe = [chiamata(n, "propose", {"proposal": dict(NOTA, text=f"Nota {chi} numero {n}.")})
                     for n in range(quante)]
            processo = subprocess.run([sys.executable, str(RADICE / "programma.py"), "--config", str(self.config),
                                       "serve"], input="\n".join(righe) + "\n", capture_output=True,
                                      encoding="utf-8", timeout=120)
            risultati.append(processo)

        risultati: list = []
        fili = [threading.Thread(target=server, args=(chi, risultati)) for chi in ("Code", "app")]
        for filo in fili:
            filo.start()
        for filo in fili:
            filo.join()
        for processo in risultati:
            self.assertEqual(processo.returncode, 0, processo.stderr)
            self.assertEqual(processo.stdout.count("ACCETTATA: la nota"), quante)
        note = sorted(p.name for p in (self.cartella / "quaderno" / "note").iterdir())
        self.assertEqual(note, [f"{n:04d}.md" for n in range(1, 2 * quante + 1)])
        self.assertTrue(self.comando("check").startswith(f"Quaderno in ordine: {2 * quante} note"))


class TestTrasportoInMemoria(ConTaccuino):
    def test_righe_vuote_e_solo_risposte(self):
        uscita = io.StringIO()
        mcp_stdio.servi(self.taccuino, ["\n", json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                                        json.dumps({"jsonrpc": "2.0", "id": 7, "method": "ping"})], uscita)
        self.assertEqual(uscita.getvalue(), '{"jsonrpc": "2.0", "id": 7, "result": {}}\n')


if __name__ == "__main__":
    unittest.main()
