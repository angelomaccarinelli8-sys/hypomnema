"""Il trasporto HTTP del server MCP (dalla 0.11.0): «streamable HTTP» in risposta JSON semplice, con la sola
libreria standard, sullo stesso cuore del trasporto stdio (``servizio``).

Regole fisse (non sono impostazioni):
- ascolta **solo su 127.0.0.1**: dall'esterno lo raggiunge soltanto il tunnel che l'utente accende sul suo PC;
- **una chiave per taccuino**, nell'indirizzo (``/<chiave>/mcp``) oppure, dalla 0.11.0 seconda parte (I0285),
  nell'intestazione ``X-Hypomnema-Key: <chiave>`` con l'indirizzo ``/mcp``: così l'indirizzo da solo non apre
  niente. Se ci sono tutte e due, devono essere la stessa chiave. Ogni altro indirizzo (anche quelli che un client
  prova per cercare un login, come ``/.well-known/oauth-protected-resource``) risponde 404 subito, senza corpo;
- **la chiave non si scrive mai**: niente righe per richiesta (``log_message`` spento), niente percorsi nei
  messaggi, errori interni senza dettagli;
- **mai il taccuino della configurazione di base** (``~/Hypomnema``): se il file dei taccuini lo nomina, il server
  non parte.

Il file dei taccuini lo scrive l'utente, fuori dal repository::

    porta = 8765

    [[taccuino]]
    nome = "secondo"
    config = "C:/Users/nome/Hypomnema-Secondo/hypomnema-chat.toml"
    chiave = "…almeno 32 caratteri: lettere, cifre, - e _…"
"""

from __future__ import annotations

import hmac
import json
import re
import sys
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TextIO

from hypomnema import avvio, configurazione, servizio
from hypomnema.configurazione import tomllib

INDIRIZZO = "127.0.0.1"
LUNGHEZZA_MINIMA_CHIAVE = 32
CHIAVE_VALIDA = re.compile(r"[A-Za-z0-9_-]+")
# L'intestazione con la chiave (I0285): nel modulo del connettore di claude.ai, «Intestazioni della richiesta».
INTESTAZIONE_CHIAVE = "X-Hypomnema-Key"
# Una richiesta più grande è rifiutata (413): una proposta o una copia dell'archivio stanno molto sotto.
LIMITE_RICHIESTA = 4 * 1024 * 1024
ATTESA_SECONDI = 30


class ErroreTaccuini(Exception):
    """Il file dei taccuini non va. Il messaggio non contiene mai una chiave."""


def leggi_taccuini(file: Path) -> tuple[int, list[tuple[str, servizio.Taccuino]]]:
    """La porta e le coppie (chiave, taccuino) del file, controllate. Errore se un taccuino è quello di base."""
    try:
        dati = tomllib.loads(file.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise ErroreTaccuini(f"non trovo il file dei taccuini «{file}».")
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        # Senza dettagli: il messaggio di errore potrebbe citare un pezzo del file, cioè una chiave.
        raise ErroreTaccuini(f"il file dei taccuini «{file}» non è scritto correttamente (TOML in UTF-8).")
    porta = dati.get("porta")
    if not isinstance(porta, int) or isinstance(porta, bool) or not 1024 <= porta <= 65535:
        raise ErroreTaccuini("nel file dei taccuini serve «porta = …», un numero da 1024 a 65535 (per esempio 8765).")
    elenco = dati.get("taccuino")
    if not isinstance(elenco, list) or not elenco:
        raise ErroreTaccuini("nel file dei taccuini serve almeno un [[taccuino]] con nome, config e chiave.")
    base = avvio.configurazione_di_base().parent
    coppie: list[tuple[str, servizio.Taccuino]] = []
    for posto, voce in enumerate(elenco, start=1):
        nome = voce.get("nome") if isinstance(voce, dict) else None
        if not isinstance(nome, str) or not nome.strip():
            raise ErroreTaccuini(f"il taccuino n. {posto} non ha un «nome».")
        chiave, config = voce.get("chiave"), voce.get("config")
        if not isinstance(config, str) or not config:
            raise ErroreTaccuini(f"il taccuino «{nome}» non ha «config», il percorso della sua configurazione.")
        if (not isinstance(chiave, str) or len(chiave) < LUNGHEZZA_MINIMA_CHIAVE
                or not CHIAVE_VALIDA.fullmatch(chiave)):
            raise ErroreTaccuini(
                f"la chiave del taccuino «{nome}» non va: servono almeno {LUNGHEZZA_MINIMA_CHIAVE} caratteri, solo "
                "lettere, cifre, - e _. Creala con:  py -c \"import secrets; print(secrets.token_urlsafe(32))\"")
        if any(hmac.compare_digest(chiave, altra) for altra, _ in coppie):
            raise ErroreTaccuini(f"il taccuino «{nome}» ha la stessa chiave di un altro: ogni taccuino ha la sua.")
        percorso = Path(config)
        if not percorso.is_absolute():
            percorso = file.parent / percorso
        try:
            taccuino = servizio.Taccuino(nome, percorso)
        except configurazione.ErroreConfigurazione as errore:
            raise ErroreTaccuini(f"taccuino «{nome}»: {errore}")
        if avvio._dentro(taccuino.cartella_quaderno.resolve(), base.resolve()) or avvio._dentro(taccuino.config, base):
            raise ErroreTaccuini(
                f"il taccuino «{nome}» è nella cartella {base}, quella della configurazione di base: il server HTTP "
                "non la serve mai. Toglilo dal file dei taccuini.")
        coppie.append((chiave, taccuino))
    return porta, coppie


class ServerHTTP(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, porta: int, coppie: list[tuple[str, servizio.Taccuino]]):
        self.coppie = coppie
        super().__init__((INDIRIZZO, porta), Gestore)

    def handle_error(self, request, client_address) -> None:
        # Mai il dettaglio: potrebbe contenere l'indirizzo chiesto, cioè la chiave.
        print("Hypomnema: errore interno durante una richiesta (dettagli non scritti).", file=sys.stderr)


class Gestore(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "hypomnema"
    sys_version = ""
    timeout = ATTESA_SECONDI

    def log_message(self, format, *args) -> None:  # noqa: A002 - il nome è quello di http.server
        """Spento: la riga di ogni richiesta conterrebbe l'indirizzo, cioè la chiave."""

    def _taccuino(self) -> servizio.Taccuino | None:
        parti = self.path.split("?", 1)[0].split("/")
        intestazione = self.headers.get_all(INTESTAZIONE_CHIAVE) or []
        if len(intestazione) > 1:
            return None
        if parti == ["", "mcp"] and intestazione:
            cercata = intestazione[0].strip()
        elif len(parti) == 3 and parti[0] == "" and parti[2] == "mcp":
            cercata = parti[1]
            # Chiave nell'indirizzo e nell'intestazione: valgono solo se sono la stessa.
            if intestazione and not hmac.compare_digest(intestazione[0].strip().encode("utf-8"),
                                                        cercata.encode("utf-8")):
                return None
        else:
            return None
        trovato = None
        for chiave, taccuino in self.server.coppie:
            # Tutte le chiavi, sempre: il tempo della risposta non dice niente su quale chiave quasi va.
            if hmac.compare_digest(cercata.encode("utf-8"), chiave.encode("utf-8")):
                trovato = taccuino
        return trovato

    def _rispondi(self, codice: int, corpo: bytes = b"", intestazioni: dict | None = None) -> None:
        self.send_response(codice)
        for nome, valore in (intestazioni or {}).items():
            self.send_header(nome, valore)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if corpo and self.command != "HEAD":
            self.wfile.write(corpo)

    def do_POST(self) -> None:  # noqa: N802 - il nome è quello di http.server
        taccuino = self._taccuino()
        if taccuino is None:
            self.close_connection = True
            return self._rispondi(404)
        try:
            lunghezza = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.close_connection = True
            return self._rispondi(411)
        if lunghezza < 0 or lunghezza > LIMITE_RICHIESTA:
            self.close_connection = True
            return self._rispondi(413)
        testo = self.rfile.read(lunghezza).decode("utf-8", errors="replace")
        try:
            risposta = servizio.rispondi_al_testo(taccuino, testo)
        except Exception:  # noqa: BLE001 - un errore del programma non deve dire niente fuori
            print("Hypomnema: errore interno durante una richiesta (dettagli non scritti).", file=sys.stderr)
            return self._rispondi(500)
        if risposta is None:
            return self._rispondi(202)  # una notifica: accettata, niente da rispondere
        intestazioni = {"Content-Type": "application/json; charset=utf-8"}
        if "result" in risposta and isinstance(risposta["result"], dict) and "serverInfo" in risposta["result"]:
            intestazioni["Mcp-Session-Id"] = uuid.uuid4().hex
        corpo = json.dumps(risposta, ensure_ascii=False).encode("utf-8")
        return self._rispondi(200, corpo, intestazioni)

    def _non_permesso(self) -> None:
        if self._taccuino() is None:
            self.close_connection = True
            return self._rispondi(404)
        # Lo streaming (GET) e la chiusura della sessione (DELETE) non servono: si risponde solo con POST.
        return self._rispondi(405, intestazioni={"Allow": "POST"})

    do_GET = do_DELETE = do_PUT = do_PATCH = do_HEAD = do_OPTIONS = _non_permesso  # noqa: N815


def crea_server(file: Path, porta: int | None = None) -> ServerHTTP:
    """Il server pronto, non ancora avviato (``porta`` serve alle prove: 0 = una porta libera qualsiasi)."""
    porta_del_file, coppie = leggi_taccuini(file)
    return ServerHTTP(porta_del_file if porta is None else porta, coppie)


def avvia(file: Path, uscita: TextIO, errori: TextIO) -> int:
    try:
        server = crea_server(file)
    except ErroreTaccuini as errore:
        print(f"ERRORE: {errore}", file=errori)
        return 2
    except OSError as errore:
        print(f"ERRORE: non posso ascoltare su {INDIRIZZO}: {errore.strerror or errore}. La porta è già usata?",
              file=errori)
        return 2
    porta = server.server_address[1]
    print(f"Server di Hypomnema in ascolto su http://{INDIRIZZO}:{porta} (solo questo computer).", file=uscita)
    for _, taccuino in server.coppie:
        print(f"Taccuino servito: {taccuino.nome} ({taccuino.cartella_quaderno}).", file=uscita)
    print(f"Il tunnel punta a http://{INDIRIZZO}:{porta}; l'indirizzo da dare a Claude è "
          "https://<indirizzo del tunnel>/<chiave>/mcp, oppure https://<indirizzo del tunnel>/mcp con la chiave "
          f"nell'intestazione {INTESTAZIONE_CHIAVE} (la chiave è nel file dei taccuini: qui non si scrive).",
          file=uscita)
    print("Per fermarlo: Ctrl+C.", file=uscita)
    uscita.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server fermato.", file=uscita)
    finally:
        server.server_close()
    return 0
