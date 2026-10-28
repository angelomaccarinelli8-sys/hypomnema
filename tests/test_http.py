"""Test della 0.11.0, prima parte: il trasporto HTTP del server MCP (solo 127.0.0.1, una chiave per taccuino, la
chiave mai scritta, indirizzi sconosciuti 404, mai il taccuino della configurazione di base). Solo quaderni
inventati."""

import http.client
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from hypomnema import avvio, mcp_http
from tests.esecutore import RADICE

CHIAVE_A = "A" * 20 + "-chiave_di_prova-uno-0123456789"
CHIAVE_B = "B" * 20 + "-chiave_di_prova-due-0123456789"
NOTA = {"date": "2026-01-15", "source": "chat di prova", "author": "user", "knowledge": "stated", "kind": "fact",
        "text": "Il pozzo è dietro la casa."}
SCONOSCIUTI = ("/", "/mcp", "/.well-known/oauth-protected-resource", "/.well-known/oauth-authorization-server",
               f"/.well-known/oauth-protected-resource/{CHIAVE_A}/mcp", "/authorize", "/register", "/token",
               f"/{CHIAVE_A}", f"/{CHIAVE_A}/mcp/altro", f"/{CHIAVE_A[:-1]}/mcp", f"/{CHIAVE_A}x/mcp",
               "/favicon.ico")


def taccuino(cartella: Path) -> Path:
    cartella.mkdir(parents=True)
    config = cartella / "hypomnema-chat.toml"
    shutil.copy(RADICE / "chat" / "hypomnema-chat.toml", config)
    return config


def file_taccuini(cartella: Path, voci: list[tuple[str, str, str]], porta: int = 8765) -> Path:
    righe = [f"porta = {porta}", ""]
    for nome, config, chiave in voci:
        righe += ["[[taccuino]]", f'nome = "{nome}"', f'config = "{Path(config).as_posix()}"', f'chiave = "{chiave}"', ""]
    file = cartella / "server-http.toml"
    file.write_text("\n".join(righe), encoding="utf-8")
    return file


def porta_libera() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class ConCartella(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cartella = Path(self._tmp.name)
        # La casa finta: la configurazione di base è <tmp>/casa/Hypomnema/hypomnema.toml.
        self.casa = self.cartella / "casa"
        patch = mock.patch.object(avvio, "configurazione_di_base",
                                  return_value=self.casa / "Hypomnema" / "hypomnema.toml")
        patch.start()
        self.addCleanup(patch.stop)
        self.config_a = taccuino(self.casa / "Hypomnema-Secondo")
        self.config_b = taccuino(self.cartella / "terzo")

    def tearDown(self):
        self._tmp.cleanup()


class TestFileDeiTaccuini(ConCartella):
    def errore(self, voci, porta=8765) -> str:
        with self.assertRaises(mcp_http.ErroreTaccuini) as preso:
            mcp_http.leggi_taccuini(file_taccuini(self.cartella, voci, porta))
        return str(preso.exception)

    def test_file_buono(self):
        porta, coppie = mcp_http.leggi_taccuini(file_taccuini(self.cartella, [("secondo", self.config_a, CHIAVE_A),
                                                                              ("terzo", self.config_b, CHIAVE_B)]))
        self.assertEqual(porta, 8765)
        self.assertEqual([t.nome for _, t in coppie], ["secondo", "terzo"])

    def test_mai_il_taccuino_di_base(self):
        """La cartella Hypomnema-Secondo accanto a Hypomnema passa; Hypomnema no, con qualunque configurazione."""
        base = taccuino(self.casa / "Hypomnema")
        messaggio = self.errore([("mio", base, CHIAVE_A)])
        self.assertIn("non la serve mai", messaggio)
        # Anche la configurazione della chat accanto a quella di base, o un quaderno dentro ~/Hypomnema scelto da
        # una configurazione che sta altrove.
        chat = base.parent / "hypomnema.toml"
        shutil.copy(base, chat)
        self.assertIn("non la serve mai", self.errore([("mio", chat, CHIAVE_A)]))
        fuori = self.cartella / "fuori"
        fuori.mkdir()
        testo = base.read_text(encoding="utf-8").replace('cartella = "quaderno"',
                                                         f'cartella = "{(base.parent / "quaderno").as_posix()}"', 1)
        (fuori / "hypomnema.toml").write_text(testo, encoding="utf-8")
        self.assertIn("non la serve mai", self.errore([("mio", fuori / "hypomnema.toml", CHIAVE_A)]))

    def test_chiavi_sbagliate_e_mai_scritte(self):
        for chiave in ("corta", CHIAVE_A[:-2] + "é!", ""):
            with self.subTest(chiave=chiave):
                messaggio = self.errore([("secondo", self.config_a, chiave)])
                self.assertIn("la chiave del taccuino «secondo» non va", messaggio)
                if chiave:
                    self.assertNotIn(chiave, messaggio)
        doppia = self.errore([("secondo", self.config_a, CHIAVE_A), ("terzo", self.config_b, CHIAVE_A)])
        self.assertIn("stessa chiave", doppia)
        self.assertNotIn(CHIAVE_A, doppia)

    def test_file_scritto_male_senza_dettagli(self):
        file = self.cartella / "server-http.toml"
        file.write_text(f'porta = 8765\nchiave = "{CHIAVE_A}\n', encoding="utf-8")
        with self.assertRaises(mcp_http.ErroreTaccuini) as preso:
            mcp_http.leggi_taccuini(file)
        self.assertNotIn(CHIAVE_A, str(preso.exception))

    def test_porta_e_voci(self):
        self.assertIn("porta", self.errore([("secondo", self.config_a, CHIAVE_A)], porta=80))
        self.assertIn("config", self.errore([("secondo", "", CHIAVE_A)]))
        self.assertIn("non trovo il file di configurazione",
                      self.errore([("secondo", self.cartella / "non-c-e.toml", CHIAVE_A)]))
        file = self.cartella / "vuoto.toml"
        file.write_text("porta = 8765\n", encoding="utf-8")
        with self.assertRaises(mcp_http.ErroreTaccuini):
            mcp_http.leggi_taccuini(file)


class ConServer(ConCartella):
    def setUp(self):
        super().setUp()
        file = file_taccuini(self.cartella, [("secondo", self.config_a, CHIAVE_A), ("terzo", self.config_b, CHIAVE_B)])
        self.server = mcp_http.crea_server(file, porta=0)
        self.porta = self.server.server_address[1]
        self.filo = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.filo.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        super().tearDown()

    def richiesta(self, metodo: str, percorso: str, corpo=None, intestazioni=None):
        connessione = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=30)
        dati = None if corpo is None else (corpo if isinstance(corpo, bytes) else json.dumps(corpo).encode("utf-8"))
        connessione.request(metodo, percorso, body=dati, headers={"Content-Type": "application/json",
                                                                 **(intestazioni or {})})
        risposta = connessione.getresponse()
        risultato = risposta.status, dict(risposta.getheaders()), risposta.read()
        connessione.close()
        return risultato

    def mcp(self, chiave: str, numero: int, metodo: str, parametri=None):
        stato, _, corpo = self.richiesta("POST", f"/{chiave}/mcp", {"jsonrpc": "2.0", "id": numero, "method": metodo,
                                                                    "params": parametri or {}})
        self.assertEqual(stato, 200)
        return json.loads(corpo)["result"]


class TestServerHTTP(ConServer):
    def test_solo_127_0_0_1(self):
        self.assertEqual(mcp_http.INDIRIZZO, "127.0.0.1")
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_giro_completo(self):
        stato, intestazioni, corpo = self.richiesta(
            "POST", f"/{CHIAVE_A}/mcp", {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                         "params": {"protocolVersion": "2025-06-18"}})
        self.assertEqual(stato, 200)
        self.assertTrue(intestazioni["Content-Type"].startswith("application/json"))
        self.assertEqual(len(intestazioni["Mcp-Session-Id"]), 32)
        self.assertEqual(json.loads(corpo)["result"]["serverInfo"]["name"], "hypomnema")
        stato, _, corpo = self.richiesta("POST", f"/{CHIAVE_A}/mcp",
                                         {"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.assertEqual((stato, corpo), (202, b""))
        self.assertEqual(len(self.mcp(CHIAVE_A, 2, "tools/list")["tools"]), 10)
        self.assertIn("Dove eravamo rimasti", self.mcp(CHIAVE_A, 3, "tools/call", {"name": "recap"})["content"][0]["text"])
        proposta = self.mcp(CHIAVE_A, 4, "tools/call", {"name": "propose", "arguments": {"proposal": NOTA}})
        self.assertIn("ACCETTATA: la nota 0001", proposta["content"][0]["text"])
        self.assertIn("Quaderno in ordine", proposta["content"][0]["text"])
        rifiutata = self.mcp(CHIAVE_A, 5, "tools/call",
                             {"name": "propose", "arguments": {"proposal": dict(NOTA, author="claude", kind="decision")}})
        self.assertIn("RIFIUTATA", rifiutata["content"][0]["text"])
        trovata = self.mcp(CHIAVE_A, 6, "tools/call", {"name": "search", "arguments": {"word": "pozzo"}})
        self.assertIn("Trovata 1 nota", trovata["content"][0]["text"])

    def test_ogni_chiave_il_suo_taccuino(self):
        self.mcp(CHIAVE_A, 1, "tools/call", {"name": "propose", "arguments": {"proposal": NOTA}})
        self.assertTrue((self.config_a.parent / "quaderno" / "note" / "0001.md").is_file())
        self.assertFalse((self.config_b.parent / "quaderno" / "note").exists())
        vuota = self.mcp(CHIAVE_B, 2, "tools/call", {"name": "search", "arguments": {"word": "pozzo"}})
        self.assertIn("Nessuna nota", vuota["content"][0]["text"])

    def test_indirizzi_sconosciuti_404_senza_corpo(self):
        for percorso in SCONOSCIUTI:
            for metodo in ("GET", "POST", "HEAD", "OPTIONS", "DELETE"):
                with self.subTest(percorso=percorso, metodo=metodo):
                    stato, _, corpo = self.richiesta(metodo, percorso, {} if metodo == "POST" else None)
                    self.assertEqual((stato, corpo), (404, b""))

    def test_con_la_chiave_solo_post(self):
        for metodo in ("GET", "DELETE", "PUT", "OPTIONS"):
            with self.subTest(metodo=metodo):
                stato, intestazioni, corpo = self.richiesta(metodo, f"/{CHIAVE_A}/mcp")
                self.assertEqual((stato, intestazioni["Allow"], corpo), (405, "POST", b""))

    def test_richiesta_troppo_grande(self):
        stato, _, _ = self.richiesta("POST", f"/{CHIAVE_A}/mcp", b"x",
                                     {"Content-Length": str(mcp_http.LIMITE_RICHIESTA + 1)})
        self.assertEqual(stato, 413)

    def test_json_sbagliato(self):
        stato, _, corpo = self.richiesta("POST", f"/{CHIAVE_A}/mcp", b"{non json")
        self.assertEqual(stato, 200)
        self.assertEqual(json.loads(corpo)["error"]["code"], -32700)

    def test_niente_righe_per_richiesta(self):
        scritto_err, scritto_out = io.StringIO(), io.StringIO()
        with redirect_stderr(scritto_err), redirect_stdout(scritto_out):
            self.mcp(CHIAVE_A, 1, "tools/call", {"name": "check"})
            self.richiesta("GET", f"/{CHIAVE_A}/mcp")
            self.richiesta("POST", f"/{CHIAVE_B}x/mcp", {})
        self.assertEqual((scritto_err.getvalue(), scritto_out.getvalue()), ("", ""))


class TestChiaveNellIntestazione(ConServer):
    """I0285: la chiave anche nell'intestazione X-Hypomnema-Key, con l'indirizzo /mcp che da solo non apre niente."""

    def con_intestazione(self, percorso: str, chiave, metodo: str = "POST"):
        corpo = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"} if metodo == "POST" else None
        intestazioni = {} if chiave is None else {mcp_http.INTESTAZIONE_CHIAVE: chiave}
        return self.richiesta(metodo, percorso, corpo, intestazioni)

    def test_intestazione_apre_il_suo_taccuino(self):
        stato, _, corpo = self.con_intestazione("/mcp", CHIAVE_B)
        self.assertEqual(stato, 200)
        self.assertEqual(len(json.loads(corpo)["result"]["tools"]), 10)
        proposta = {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "propose", "arguments": {"proposal": NOTA}}}
        stato, _, _ = self.richiesta("POST", "/mcp", proposta, {"x-hypomnema-key": CHIAVE_B})  # maiuscole indifferenti
        self.assertEqual(stato, 200)
        self.assertTrue((self.config_b.parent / "quaderno" / "note" / "0001.md").is_file())
        self.assertFalse((self.config_a.parent / "quaderno" / "note").exists())

    def test_senza_chiave_giusta_404(self):
        for chiave in (None, "", CHIAVE_A[:-1], CHIAVE_A + "x", "sbagliata"):
            with self.subTest(chiave=chiave):
                self.assertEqual(self.con_intestazione("/mcp", chiave)[0::2], (404, b""))
        # L'intestazione non apre indirizzi diversi da /mcp.
        for percorso in ("/", "/mcp/", "/altro/mcp", "/.well-known/oauth-protected-resource"):
            with self.subTest(percorso=percorso):
                self.assertEqual(self.con_intestazione(percorso, CHIAVE_A)[0::2], (404, b""))

    def test_indirizzo_e_intestazione_devono_coincidere(self):
        self.assertEqual(self.con_intestazione(f"/{CHIAVE_A}/mcp", CHIAVE_A)[0], 200)
        self.assertEqual(self.con_intestazione(f"/{CHIAVE_A}/mcp", CHIAVE_B)[0::2], (404, b""))

    def test_due_intestazioni_404(self):
        connessione = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=30)
        connessione.putrequest("POST", "/mcp")
        connessione.putheader(mcp_http.INTESTAZIONE_CHIAVE, CHIAVE_A)
        connessione.putheader(mcp_http.INTESTAZIONE_CHIAVE, CHIAVE_B)
        connessione.putheader("Content-Length", "2")
        connessione.endheaders(b"{}")
        risposta = connessione.getresponse()
        self.assertEqual((risposta.status, risposta.read()), (404, b""))
        connessione.close()

    def test_con_intestazione_solo_post(self):
        stato, intestazioni, _ = self.con_intestazione("/mcp", CHIAVE_A, "GET")
        self.assertEqual((stato, intestazioni["Allow"]), (405, "POST"))

    def test_niente_righe_neanche_con_intestazione(self):
        scritto_err, scritto_out = io.StringIO(), io.StringIO()
        with redirect_stderr(scritto_err), redirect_stdout(scritto_out):
            self.con_intestazione("/mcp", CHIAVE_A)
            self.con_intestazione("/mcp", CHIAVE_A + "x")
        self.assertEqual((scritto_err.getvalue(), scritto_out.getvalue()), ("", ""))


class TestLaChiaveNonSiScriveMai(ConCartella):
    """Un processo vero, con le sue uscite: richieste buone, sbagliate e malformate; la chiave non compare mai."""

    def test_processo_vero(self):
        porta = porta_libera()
        file = file_taccuini(self.cartella, [("secondo", self.config_a, CHIAVE_A)], porta)
        codice = ("import sys; from unittest import mock; sys.path.insert(0, sys.argv[1]); "
                  "from hypomnema import avvio; from pathlib import Path; "
                  "mock.patch.object(avvio, 'configurazione_di_base', return_value=Path(sys.argv[3])).start(); "
                  "from hypomnema.cli import main; sys.exit(main(['serve', '--http', sys.argv[2]]))")
        processo = subprocess.Popen(
            [sys.executable, "-c", codice, str(RADICE), str(file), str(self.casa / "Hypomnema" / "hypomnema.toml")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={**os.environ, "PYTHONUNBUFFERED": "1"})
        try:
            prima = processo.stdout.readline().decode("utf-8")
            self.assertIn(f"in ascolto su http://127.0.0.1:{porta}", prima)
            richieste = [
                ("POST", f"/{CHIAVE_A}/mcp", json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                                         "params": {"name": "propose",
                                                                    "arguments": {"proposal": NOTA}}}).encode()),
                ("POST", f"/{CHIAVE_A}/mcp", b"{non json"),
                ("GET", f"/{CHIAVE_A}/mcp", None),
                ("GET", f"/.well-known/oauth-protected-resource/{CHIAVE_A}/mcp", None),
                ("POST", f"/{CHIAVE_A}x/mcp", b"{}"),
            ]
            for metodo, percorso, corpo in richieste:
                connessione = http.client.HTTPConnection("127.0.0.1", porta, timeout=30)
                connessione.request(metodo, percorso, body=corpo)
                connessione.getresponse().read()
                connessione.close()
            # Una richiesta malformata, a mano: http.server la rifiuta da solo (400).
            with socket.create_connection(("127.0.0.1", porta), timeout=30) as grezza:
                grezza.sendall(f"BOH /{CHIAVE_A}/mcp HTTP/9.9 altro\r\n\r\n".encode())
                grezza.recv(4096)
        finally:
            processo.terminate()
            uscita, errori = processo.communicate(timeout=30)
        tutto = prima + uscita.decode("utf-8", errors="replace") + errori.decode("utf-8", errors="replace")
        self.assertNotIn(CHIAVE_A, tutto)
        self.assertNotIn(CHIAVE_A[:16], tutto)
        self.assertTrue((self.config_a.parent / "quaderno" / "note" / "0001.md").is_file())

    def test_avvio_rifiutato_non_scrive_la_chiave(self):
        base = taccuino(self.casa / "Hypomnema")
        file = file_taccuini(self.cartella, [("mio", base, CHIAVE_A)])
        uscita, errori = io.StringIO(), io.StringIO()
        self.assertEqual(mcp_http.avvia(file, uscita, errori), 2)
        self.assertIn("non la serve mai", errori.getvalue())
        self.assertNotIn(CHIAVE_A, uscita.getvalue() + errori.getvalue())


if __name__ == "__main__":
    unittest.main()
