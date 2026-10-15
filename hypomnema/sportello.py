"""Lo sportello: l'unica porta d'ingresso del quaderno.

Riceve una nota proposta in formato JSON (testo UTF-8), la controlla con le regole fisse,
la salva come file Markdown se è completa, e annota sempre il passaggio nel registro.
"""

import json
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from hypomnema import archivio as testimone_archivio, quaderno, registro, regole, risposte as testimone_risposte, testimone
from hypomnema.configurazione import Configurazione
from hypomnema.nota import Nota, numeri


@dataclass(frozen=True)
class Esito:
    accettata: bool
    id_nota: str | None
    percorso: Path | None
    motivi: list[str]


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
    registro.RegistroToccato.
    """
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
        motivi += regole.controlla(proposta, note_esistenti, messaggi, config.segno_citazione, risposte)

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
    chiude = _facoltativo(proposta, "done")
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
        corregge=_facoltativo(proposta, "corrects"),
        done=numeri(chiude) if chiude is not None else None,
        riprendere_il=_facoltativo(proposta, "remind"),
        citazione=citazione,
        contesto=_facoltativo(proposta, "context"),
        da_risposta=da_risposta,
        verifica=regole.verifica(
            autore, testo, citazione, messaggi, config.segno_citazione, config.in_chat,
            da_risposta=da_risposta is not None, risposte=risposte, in_pausa=in_pausa,
            archivio=testimone_archivio.leggi_messaggi(config) if config.file_archivio else None,
            diario_chat=testimone_archivio.leggi_risposte(config) if config.file_archivio else None,
        ),
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
    return Esito(accettata=True, id_nota=id_nota, percorso=percorso, motivi=[])
