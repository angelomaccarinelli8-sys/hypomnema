"""Le regole fisse dello sportello.

Questi valori non sono impostazioni: sono i principi di Hypomnema
(provenienza sempre, l'incerto resta incerto, le decisioni sono dell'utente).
Per questo stanno nel codice e non nel file di configurazione.

Dalla versione 0.5.0 la struttura è in inglese: i nomi dei campi, i valori e i motivi di rifiuto
(che legge Claude). I nomi e i valori italiani di prima valgono per sempre: una proposta può usare
«autore: utente» o «author: user», e la nota nuova si scrive comunque in inglese.
"""

import re
from datetime import date, datetime

from hypomnema.nota import TITOLI_CONTESTO, VALORI_ITALIANI, Nota, chiuse, numeri
from hypomnema.testimone import Messaggio, Ritrovamento, trova_citazione

CAMPI_OBBLIGATORI = ("date", "source", "author", "knowledge", "kind", "text")
CAMPI_FACOLTATIVI = (
    "priority", "confirms", "corrects", "done", "remind", "quote", "context", "from_reply",
)
# Campi che possono andare a capo: tutti gli altri devono stare su una riga.
CAMPI_SU_PIU_RIGHE = ("text", "quote", "context")
CAMPI_AMMESSI = CAMPI_OBBLIGATORI + CAMPI_FACOLTATIVI

# I nomi italiani dei campi, accettati per sempre nelle proposte.
NOMI_ITALIANI = {
    "data": "date", "fonte": "source", "autore": "author", "tipo": "knowledge", "natura": "kind",
    "testo": "text", "priorità": "priority", "conferma_di": "confirms", "corregge": "corrects",
    "riprendere_il": "remind", "citazione": "quote", "contesto": "context", "da_risposta": "from_reply",
}
# I valori italiani, accettati per sempre nelle proposte (gli stessi che si leggono nelle note vecchie).
VALORI_ITALIANI_PER_CAMPO = {
    "author": VALORI_ITALIANI["autore"], "knowledge": VALORI_ITALIANI["tipo"], "kind": VALORI_ITALIANI["natura"],
    "priority": VALORI_ITALIANI["priorita"], "from_reply": VALORI_ITALIANI["da_risposta"],
}

AUTORI = ("user", "claude")
TIPI = ("stated", "observed", "inferred")
NATURE = ("fact", "idea", "decision", "open", "todo")
PRIORITA = ("high", "normal", "low")
VALORI_AMMESSI = {"author": AUTORI, "knowledge": TIPI, "kind": NATURE, "priority": PRIORITA}
# Cosa può diventare una questione chiusa: la natura della nota che la chiude.
NATURE_CHE_CHIUDONO = ("decision", "todo", "fact", "idea")

# Perché ogni campo obbligatorio serve: compare nel motivo del rifiuto.
PERCHE_SERVE = {
    "date": "every note must say when it was said or observed",
    "source": "every note must say where it comes from",
    "author": "every note must say who said it (user or claude)",
    "knowledge": "every note must say whether it is stated, observed or inferred",
    "kind": "every note must say whether it is a fact, an idea, a decision, an open question or a todo",
    "text": "a note without text says nothing",
}

FORMATO_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?)?$")
FORMATO_GIORNO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _elenco(valori: tuple[str, ...]) -> str:
    virgolettati = [f"«{v}»" for v in valori]
    return ", ".join(virgolettati[:-1]) + " or " + virgolettati[-1]


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


def in_inglese(proposta: dict) -> tuple[dict, list[str]]:
    """La proposta con i nomi dei campi in inglese, e i motivi di rifiuto per i nomi sbagliati o doppi.

    I valori italiani di autore, tipo, natura, priorità e da_risposta diventano quelli inglesi.
    """
    tradotta: dict = {}
    motivi: list[str] = []
    nomi_usati: dict[str, str] = {}
    for nome, valore in proposta.items():
        campo = NOMI_ITALIANI.get(nome, nome)
        if campo not in CAMPI_AMMESSI:
            motivi.append(
                f"the field «{nome}» is not allowed: the allowed fields are "
                + ", ".join(CAMPI_AMMESSI) + " (the Italian names of before are accepted too)."
            )
            continue
        if campo in tradotta:
            motivi.append(f"the field «{campo}» appears twice (as «{nomi_usati[campo]}» and as «{nome}»): "
                          "it must appear only once.")
            continue
        nomi_usati[campo] = nome
        if isinstance(valore, str) and campo in VALORI_ITALIANI_PER_CAMPO:
            valore = VALORI_ITALIANI_PER_CAMPO[campo].get(valore.strip(), valore)
        tradotta[campo] = valore
    return tradotta, motivi


def controlla(
    proposta: dict, note_esistenti: list[Nota], messaggi: list[Messaggio] | None, segno: str,
    risposte: list[Messaggio] | None = None,
) -> list[str]:
    """Restituisce i motivi di rifiuto, in ordine fisso. Lista vuota = nota accettabile.

    ``proposta`` ha già i nomi dei campi in inglese (vedi ``in_inglese``).
    ``messaggi`` sono i messaggi registrati dal testimone, oppure None se il testimone è spento.
    ``segno`` è il segno di citazione del testimone.
    ``risposte`` sono le risposte di Claude registrate, oppure None se quel testimone è spento.
    """
    motivi: list[str] = []

    valori: dict[str, str] = {}
    for campo in CAMPI_AMMESSI:
        if campo not in proposta or proposta[campo] is None:
            if campo in CAMPI_OBBLIGATORI:
                motivi.append(f"the field «{campo}» is missing: {PERCHE_SERVE[campo]}.")
            continue
        valore = proposta[campo]
        if not isinstance(valore, str):
            motivi.append(f"the field «{campo}» must be text in quotes.")
            continue
        valore = valore.strip()
        if not valore:
            if campo in CAMPI_OBBLIGATORI:
                motivi.append(f"the field «{campo}» is empty: {PERCHE_SERVE[campo]}.")
            else:
                motivi.append(f"the field «{campo}» is empty: if it is not needed, remove it.")
            continue
        if campo not in CAMPI_SU_PIU_RIGHE and ("\n" in valore or "\r" in valore):
            motivi.append(f"the field «{campo}» must stay on one line.")
            continue
        valori[campo] = valore

    if "date" in valori and not _data_valida(valori["date"]):
        motivi.append(
            f"the date «{valori['date']}» is not valid: write it as YYYY-MM-DD "
            "(for example 2026-01-15), optionally with the time (2026-01-15T10:30)."
        )
    for campo, ammessi in VALORI_AMMESSI.items():
        if campo in valori and valori[campo] not in ammessi:
            motivi.append(f"the value «{valori[campo]}» is not allowed for «{campo}»: it must be {_elenco(ammessi)}.")

    autore = valori.get("author")
    natura = valori.get("kind")
    per_numero = {n.id: n for n in note_esistenti}
    if natura == "decision":
        if autore == "claude":
            motivi.append(
                "a note written by Claude cannot be a decision: only the user makes decisions. "
                "If it is Claude's proposal, save it as an idea."
            )
        if valori.get("knowledge") in TIPI and valori["knowledge"] != "stated":
            motivi.append(f"a decision must be stated by the user: it cannot be «{valori['knowledge']}».")

    if "confirms" in valori:
        riferimento = valori["confirms"]
        if natura is not None and natura != "decision":
            motivi.append("the field «confirms» is only for decisions that confirm an idea.")
        idea = per_numero.get(riferimento)
        if idea is None:
            motivi.append(f"note «{riferimento}» named in «confirms» does not exist in the notebook.")
        elif idea.natura != "idea":
            motivi.append(f"note «{riferimento}» is a «{idea.natura}», not an idea: "
                          "only an idea can be confirmed as a decision.")

    if "corrects" in valori and valori["corrects"] not in per_numero:
        motivi.append(f"note «{valori['corrects']}» named in «corrects» does not exist in the notebook.")
    if "remind" in valori:
        giorno = valori["remind"]
        valida = bool(FORMATO_GIORNO.match(giorno))
        if valida:
            try:
                date.fromisoformat(giorno)
            except ValueError:
                valida = False
        if not valida:
            motivi.append(f"the date «{giorno}» in «remind» is not valid: write only the day, as YYYY-MM-DD "
                          "(for example 2026-01-20).")
    if "done" in valori:
        motivi += _controlla_chiusura(valori, autore, natura, per_numero, note_esistenti)

    if "priority" in valori and autore == "claude":
        motivi.append("only the user can set «priority»: Claude can suggest a priority in the text of "
                      "one of its idea notes.")

    # Parole dell'utente e parole di Claude non si mescolano: in una nota dell'utente
    # il testo sono le sue parole e ciò che aggiunge Claude va in "context"; in una nota
    # di Claude tutto è di Claude e le parole dell'utente su cui si basa vanno in "quote".
    if autore == "user" and "quote" in proposta:
        motivi.append("in a note with author «user» the user's words go in the field «text»: "
                      "the field «quote» is only for Claude's notes.")
    if autore == "claude" and "context" in proposta:
        motivi.append(
            "the field «context» is only for notes with author «user», to keep Claude's explanations "
            "apart from the user's words: in a note by Claude all the text is already Claude's."
        )
    # Una nota di Claude che salva un pezzo di una sua risposta: "from_reply": "yes".
    if "from_reply" in valori:
        if valori["from_reply"] != "yes":
            motivi.append("the field «from_reply» can only be «yes»: if the note does not come from one of "
                          "Claude's replies, remove it.")
        if autore == "user":
            motivi.append(
                "the field «from_reply» is only for Claude's notes: if the user makes one of Claude's "
                "replies their own, the note is the user's and where it comes from goes in «source»."
            )
        if "quote" in valori:
            motivi.append("a note cannot have both «from_reply» and «quote»: it comes either from one of "
                          "Claude's replies or from the user's words, not from both.")
        if (
            risposte is not None and autore == "claude" and valori["from_reply"] == "yes"
            and "text" in valori and trova_citazione(risposte, valori["text"], segno) is None
        ):
            motivi.append(
                "the text is not found, word for word, in any recorded reply of Claude: copy the exact "
                "piece of your reply. In the replies file code blocks may be replaced by their "
                "fingerprint: if the piece contains code, save it without the code."
            )

    for campo in ("text", "context"):
        righe = [r.rstrip("\r") for r in valori.get(campo, "").split("\n")]
        for titolo in TITOLI_CONTESTO:
            if campo in valori and titolo in righe:
                motivi.append(f"the field «{campo}» cannot contain the line «{titolo}»: "
                              "it is reserved for the note format.")

    # Regola del testimone: con il testimone acceso, il testo di una nota dell'utente
    # e la citazione di una nota di Claude devono comparire parola per parola in un messaggio.
    if messaggi is not None:
        if autore == "user" and "text" in valori and trova_citazione(messaggi, valori["text"], segno) is None:
            motivi.append(
                "the text is not found, word for word, in any message recorded by the witness: in a "
                "note by the user the text is their exact words; Claude's explanations and summaries "
                "go in the field «context»."
            )
        if autore == "claude" and "quote" in valori and trova_citazione(messaggi, valori["quote"], segno) is None:
            motivi.append(
                "the quote is not found, word for word, in any message recorded by the witness: copy the "
                "user's exact words, without summarising or changing them."
            )

    return motivi


def _controlla_chiusura(valori, autore, natura, per_numero, note_esistenti) -> list[str]:
    """Le regole di «done»: chiude open, todo e promemoria, una volta sola."""
    elenco = numeri(valori["done"])
    if any(not n.isdigit() for n in elenco):
        return ["the field «done» must list note numbers separated by commas, for example «0012, 0015»."]
    motivi = []
    if natura == "open":
        motivi.append("a note that closes something cannot be «open»: its kind says what the question "
                      "became (decision, todo, fact or idea).")
    gia_chiuse = chiuse(note_esistenti)
    visti = set()
    for numero in elenco:
        if numero in visti:
            motivi.append(f"note «{numero}» is listed twice in «done».")
            continue
        visti.add(numero)
        nota = per_numero.get(numero)
        if nota is None:
            motivi.append(f"note «{numero}» named in «done» does not exist in the notebook.")
            continue
        if nota.natura not in ("open", "todo") and nota.riprendere_il is None:
            consiglio = "«corrects» (or «confirms», for an idea)" if nota.natura == "idea" else "«corrects»"
            motivi.append(
                f"note «{numero}» is a «{nota.natura}»: «done» closes only open, todo and reminder notes "
                f"(with «remind»). A fact, a decision or an idea is not closed: write a new note with {consiglio}."
            )
            continue
        if nota.natura == "open" and autore != "user":
            motivi.append(f"only the user can close an open note («{numero}»): Claude can suggest it, but "
                          "the closing note must have author «user».")
        if numero in gia_chiuse:
            motivi.append(f"note «{numero}» is already closed by note «{gia_chiuse[numero]}».")
    return motivi


def _dicitura(cosa: str, trovato: Ritrovamento) -> str:
    if trovato.riportata:
        return f"quote reported by the user, found in the message of {trovato.messaggio.quando}"
    return f"{cosa} in the message of {trovato.messaggio.quando}"


def _riscontro(copiati: list[Messaggio] | None, testo: str, segno: str, cosa: str, che: str) -> str | None:
    """La dicitura del livello «riscontrato sull'archivio della chat» (in inglese «matched»), o None."""
    if not copiati:
        return None
    trovato = trova_citazione(copiati, testo, segno)
    if trovato is None:
        return None
    m = trovato.messaggio
    return f"{cosa} in the chat archive {m.chat}, {che} of turn {m.turno} ({m.quando}, copied by Claude)"


# Perché manca la verifica: il testimone c'è ma è spento, oppure siamo nella chat di Claude,
# dove il testimone non esiste, oppure l'utente ha messo in pausa i testimoni. Fa parte della
# dicitura scritta nella nota.
SENZA_TESTIMONE = "witness off"
SENZA_TESTIMONE_IN_CHAT = "chat, no witness"
SENZA_RISPOSTE = "replies witness off"
SENZA_TESTIMONE_IN_PAUSA = "witnesses paused"


def verifica(
    autore: str, testo: str, citazione: str | None, messaggi: list[Messaggio] | None, segno: str,
    in_chat: bool = False, da_risposta: bool = False, risposte: list[Messaggio] | None = None,
    in_pausa: bool = False, archivio: list[Messaggio] | None = None, diario_chat: list[Messaggio] | None = None,
) -> str | None:
    """La dicitura "verification" da scrivere nella nota accettata (None = nessuna dicitura).

    Tre livelli: verificato dal testimone («found»), riscontrato sull'archivio della chat
    («matched», con l'indirizzo della chat), non verificato («not verified»).
    """
    if da_risposta:
        riscontro = _riscontro(diario_chat, testo, segno, "text matched", "reply")
        if risposte is None and riscontro:
            return riscontro
        if risposte is None:
            perche = SENZA_TESTIMONE_IN_CHAT if in_chat else SENZA_TESTIMONE_IN_PAUSA if in_pausa else SENZA_RISPOSTE
            return f"reply not verified ({perche})"
        trovato = trova_citazione(risposte, testo, segno)
        return f"text found in Claude's reply of {trovato.messaggio.quando}"
    if messaggi is None:
        perche = SENZA_TESTIMONE_IN_CHAT if in_chat else SENZA_TESTIMONE_IN_PAUSA if in_pausa else SENZA_TESTIMONE
        if autore == "user":
            return _riscontro(archivio, testo, segno, "text matched", "message") or f"author not verified ({perche})"
        if citazione is not None:
            return (_riscontro(archivio, citazione, segno, "quote matched", "message")
                    or f"quote not verified ({perche})")
        return None
    if autore == "user":
        return _dicitura("text found", trova_citazione(messaggi, testo, segno))
    if citazione is not None:
        return _dicitura("quote found", trova_citazione(messaggi, citazione, segno))
    return None
