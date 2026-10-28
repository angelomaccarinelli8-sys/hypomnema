"""Il cuore del server MCP (dalla 0.11.0): gli strumenti di Hypomnema, senza sapere come arrivano le richieste.

Ogni strumento è un comando di sempre (``status``, ``recap``, ``propose``…), lanciato con ``cli.main`` sulla
configurazione del taccuino: stessi messaggi, stesse regole, lo stesso sportello. Il cuore riceve il taccuino da
fuori (``Taccuino``) e nessuno strumento accetta percorsi o configurazioni: il server lavora solo sul taccuino che
gli è stato dato all'avvio.

I trasporti (``mcp_stdio`` per Claude Code e l'app desktop, ``mcp_http`` per il tunnel) passano a ``rispondi``
la richiesta JSON-RPC già letta e scrivono la risposta: non sanno niente di note.
"""

from __future__ import annotations

import io
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from hypomnema import __version__, configurazione, modelli

# Le versioni del protocollo MCP che il server sa parlare, dalla più recente.
VERSIONI_PROTOCOLLO = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")

ORIGINE_MCP = "(strumento MCP)"

# La scheda corta: le istruzioni che il server dà a Claude all'inizio (al posto della skill lunga).
ISTRUZIONI = """\
Hypomnema is the user's permanent memory notebook. You never write its files: you PROPOSE notes with the
`propose` tool and the desk (fixed rules, no AI) decides whether they get in. Talk to the user in Italian.

At the start of a chat: `check`, then `recap` and tell the user in three lines at most where you left off
(notes chosen by the user apart from the diary); as soon as the topic is clear, `tree` with `about` for that
branch only; then `review` and say only how many things it found and the most urgent one.

Proposals (one note = one thing; take the model with `template`):
- `author: user` only for the user's exact words, copied in `text` without changing a single one (your
  additions go in `context`); otherwise `author: claude`, with the user's words in `quote`.
- `knowledge`: stated, observed or inferred (when in doubt, inferred). `kind`: fact, idea, decision (only the
  user's, explicitly), open, todo. An idea becomes a decision only with a new user's note with `confirms`.
- To change a note: `corrects`, `updates`, `done`, `reopens`, `integrates`, `cancels` with the number only
  ("0049"). Before a new idea or fact, look at its sub-branch with `tree`: if a live note of the same author and
  kind is there, propose `integrates`.
- After every `propose` the server runs `check` and returns it: if it says «ATTENZIONE», tell the user and
  repair nothing.
- ACCETTATA = saved; RIFIUTATA = not saved: explain the reasons in plain Italian. Never get around a rule.
- Here there is no witness: the user's notes are saved as «non verificate» (or «riscontrate sull'archivio della
  chat» after `archive`). Say it to the user as it is, never «verificate».

Never put in the notebook other people's health data, or data about clients (the user's or anyone else's): if
the user asks, say «Questo nel taccuino non lo scrivo: sono dati sensibili di altre persone.»

Use what you find for what it is: a decision is a decision, an idea only a proposal, an inferred note a
hypothesis. Cite notes by their code («dalla nota T0004.2»). Never invent notes the tools did not return.
"""


# La frase del servizio chiuso (0.11.0, seconda parte): solo dove il file dei taccuini ha la riga «autore». Dice
# la verità sulla natura del servizio; non chiede a Claude di nascondere niente.
SERVIZIO_CHIUSO = """
This notebook is a closed service run by its author, {autore}: the program that checks and saves the notes runs on
the author's server and is not shared. You only see the tools and their answers. If the user asks how it works,
explain what each tool does and how to use it; for anything about how it works inside, tell them they can ask
{autore}.
"""


def istruzioni(taccuino: "Taccuino") -> str:
    """La scheda per Claude: con la frase del servizio chiuso se il taccuino ha un autore."""
    if taccuino.autore is None:
        return ISTRUZIONI
    return ISTRUZIONI + SERVIZIO_CHIUSO.format(autore=taccuino.autore)


class ErroreArgomenti(ValueError):
    """Gli argomenti di uno strumento non vanno bene."""


@dataclass
class Taccuino:
    """Un taccuino servito: un nome e la sua configurazione, controllata quando si crea.

    Il blocco ``passaggio`` mette in fila le chiamate allo stesso taccuino (il trasporto HTTP ne riceve più
    di una insieme); tra processi diversi vale il blocco dello sportello.
    """

    nome: str
    config: Path
    orologio: Callable[[], datetime | None] = lambda: None
    # L'autore del servizio (riga «autore» del file dei taccuini): None = nessuna frase del servizio chiuso.
    autore: str | None = None
    passaggio: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.config = Path(self.config).resolve()
        # Errore subito, all'avvio, se la configurazione non va: ErroreConfigurazione.
        self.cartella_quaderno = configurazione.carica(str(self.config)).cartella_quaderno


@dataclass(frozen=True)
class Strumento:
    nome: str
    descrizione: str
    proprieta: dict
    richiesti: tuple[str, ...] = ()

    def schema(self) -> dict:
        schema = {"type": "object", "properties": self.proprieta, "additionalProperties": False}
        if self.richiesti:
            schema["required"] = list(self.richiesti)
        return schema


ETICHETTE = {"type": "array", "items": {"type": "string"}}
VERO_FALSO = {"type": "boolean"}

STRUMENTI = (
    Strumento("status", "Witness, time zone and labels of the notebook (read only).", {}),
    Strumento("check", "Check that the notebook is in order (read only). If it says «ATTENZIONE», tell the user: "
                       "repair nothing.", {}),
    Strumento("recap", "Where we left off: overdue reminders, open questions, todos, latest decisions, last diary "
                       "lines. Optional filters by labels CHI (who) and COSA (about).",
              {"who": ETICHETTE, "about": ETICHETTE}),
    Strumento("review", "What is worth looking at, with fixed rules (read only). `proposals`: also the ready-made "
                        "proposals, to fill with the user's words and propose one at a time.",
              {"proposals": VERO_FALSO}),
    Strumento("tree", "Branch → sub-branches → notes, integration chains on one line. Use `about` for one branch "
                      "only; `all` also shows closed and cancelled notes.",
              {"about": ETICHETTE, "all": VERO_FALSO}),
    Strumento("search", "Search the notes by exact word (case-insensitive), most recent first, each with its "
                        "history. Closed notes only with `all`. Filters `about` (COSA) and `who` (CHI); with a "
                        "filter `word` can be omitted.",
              {"word": {"type": "string"}, "all": VERO_FALSO, "about": ETICHETTE, "who": ETICHETTE}),
    Strumento("labels", "The labels CHI and COSA of the notebook, with how many notes have each (read only).", {}),
    Strumento("template", "The empty proposal for a move, with only the allowed fields. Without `move`, the list.",
              {"move": {"type": "string", "enum": list(modelli.MOSSE)}}),
    Strumento("propose", "Pass a note (the proposal, as a JSON object) to the desk. It answers ACCETTATA or "
                         "RIFIUTATA with the reasons; then the server runs `check` and adds its answer.",
              {"proposal": {"type": "object"}}, ("proposal",)),
    Strumento("archive", "Copy this chat from the chat archive into the notebook: {chat, fuso, messaggi:[{turno, "
                         "quando, chi, testo}]}, exactly as the archive returns it. Then the server runs `check`.",
              {"archive": {"type": "object"}}, ("archive",)),
)
PER_NOME = {s.nome: s for s in STRUMENTI}


def _controlla_argomenti(strumento: Strumento, argomenti) -> dict:
    if argomenti is None:
        argomenti = {}
    if not isinstance(argomenti, dict):
        raise ErroreArgomenti("the arguments must be an object")
    for chiave in argomenti:
        if chiave not in strumento.proprieta:
            raise ErroreArgomenti(f"unknown argument «{chiave}» for {strumento.nome}")
    for chiave in strumento.richiesti:
        if chiave not in argomenti:
            raise ErroreArgomenti(f"missing argument «{chiave}»")
    for chiave, valore in argomenti.items():
        tipo = strumento.proprieta[chiave]["type"]
        if tipo == "array":
            if not isinstance(valore, list) or not all(isinstance(v, str) for v in valore):
                raise ErroreArgomenti(f"«{chiave}» must be a list of strings")
        elif tipo == "boolean" and not isinstance(valore, bool):
            raise ErroreArgomenti(f"«{chiave}» must be true or false")
        elif tipo == "string" and not isinstance(valore, str):
            raise ErroreArgomenti(f"«{chiave}» must be a string")
        elif tipo == "object" and not isinstance(valore, dict):
            raise ErroreArgomenti(f"«{chiave}» must be an object")
        if "enum" in strumento.proprieta[chiave] and valore not in strumento.proprieta[chiave]["enum"]:
            raise ErroreArgomenti(f"«{chiave}» must be one of: {', '.join(strumento.proprieta[chiave]['enum'])}")
    return argomenti


def _comando(nome: str, argomenti: dict) -> list[str]:
    """La riga di comando di uno strumento. I valori vanno sempre come ``--opzione=valore`` o dopo ``--``: un valore
    che comincia con «-» (per esempio «--config») resta un valore e non diventa un'opzione."""
    riga = [nome]
    if argomenti.get("all"):
        riga.append("--all")
    if argomenti.get("proposals"):
        riga.append("--proposals")
    riga += [f"--who={v}" for v in argomenti.get("who", [])]
    riga += [f"--about={v}" for v in argomenti.get("about", [])]
    if nome == "search" and "word" in argomenti:
        riga += ["--", argomenti["word"]]
    if nome == "template" and "move" in argomenti:
        riga.append(argomenti["move"])
    if nome in ("propose", "archive"):
        riga.append("-")
    return riga


def _lancia(taccuino: Taccuino, riga: list[str], entrata: bytes | None = None) -> tuple[int, str]:
    from hypomnema.cli import main  # qui, perché cli importa questo file per il comando serve

    uscita = io.StringIO()
    codice = main(["--config", str(taccuino.config), *riga], adesso=taccuino.orologio(), uscita=uscita,
                  errori=uscita, entrata=entrata)
    return codice, uscita.getvalue()


def chiama(taccuino: Taccuino, nome: str, argomenti) -> tuple[str, bool]:
    """Esegue uno strumento: (testo della risposta, errore?). Errore solo per il codice 2 (configurazione, file
    non valido): una nota RIFIUTATA è una risposta normale. ``KeyError`` se lo strumento non esiste,
    ``ErroreArgomenti`` se gli argomenti non vanno."""
    strumento = PER_NOME[nome]
    argomenti = _controlla_argomenti(strumento, argomenti)
    entrata = None
    if nome in ("propose", "archive"):
        entrata = json.dumps(argomenti[nome if nome == "archive" else "proposal"], ensure_ascii=False).encode("utf-8")
    with taccuino.passaggio:
        codice, testo = _lancia(taccuino, _comando(nome, argomenti), entrata)
        if nome in ("propose", "archive"):
            _, controllo = _lancia(taccuino, ["check"])
            testo += "\nControllo dopo il passaggio (check):\n" + controllo
    return testo, codice == 2


# --- JSON-RPC: la stessa risposta per ogni trasporto ---------------------------------------------------------

ERRORE_FORMATO, RICHIESTA_NON_VALIDA, METODO_SCONOSCIUTO, PARAMETRI_NON_VALIDI = -32700, -32600, -32601, -32602


def _errore(id_richiesta, codice: int, messaggio: str) -> dict:
    return {"jsonrpc": "2.0", "id": id_richiesta, "error": {"code": codice, "message": messaggio}}


def _risultato(id_richiesta, risultato: dict) -> dict:
    return {"jsonrpc": "2.0", "id": id_richiesta, "result": risultato}


def elenco_strumenti() -> list[dict]:
    return [{"name": s.nome, "description": s.descrizione, "inputSchema": s.schema()} for s in STRUMENTI]


def rispondi(taccuino: Taccuino, messaggio) -> dict | None:
    """La risposta a un messaggio JSON-RPC già letto; ``None`` per le notifiche (nessuna risposta)."""
    if not isinstance(messaggio, dict) or messaggio.get("jsonrpc") != "2.0" or not isinstance(
            messaggio.get("method", ""), str):
        return _errore(None, RICHIESTA_NON_VALIDA, "invalid request")
    if "method" not in messaggio:
        return None  # una risposta del client: non abbiamo chiesto niente
    if "id" not in messaggio:
        return None  # una notifica (per esempio notifications/initialized)
    id_richiesta, metodo = messaggio["id"], messaggio["method"]
    parametri = messaggio.get("params") or {}
    if not isinstance(parametri, dict):
        return _errore(id_richiesta, PARAMETRI_NON_VALIDI, "params must be an object")
    if metodo == "initialize":
        chiesta = parametri.get("protocolVersion")
        return _risultato(id_richiesta, {
            "protocolVersion": chiesta if chiesta in VERSIONI_PROTOCOLLO else VERSIONI_PROTOCOLLO[0],
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "hypomnema", "version": __version__},
            "instructions": istruzioni(taccuino),
        })
    if metodo == "ping":
        return _risultato(id_richiesta, {})
    if metodo == "tools/list":
        return _risultato(id_richiesta, {"tools": elenco_strumenti()})
    if metodo == "tools/call":
        nome = parametri.get("name")
        if nome not in PER_NOME:
            return _errore(id_richiesta, PARAMETRI_NON_VALIDI, f"unknown tool: {nome}")
        try:
            testo, errore = chiama(taccuino, nome, parametri.get("arguments"))
        except ErroreArgomenti as e:
            testo, errore = f"ERRORE: {e}", True
        return _risultato(id_richiesta, {"content": [{"type": "text", "text": testo}], "isError": errore})
    return _errore(id_richiesta, METODO_SCONOSCIUTO, f"unknown method: {metodo}")


def rispondi_al_testo(taccuino: Taccuino, testo: str) -> dict | None:
    """Come ``rispondi``, partendo dal testo JSON (un errore di formato ha la sua risposta)."""
    try:
        messaggio = json.loads(testo)
    except ValueError:
        return _errore(None, ERRORE_FORMATO, "parse error")
    return rispondi(taccuino, messaggio)
