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


def file_taccuini(cartella: Path, voci: list[tuple[str, str, str]], porta: int = 8765, altre: tuple = ()) -> Path:
    """Una voce con la chiave che comincia con «impronta:» scrive l'impronta al posto della chiave."""
    righe = [f"porta = {porta}", *altre, ""]
    for nome, config, chiave in voci:
        riga = (f'impronta = "{chiave[len("impronta:"):]}"' if chiave.startswith("impronta:")
                else f'chiave = "{chiave}"')
        righe += ["[[taccuino]]", f'nome = "{nome}"', f'config = "{Path(config).as_posix()}"', riga, ""]
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
    """I0285: la chiave anche nell'intestazione x-api-key, con l'indirizzo /mcp che da solo non apre niente."""

    def test_nome_della_lista_di_serie_di_claude(self):
        # Un nome fuori dalla lista di serie di claude.ai andrebbe fatto approvare ad Anthropic.
        self.assertEqual(mcp_http.INTESTAZIONE_CHIAVE, "x-api-key")

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
        stato, _, _ = self.richiesta("POST", "/mcp", proposta, {"X-API-KEY": CHIAVE_B})  # maiuscole indifferenti
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


class TestImpronte(ConCartella):
    """Seconda parte: nel file dei taccuini l'impronta SHA-256 al posto della chiave; la chiave apre lo stesso."""

    def test_impronta_come_get_filehash(self):
        # Il valore di Get-FileHash -Algorithm SHA256 di PowerShell, in minuscolo, su un file con «abc» senza a capo.
        self.assertEqual(mcp_http.impronta("abc"),
                         "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_impronta_apre_il_taccuino(self):
        file = file_taccuini(self.cartella, [("secondo", self.config_a, "impronta:" + mcp_http.impronta(CHIAVE_A)),
                                             ("terzo", self.config_b, CHIAVE_B)])
        server = mcp_http.crea_server(file, porta=0)
        self.addCleanup(server.server_close)
        filo = threading.Thread(target=server.serve_forever, daemon=True)
        filo.start()
        self.addCleanup(server.shutdown)
        porta = server.server_address[1]
        for percorso, intestazioni, atteso in ((f"/{CHIAVE_A}/mcp", {}, 200), ("/mcp", {"x-api-key": CHIAVE_A}, 200),
                                               ("/mcp", {"x-api-key": mcp_http.impronta(CHIAVE_A)}, 404),
                                               (f"/{mcp_http.impronta(CHIAVE_A)}/mcp", {}, 404),
                                               ("/mcp", {"x-api-key": CHIAVE_B}, 200)):
            with self.subTest(percorso=percorso, intestazioni=intestazioni):
                connessione = http.client.HTTPConnection("127.0.0.1", porta, timeout=30)
                connessione.request("POST", percorso, body=b'{"jsonrpc":"2.0","id":1,"method":"ping"}',
                                    headers=intestazioni)
                self.assertEqual(connessione.getresponse().status, atteso)
                connessione.close()

    def test_impronte_sbagliate(self):
        for segno in ("abc", mcp_http.impronta(CHIAVE_A).upper(), mcp_http.impronta(CHIAVE_A) + "0"):
            with self.subTest(segno=segno):
                with self.assertRaises(mcp_http.ErroreTaccuini) as preso:
                    mcp_http.leggi_taccuini(file_taccuini(self.cartella, [("secondo", self.config_a,
                                                                           "impronta:" + segno)]))
                self.assertIn("l'impronta del taccuino «secondo» non va", str(preso.exception))
        # La stessa chiave scritta una volta in chiaro e una come impronta.
        with self.assertRaises(mcp_http.ErroreTaccuini) as preso:
            mcp_http.leggi_taccuini(file_taccuini(self.cartella, [
                ("secondo", self.config_a, CHIAVE_A), ("terzo", self.config_b, "impronta:" + mcp_http.impronta(CHIAVE_A))]))
        self.assertIn("stessa chiave", str(preso.exception))
        file = self.cartella / "doppia.toml"
        file.write_text(f'porta = 8765\n[[taccuino]]\nnome = "a"\nconfig = "{self.config_a.as_posix()}"\n'
                        f'chiave = "{CHIAVE_A}"\nimpronta = "{mcp_http.impronta(CHIAVE_A)}"\n', encoding="utf-8")
        with self.assertRaises(mcp_http.ErroreTaccuini) as preso:
            mcp_http.leggi_taccuini(file)
        self.assertIn("sia «chiave» sia «impronta»", str(preso.exception))
        self.assertNotIn(CHIAVE_A, str(preso.exception))

    def test_nomi_doppi(self):
        with self.assertRaises(mcp_http.ErroreTaccuini) as preso:
            mcp_http.leggi_taccuini(file_taccuini(self.cartella, [("uno", self.config_a, CHIAVE_A),
                                                                  ("uno", self.config_b, CHIAVE_B)]))
        self.assertIn("due taccuini si chiamano «uno»", str(preso.exception))


class TestLimiti(ConCartella):
    """Seconda parte: richieste e proposte al minuto, per taccuino, scritte nel file dei taccuini."""

    def test_limiti_del_file(self):
        file = file_taccuini(self.cartella, [("secondo", self.config_a, CHIAVE_A)])
        self.assertEqual(mcp_http.leggi_limiti(file), (30, 10))
        file = file_taccuini(self.cartella, [("secondo", self.config_a, CHIAVE_A)],
                             altre=("richieste_al_minuto = 7", "proposte_al_minuto = 2"))
        self.assertEqual(mcp_http.leggi_limiti(file), (7, 2))
        for riga in ("richieste_al_minuto = 0", 'proposte_al_minuto = "10"', "proposte_al_minuto = true"):
            with self.subTest(riga=riga):
                with self.assertRaises(mcp_http.ErroreTaccuini):
                    mcp_http.leggi_taccuini(file_taccuini(self.cartella, [("secondo", self.config_a, CHIAVE_A)],
                                                          altre=(riga,)))

    def test_finestra_di_un_minuto(self):
        adesso = [1000.0]
        limiti = mcp_http.Limiti(3, 2, orologio=lambda: adesso[0])
        self.assertEqual([limiti.passa(True), limiti.passa(True), limiti.passa(True)], [None, None, "proposte"])
        self.assertIsNone(limiti.passa(False))  # la proposta rifiutata non conta: c'è posto per una richiesta
        self.assertEqual(limiti.passa(False), "richieste")
        adesso[0] += 59.9
        self.assertEqual(limiti.passa(False), "richieste")
        adesso[0] += 0.1  # un minuto dopo le prime due
        self.assertIsNone(limiti.passa(True))

    def test_429_con_il_messaggio_per_claude(self):
        file = file_taccuini(self.cartella, [("secondo", self.config_a, CHIAVE_A), ("terzo", self.config_b, CHIAVE_B)],
                             altre=("richieste_al_minuto = 4", "proposte_al_minuto = 2"))
        server = mcp_http.crea_server(file, porta=0)
        self.addCleanup(server.server_close)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown)

        def manda(chiave, metodo, nome=None, numero=1):
            richiesta = {"jsonrpc": "2.0", "id": numero, "method": metodo}
            if nome:
                richiesta["params"] = {"name": nome, "arguments": {"proposal": dict(NOTA, text=f"Nota {numero}.")}}
            connessione = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=30)
            connessione.request("POST", "/mcp", body=json.dumps(richiesta).encode(), headers={"x-api-key": chiave})
            risposta = connessione.getresponse()
            risultato = risposta.status, dict(risposta.getheaders()), risposta.read()
            connessione.close()
            return risultato

        self.assertEqual(manda(CHIAVE_A, "tools/call", "propose", 1)[0], 200)
        self.assertEqual(manda(CHIAVE_A, "tools/call", "propose", 2)[0], 200)
        stato, intestazioni, corpo = manda(CHIAVE_A, "tools/call", "propose", 3)
        self.assertEqual((stato, intestazioni["Retry-After"]), (429, "60"))
        risposta = json.loads(corpo)
        self.assertEqual(risposta["id"], 3)
        self.assertIn("at most 2 proposals (propose) per minute", risposta["error"]["message"])
        self.assertIn("Nothing was saved", risposta["error"]["message"])
        self.assertFalse((self.config_a.parent / "quaderno" / "note" / "0003.md").exists())
        self.assertEqual(manda(CHIAVE_A, "ping")[0], 200)
        self.assertEqual(manda(CHIAVE_A, "ping")[0], 200)
        stato, _, corpo = manda(CHIAVE_A, "ping")
        self.assertEqual(stato, 429)
        self.assertIn("at most 4 requests per minute", json.loads(corpo)["error"]["message"])
        # L'altro taccuino ha i suoi limiti.
        self.assertEqual(manda(CHIAVE_B, "tools/call", "propose", 1)[0], 200)


class TestTaccuinoNuovo(ConCartella):
    """Seconda parte: notebook-new crea il taccuino online con la sola impronta; la chiave non passa di qui."""

    def setUp(self):
        super().setUp()
        self.server = self.cartella / "server"
        self.server.mkdir()
        self.file = self.server / "taccuini.toml"
        self.file.write_text("porta = 8765\nrichieste_al_minuto = 30\nproposte_al_minuto = 10\n", encoding="utf-8")

    def lancia(self, *argomenti):
        from hypomnema.cli import main
        uscita = io.StringIO()
        codice = main(["notebook-new", "--file", str(self.file), *argomenti], uscita=uscita, errori=uscita)
        return codice, uscita.getvalue()

    def test_crea_e_il_server_lo_apre(self):
        codice, testo = self.lancia("--name", "prova", "--fingerprint", mcp_http.impronta(CHIAVE_A))
        self.assertEqual(codice, 0, testo)
        self.assertIn("Taccuino «prova» creato", testo)
        cartella = self.server / "prova"
        self.assertEqual((cartella / "hypomnema.toml").read_bytes(), mcp_http.MODELLO_ONLINE.read_bytes())
        self.assertEqual((cartella / "quaderno" / "etichette.toml").read_text(encoding="utf-8"),
                         mcp_http.ETICHETTE_VUOTE)
        scritto = self.file.read_text(encoding="utf-8")
        self.assertIn(f'[[taccuino]]\nnome = "prova"\nconfig = "prova/hypomnema.toml"\n'
                      f'impronta = "{mcp_http.impronta(CHIAVE_A)}"\n', scritto)
        self.assertNotIn(CHIAVE_A, scritto)
        # Un secondo, con i nomi italiani; poi il server apre ognuno con la sua chiave.
        codice, testo = self.lancia("--nome", "amico", "--impronta", mcp_http.impronta(CHIAVE_B).upper())
        self.assertEqual(codice, 0, testo)
        porta, coppie = mcp_http.leggi_taccuini(self.file)
        self.assertEqual([t.nome for _, t in coppie], ["prova", "amico"])
        self.assertEqual(coppie[0][0], mcp_http.impronta(CHIAVE_A))

    def test_nota_online_marcata(self):
        self.lancia("--name", "prova", "--fingerprint", mcp_http.impronta(CHIAVE_A))
        _, coppie = mcp_http.leggi_taccuini(self.file)
        from hypomnema import servizio
        testo, errore = servizio.chiama(coppie[0][1], "propose", {"proposal": NOTA})
        self.assertFalse(errore)
        self.assertIn("ACCETTATA", testo)
        nota = (self.server / "prova" / "quaderno" / "note" / "0001.md").read_text(encoding="utf-8")
        self.assertIn("- verification: author not verified (online, no witness)\n", nota)
        stato, _ = servizio.chiama(coppie[0][1], "status", {})
        self.assertIn("NON C'È (taccuino online)", stato)

    def test_rifiuti_senza_creare_niente(self):
        self.lancia("--name", "prova", "--fingerprint", mcp_http.impronta(CHIAVE_A))
        prima = self.file.read_bytes()
        for argomenti, atteso in (
                (("--name", "prova", "--fingerprint", mcp_http.impronta(CHIAVE_B)), "c'è già un taccuino"),
                (("--name", "altro", "--fingerprint", mcp_http.impronta(CHIAVE_A)), "già di un altro taccuino"),
                (("--name", "Prova!", "--fingerprint", mcp_http.impronta(CHIAVE_B)), "il nome «Prova!» non va"),
                (("--name", "../fuori", "--fingerprint", mcp_http.impronta(CHIAVE_B)), "non va"),
                (("--name", "altro", "--fingerprint", "abc"), "l'impronta non va"),
                (("--name", "altro", "--fingerprint", CHIAVE_B), "l'impronta non va")):
            with self.subTest(argomenti=argomenti):
                codice, testo = self.lancia(*argomenti)
                self.assertEqual(codice, 2)
                self.assertIn(atteso, testo)
                self.assertIn("Non ho creato niente", testo)
                self.assertNotIn(CHIAVE_B, testo)
        self.assertEqual(self.file.read_bytes(), prima)
        self.assertEqual(sorted(p.name for p in self.server.iterdir()), ["prova", "taccuini.toml"])
        (self.server / "esiste").mkdir()
        codice, testo = self.lancia("--name", "esiste", "--fingerprint", mcp_http.impronta(CHIAVE_B))
        self.assertEqual(codice, 2)
        self.assertIn("c'è già", testo)

    def test_mai_nella_cartella_di_base(self):
        base = self.casa / "Hypomnema"
        base.mkdir(parents=True)
        self.file = base / "taccuini.toml"
        self.file.write_text("porta = 8765\n", encoding="utf-8")
        codice, testo = self.lancia("--name", "prova", "--fingerprint", mcp_http.impronta(CHIAVE_A))
        self.assertEqual(codice, 2)
        self.assertIn("non la serve mai", testo)
        self.assertFalse((base / "prova").exists())


class TestEtichetteDelTaccuino(ConCartella):
    """Pezzo 4: la lista delle etichette del tester, scritta dall'utente, controllata e caricata nel taccuino online;
    mai sopra una lista con dentro qualcosa senza conferma, e la lista di prima resta accanto."""

    LISTA = 'chi = ["Anna"]\ncosa = ["orto", "bilancio"]\n\n[rami.orto]\npomodori = ["pomodori", "pomodoro"]\n'

    def setUp(self):
        super().setUp()
        self.server = self.cartella / "server"
        self.server.mkdir()
        self.file = self.server / "taccuini.toml"
        self.file.write_text("porta = 8765\n", encoding="utf-8")
        mcp_http.crea_taccuino(self.file, "prova", mcp_http.impronta(CHIAVE_A))
        self.quaderno = self.server / "prova" / "quaderno"

    def lancia(self, testo, *argomenti, ora=0):
        from datetime import datetime, timedelta, timezone
        from hypomnema.cli import main
        lista = self.cartella / "lista.toml"
        lista.write_bytes(testo.encode("utf-8"))
        uscita = io.StringIO()
        adesso = datetime(2026, 10, 29, 10, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=ora)
        codice = main(["notebook-labels", "--labels", str(lista), *argomenti], adesso=adesso, uscita=uscita,
                      errori=uscita)
        return codice, uscita.getvalue()

    def test_solo_controllo(self):
        self.assertEqual(self.lancia(self.LISTA), (0, "Etichette scritte bene: 1 CHI, 2 COSA, 1 rami con sotto-rami.\n"))
        codice, testo = self.lancia('cosa = ["orto", "orto"]\n')
        self.assertEqual(codice, 2)
        self.assertIn("è ripetuta", testo)
        self.assertNotIn("tmp", testo)
        codice, testo = self.lancia('cosa = [\n')
        self.assertEqual(codice, 2)
        self.assertIn("non è scritto correttamente", testo)
        self.assertEqual(self.lancia("chi = []\n")[0], 2)
        self.assertEqual(self.lancia(self.LISTA, "--file", str(self.file))[0], 2)  # --file senza --name

    def test_carica_sopra_la_lista_vuota_e_tiene_quella_di_prima(self):
        codice, testo = self.lancia(self.LISTA, "--file", str(self.file), "--name", "prova")
        self.assertEqual(codice, 0, testo)
        self.assertIn("Etichette caricate nel taccuino «prova»: 1 CHI, 2 COSA", testo)
        self.assertIn("etichette-fino-al-2026-10-29-100000.toml", testo)
        self.assertEqual((self.quaderno / "etichette.toml").read_text(encoding="utf-8"), self.LISTA)
        self.assertEqual((self.quaderno / "etichette-fino-al-2026-10-29-100000.toml").read_text(encoding="utf-8"),
                         mcp_http.ETICHETTE_VUOTE)
        # Lo sportello del taccuino la usa subito.
        _, coppie = mcp_http.leggi_taccuini(self.file)
        from hypomnema import servizio
        etichette, _ = servizio.chiama(coppie[0][1], "labels", {})
        self.assertIn("bilancio", etichette)

    def test_mai_sopra_una_lista_piena_senza_conferma(self):
        self.lancia(self.LISTA, "--file", str(self.file), "--name", "prova")
        altra = 'cosa = ["casa"]\n'
        codice, testo = self.lancia(altra, "--file", str(self.file), "--name", "prova", ora=5)
        self.assertEqual(codice, 2)
        self.assertIn("ha già una lista di etichette con qualcosa dentro", testo)
        self.assertIn("Non ho cambiato niente", testo)
        self.assertEqual((self.quaderno / "etichette.toml").read_text(encoding="utf-8"), self.LISTA)
        codice, testo = self.lancia(altra, "--file", str(self.file), "--name", "prova", "--sostituisci", ora=5)
        self.assertEqual(codice, 0, testo)
        self.assertEqual((self.quaderno / "etichette.toml").read_text(encoding="utf-8"), altra)
        self.assertEqual((self.quaderno / "etichette-fino-al-2026-10-29-100005.toml").read_text(encoding="utf-8"),
                         self.LISTA)
        self.assertEqual(sorted(p.name for p in self.quaderno.glob("etichette*.toml")),
                         ["etichette-fino-al-2026-10-29-100000.toml", "etichette-fino-al-2026-10-29-100005.toml",
                          "etichette.toml"])

    def test_lista_sbagliata_o_taccuino_che_non_c_e(self):
        prima = (self.quaderno / "etichette.toml").read_bytes()
        for testo, argomenti, atteso in (
                ('cosa = ["a,b"]\n', ("--name", "prova"), "virgola"),
                (self.LISTA, ("--name", "altro"), "non c'è un taccuino che si chiama «altro»"),
                (self.LISTA, ("--name", "../prova"), "non va")):
            with self.subTest(atteso=atteso):
                codice, uscita = self.lancia(testo, "--file", str(self.file), *argomenti)
                self.assertEqual(codice, 2)
                self.assertIn(atteso, uscita)
        self.assertEqual((self.quaderno / "etichette.toml").read_bytes(), prima)
        self.assertEqual(len(list(self.quaderno.glob("etichette*.toml"))), 1)

    def test_fine_riga_di_windows(self):
        codice, _ = self.lancia(self.LISTA.replace("\n", "\r\n"), "--file", str(self.file), "--name", "prova")
        self.assertEqual(codice, 0)
        self.assertEqual((self.quaderno / "etichette.toml").read_bytes(), self.LISTA.encode("utf-8"))


class TestServizioChiuso(ConCartella):
    """Il servizio chiuso: la frase onesta nella scheda solo con la riga «autore»; online lo stato senza percorsi e il
    suggerimento del tipo senza le sequenze di parole."""

    def scheda(self, *altre):
        file = file_taccuini(self.cartella, [("secondo", self.config_a, CHIAVE_A)], altre=altre)
        _, coppie = mcp_http.leggi_taccuini(file)
        from hypomnema import servizio
        risposta = servizio.rispondi(coppie[0][1], {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        return risposta["result"]["instructions"]

    def test_frase_solo_con_l_autore(self):
        from hypomnema import servizio
        self.assertEqual(self.scheda(), servizio.ISTRUZIONI)
        scheda = self.scheda('autore = "Angelo"')
        self.assertTrue(scheda.startswith(servizio.ISTRUZIONI))
        self.assertIn("This notebook is a closed service run by its author, Angelo:", scheda)
        self.assertIn("tell them they can ask\nAngelo.", scheda)
        # La frase non chiede di nascondere, negare o mentire.
        frase = scheda[len(servizio.ISTRUZIONI):].lower()
        for parola in ("hide", "deny", "lie", "secret", "reveal", "do not tell", "don't tell", "refuse", "never"):
            self.assertNotRegex(frase, rf"\b{parola}\b")

    def test_autore_scritto_male(self):
        for riga in ('autore = ""', "autore = 3", 'autore = "a\\nb"'):
            with self.subTest(riga=riga):
                with self.assertRaises(mcp_http.ErroreTaccuini) as preso:
                    mcp_http.leggi_taccuini(file_taccuini(self.cartella, [("secondo", self.config_a, CHIAVE_A)],
                                                          altre=(riga,)))
                self.assertIn("«autore»", str(preso.exception))

    def test_stato_online_senza_percorsi(self):
        server = self.cartella / "server"
        server.mkdir()
        file = server / "taccuini.toml"
        file.write_text("porta = 8765\n", encoding="utf-8")
        self.assertIsNotNone(mcp_http.crea_taccuino(file, "prova", mcp_http.impronta(CHIAVE_A)))
        _, coppie = mcp_http.leggi_taccuini(file)
        from hypomnema import servizio
        stato, _ = servizio.chiama(coppie[0][1], "status", {})
        self.assertTrue(stato.startswith("Taccuino: online (i percorsi sul server non si mostrano).\n"))
        self.assertNotIn(str(self.cartella), stato)
        self.assertNotIn("/", stato.replace("Europe/Rome", ""))
        # Anche l'errore delle etichette scritte male non dice dove sta il taccuino.
        (server / "prova" / "quaderno" / "etichette.toml").write_text("cosa = [\n", encoding="utf-8")
        stato, _ = servizio.chiama(coppie[0][1], "status", {})
        self.assertIn("Etichette: ERRORE", stato)
        self.assertNotIn(str(self.cartella), stato)
        self.assertIn("<taccuino>/quaderno", stato)

    def test_suggerimento_del_tipo(self):
        from types import SimpleNamespace
        from hypomnema.cli import _stampa_suggerimento
        esito = SimpleNamespace(integrazione=None, suggerimento=("decision", ["ho deciso di", "abbiamo deciso"], "idea"))
        a_casa, online = io.StringIO(), io.StringIO()
        _stampa_suggerimento(esito, a_casa)
        _stampa_suggerimento(esito, online, online=True)
        self.assertIn("«ho deciso di»", a_casa.getvalue())
        self.assertEqual(online.getvalue(), "SUGGERIMENTO (non cambia niente): forse è una decisione (decision). È "
                                            "giusto il tipo idea? Per cambiarlo serve updates.\n")

    def test_check_dice_cosa_fa_non_come(self):
        from hypomnema import servizio
        self.assertEqual(servizio.PER_NOME["check"].descrizione, "Check that the notebook is in order (read only). If "
                                                                "it says «ATTENZIONE», tell the user: repair nothing.")


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
