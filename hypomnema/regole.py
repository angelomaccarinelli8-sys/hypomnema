"""Le regole fisse dello sportello.

Questi valori non sono impostazioni: sono i principi di Hypomnema
(provenienza sempre, l'incerto resta incerto, le decisioni sono dell'utente).
Per questo stanno nel codice e non nel file di configurazione.

Dalla versione 0.5.0 la struttura è in inglese: i nomi dei campi, i valori e i motivi di rifiuto
(che legge Claude). I nomi e i valori italiani di prima valgono per sempre: una proposta può usare
«autore: utente» o «author: user», e la nota nuova si scrive comunque in inglese.

Dalla versione 0.6.0 ogni cambiamento è una versione nuova della nota (vedi ``versioni``): le
proposte con ``corrects``, ``updates``, ``done`` o ``reopens`` cambiano sempre l'ultima versione.
"""

import re
from dataclasses import replace
from datetime import date, datetime

from hypomnema import etichette as lista_etichette, versioni
from hypomnema.nota import (
    TITOLI_CONTESTO, TITOLO_CAMBIO, TITOLO_CONTESTO_CAMBIO, TITOLO_DA_NOTA, VALORI_ITALIANI, Nota, numeri,
)
from hypomnema.testimone import Messaggio, Ritrovamento, trova_citazione

CAMPI_OBBLIGATORI = ("date", "source", "author", "knowledge", "kind", "text")
CAMPI_FACOLTATIVI = (
    "priority", "confirms", "corrects", "updates", "done", "reopens", "remind", "quote", "context", "from_reply",
    "who", "about", "integrates", "from_note", "cancels",
)
# Le etichette (dalla 0.7.0): CHI (who) e COSA (about), dalla lista del file etichette.toml del quaderno.
CAMPI_ETICHETTE = ("who", "about")
# I campi che cambiano una nota che c'è già: ognuno crea una versione nuova. Uno per proposta.
CAMPI_CAMBIAMENTO = ("corrects", "updates", "done", "reopens", "integrates", "cancels")
# Campi che possono andare a capo: tutti gli altri devono stare su una riga.
CAMPI_SU_PIU_RIGHE = ("text", "quote", "context")
CAMPI_AMMESSI = CAMPI_OBBLIGATORI + CAMPI_FACOLTATIVI

# I nomi italiani dei campi, accettati per sempre nelle proposte.
NOMI_ITALIANI = {
    "data": "date", "fonte": "source", "autore": "author", "tipo": "knowledge", "natura": "kind",
    "testo": "text", "priorità": "priority", "conferma_di": "confirms", "corregge": "corrects",
    "aggiorna": "updates", "riapre": "reopens", "integra": "integrates", "da_nota": "from_note",
    "annulla": "cancels",
    "riprendere_il": "remind", "citazione": "quote", "contesto": "context", "da_risposta": "from_reply",
    "chi": "who", "cosa": "about",
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
    risposte: list[Messaggio] | None = None, segno_chiusa: str = versioni.SEGNO_CHIUSA,
    etichette: "lista_etichette.Etichette | None" = None,
) -> list[str]:
    """Restituisce i motivi di rifiuto, in ordine fisso. Lista vuota = nota accettabile.

    ``proposta`` ha già i nomi dei campi in inglese (vedi ``in_inglese``).
    ``messaggi`` sono i messaggi registrati dal testimone, oppure None se il testimone è spento.
    ``segno`` è il segno di citazione del testimone.
    ``risposte`` sono le risposte di Claude registrate, oppure None se quel testimone è spento.
    ``etichette`` è la lista del file etichette.toml del quaderno, oppure None se il file non c'è.
    """
    motivi: list[str] = []
    # In un cambiamento «kind» è facoltativo: se manca, la natura resta quella dell'ultima versione.
    cambiamento = any(proposta.get(c) is not None for c in CAMPI_CAMBIAMENTO)
    # Dalla 0.9.0: integrare un'altra nota (integrates + from_note) non ha testo: si copia quello dell'altra nota.
    integra_nota = proposta.get("integrates") is not None and proposta.get("from_note") is not None

    valori: dict[str, str] = {}
    for campo in CAMPI_AMMESSI:
        if campo not in proposta or proposta[campo] is None:
            if campo in CAMPI_OBBLIGATORI and not (campo == "kind" and cambiamento) \
                    and not (campo == "text" and integra_nota):
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
    quaderno = versioni.Quaderno(note_esistenti)
    if natura == "decision":
        if autore == "claude" and not cambiamento:
            motivi.append(
                "a note written by Claude cannot be a decision: only the user makes decisions. "
                "If it is Claude's proposal, save it as an idea."
            )
        if valori.get("knowledge") in TIPI and valori["knowledge"] != "stated":
            motivi.append(f"a decision must be stated by the user: it cannot be «{valori['knowledge']}».")

    if "confirms" in valori:
        if natura is not None and natura != "decision":
            motivi.append("the field «confirms» is only for decisions that confirm an idea.")
        rimando = quaderno.risolvi(valori["confirms"], "confirms")
        vecchia = versioni.ultima_o_motivo(rimando, segno_chiusa)
        if rimando.motivo is not None:
            motivi.append(rimando.motivo)
        elif vecchia is not None:
            motivi.append(vecchia)
        elif rimando.storia.ultima.contenuto.natura != "idea":
            motivi.append(f"note «{valori['confirms']}» is a «{rimando.storia.ultima.contenuto.natura}», not an "
                          "idea: only an idea can be confirmed as a decision.")

    motivi += _controlla_etichette(valori, etichette)
    if not cambiamento and natura == "idea" and "text" in valori and autore in AUTORI:
        motivi += _controlla_sotto_ramo(valori, autore, note_esistenti, etichette)

    if "from_note" in valori and "integrates" not in valori:
        motivi.append("«from_note» goes only with «integrates»: it names the note to integrate.")

    usati = [c for c in CAMPI_CAMBIAMENTO if c in valori]
    if len(usati) > 1:
        motivi.append("a proposal can make only one change: use only one of «corrects», «updates», «done» "
                      "and «reopens».")
    elif usati and "confirms" in valori:
        motivi.append(f"«confirms» makes a new decision note: it cannot be used together with «{usati[0]}».")
    elif usati:
        motivi += _controlla_cambiamento(usati[0], valori, autore, natura, quaderno, segno_chiusa, etichette)

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
        for titolo in (*TITOLI_CONTESTO, TITOLO_CAMBIO, TITOLO_CONTESTO_CAMBIO):
            if campo in valori and titolo in righe:
                motivi.append(f"the field «{campo}» cannot contain the line «{titolo}»: "
                              "it is reserved for the note format.")
        if campo in valori and any(r.startswith(TITOLO_DA_NOTA) for r in righe):
            motivi.append(f"the field «{campo}» cannot contain a line starting with «{TITOLO_DA_NOTA.strip()}»: "
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


def dopo_il_cambiamento(campo: str, valori: dict, storia: "versioni.Storia", lista=None, quaderno=None) -> Nota:
    """Come sarà la nota dopo il cambiamento (senza il blocco del cambiamento e senza verifica).

    Dalla 0.8.0 le COSA messe dallo sportello si ricalcolano dal testo della versione nuova, con la lista
    ``lista`` di adesso: seguono il testo. Quelle proposte a mano restano (o cambiano con ``updates``).
    """
    attuale = storia.ultima.contenuto
    a_mano = lista_etichette.cosa_a_mano(attuale)
    if campo == "corrects":
        dopo = Nota(
            id=attuale.id, data=valori.get("date", attuale.data), fonte=valori.get("source", attuale.fonte),
            autore=valori.get("author", attuale.autore), tipo=valori.get("knowledge", attuale.tipo),
            natura=valori.get("kind", attuale.natura), testo=valori.get("text", attuale.testo),
            conferma_di=attuale.conferma_di, riprendere_il=valori.get("remind", attuale.riprendere_il),
            citazione=valori.get("quote"), contesto=valori.get("context"), da_risposta=valori.get("from_reply"),
            priorita=valori.get("priority", attuale.priorita), stato=attuale.stato,
            chi=attuale.chi,
        )
    elif campo == "updates":
        if "about" in valori:
            a_mano = lista_etichette.separa(valori["about"])
        dopo = replace(attuale, natura=valori.get("kind", attuale.natura),
                       priorita=valori.get("priority", attuale.priorita),
                       riprendere_il=valori.get("remind", attuale.riprendere_il),
                       chi=lista_etichette.separa(valori["who"]) if "who" in valori else attuale.chi)
    elif campo == "done":
        dopo = replace(attuale, natura=valori.get("kind", attuale.natura), stato=versioni.CHIUSA)
    elif campo == "cancels":
        dopo = replace(attuale, stato=versioni.ANNULLATA)
    elif campo == "integrates":
        # Dalla 0.9.0: il testo di prima resta intatto; in fondo, dopo una riga vuota, le parole nuove (a) oppure il
        # testo dell'altra nota così com'è (b).
        if "from_note" in valori:
            pezzo = quaderno.risolvi(valori["from_note"], "from_note").storia.ultima.contenuto.testo
        else:
            pezzo = valori["text"]
        dopo = replace(attuale, testo=attuale.testo + "\n\n" + pezzo)
    else:
        dopo = replace(attuale, natura=valori.get("kind", storia.natura_prima_della_chiusura()), stato=None,
                       priorita=valori.get("priority", attuale.priorita),
                       riprendere_il=valori.get("remind", attuale.riprendere_il))
    cosa, dal_testo = lista_etichette.cosa_finali(a_mano, lista_etichette.trova_nel_testo(dopo.testo, lista))
    return replace(dopo, cosa=cosa, cosa_dal_testo=dal_testo)


def _controlla_cambiamento(campo, valori, autore, natura, quaderno, segno_chiusa, lista=None) -> list[str]:
    """Le regole dei cambiamenti: si cambia l'ultima versione, e solo chi può."""
    motivi = []
    if campo != "corrects" and "from_reply" in valori:
        motivi.append(f"the field «from_reply» belongs to the text of a note: it can be used only in a "
                      f"new note or with «corrects», not with «{campo}».")
    # Dalla 0.7.0 un cambiamento chiesto dall'utente può avere il contesto di Claude (accanto al motivo,
    # che sono le parole dell'utente); in quelli di Claude lo vieta già la regola generale.
    if campo == "cancels":
        for estraneo in ("kind", "priority", "remind"):
            if estraneo in valori:
                motivi.append(f"«cancels» only cancels the note (it no longer counts): «{estraneo}» is not allowed.")
    if campo == "integrates":
        for estraneo in ("kind", "priority", "remind", "context"):
            if estraneo in valori:
                motivi.append(f"«integrates» only adds text at the end of the note: «{estraneo}» is not allowed "
                              "(to change kind, priority or reminder use «updates»).")
        if "from_note" in valori and "text" in valori:
            motivi.append("with «from_note» the text added is the text of that note, as it is: remove «text». To add "
                          "new words instead, use «integrates» without «from_note».")
    if campo != "updates":
        for etichetta in CAMPI_ETICHETTE:
            if etichetta in valori:
                motivi.append(f"the labels («{etichetta}») change only with «updates», not with «{campo}».")
    if campo == "done":
        for estraneo in ("priority", "remind"):
            if estraneo in valori:
                motivi.append(f"«done» only closes (and can say with «kind» what the note became): to change "
                              f"«{estraneo}» use «updates».")
        elenco = numeri(valori["done"])
    else:
        elenco = (valori[campo],)
        if "," in valori[campo]:
            return motivi + [f"«{campo}» names only one note: write one number, for example «0012»."]

    viste: dict[str, str] = {}
    for numero in elenco:
        if numero in viste.values():
            motivi.append(f"note «{numero}» is listed twice in «{campo}».")
            continue
        rimando = quaderno.risolvi(numero, campo)
        if rimando.motivo is not None:
            motivi.append(rimando.motivo)
            continue
        storia = rimando.storia
        if storia.base in viste:
            motivi.append(f"«{viste[storia.base]}» and «{numero}» are the same note ({storia.base}): list it once.")
            continue
        viste[storia.base] = numero
        vecchia = versioni.ultima_o_motivo(rimando, segno_chiusa)
        if vecchia is not None:
            motivi.append(vecchia)
            continue
        ultima = storia.ultima
        attuale = ultima.contenuto
        codice = ultima.codice(segno_chiusa)

        if ultima.annullata and campo != "reopens":
            motivi.append(f"note «{numero}» is cancelled ({codice}): to make it count again use «reopens».")
            continue
        if campo == "cancels":
            if ultima.chiusa:
                motivi.append(f"note «{numero}» is closed ({codice}): it was done, it cannot be cancelled. To "
                              "reopen it use «reopens».")
                continue
            if attuale.autore == "user" and autore != "user":
                motivi.append(f"note «{numero}» is the user's: only the user can cancel it. Claude can suggest it.")
                continue
        if campo == "done":
            if ultima.chiusa:
                motivi.append(f"note «{numero}» is already closed ({codice}): to reopen it use «reopens».")
                continue
            if attuale.natura not in ("open", "todo") and attuale.riprendere_il is None:
                motivi.append(
                    f"note «{numero}» is a «{attuale.natura}»: «done» closes only open, todo and reminder notes "
                    "(with «remind»). A fact, a decision or an idea is not closed: correct it with «corrects» "
                    "or change it with «updates»."
                )
                continue
            if attuale.natura == "open" and autore != "user":
                motivi.append(f"only the user can close an open note («{numero}»): Claude can suggest it, but "
                              "the proposal must have author «user».")
            if natura is not None and natura != attuale.natura and natura not in versioni.NATURE_DOPO_LA_CHIUSURA:
                motivi.append(f"closing cannot turn note «{numero}» into «{natura}»: to change its kind use "
                              "«updates».")
                continue
        if campo == "reopens":
            if not ultima.chiusa and not ultima.annullata:
                motivi.append(f"note «{numero}» is not closed ({codice}): only a closed or cancelled note can be "
                              "reopened.")
                continue
            if ultima.annullata and attuale.autore == "user" and autore != "user":
                motivi.append(f"note «{numero}» is the user's: only the user can make it count again.")
                continue
            if storia.natura_prima_della_chiusura() == "open" and autore != "user":
                motivi.append(f"only the user can reopen an open note («{numero}»): Claude can suggest it.")
        if campo == "corrects" and attuale.autore == "user" and autore != "user":
            motivi.append(f"the text of note «{numero}» is the user's words: only the user can correct it. "
                          "Claude can suggest the correction to the user, or save its own idea note.")
            continue
        if (campo == "updates" and any(e in valori for e in CAMPI_ETICHETTE) and attuale.autore == "user"
                and autore != "user" and (attuale.chi or lista_etichette.cosa_a_mano(attuale))):
            motivi.append(f"only the user can change the labels of one of the user's notes once they are set "
                          f"(note «{numero}» has them already): Claude can suggest the change to the user.")
            continue

        if campo == "integrates":
            fermo = _controlla_integrazione(valori, autore, quaderno, storia, numero, codice, lista)
            if fermo:
                motivi += fermo
                continue
        dopo = dopo_il_cambiamento(campo, valori, storia, lista, quaderno)
        prima_natura = storia.natura_prima_della_chiusura() if campo == "reopens" else attuale.natura
        if dopo.natura != prima_natura:
            motivo = versioni.natura_che_cambia(prima_natura, dopo.natura, autore, attuale.autore, campo)
            if motivo is not None:
                motivi.append(motivo)
                continue
        if campo in ("corrects", "updates") and not versioni.differenze(attuale, dopo):
            motivi.append(f"«{campo}» on note «{numero}» changes nothing: "
                          + ("the new text is the same as the current one." if campo == "corrects"
                             else "write in «kind», «priority», «remind», «who» or «about» the new value."))
    return motivi


def _controlla_etichette(valori: dict, etichette) -> list[str]:
    """Le etichette di una proposta: dalla lista del quaderno, al massimo due per campo, senza doppioni."""
    motivi = []
    for campo in CAMPI_ETICHETTE:
        if campo not in valori:
            continue
        if etichette is None:
            motivi.append(f"there are no labels in this notebook yet, so «{campo}» cannot be used: the user chooses "
                          "the labels, and they are added to the notebook's list of labels.")
            continue
        scelte = lista_etichette.separa(valori[campo])
        ammesse = etichette.ammesse(campo)
        if any(not s for s in scelte):
            motivi.append(f"«{campo}» has an empty label: write the labels separated by a comma, for example "
                          f"«{', '.join(ammesse[:2]) or 'Anna, Marco'}».")
            continue
        if len(scelte) > lista_etichette.MASSIMO_PER_NOTA:
            motivi.append(f"a note can have at most {lista_etichette.MASSIMO_PER_NOTA} «{campo}» labels: "
                          f"«{valori[campo]}» has {len(scelte)}.")
        for ripetuta in sorted({s for s in scelte if scelte.count(s) > 1}):
            motivi.append(f"the label «{ripetuta}» is repeated in «{campo}»: write it once.")
        for scelta in dict.fromkeys(scelte):
            if scelta not in ammesse:
                elenco = ", ".join(ammesse) if ammesse else f"none (the list «{dict(lista_etichette.CAMPI_INVERSI)[campo]}» is empty)"
                motivi.append(f"the label «{scelta}» is not in the list of «{campo}» labels: the allowed ones are "
                              f"{elenco}. Only the user adds labels, in the file {lista_etichette.NOME_FILE}.")
    return motivi


def _controlla_sotto_ramo(valori, autore, note_esistenti, lista) -> list[str]:
    """La regola dell'integrazione (dalla 0.10.0, I0213): un'idea nuova nel sotto-ramo di un'idea viva dello stesso
    autore non apre un'altra nota, ma si integra in quella."""
    from hypomnema import albero
    trovate = albero.gia_nel_sotto_ramo(note_esistenti, lista, autore, "idea", valori["text"],
                                        _etichette_della_proposta(valori))
    if not trovate:
        return []
    storia, (ramo, sotto) = trovate[0]
    altre = "".join(f" Also in this sub-branch: {', '.join(s.base for s, _ in trovate[1:])}." if trovate[1:] else "")
    return [f"this idea already has its note ({storia.base}, sub-branch {ramo}/{sotto}): propose it as an integration "
            f"of {storia.base} («integrates»: «{storia.base}», with only the new words in «text», no «kind» and no "
            f"«about»).{altre} If they are really different ideas, tell the user: the sub-branches of the labels must be "
            "made more precise, and only the user can do it."]


def _etichette_della_proposta(valori) -> tuple[str, ...] | None:
    return lista_etichette.separa(valori["about"]) if "about" in valori else None


def _controlla_integrazione(valori, autore, quaderno, storia, numero, codice, lista) -> list[str]:
    """Le regole di «integrates» (dalla 0.9.0): (a) parole nuove in fondo; (b) il testo di un'altra nota in fondo."""
    attuale = storia.ultima.contenuto
    if storia.ultima.chiusa or storia.ultima.annullata or storia.integrata_in is not None:
        return [f"note «{numero}» ({codice}) is closed or integrated into another note: it cannot be integrated."]
    if "from_note" not in valori:
        if autore != attuale.autore:
            return [f"note «{numero}» is written by «{attuale.autore}»: only «{attuale.autore}» can add words to it, "
                    "so that the user's words and Claude's never mix."]
        return []
    rimando = quaderno.risolvi(valori["from_note"], "from_note")
    if rimando.motivo is not None:
        return [rimando.motivo]
    altra = rimando.storia
    if altra is storia:
        return ["«integrates» and «from_note» name the same note: a note cannot be integrated into itself."]
    if altra.ultima.chiusa or altra.ultima.annullata or altra.integrata_in is not None:
        return [f"note «{valori['from_note']}» is closed or already integrated into another note: it cannot be "
                "integrated again."]
    sua = altra.ultima.contenuto
    if sua.autore != attuale.autore:
        return [f"notes «{numero}» ({attuale.autore}) and «{valori['from_note']}» ({sua.autore}) have different "
                "authors: the user's words and Claude's never mix in one note."]
    if sua.autore == "user" and autore != "user":
        return [f"note «{valori['from_note']}» is the user's: only the user can integrate it into another note "
                "(it would leave the recap)."]

    def cosa(nota):
        return set(lista_etichette.cosa_finali(lista_etichette.cosa_a_mano(nota),
                                               lista_etichette.trova_nel_testo(nota.testo, lista))[0] or ())
    if not cosa(attuale) & cosa(sua):
        return [f"notes «{numero}» and «{valori['from_note']}» have no COSA label in common: only notes about the "
                "same thing can be integrated."]
    return []


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
SENZA_TESTIMONE_ONLINE = "online, no witness"
SENZA_RISPOSTE = "replies witness off"
SENZA_TESTIMONE_IN_PAUSA = "witnesses paused"


def verifica(
    autore: str, testo: str, citazione: str | None, messaggi: list[Messaggio] | None, segno: str,
    in_chat: bool = False, da_risposta: bool = False, risposte: list[Messaggio] | None = None,
    in_pausa: bool = False, archivio: list[Messaggio] | None = None, diario_chat: list[Messaggio] | None = None,
    online: bool = False,
) -> str | None:
    """La dicitura "verification" da scrivere nella nota accettata (None = nessuna dicitura).

    Tre livelli: verificato dal testimone («found»), riscontrato sull'archivio della chat
    («matched», con l'indirizzo della chat), non verificato («not verified»).
    """
    in_chat_o_online = SENZA_TESTIMONE_ONLINE if online else SENZA_TESTIMONE_IN_CHAT
    if da_risposta:
        riscontro = _riscontro(diario_chat, testo, segno, "text matched", "reply")
        if risposte is None and riscontro:
            return riscontro
        if risposte is None:
            perche = in_chat_o_online if in_chat else SENZA_TESTIMONE_IN_PAUSA if in_pausa else SENZA_RISPOSTE
            return f"reply not verified ({perche})"
        trovato = trova_citazione(risposte, testo, segno)
        return f"text found in Claude's reply of {trovato.messaggio.quando}"
    if messaggi is None:
        perche = in_chat_o_online if in_chat else SENZA_TESTIMONE_IN_PAUSA if in_pausa else SENZA_TESTIMONE
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
