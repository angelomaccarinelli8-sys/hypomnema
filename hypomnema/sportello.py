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
from hypomnema.nota import Nota


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
        return None, ["il file non è salvato con la codifica UTF-8: salvalo in UTF-8 e riprova."]
    try:
        dati = json.loads(testo, object_pairs_hook=_senza_doppioni)
    except _CampoDoppio as errore:
        return None, [f"il campo «{errore.args[0]}» compare due volte: deve comparire una volta sola."]
    except json.JSONDecodeError as errore:
        return None, [
            "la proposta non è scritta in formato JSON corretto: controlla virgole, "
            f"virgolette e parentesi (errore a riga {errore.lineno}, colonna {errore.colno})."
        ]
    if not isinstance(dati, dict):
        return None, [
            "la proposta deve essere una sola nota, scritta tra parentesi graffe { } "
            "con i campi della nota."
        ]
    return dati, []


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
        motivi = regole.controlla(proposta, note_esistenti, messaggi, config.segno_citazione, risposte)

    if motivi:
        registro.annota(config, adesso, origine, None, motivi)
        return Esito(accettata=False, id_nota=None, percorso=None, motivi=motivi)

    id_nota = quaderno.prossimo_id(note_esistenti, config.cifre_numero_nota)
    conferma = proposta.get("conferma_di")
    citazione = proposta.get("citazione")
    if citazione is not None:
        # Nel file della nota la citazione sta su una riga: spazi e a capo ridotti a uno.
        citazione = testimone.normalizza(citazione)
    autore = proposta["autore"].strip()
    testo = proposta["testo"].strip()
    contesto = proposta.get("contesto")
    nota = Nota(
        id=id_nota,
        data=proposta["data"].strip(),
        fonte=proposta["fonte"].strip(),
        autore=autore,
        tipo=proposta["tipo"].strip(),
        natura=proposta["natura"].strip(),
        testo=testo,
        conferma_di=conferma.strip() if conferma is not None else None,
        citazione=citazione,
        contesto=contesto.strip() if contesto is not None else None,
        da_risposta=proposta["da_risposta"].strip() if proposta.get("da_risposta") is not None else None,
        verifica=regole.verifica(
            autore, testo, citazione, messaggi, config.segno_citazione, config.in_chat,
            da_risposta=proposta.get("da_risposta") is not None, risposte=risposte, in_pausa=in_pausa,
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
