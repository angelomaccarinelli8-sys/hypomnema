"""Il testimone delle risposte di Claude: registra il testo di ogni risposta, con data e ora.

Claude Code lancia ``hypomnema risposte`` quando Claude ha finito di rispondere (aggancio "Stop"
in ``hooks/hooks.json``) e gli passa in JSON il campo ``last_assistant_message``, il testo
dell'ultima risposta. Il programma lo aggiunge in fondo al file delle risposte, una riga JSON per
risposta. Il file si apre solo in aggiunta.

    {"quando": "2026-01-15T10:00:30+01:00", "testo": "il testo della risposta"}
    {"quando": "2026-01-15T10:01:30+01:00", "privato": "risposta a un messaggio privato, non registrata"}

Se ``ometti_codice = true``, ogni blocco di codice (tra tre apici inversi) diventa una riga
``[blocco di codice di N righe omesso, impronta XXXXXXXXXXXX]``: l'impronta sono le prime 12 cifre
esadecimali dello SHA-256 del contenuto del blocco (le sue righe, ciascuna con il suo a capo), la
stessa che ``hypomnema impronta`` calcola per un file con quel contenuto.

Funziona solo insieme al testimone dell'utente: serve il messaggio a cui Claude risponde per sapere
se era privato. Se il messaggio non si trova, per prudenza la risposta non viene registrata.
"""

import hashlib
import json
import re
from datetime import datetime

from hypomnema import testimone
from hypomnema.configurazione import Configurazione
from hypomnema.testimone import ErroreTestimone, Messaggio

DICITURA_PRIVATA = "risposta a un messaggio privato, non registrata"
DICITURA_SENZA_MESSAGGIO = "risposta a un messaggio non trovato nel testimone, non registrata"
DICITURA_IN_PAUSA = "risposta durante la pausa, non registrata"
DICITURA_COMANDO = "risposta a un comando di pausa o di ripresa, non registrata"

# Una riga che apre un blocco di codice: fino a 3 spazi, poi almeno tre apici inversi.
_APERTURA = re.compile(r"^ {0,3}(`{3,})")


def impronta(dati: bytes) -> str:
    """Le prime 12 cifre esadecimali dello SHA-256."""
    return hashlib.sha256(dati).hexdigest()[:12]


def _riga_omessa(contenuto: list[str]) -> str:
    dati = "".join(riga + "\n" for riga in contenuto).encode("utf-8")
    quante = "1 riga" if len(contenuto) == 1 else f"{len(contenuto)} righe"
    return f"[blocco di codice di {quante} omesso, impronta {impronta(dati)}]"


def ometti_codice(testo: str) -> str:
    """Sostituisce ogni blocco di codice con una riga che dice quante righe ha e la sua impronta.

    Un blocco si apre con una riga che inizia con almeno tre apici inversi e si chiude con una riga
    di soli apici inversi, almeno quanti quelli di apertura. Un blocco mai chiuso arriva fino in fondo.
    """
    righe = testo.split("\n")
    uscita: list[str] = []
    i = 0
    while i < len(righe):
        apertura = _APERTURA.match(righe[i])
        if not apertura:
            uscita.append(righe[i])
            i += 1
            continue
        chiusura = re.compile(r"^ {0,3}`{%d,}[ \t]*$" % len(apertura.group(1)))
        fine = i + 1
        while fine < len(righe) and not chiusura.match(righe[fine]):
            fine += 1
        uscita.append(_riga_omessa(righe[i + 1:fine]))
        i = fine + 1
    return "\n".join(uscita)


def _messaggio_dell_utente(config: Configurazione, prompt_id: str | None) -> Messaggio | None:
    """Il messaggio dell'utente a cui risponde Claude, oppure None se non si trova.

    Se la risposta ha un ``prompt_id`` e i messaggi ce l'hanno, si cerca quello uguale; altrimenti
    è l'ultimo messaggio registrato (Claude Code registra il messaggio prima che Claude risponda).
    """
    messaggi = testimone.leggi_messaggi(config)
    if not messaggi:
        return None
    if prompt_id is not None:
        for messaggio in reversed(messaggi):
            if messaggio.prompt_id == prompt_id:
                return messaggio
        if messaggi[-1].prompt_id is not None:
            return None
    return messaggi[-1]


def registra(config: Configurazione, adesso: datetime, contenuto: bytes) -> bool:
    """Aggiunge la risposta al file delle risposte. Restituisce False se è spento."""
    if not config.risposte_attive:
        return False
    try:
        dati = json.loads(contenuto.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ErroreTestimone("la risposta in arrivo non è in formato JSON UTF-8.")
    if not isinstance(dati, dict) or not isinstance(dati.get("last_assistant_message"), str):
        raise ErroreTestimone(
            "la risposta in arrivo non contiene il campo «last_assistant_message» con il testo."
        )
    prompt_id = dati.get("prompt_id") if isinstance(dati.get("prompt_id"), str) else None

    voce: dict[str, object] = {"quando": adesso.isoformat(timespec="seconds")}
    messaggio = _messaggio_dell_utente(config, prompt_id)
    if messaggio is None:
        voce["privato"] = DICITURA_SENZA_MESSAGGIO
    elif messaggio.privato in (testimone.DICITURA_PAUSA, testimone.DICITURA_RIPRESA):
        voce["privato"] = DICITURA_COMANDO
    elif messaggio.privato == testimone.DICITURA_IN_PAUSA or testimone.in_pausa(testimone.leggi_messaggi(config)):
        voce["privato"] = DICITURA_IN_PAUSA
    elif messaggio.testo is None:
        voce["privato"] = DICITURA_PRIVATA
    else:
        testo = dati["last_assistant_message"]
        voce["testo"] = ometti_codice(testo) if config.ometti_codice else testo
    if prompt_id is not None:
        voce["prompt_id"] = prompt_id

    config.cartella_quaderno.mkdir(parents=True, exist_ok=True)
    with open(config.file_risposte, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(voce, ensure_ascii=False) + "\n")
    return True


def leggi_risposte(config: Configurazione) -> list[Messaggio]:
    """Tutte le risposte registrate, nell'ordine in cui sono arrivate."""
    if config.file_risposte is None:
        return []
    return testimone.leggi_messaggi(config, config.file_risposte, "delle risposte")
