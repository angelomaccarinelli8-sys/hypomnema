"""Le regole fisse dello sportello.

Questi valori non sono impostazioni: sono i principi di Hypomnema
(provenienza sempre, l'incerto resta incerto, le decisioni sono dell'utente).
Per questo stanno nel codice e non nel file di configurazione.
"""

import re
from datetime import date, datetime

from hypomnema.nota import Nota
from hypomnema.testimone import Messaggio, trova_citazione

CAMPI_OBBLIGATORI = ("data", "fonte", "autore", "tipo", "natura", "testo")
CAMPI_FACOLTATIVI = ("conferma_di", "citazione")
# Campi che possono andare a capo: tutti gli altri devono stare su una riga.
CAMPI_SU_PIU_RIGHE = ("testo", "citazione")
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
    proposta: dict, note_esistenti: list[Nota], messaggi: list[Messaggio] | None
) -> list[str]:
    """Restituisce i motivi di rifiuto, in ordine fisso. Lista vuota = nota accettabile.

    ``messaggi`` sono i messaggi registrati dal testimone, oppure None se il testimone è spento.
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

    # Regola del testimone: con il testimone acceso, una nota dell'utente deve citare
    # parola per parola un messaggio registrato. Se c'è una citazione, va sempre trovata.
    if messaggi is not None:
        if valori.get("autore") == "utente" and proposta.get("citazione") is None:
            motivi.append(
                "manca il campo «citazione»: una nota con autore «utente» deve riportare, "
                "parola per parola, le parole dell'utente registrate dal testimone."
            )
        if "citazione" in valori and trova_citazione(messaggi, valori["citazione"]) is None:
            motivi.append(
                "la citazione non si trova, parola per parola, in nessun messaggio registrato "
                "dal testimone: copia le parole esatte dell'utente, senza riassumerle o cambiarle."
            )

    return motivi


def verifica(autore: str, citazione: str | None, messaggi: list[Messaggio] | None) -> str | None:
    """La dicitura "verifica" da scrivere nella nota accettata (None = nessuna dicitura)."""
    if messaggi is None:
        if autore == "utente":
            return "autore non verificato (testimone spento)"
        if citazione is not None:
            return "citazione non verificata (testimone spento)"
        return None
    if citazione is None:
        return None
    trovato = trova_citazione(messaggi, citazione)
    return f"citazione trovata nel messaggio del {trovato.quando}"
