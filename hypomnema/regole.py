"""Le regole fisse dello sportello.

Questi valori non sono impostazioni: sono i principi di Hypomnema
(provenienza sempre, l'incerto resta incerto, le decisioni sono dell'utente).
Per questo stanno nel codice e non nel file di configurazione.
"""

import re
from datetime import date, datetime

from hypomnema.nota import TITOLO_CONTESTO, Nota
from hypomnema.testimone import Messaggio, Ritrovamento, trova_citazione

CAMPI_OBBLIGATORI = ("data", "fonte", "autore", "tipo", "natura", "testo")
CAMPI_FACOLTATIVI = ("conferma_di", "citazione", "contesto", "da_risposta")
# Campi che possono andare a capo: tutti gli altri devono stare su una riga.
CAMPI_SU_PIU_RIGHE = ("testo", "citazione", "contesto")
CAMPI_AMMESSI = CAMPI_OBBLIGATORI + CAMPI_FACOLTATIVI

AUTORI = ("utente", "claude")
TIPI = ("osservata", "dichiarata", "dedotta")
NATURE = ("idea", "decisione", "fatto", "discorso aperto")

# Perché ogni campo obbligatorio serve: compare nel motivo del rifiuto.
PERCHE_SERVE = {
    "data": "ogni nota deve dire quando è stata detta o osservata",
    "fonte": "ogni nota deve dire da dove viene",
    "autore": "ogni nota deve dire chi l'ha detta (utente o claude)",
    "tipo": "ogni nota deve dire se è osservata, dichiarata o dedotta",
    "natura": "ogni nota deve dire se è un'idea, una decisione, un fatto o un discorso aperto",
    "testo": "una nota senza testo non dice niente",
}

FORMATO_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?)?$")


def _elenco(valori: tuple[str, ...]) -> str:
    virgolettati = [f"«{v}»" for v in valori]
    return ", ".join(virgolettati[:-1]) + " o " + virgolettati[-1]


def _data_valida(valore: str) -> bool:
    if not FORMATO_DATA.match(valore):
        return False
    try:
        if "T" in valore:
            datetime.fromisoformat(valore)
        else:
            date.fromisoformat(valore)
    except ValueError:
        return False
    return True


def controlla(
    proposta: dict, note_esistenti: list[Nota], messaggi: list[Messaggio] | None, segno: str,
    risposte: list[Messaggio] | None = None,
) -> list[str]:
    """Restituisce i motivi di rifiuto, in ordine fisso. Lista vuota = nota accettabile.

    ``messaggi`` sono i messaggi registrati dal testimone, oppure None se il testimone è spento.
    ``segno`` è il segno di citazione del testimone.
    ``risposte`` sono le risposte di Claude registrate, oppure None se quel testimone è spento.
    """
    motivi: list[str] = []

    for campo in proposta:
        if campo not in CAMPI_AMMESSI:
            motivi.append(
                f"il campo «{campo}» non è previsto: i campi ammessi sono "
                + ", ".join(CAMPI_AMMESSI) + "."
            )

    valori: dict[str, str] = {}
    for campo in CAMPI_AMMESSI:
        if campo not in proposta or proposta[campo] is None:
            if campo in CAMPI_OBBLIGATORI:
                motivi.append(f"manca il campo «{campo}»: {PERCHE_SERVE[campo]}.")
            continue
        valore = proposta[campo]
        if not isinstance(valore, str):
            motivi.append(f"il campo «{campo}» deve essere un testo tra virgolette.")
            continue
        valore = valore.strip()
        if not valore:
            if campo in CAMPI_OBBLIGATORI:
                motivi.append(f"il campo «{campo}» è vuoto: {PERCHE_SERVE[campo]}.")
            else:
                motivi.append(f"il campo «{campo}» è vuoto: se non serve, toglilo.")
            continue
        if campo not in CAMPI_SU_PIU_RIGHE and ("\n" in valore or "\r" in valore):
            motivi.append(f"il campo «{campo}» deve stare su una riga sola.")
            continue
        valori[campo] = valore

    if "data" in valori and not _data_valida(valori["data"]):
        motivi.append(
            f"la data «{valori['data']}» non è valida: scrivila come AAAA-MM-GG "
            "(per esempio 2026-01-15), se vuoi con l'ora (2026-01-15T10:30)."
        )
    for campo, ammessi in (("autore", AUTORI), ("tipo", TIPI), ("natura", NATURE)):
        if campo in valori and valori[campo] not in ammessi:
            motivi.append(
                f"il valore «{valori[campo]}» non è ammesso per «{campo}»: "
                f"deve essere {_elenco(ammessi)}."
            )

    natura = valori.get("natura")
    if natura == "decisione":
        if valori.get("autore") == "claude":
            motivi.append(
                "una nota scritta da Claude non può essere una decisione: le decisioni "
                "le prende solo l'utente. Se è una proposta di Claude, salvala come idea."
            )
        if "tipo" in valori and valori["tipo"] != "dichiarata" and valori["tipo"] in TIPI:
            motivi.append(
                "una decisione deve essere dichiarata dall'utente: non può essere "
                f"«{valori['tipo']}»."
            )

    if "conferma_di" in valori:
        riferimento = valori["conferma_di"]
        if natura is not None and natura != "decisione":
            motivi.append(
                "il campo «conferma_di» si usa solo per le decisioni che confermano un'idea."
            )
        idea = next((n for n in note_esistenti if n.id == riferimento), None)
        if idea is None:
            motivi.append(
                f"la nota «{riferimento}» indicata in «conferma_di» non esiste nel quaderno."
            )
        elif idea.natura != "idea":
            motivi.append(
                f"la nota «{riferimento}» ha natura «{idea.natura}», non è un'idea: "
                "si può confermare come decisione solo un'idea."
            )

    # Parole dell'utente e parole di Claude non si mescolano: in una nota dell'utente
    # il testo sono le sue parole e ciò che aggiunge Claude va in "contesto"; in una nota
    # di Claude tutto è di Claude e le parole dell'utente su cui si basa vanno in "citazione".
    autore = valori.get("autore")
    if autore == "utente" and "citazione" in proposta:
        motivi.append(
            "in una nota con autore «utente» le sue parole vanno nel campo «testo»: "
            "il campo «citazione» si usa solo nelle note di Claude."
        )
    if autore == "claude" and "contesto" in proposta:
        motivi.append(
            "il campo «contesto» si usa solo nelle note con autore «utente», per tenere le "
            "spiegazioni di Claude separate dalle parole dell'utente: in una nota di Claude "
            "tutto il testo è già di Claude."
        )
    # Una nota di Claude che salva un pezzo di una sua risposta: "da_risposta": "sì".
    if "da_risposta" in valori:
        if valori["da_risposta"] != "sì":
            motivi.append("il campo «da_risposta» può valere solo «sì»: se la nota non viene da una "
                          "risposta di Claude, toglilo.")
        if autore == "utente":
            motivi.append(
                "il campo «da_risposta» si usa solo nelle note di Claude: se l'utente fa sua una "
                "risposta di Claude, la nota è dell'utente e la provenienza va nella «fonte»."
            )
        if "citazione" in valori:
            motivi.append("una nota non può avere insieme «da_risposta» e «citazione»: viene da una "
                          "risposta di Claude oppure dalle parole dell'utente, non da tutte e due.")
        if (
            risposte is not None and autore == "claude" and valori["da_risposta"] == "sì"
            and "testo" in valori and trova_citazione(risposte, valori["testo"], segno) is None
        ):
            motivi.append(
                "il testo non si trova, parola per parola, in nessuna risposta di Claude registrata: "
                "copia il pezzo esatto della tua risposta. Nel file delle risposte i blocchi di codice "
                "possono essere sostituiti dalla loro impronta: se il pezzo contiene codice, salvalo "
                "senza il codice."
            )

    for campo in ("testo", "contesto"):
        if campo in valori and TITOLO_CONTESTO in (r.rstrip("\r") for r in valori[campo].split("\n")):
            motivi.append(
                f"il campo «{campo}» non può contenere la riga «{TITOLO_CONTESTO}»: "
                "è riservata al formato della nota."
            )

    # Regola del testimone: con il testimone acceso, il testo di una nota dell'utente
    # e la citazione di una nota di Claude devono comparire parola per parola in un messaggio.
    if messaggi is not None:
        if autore == "utente" and "testo" in valori and trova_citazione(messaggi, valori["testo"], segno) is None:
            motivi.append(
                "il testo non si trova, parola per parola, in nessun messaggio registrato dal "
                "testimone: in una nota dell'utente il testo sono le sue parole esatte; "
                "spiegazioni e riassunti di Claude vanno nel campo «contesto»."
            )
        if autore == "claude" and "citazione" in valori and trova_citazione(messaggi, valori["citazione"], segno) is None:
            motivi.append(
                "la citazione non si trova, parola per parola, in nessun messaggio registrato "
                "dal testimone: copia le parole esatte dell'utente, senza riassumerle o cambiarle."
            )

    return motivi


def _dicitura(cosa: str, trovato: Ritrovamento) -> str:
    if trovato.riportata:
        return f"citazione riportata dall'utente, trovata nel messaggio del {trovato.messaggio.quando}"
    return f"{cosa} nel messaggio del {trovato.messaggio.quando}"


# Perché manca la verifica: il testimone c'è ma è spento, oppure siamo nella chat di Claude,
# dove il testimone non esiste. Fa parte della dicitura scritta nella nota.
def _riscontro(copiati: list[Messaggio] | None, testo: str, segno: str, cosa: str, che: str) -> str | None:
    """La dicitura del livello «riscontrato sull'archivio della chat», oppure None se non si trova."""
    if not copiati:
        return None
    trovato = trova_citazione(copiati, testo, segno)
    if trovato is None:
        return None
    m = trovato.messaggio
    return f"{cosa} sull'archivio della chat {m.chat}, {che} del {m.quando} (copiato da Claude)"


SENZA_TESTIMONE = "testimone spento"
SENZA_TESTIMONE_IN_CHAT = "chat, senza testimone"


SENZA_RISPOSTE = "registro delle risposte spento"
# Note prese mentre l'utente ha messo in pausa i testimoni (/hypomnema:pausa).
SENZA_TESTIMONE_IN_PAUSA = "testimoni in pausa"


def verifica(
    autore: str, testo: str, citazione: str | None, messaggi: list[Messaggio] | None, segno: str,
    in_chat: bool = False, da_risposta: bool = False, risposte: list[Messaggio] | None = None,
    in_pausa: bool = False, archivio: list[Messaggio] | None = None, diario_chat: list[Messaggio] | None = None,
) -> str | None:
    """La dicitura "verifica" da scrivere nella nota accettata (None = nessuna dicitura).

    Tre livelli: verificato dal testimone («trovato»), riscontrato sull'archivio della chat
    («riscontrato», con l'indirizzo della chat), non verificato.
    """
    if da_risposta:
        riscontro = _riscontro(diario_chat, testo, segno, "testo riscontrato", "risposta")
        if risposte is None and riscontro:
            return riscontro
        if risposte is None:
            perche = SENZA_TESTIMONE_IN_CHAT if in_chat else SENZA_TESTIMONE_IN_PAUSA if in_pausa else SENZA_RISPOSTE
            return f"risposta non verificata ({perche})"
        trovato = trova_citazione(risposte, testo, segno)
        return f"testo trovato nella risposta di Claude del {trovato.messaggio.quando}"
    if messaggi is None:
        perche = SENZA_TESTIMONE_IN_CHAT if in_chat else SENZA_TESTIMONE_IN_PAUSA if in_pausa else SENZA_TESTIMONE
        if autore == "utente":
            return _riscontro(archivio, testo, segno, "testo riscontrato", "messaggio") or f"autore non verificato ({perche})"
        if citazione is not None:
            return (_riscontro(archivio, citazione, segno, "citazione riscontrata", "messaggio")
                    or f"citazione non verificata ({perche})")
        return None
    if autore == "utente":
        return _dicitura("testo trovato", trova_citazione(messaggi, testo, segno))
    if citazione is not None:
        return _dicitura("citazione trovata", trova_citazione(messaggi, citazione, segno))
    return None
