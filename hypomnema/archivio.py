"""Il testimone dell'archivio: la conversazione della chat, copiata dall'archivio di Claude.

Nella chat di claude.ai non c'è il testimone, ma Claude può rileggere la conversazione come è salvata
nell'archivio delle chat: le parole dell'utente, la data e l'ora di ogni messaggio (al minuto, con il
fuso indicato a parte), il numero progressivo del turno e l'indirizzo della chat. Claude passa questa
copia al comando ``hypomnema archivio <file.json>``, così come la restituisce lo strumento:

    {"chat": "https://claude.ai/chat/…", "fuso": "UTC+02:00",
     "messaggi": [{"turno": 12, "quando": "Fri 2026-10-09 17:46", "chi": "utente", "testo": "…"},
                  {"turno": 13, "quando": "Fri 2026-10-09 17:46", "chi": "claude", "testo": "…"}]}

I messaggi dell'utente vanno nel file dell'archivio (``archivio-chat.jsonl``), le risposte di Claude
nel diario della chat (``diario-chat.jsonl``), solo in aggiunta e senza doppioni: un messaggio è già
presente se ha lo stesso indirizzo della chat e lo stesso numero di turno (l'ora, al minuto, non
basta). Dai messaggi dell'utente si tolgono gli avvisi tecnici che l'app inserisce tra
``<system-reminder>`` e ``</system-reminder>``.

Lo strumento che rilegge la chat scrive «<», «>» e «&» come «&lt;», «&gt;» e «&amp;». Claude copia il
testo così com'è, senza convertire niente; li converte questo programma, con una regola fissa, prima
di tutto il resto: così gli avvisi tecnici si riconoscono in tutte e due le forme e nel quaderno
finiscono i segni veri. Limite dichiarato: un «&lt;» scritto davvero dall'utente diventa «<».
Ogni riga dice da dove viene:

    {"quando": "2026-10-09T17:46:00+02:00", "chat": "https://claude.ai/chat/…", "turno": 12, "testo": "…", "origine": "copiato dall'archivio della chat da Claude"}
    {"quando": "…", "chat": "…", "turno": 14, "privato": "messaggio privato, non copiato", "origine": "…"}

Limite dichiarato: il testo passa da Claude prima di arrivare qui, quindi Claude potrebbe alterarlo.
Per questo le note riscontrate così portano l'indirizzo della chat: chiunque può aprirla e controllare.
"""

import json
import re
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone

from hypomnema import blocco
from hypomnema.configurazione import Configurazione
from hypomnema.risposte import ometti_codice
from hypomnema.testimone import ErroreTestimone, Messaggio

ORIGINE = "copiato dall'archivio della chat da Claude"
DICITURA_PRIVATO = "messaggio privato, non copiato"
DICITURA_RISPOSTA_PRIVATA = "risposta a un messaggio privato, non copiata"
CHI = ("utente", "claude")

# Data e ora come le dà lo strumento dell'archivio: «Fri 2026-10-09 17:46» (il giorno è facoltativo).
_QUANDO = re.compile(r"^(?:[A-Za-z]{3} )?(\d{4}-\d{2}-\d{2}) (\d{2}):(\d{2})$")
# Il fuso, indicato a parte: «UTC+02:00».
_FUSO = re.compile(r"^UTC([+-])(\d{2}):(\d{2})$")
# Gli avvisi tecnici dell'app nei messaggi dell'utente.
_AVVISO = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)
_SEGNI_AVVISO = ("<system-reminder>", "</system-reminder>")


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
    avvisi_tolti: int = 0  # avvisi tecnici tolti dai messaggi dell'utente


def _data(valore) -> datetime | None:
    if not isinstance(valore, str):
        return None
    try:
        momento = datetime.fromisoformat(valore)
    except ValueError:
        return None
    return momento if momento.tzinfo is not None else None


def _turno_valido(turno) -> bool:
    return isinstance(turno, int) and not isinstance(turno, bool) and turno >= 0


def _chat_valida(chat) -> bool:
    return isinstance(chat, str) and chat.startswith("https://") and len(chat.split()) == 1


# Le tre sostituzioni dello strumento che rilegge la chat, nell'ordine giusto per tornare indietro:
# «&amp;» per ultimo, così «&amp;lt;» diventa «&lt;» e non «<».
_SEGNI_HTML = (("&lt;", "<"), ("&gt;", ">"), ("&amp;", "&"))


def segni_veri(testo: str) -> str:
    """Riporta «&lt;», «&gt;» e «&amp;» ai segni «<», «>» e «&»."""
    parti = testo.split("&amp;")
    for scritto, segno in _SEGNI_HTML[:2]:
        parti = [parte.replace(scritto, segno) for parte in parti]
    return "&".join(parti)


def togli_avvisi(testo: str) -> tuple[str, int]:
    """Toglie gli avvisi tecnici <system-reminder>…</system-reminder> e gli spazi rimasti ai bordi.

    Restituisce il testo pulito e quanti avvisi ha tolto. Se resta un segno di avviso senza la sua
    coppia, solleva ErroreArchivio: meglio fermarsi che salvare un avviso a metà.
    """
    pulito, quanti = _AVVISO.subn("", testo)
    if any(segno in pulito for segno in _SEGNI_AVVISO):
        raise ErroreArchivio("c'è un avviso tecnico <system-reminder> senza la sua chiusura: controlla la copia.")
    return (pulito.strip() if quanti else pulito), quanti


def voce_valida(riga: str) -> Messaggio | None:
    """La voce di una riga dei file dell'archivio, oppure None se la riga non ha il formato previsto."""
    try:
        voce = json.loads(riga)
    except json.JSONDecodeError:
        return None
    if (
        not isinstance(voce, dict) or _data(voce.get("quando")) is None or not _chat_valida(voce.get("chat"))
        or not _turno_valido(voce.get("turno")) or voce.get("origine") != ORIGINE
    ):
        return None
    altri = set(voce) - {"quando", "chat", "turno", "origine"}
    comuni = dict(quando=voce["quando"], chat=voce["chat"], turno=voce["turno"])
    if altri == {"testo"} and isinstance(voce["testo"], str):
        return Messaggio(testo=voce["testo"], **comuni)
    if altri == {"privato"} and isinstance(voce["privato"], str):
        return Messaggio(testo=None, privato=voce["privato"], **comuni)
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


def _fuso(valore) -> timezone:
    corrispondenza = _FUSO.match(valore) if isinstance(valore, str) else None
    if corrispondenza is None:
        raise ErroreArchivio("il campo «fuso» deve essere il fuso orario come lo dà l'archivio, per esempio UTC+02:00.")
    segno, ore, minuti = corrispondenza.groups()
    scarto = timedelta(hours=int(ore), minutes=int(minuti))
    return timezone(-scarto if segno == "-" else scarto)


def _leggi_copia(contenuto: bytes):
    """L'indirizzo della chat e i messaggi (turno, quando, chi, testo, avvisi tolti), in ordine di turno."""
    try:
        dati = json.loads(contenuto.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ErroreArchivio("la copia dell'archivio non è in formato JSON UTF-8.")
    if not isinstance(dati, dict) or set(dati) != {"chat", "fuso", "messaggi"}:
        raise ErroreArchivio("la copia dell'archivio deve avere solo i campi «chat», «fuso» e «messaggi».")
    chat = dati["chat"]
    if not _chat_valida(chat):
        raise ErroreArchivio("il campo «chat» deve essere l'indirizzo della chat, che comincia con https://.")
    fuso = _fuso(dati["fuso"])
    if not isinstance(dati["messaggi"], list) or not dati["messaggi"]:
        raise ErroreArchivio("il campo «messaggi» deve essere un elenco con almeno un messaggio.")
    messaggi, turni = [], set()
    for numero, voce in enumerate(dati["messaggi"], start=1):
        if not isinstance(voce, dict) or set(voce) != {"turno", "quando", "chi", "testo"}:
            raise ErroreArchivio(f"il messaggio {numero} deve avere solo i campi «turno», «quando», «chi» e «testo».")
        if not _turno_valido(voce["turno"]):
            raise ErroreArchivio(f"nel messaggio {numero} «turno» deve essere il numero del turno (0 o più).")
        if (voce["turno"], voce["chi"]) in turni:
            raise ErroreArchivio(f"il messaggio {numero} ripete un turno già presente nella copia.")
        turni.add((voce["turno"], voce["chi"]))
        corrispondenza = _QUANDO.match(voce["quando"]) if isinstance(voce["quando"], str) else None
        if corrispondenza is None:
            raise ErroreArchivio(f"il messaggio {numero} ha una data e ora non valida: serve la forma "
                                 "dell'archivio, per esempio «Fri 2026-10-09 17:46».")
        giorno, ore, minuti = corrispondenza.groups()
        try:
            momento = datetime.fromisoformat(f"{giorno}T{ore}:{minuti}").replace(tzinfo=fuso)
        except ValueError:
            raise ErroreArchivio(f"il messaggio {numero} ha una data che non esiste: «{voce['quando']}».")
        if voce["chi"] not in CHI:
            raise ErroreArchivio(f"nel messaggio {numero} «chi» deve essere «utente» oppure «claude».")
        if not isinstance(voce["testo"], str):
            raise ErroreArchivio(f"nel messaggio {numero} «testo» deve essere un testo.")
        testo = segni_veri(voce["testo"])
        testo, tolti = togli_avvisi(testo) if voce["chi"] == "utente" else (testo, 0)
        messaggi.append((voce["turno"], momento.isoformat(), voce["chi"], testo, tolti))
    messaggi.sort(key=lambda m: (m[0], CHI.index(m[2])))
    return chat, messaggi


def copia(config: Configurazione, contenuto: bytes) -> Esito:
    """Aggiunge ai file dell'archivio i messaggi nuovi. Non scrive niente se la copia non è valida.

    La copia si controlla prima di prendere il blocco del quaderno (vedi ``blocco``); poi, con il
    blocco, si leggono i messaggi già presenti e si aggiungono quelli nuovi.
    """
    if config.file_archivio is None:
        raise ErroreArchivio("la configurazione non ha la sezione [archivio]: serve la configurazione per la chat.")
    chat, messaggi = _leggi_copia(contenuto)
    with blocco.blocco(config.cartella_quaderno, crea=True):
        return _aggiungi(config, chat, messaggi)


def _aggiungi(config: Configurazione, chat, messaggi) -> Esito:
    file_per = {"utente": config.file_archivio, "claude": config.file_diario_chat}
    presenti = {
        "utente": {(m.chat, m.turno): m for m in leggi_messaggi(config)},
        "claude": {(m.chat, m.turno): m for m in leggi_risposte(config)},
    }
    # Per sapere se una risposta segue un messaggio privato: i messaggi dell'utente di questa chat,
    # già copiati e nuovi, per numero di turno.
    privati_della_chat = {m.turno: m.testo is None for m in presenti["utente"].values() if m.chat == chat}
    privati_della_chat.update({turno: testo.lstrip().startswith(config.prefisso_privato)
                               for turno, _, chi, testo, _ in messaggi if chi == "utente"})

    def privato_prima_di(turno: int) -> bool:
        precedenti = [t for t in privati_della_chat if t <= turno]
        return bool(precedenti) and privati_della_chat[max(precedenti)]

    conti = Esito()
    righe = {"utente": [], "claude": []}
    for turno, quando, chi, testo, tolti in messaggi:
        conti = replace(conti, avvisi_tolti=conti.avvisi_tolti + tolti)
        chiave = (chat, turno)
        da_scrivere = ometti_codice(testo) if chi == "claude" and config.archivio_ometti_codice else testo
        if chiave in presenti[chi]:
            vecchio = presenti[chi][chiave]
            conti = replace(conti, gia_presenti=conti.gia_presenti + 1)
            if vecchio.testo is not None and vecchio.testo != da_scrivere:
                conti = replace(conti, diversi=conti.diversi + 1)
            continue
        voce: dict[str, object] = {"quando": quando, "chat": chat, "turno": turno}
        if chi == "utente" and testo.lstrip().startswith(config.prefisso_privato):
            voce["privato"] = DICITURA_PRIVATO
            conti = replace(conti, privati=conti.privati + 1)
        elif chi == "claude" and privato_prima_di(turno):
            voce["privato"] = DICITURA_RISPOSTA_PRIVATA
            conti = replace(conti, risposte_private=conti.risposte_private + 1)
        else:
            voce["testo"] = da_scrivere
            conti = replace(conti, **{chi: getattr(conti, chi) + 1})
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
    """Per «controlla»: le coppie (riga, riga già vista) con stessa chat e stesso turno, e le righe non valide."""
    if file is None or not file.is_file():
        return [], []
    testo = file.read_bytes().decode("utf-8", errors="replace")
    righe = testo.split("\n")
    if righe and righe[-1] == "":
        righe = righe[:-1]
    viste: dict[tuple[str, int], int] = {}
    doppioni, rovinate = [], []
    for numero, riga in enumerate(righe, start=1):
        voce = voce_valida(riga)
        if voce is None:
            rovinate.append(numero)
            continue
        chiave = (voce.chat, voce.turno)
        if chiave in viste:
            doppioni.append((numero, viste[chiave]))
        else:
            viste[chiave] = numero
    return doppioni, rovinate
