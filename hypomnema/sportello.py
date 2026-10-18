"""Lo sportello: l'unica porta d'ingresso del quaderno.

Riceve una nota proposta in formato JSON (testo UTF-8), la controlla con le regole fisse,
la salva come file Markdown se è completa, e annota sempre il passaggio nel registro.

Una proposta con ``corrects``, ``updates``, ``done`` o ``reopens`` non crea una nota nuova: crea
la versione successiva della nota (``0049.1.md``), una per ogni nota chiusa con ``done``, ognuna
con la sua riga nel registro.
"""

import json
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from hypomnema import (
    archivio as testimone_archivio, blocco, quaderno, registro, regole, risposte as testimone_risposte, testimone, versioni,
)
from hypomnema import configurazione
from hypomnema.configurazione import Configurazione
from hypomnema.nota import Cambio, Nota, numeri


@dataclass(frozen=True)
class Esito:
    accettata: bool
    id_nota: str | None
    percorso: Path | None
    motivi: list[str]
    # Tutte le note o versioni scritte: (numero, percorso). Più di una solo con «done» su più note.
    scritte: tuple[tuple[str, Path], ...] = ()


class _CampoDoppio(Exception):
    pass


def _senza_doppioni(coppie: list[tuple[str, object]]) -> dict:
    risultato: dict = {}
    for chiave, valore in coppie:
        if chiave in risultato:
            raise _CampoDoppio(chiave)
        risultato[chiave] = valore
    return risultato


def _leggi_proposta(contenuto: bytes) -> tuple[dict | None, list[str]]:
    try:
        # "utf-8-sig" accetta anche i file con il segno iniziale che aggiungono alcuni programmi Windows.
        testo = contenuto.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None, ["the file is not saved in UTF-8: save it in UTF-8 and try again."]
    try:
        dati = json.loads(testo, object_pairs_hook=_senza_doppioni)
    except _CampoDoppio as errore:
        return None, [f"the field «{errore.args[0]}» appears twice: it must appear only once."]
    except json.JSONDecodeError as errore:
        return None, [
            "the proposal is not valid JSON: check commas, quotes and brackets "
            f"(error at line {errore.lineno}, column {errore.colno})."
        ]
    if not isinstance(dati, dict):
        return None, [
            "the proposal must be a single note, written between braces { } with the note's fields."
        ]
    return dati, []


def _facoltativo(proposta: dict, campo: str) -> str | None:
    valore = proposta.get(campo)
    return valore.strip() if valore is not None else None


def ricevi(contenuto: bytes, origine: str, config: Configurazione, adesso: datetime) -> Esito:
    """Esamina una proposta e restituisce l'esito. Annota sempre il passaggio nel registro.

    Se il registro è stato toccato a mano (non finisce con un a capo) non scrive niente e solleva
    registro.RegistroToccato. Tiene il blocco del quaderno per tutto il passaggio (vedi ``blocco``);
    se un altro passaggio lo tiene troppo a lungo solleva blocco.QuadernoOccupato senza scrivere.
    """
    adesso = configurazione.nel_fuso(config, adesso)
    # Prima del blocco, così un registro toccato a mano ferma tutto senza creare niente; poi di nuovo
    # dentro il passaggio.
    registro.controlla_fine(config)
    with blocco.blocco(config.cartella_quaderno, crea=True):
        return _ricevi(contenuto, origine, config, adesso)


def _ricevi(contenuto: bytes, origine: str, config: Configurazione, adesso: datetime) -> Esito:
    registro.controlla_fine(config)
    note_esistenti = quaderno.leggi_note(config)
    messaggi = testimone.leggi_messaggi(config) if config.testimone_attivo else None
    risposte = testimone_risposte.leggi_risposte(config) if config.risposte_attive else None
    in_pausa = messaggi is not None and testimone.in_pausa(messaggi) is not None
    if in_pausa:
        # In pausa i testimoni non registrano: niente verifica, e la nota lo dice
        # («autore non verificato (testimoni in pausa)»).
        messaggi = risposte = None
    proposta, motivi = _leggi_proposta(contenuto)
    if proposta is not None:
        # I nomi e i valori italiani di prima valgono per sempre: qui diventano inglesi.
        proposta, motivi = regole.in_inglese(proposta)
        motivi += regole.controlla(proposta, note_esistenti, messaggi, config.segno_citazione, risposte,
                                   config.segno_chiusa)

    if motivi:
        registro.annota(config, adesso, origine, None, motivi)
        return Esito(accettata=False, id_nota=None, percorso=None, motivi=motivi)

    id_nota = quaderno.prossimo_id(note_esistenti, config.cifre_numero_nota)
    citazione = _facoltativo(proposta, "quote")
    if citazione is not None:
        # Nel file della nota la citazione sta su una riga: spazi e a capo ridotti a uno.
        citazione = testimone.normalizza(citazione)
    autore = proposta["author"].strip()
    testo = proposta["text"].strip()
    da_risposta = _facoltativo(proposta, "from_reply")
    dicitura = regole.verifica(
        autore, testo, citazione, messaggi, config.segno_citazione, config.in_chat,
        da_risposta=da_risposta is not None, risposte=risposte, in_pausa=in_pausa,
        archivio=testimone_archivio.leggi_messaggi(config) if config.file_archivio else None,
        diario_chat=testimone_archivio.leggi_risposte(config) if config.file_archivio else None,
    )
    campo = next((c for c in regole.CAMPI_CAMBIAMENTO if _facoltativo(proposta, c) is not None), None)
    if campo is not None:
        valori = {k: v.strip() for k, v in proposta.items() if isinstance(v, str)}
        if citazione is not None:
            valori["quote"] = citazione
        return _versioni(config, adesso, origine, note_esistenti, campo, valori, dicitura)
    nota = Nota(
        id=id_nota,
        data=proposta["date"].strip(),
        fonte=proposta["source"].strip(),
        autore=autore,
        tipo=proposta["knowledge"].strip(),
        natura=proposta["kind"].strip(),
        testo=testo,
        priorita=_facoltativo(proposta, "priority"),
        conferma_di=_facoltativo(proposta, "confirms"),
        riprendere_il=_facoltativo(proposta, "remind"),
        citazione=citazione,
        contesto=_facoltativo(proposta, "context"),
        da_risposta=da_risposta,
        verifica=dicitura,
    )
    config.cartella_note.mkdir(parents=True, exist_ok=True)
    numero = int(id_nota)
    while True:
        nota = replace(nota, id=str(numero).zfill(config.cifre_numero_nota))
        percorso = config.cartella_note / f"{nota.id}.md"
        try:
            # Modo "x": se il file esiste già, Python si ferma invece di sovrascriverlo.
            with open(percorso, "x", encoding="utf-8", newline="\n") as f:
                f.write(nota.in_markdown())
            break
        except FileExistsError:
            # Un altro passaggio ha appena preso questo numero: si prova il successivo.
            # Finisce sempre, perché i file già presenti sono in numero finito.
            numero += 1
    id_nota = nota.id
    registro.annota(config, adesso, origine, id_nota, [])
    return Esito(accettata=True, id_nota=id_nota, percorso=percorso, motivi=[], scritte=((id_nota, percorso),))


def _versioni(config, adesso, origine, note_esistenti, campo, valori, dicitura) -> Esito:
    """Scrive la versione successiva di ogni nota cambiata. Le regole sono già state controllate tutte."""
    elenco = numeri(valori[campo]) if campo == "done" else (valori[campo],)
    archivio_note = versioni.Quaderno(note_esistenti)
    cambio = Cambio(
        data=valori["date"], fonte=valori["source"], autore=valori["author"], tipo=valori["knowledge"], cambio="",
        citazione=None if campo == "corrects" else valori.get("quote"), verifica=dicitura,
        # In una correzione le parole nuove sono il testo stesso: non c'è un motivo a parte.
        motivo=None if campo == "corrects" else valori["text"],
    )
    config.cartella_note.mkdir(parents=True, exist_ok=True)
    scritte = []
    for numero in elenco:
        storia = archivio_note.risolvi(numero, campo).storia
        attuale = storia.ultima.contenuto
        dopo = regole.dopo_il_cambiamento(campo, valori, storia)
        voci = versioni.differenze(attuale, dopo)
        if campo == "done":
            voci.insert(0, versioni.CHIUSA)
        elif campo == "reopens":
            voci.insert(0, versioni.RIAPERTA)
        id_versione = storia.prossima_versione()
        nota = replace(
            dopo, id=id_versione, corregge=None, done=None,
            verifica=dicitura if campo == "corrects" else attuale.verifica,
            cambio=replace(cambio, cambio="; ".join(voci)),
        )
        percorso = config.cartella_note / f"{id_versione}.md"
        try:
            # Modo "x": se il file esiste già, Python si ferma invece di sovrascriverlo.
            with open(percorso, "x", encoding="utf-8", newline="\n") as f:
                f.write(nota.in_markdown())
        except FileExistsError:
            # Un altro passaggio ha appena cambiato la stessa nota: questo cambiamento è stato
            # controllato su una versione che non è più l'ultima, quindi non si scrive.
            motivi = [f"version {id_versione} was written by another passage in the meantime: nothing more "
                      "was written. Look at the note again and make a new proposal."]
            registro.annota(config, adesso, origine, None, motivi)
            return Esito(accettata=False, id_nota=None, percorso=None, motivi=motivi, scritte=tuple(scritte))
        registro.annota(config, adesso, origine, id_versione, [])
        scritte.append((id_versione, percorso))
    return Esito(accettata=True, id_nota=scritte[0][0], percorso=scritte[0][1], motivi=[], scritte=tuple(scritte))
