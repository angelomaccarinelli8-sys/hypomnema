"""Il trasporto HTTP del server MCP (dalla 0.11.0): «streamable HTTP» in risposta JSON semplice, con la sola
libreria standard, sullo stesso cuore del trasporto stdio (``servizio``).

Regole fisse (non sono impostazioni):
- ascolta **solo su 127.0.0.1**: dall'esterno lo raggiunge soltanto il tunnel che l'utente accende sul suo PC;
- **una chiave per taccuino**, nell'indirizzo (``/<chiave>/mcp``) oppure, dalla 0.11.0 seconda parte (I0285),
  nell'intestazione ``x-api-key: <chiave>`` con l'indirizzo ``/mcp``: così l'indirizzo da solo non apre
  niente. Se ci sono tutte e due, devono essere la stessa chiave. Ogni altro indirizzo (anche quelli che un client
  prova per cercare un login, come ``/.well-known/oauth-protected-resource``) risponde 404 subito, senza corpo;
- **la chiave non si scrive mai**: niente righe per richiesta (``log_message`` spento), niente percorsi nei
  messaggi, errori interni senza dettagli;
- **mai il taccuino della configurazione di base** (``~/Hypomnema``): se il file dei taccuini lo nomina, il server
  non parte;
- **due limiti per taccuino** (seconda parte): richieste al minuto in tutto e proposte (``propose``) al minuto.
  Oltre, 429 con un messaggio per Claude. Si contano solo le richieste accettate, nell'ultimo minuto.

Al posto della chiave il file può avere la sua **impronta** (SHA-256, 64 cifre esadecimali): è il modo del server
online, dove la chiave non arriva mai (nasce sul PC di chi crea il taccuino, vedi ``notebook-new``).

Il file dei taccuini lo scrive l'utente, fuori dal repository::

    porta = 8765
    autore = "Angelo"          # facoltativa: chi gestisce il servizio; con questa riga la scheda per Claude dice
                               # che il taccuino è un servizio chiuso e che sui dettagli interni si chiede a lui
    richieste_al_minuto = 30   # facoltativa, se manca vale 30
    proposte_al_minuto = 10    # facoltativa, se manca vale 10

    [[taccuino]]
    nome = "secondo"
    config = "C:/Users/nome/Hypomnema-Secondo/hypomnema-chat.toml"
    chiave = "…almeno 32 caratteri: lettere, cifre, - e _…"    # oppure  impronta = "…64 cifre esadecimali…"
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import sys
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime
from typing import TextIO

from hypomnema import aggiunta, avvio, configurazione, etichette, servizio
from hypomnema.configurazione import tomllib

INDIRIZZO = "127.0.0.1"
LUNGHEZZA_MINIMA_CHIAVE = 32
CHIAVE_VALIDA = re.compile(r"[A-Za-z0-9_-]+")
IMPRONTA_VALIDA = re.compile(r"[0-9a-f]{64}")
# L'intestazione con la chiave (I0285): nel modulo del connettore di claude.ai, «Request headers». Deve essere un
# nome della lista di serie di claude.ai: un nome nuovo andrebbe fatto approvare ad Anthropic.
INTESTAZIONE_CHIAVE = "x-api-key"
# I limiti quando il file dei taccuini non li scrive.
RICHIESTE_AL_MINUTO = 30
PROPOSTE_AL_MINUTO = 10
# Una richiesta più grande è rifiutata (413): una proposta o una copia dell'archivio stanno molto sotto.
LIMITE_RICHIESTA = 4 * 1024 * 1024
ATTESA_SECONDI = 30


class ErroreTaccuini(Exception):
    """Il file dei taccuini non va. Il messaggio non contiene mai una chiave."""


def impronta(chiave: str) -> str:
    """L'impronta SHA-256 della chiave, in esadecimale minuscolo (la stessa di ``Get-FileHash`` di PowerShell)."""
    return hashlib.sha256(chiave.encode("utf-8")).hexdigest()


@dataclass
class Limiti:
    """Le richieste accettate nell'ultimo minuto, per un taccuino. ``orologio`` serve alle prove."""

    richieste: int
    proposte: int
    orologio: object = time.monotonic
    _richieste: deque = field(default_factory=deque)
    _proposte: deque = field(default_factory=deque)
    _blocco: threading.Lock = field(default_factory=threading.Lock)

    def passa(self, proposta: bool) -> str | None:
        """None se la richiesta passa (e la conta); altrimenti quale limite è stato superato."""
        with self._blocco:
            adesso = self.orologio()
            for coda in (self._richieste, self._proposte):
                while coda and coda[0] <= adesso - 60:
                    coda.popleft()
            if len(self._richieste) >= self.richieste:
                return "richieste"
            if proposta and len(self._proposte) >= self.proposte:
                return "proposte"
            self._richieste.append(adesso)
            if proposta:
                self._proposte.append(adesso)
            return None


def _limite(dati: dict, nome: str, normale: int) -> int:
    valore = dati.get(nome, normale)
    if not isinstance(valore, int) or isinstance(valore, bool) or valore < 1:
        raise ErroreTaccuini(f"nel file dei taccuini «{nome}» deve essere un numero intero da 1 in su.")
    return valore


def leggi_limiti(file: Path) -> tuple[int, int]:
    """I due limiti del file dei taccuini (richieste e proposte al minuto)."""
    dati = tomllib.loads(file.read_text(encoding="utf-8-sig"))
    return (_limite(dati, "richieste_al_minuto", RICHIESTE_AL_MINUTO),
            _limite(dati, "proposte_al_minuto", PROPOSTE_AL_MINUTO))


def leggi_taccuini(file: Path) -> tuple[int, list[tuple[str, servizio.Taccuino]]]:
    """La porta e le coppie (impronta della chiave, taccuino) del file, controllate. Errore se un taccuino è quello
    di base. Una voce con ``chiave`` ha la stessa impronta di una voce con ``impronta``."""
    try:
        dati = tomllib.loads(file.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise ErroreTaccuini(f"non trovo il file dei taccuini «{file}».")
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        # Senza dettagli: il messaggio di errore potrebbe citare un pezzo del file, cioè una chiave.
        raise ErroreTaccuini(f"il file dei taccuini «{file}» non è scritto correttamente (TOML in UTF-8).")
    autore = dati.get("autore")
    if autore is not None and (not isinstance(autore, str) or not autore.strip() or "\n" in autore
                               or len(autore) > 60):
        raise ErroreTaccuini("nel file dei taccuini «autore» deve essere un nome su una riga, per esempio "
                             "autore = \"Angelo\" (oppure va tolta).")
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
        if "impronta" in voce:
            if chiave is not None:
                raise ErroreTaccuini(f"il taccuino «{nome}» ha sia «chiave» sia «impronta»: ne serve una sola.")
            segno = voce["impronta"]
            if not isinstance(segno, str) or not IMPRONTA_VALIDA.fullmatch(segno):
                raise ErroreTaccuini(f"l'impronta del taccuino «{nome}» non va: servono 64 cifre esadecimali "
                                     "minuscole (SHA-256 della chiave).")
        elif (not isinstance(chiave, str) or len(chiave) < LUNGHEZZA_MINIMA_CHIAVE
                or not CHIAVE_VALIDA.fullmatch(chiave)):
            raise ErroreTaccuini(
                f"la chiave del taccuino «{nome}» non va: servono almeno {LUNGHEZZA_MINIMA_CHIAVE} caratteri, solo "
                "lettere, cifre, - e _. Creala con:  py -c \"import secrets; print(secrets.token_urlsafe(32))\"")
        else:
            segno = impronta(chiave)
        if any(hmac.compare_digest(segno, altra) for altra, _ in coppie):
            raise ErroreTaccuini(f"il taccuino «{nome}» ha la stessa chiave di un altro: ogni taccuino ha la sua.")
        percorso = Path(config)
        if not percorso.is_absolute():
            percorso = file.parent / percorso
        try:
            taccuino = servizio.Taccuino(nome, percorso, autore=autore.strip() if autore else None)
        except configurazione.ErroreConfigurazione as errore:
            raise ErroreTaccuini(f"taccuino «{nome}»: {errore}")
        if avvio._dentro(taccuino.cartella_quaderno.resolve(), base.resolve()) or avvio._dentro(taccuino.config, base):
            raise ErroreTaccuini(
                f"il taccuino «{nome}» è nella cartella {base}, quella della configurazione di base: il server HTTP "
                "non la serve mai. Toglilo dal file dei taccuini.")
        if any(altro.nome == nome for _, altro in coppie):
            raise ErroreTaccuini(f"due taccuini si chiamano «{nome}»: ogni taccuino ha il suo nome.")
        coppie.append((segno, taccuino))
    leggi_limiti(file)
    return porta, coppie


NOME_VALIDO = re.compile(r"[a-z0-9][a-z0-9-]{0,39}")
MODELLO_ONLINE = Path(__file__).resolve().parent.parent / "online" / "hypomnema-online.toml"
ETICHETTE_VUOTE = """\
# Le etichette di questo taccuino (vedi esempi/etichette.toml nel repository di Hypomnema). Per ora vuote.
chi = []
cosa = []
"""


def crea_taccuino(file: Path, nome: str, segno: str) -> Path:
    """Crea un taccuino online accanto al file dei taccuini (cartella ``<nome>``, configurazione online, quaderno con
    ``etichette.toml`` vuoto) e aggiunge la sua voce, con la sola impronta della chiave, in fondo al file. La
    chiave non arriva mai qui. Restituisce la cartella del taccuino. Niente si crea se qualcosa non va."""
    if not NOME_VALIDO.fullmatch(nome):
        raise ErroreTaccuini(f"il nome «{nome}» non va: da 1 a 40 caratteri, solo lettere minuscole, cifre e -, "
                             "e il primo non è un -.")
    if not IMPRONTA_VALIDA.fullmatch(segno):
        raise ErroreTaccuini("l'impronta non va: servono 64 cifre esadecimali minuscole (SHA-256 della chiave).")
    if not file.is_file():
        raise ErroreTaccuini(f"non trovo il file dei taccuini «{file}».")
    try:
        dati = tomllib.loads(file.read_text(encoding="utf-8-sig"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        raise ErroreTaccuini(f"il file dei taccuini «{file}» non è scritto correttamente (TOML in UTF-8).")
    for voce in dati.get("taccuino", []):
        if not isinstance(voce, dict):
            continue
        if voce.get("nome") == nome:
            raise ErroreTaccuini(f"c'è già un taccuino che si chiama «{nome}».")
        altra = voce.get("impronta") or (impronta(voce["chiave"]) if isinstance(voce.get("chiave"), str) else "")
        if isinstance(altra, str) and hmac.compare_digest(altra, segno):
            raise ErroreTaccuini("questa chiave è già di un altro taccuino: creane una nuova.")
    cartella = file.parent / nome
    if cartella.exists():
        raise ErroreTaccuini(f"la cartella «{cartella}» c'è già: scegli un altro nome.")
    base = avvio.configurazione_di_base().parent
    if avvio._dentro(cartella.resolve(), base.resolve()):
        raise ErroreTaccuini(f"la cartella «{cartella}» è dentro {base}, quella della configurazione di base: il "
                             "server HTTP non la serve mai.")
    (cartella / "quaderno").mkdir(parents=True)
    config = cartella / "hypomnema.toml"
    config.write_bytes(MODELLO_ONLINE.read_bytes())
    with open(cartella / "quaderno" / "etichette.toml", "x", encoding="utf-8", newline="\n") as etichette:
        etichette.write(ETICHETTE_VUOTE)
    testo = file.read_bytes()
    a_capo = "" if not testo or testo.endswith(b"\n") else "\n"
    aggiunta.aggiungi(file, f'{a_capo}\n[[taccuino]]\nnome = "{nome}"\nconfig = "{nome}/hypomnema.toml"\n'
                            f'impronta = "{segno}"\n')
    return cartella


def controlla_etichette(testo: str) -> "etichette.Etichette":
    """La lista delle etichette scritta in ``testo``, controllata con le stesse regole dello sportello. Errore
    (``ErroreTaccuini``) se è scritta male: il messaggio non dice dove sta il file."""
    import tempfile
    with tempfile.TemporaryDirectory() as cartella:
        (Path(cartella) / etichette.NOME_FILE).write_text(testo, encoding="utf-8", newline="\n")
        try:
            lista = etichette.leggi(Path(cartella))
        except etichette.ErroreEtichette as errore:
            raise ErroreTaccuini(str(errore).replace(f"«{Path(cartella) / etichette.NOME_FILE}»", "")
                                 .replace("  ", " ").replace(" Non ho scritto niente.", ""))
    if not lista.chi and not lista.cosa:
        raise ErroreTaccuini("la lista non ha nessuna etichetta: servono «chi» o «cosa».")
    return lista


def carica_etichette(file: Path, nome: str, testo: str, sostituisci: bool, adesso: datetime) -> Path | None:
    """Scrive la lista delle etichette nel quaderno del taccuino ``nome`` (0.11.0, seconda parte). La lista si
    controlla prima. Se ce n'è già una con delle etichette, serve ``sostituisci``. La lista che c'era non si cancella
    mai: resta accanto, con la data nel nome (la si restituisce). Le liste le scrive l'utente, mai Claude."""
    controlla_etichette(testo)
    if not NOME_VALIDO.fullmatch(nome):
        raise ErroreTaccuini(f"il nome «{nome}» non va: solo lettere minuscole, cifre e -.")
    if not file.is_file():
        raise ErroreTaccuini(f"non trovo il file dei taccuini «{file}».")
    try:
        dati = tomllib.loads(file.read_text(encoding="utf-8-sig"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        raise ErroreTaccuini(f"il file dei taccuini «{file}» non è scritto correttamente (TOML in UTF-8).")
    voce = next((v for v in dati.get("taccuino", []) if isinstance(v, dict) and v.get("nome") == nome), None)
    if voce is None or not isinstance(voce.get("config"), str):
        raise ErroreTaccuini(f"non c'è un taccuino che si chiama «{nome}».")
    percorso = Path(voce["config"])
    if not percorso.is_absolute():
        percorso = file.parent / percorso
    try:
        quaderno = configurazione.carica(str(percorso)).cartella_quaderno
    except configurazione.ErroreConfigurazione as errore:
        raise ErroreTaccuini(f"taccuino «{nome}»: {errore}")
    bersaglio = etichette.file_di(quaderno)
    vecchio = None
    if bersaglio.exists():
        try:
            prima = etichette.leggi(quaderno)
        except etichette.ErroreEtichette:
            prima = None
        if prima is None or prima.chi or prima.cosa:
            if not sostituisci:
                raise ErroreTaccuini(f"il taccuino «{nome}» ha già una lista di etichette con qualcosa dentro: per "
                                     "sostituirla serve la conferma (--replace). Quella di adesso resterebbe accanto.")
        vecchio = bersaglio.with_name(f"etichette-fino-al-{adesso.strftime('%Y-%m-%d-%H%M%S')}.toml")
        if vecchio.exists():
            raise ErroreTaccuini("c'è già una copia della lista con la stessa ora: riprova tra un secondo.")
        bersaglio.rename(vecchio)
    quaderno.mkdir(parents=True, exist_ok=True)
    with open(bersaglio, "x", encoding="utf-8", newline="\n") as nuovo:
        nuovo.write(testo.replace("\r\n", "\n"))
    return vecchio


class ServerHTTP(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, porta: int, coppie: list[tuple[str, servizio.Taccuino]], limiti: tuple[int, int] = (
            RICHIESTE_AL_MINUTO, PROPOSTE_AL_MINUTO)):
        self.coppie = coppie
        self.limiti_al_minuto = limiti
        self.limiti = {id(taccuino): Limiti(*limiti) for _, taccuino in coppie}
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
        trovato, segno = None, impronta(cercata)
        for altra, taccuino in self.server.coppie:
            # Tutte le impronte, sempre: il tempo della risposta non dice niente su quale chiave quasi va.
            if hmac.compare_digest(segno, altra):
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
        superato = self.server.limiti[id(taccuino)].passa(_e_una_proposta(testo))
        if superato is not None:
            return self._troppe(superato, testo)
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

    def _troppe(self, superato: str, testo: str) -> None:
        if superato == "proposte":
            messaggio = (f"LIMIT: at most {self.server.limiti_al_minuto[1]} proposals (propose) per minute for this "
                         "notebook. Nothing was saved. Wait one minute, then propose again, one note at a time. Tell "
                         "the user: «Ho raggiunto il limite di proposte al minuto: riprovo tra un minuto.»")
        else:
            messaggio = (f"LIMIT: at most {self.server.limiti_al_minuto[0]} requests per minute for this notebook. "
                         "Nothing was done. Wait one minute, then try again. Tell the user: «Ho raggiunto il limite "
                         "di richieste al minuto del taccuino: riprovo tra un minuto.»")
        try:
            richiesta = json.loads(testo)
            id_richiesta = richiesta.get("id") if isinstance(richiesta, dict) else None
        except ValueError:
            id_richiesta = None
        corpo = json.dumps({"jsonrpc": "2.0", "id": id_richiesta, "error": {"code": -32000, "message": messaggio}},
                           ensure_ascii=False).encode("utf-8")
        return self._rispondi(429, corpo, {"Content-Type": "application/json; charset=utf-8", "Retry-After": "60"})

    def _non_permesso(self) -> None:
        if self._taccuino() is None:
            self.close_connection = True
            return self._rispondi(404)
        # Lo streaming (GET) e la chiusura della sessione (DELETE) non servono: si risponde solo con POST.
        return self._rispondi(405, intestazioni={"Allow": "POST"})

    do_GET = do_DELETE = do_PUT = do_PATCH = do_HEAD = do_OPTIONS = _non_permesso  # noqa: N815


def _e_una_proposta(testo: str) -> bool:
    try:
        richiesta = json.loads(testo)
    except ValueError:
        return False
    return (isinstance(richiesta, dict) and richiesta.get("method") == "tools/call"
            and isinstance(richiesta.get("params"), dict) and richiesta["params"].get("name") == "propose")


def crea_server(file: Path, porta: int | None = None) -> ServerHTTP:
    """Il server pronto, non ancora avviato (``porta`` serve alle prove: 0 = una porta libera qualsiasi)."""
    porta_del_file, coppie = leggi_taccuini(file)
    return ServerHTTP(porta_del_file if porta is None else porta, coppie, leggi_limiti(file))


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
