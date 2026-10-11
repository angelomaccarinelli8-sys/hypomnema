"""Il testimone dell'archivio: la conversazione della chat, copiata dall'archivio di Claude.

Nella chat di claude.ai non c'è il testimone, ma Claude può rileggere la conversazione come è salvata
nell'archivio delle chat: le parole dell'utente, la data e l'ora di ogni messaggio e l'indirizzo della
chat. Claude passa questa copia al comando ``hypomnema archivio <file.json>``:

    {"chat": "https://claude.ai/chat/…",
     "messaggi": [{"quando": "2026-10-11T18:47:33+02:00", "chi": "utente", "testo": "…"},
                  {"quando": "2026-10-11T18:47:50+02:00", "chi": "claude", "testo": "…"}]}

I messaggi dell'utente vanno nel file dell'archivio (``archivio-chat.jsonl``), le risposte di Claude
nel diario della chat (``diario-chat.jsonl``), solo in aggiunta e senza doppioni (stesso indirizzo,
stessa data e ora). Ogni riga dice da dove viene:

    {"quando": "…", "chat": "https://claude.ai/chat/…", "testo": "…", "origine": "copiato dall'archivio della chat da Claude"}
    {"quando": "…", "chat": "…", "privato": "messaggio privato, non copiato", "origine": "…"}

Limite dichiarato: il testo passa da Claude prima di arrivare qui, quindi Claude potrebbe alterarlo.
Per questo le note riscontrate così portano l'indirizzo della chat: chiunque può aprirla e controllare.
"""

import json
from dataclasses import dataclass, replace
from datetime import datetime

from hypomnema.configurazione import Configurazione
from hypomnema.risposte import ometti_codice
from hypomnema.testimone import ErroreTestimone, Messaggio

ORIGINE = "copiato dall'archivio della chat da Claude"
DICITURA_PRIVATO = "messaggio privato, non copiato"
DICITURA_RISPOSTA_PRIVATA = "risposta a un messaggio privato, non copiata"
CHI = ("utente", "claude")


class ErroreArchivio(ErroreTestimone):
    """La copia dell'archivio non è valida, oppure un file dell'archivio è rovinato."""


@dataclass(frozen=True)
class Esito:
    utente: int = 0  # messaggi dell'utente copiati con il testo
    privati: int = 0  # messaggi dell'utente privati (solo data e ora)
    claude: int = 0  # risposte di Claude copiate
    risposte_private: int = 0  # risposte a messaggi privati (solo data e ora)
    gia_presenti: int = 0  # non duplicati
    diversi: int = 0  # già presenti ma con un testo diverso da quello arrivato ora


def _data(valore) -> datetime | None:
    if not isinstance(valore, str):
        return None
    try:
        momento = datetime.fromisoformat(valore)
    except ValueError:
        return None
    return momento if momento.tzinfo is not None else None


def _chat_valida(chat) -> bool:
    return isinstance(chat, str) and chat.startswith("https://") and len(chat.split()) == 1


def voce_valida(riga: str) -> Messaggio | None:
    """La voce di una riga dei file dell'archivio, oppure None se la riga non ha il formato previsto."""
    try:
        voce = json.loads(riga)
    except json.JSONDecodeError:
        return None
    if not isinstance(voce, dict) or _data(voce.get("quando")) is None or not _chat_valida(voce.get("chat")):
        return None
    if voce.get("origine") != ORIGINE:
        return None
    altri = set(voce) - {"quando", "chat", "origine"}
    if altri == {"testo"} and isinstance(voce["testo"], str):
        return Messaggio(quando=voce["quando"], testo=voce["testo"], chat=voce["chat"])
    if altri == {"privato"} and isinstance(voce["privato"], str):
        return Messaggio(quando=voce["quando"], testo=None, privato=voce["privato"], chat=voce["chat"])
    return None


def _leggi_file(file, nome: str) -> list[Messaggio]:
    if file is None or not file.is_file():
        return []
    try:
        righe = file.read_text(encoding="utf-8").split("\n")
    except UnicodeDecodeError:
        raise ErroreArchivio(f"il file {nome} non è in UTF-8. Controlla se è stato modificato a mano.")
    voci = []
    for numero, riga in enumerate(righe, start=1):
        if not riga.strip():
            continue
        voce = voce_valida(riga)
        if voce is None:
            raise ErroreArchivio(f"la riga {numero} del file {nome} non è valida. "
                                 "Controlla se il file è stato modificato a mano.")
        voci.append(voce)
    return voci


def leggi_messaggi(config: Configurazione) -> list[Messaggio]:
    """I messaggi dell'utente copiati dall'archivio della chat."""
    return _leggi_file(config.file_archivio, "dell'archivio della chat")


def leggi_risposte(config: Configurazione) -> list[Messaggio]:
    """Le risposte di Claude copiate dall'archivio della chat (il diario della chat)."""
    return _leggi_file(config.file_diario_chat, "del diario della chat")


def _leggi_copia(contenuto: bytes) -> tuple[str, list[tuple[datetime, str, str, str]]]:
    """L'indirizzo della chat e i messaggi (momento, quando normalizzato, chi, testo), in ordine di tempo."""
    try:
        dati = json.loads(contenuto.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ErroreArchivio("la copia dell'archivio non è in formato JSON UTF-8.")
    if not isinstance(dati, dict) or set(dati) != {"chat", "messaggi"}:
        raise ErroreArchivio("la copia dell'archivio deve avere solo i campi «chat» e «messaggi».")
    chat = dati["chat"]
    if not _chat_valida(chat):
        raise ErroreArchivio("il campo «chat» deve essere l'indirizzo della chat, che comincia con https://.")
    if not isinstance(dati["messaggi"], list) or not dati["messaggi"]:
        raise ErroreArchivio("il campo «messaggi» deve essere un elenco con almeno un messaggio.")
    messaggi = []
    for numero, voce in enumerate(dati["messaggi"], start=1):
        if not isinstance(voce, dict) or set(voce) != {"quando", "chi", "testo"}:
            raise ErroreArchivio(f"il messaggio {numero} deve avere solo i campi «quando», «chi» e «testo».")
        momento = _data(voce["quando"])
        if momento is None:
            raise ErroreArchivio(f"il messaggio {numero} ha una data e ora non valida: serve la forma "
                                 "2026-10-11T18:47:33+02:00 (con il fuso orario).")
        if voce["chi"] not in CHI:
            raise ErroreArchivio(f"nel messaggio {numero} «chi» deve essere «utente» oppure «claude».")
        if not isinstance(voce["testo"], str):
            raise ErroreArchivio(f"nel messaggio {numero} «testo» deve essere un testo.")
        messaggi.append((momento, momento.isoformat(), voce["chi"], voce["testo"]))
    messaggi.sort(key=lambda m: (m[0], CHI.index(m[2])))
    return chat, messaggi


def copia(config: Configurazione, contenuto: bytes) -> Esito:
    """Aggiunge ai file dell'archivio i messaggi nuovi. Non scrive niente se la copia non è valida."""
    if config.file_archivio is None:
        raise ErroreArchivio("la configurazione non ha la sezione [archivio]: serve la configurazione per la chat.")
    chat, messaggi = _leggi_copia(contenuto)
    file_per = {"utente": config.file_archivio, "claude": config.file_diario_chat}
    presenti = {
        "utente": {(m.chat, m.quando): m for m in leggi_messaggi(config)},
        "claude": {(m.chat, m.quando): m for m in leggi_risposte(config)},
    }
    # Per sapere se una risposta segue un messaggio privato: i messaggi dell'utente di questa chat,
    # quelli già copiati e quelli nuovi, in ordine di tempo.
    utente_della_chat = sorted(
        [(_data(m.quando), m.testo is None) for m in presenti["utente"].values() if m.chat == chat]
        + [(momento, testo.lstrip().startswith(config.prefisso_privato))
           for momento, _, chi, testo in messaggi if chi == "utente"],
        key=lambda c: c[0],
    )

    def privato_prima_di(momento: datetime) -> bool:
        precedenti = [privato for quando, privato in utente_della_chat if quando <= momento]
        return bool(precedenti) and precedenti[-1]

    conti = Esito()
    righe = {"utente": [], "claude": []}
    for momento, quando, chi, testo in messaggi:
        chiave = (chat, quando)
        if chiave in presenti[chi]:
            vecchio = presenti[chi][chiave]
            conti = replace(conti, gia_presenti=conti.gia_presenti + 1)
            if vecchio.testo is not None and vecchio.testo != (ometti_codice(testo) if chi == "claude" and config.archivio_ometti_codice else testo):
                conti = replace(conti, diversi=conti.diversi + 1)
            continue
        voce: dict[str, str] = {"quando": quando, "chat": chat}
        if chi == "utente" and testo.lstrip().startswith(config.prefisso_privato):
            voce["privato"] = DICITURA_PRIVATO
            conti = replace(conti, privati=conti.privati + 1)
        elif chi == "claude" and privato_prima_di(momento):
            voce["privato"] = DICITURA_RISPOSTA_PRIVATA
            conti = replace(conti, risposte_private=conti.risposte_private + 1)
        elif chi == "claude":
            voce["testo"] = ometti_codice(testo) if config.archivio_ometti_codice else testo
            conti = replace(conti, claude=conti.claude + 1)
        else:
            voce["testo"] = testo
            conti = replace(conti, utente=conti.utente + 1)
        voce["origine"] = ORIGINE
        righe[chi].append(json.dumps(voce, ensure_ascii=False) + "\n")
        presenti[chi][chiave] = voce_valida(righe[chi][-1])

    config.cartella_quaderno.mkdir(parents=True, exist_ok=True)
    for chi in CHI:
        if righe[chi]:
            with open(file_per[chi], "a", encoding="utf-8", newline="\n") as f:
                f.writelines(righe[chi])
    return conti


def doppioni_e_righe_rovinate(file) -> tuple[list[tuple[int, int]], list[int]]:
    """Per «controlla»: le coppie (riga, riga già vista) con stesso indirizzo e stessa ora, e le righe non valide."""
    if file is None or not file.is_file():
        return [], []
    testo = file.read_bytes().decode("utf-8", errors="replace")
    righe = testo.split("\n")
    if righe and righe[-1] == "":
        righe = righe[:-1]
    viste: dict[tuple[str, str], int] = {}
    doppioni, rovinate = [], []
    for numero, riga in enumerate(righe, start=1):
        voce = voce_valida(riga)
        if voce is None:
            rovinate.append(numero)
            continue
        chiave = (voce.chat, datetime.fromisoformat(voce.quando).isoformat())
        if chiave in viste:
            doppioni.append((numero, viste[chiave]))
        else:
            viste[chiave] = numero
    return doppioni, rovinate
