"""Lo sportello: l'unica porta d'ingresso del quaderno.

Riceve una nota proposta in formato JSON (testo UTF-8), la controlla con le regole fisse,
la salva come file Markdown se è completa, e annota sempre il passaggio nel registro.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from hypomnema import quaderno, registro, regole
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
    """Esamina una proposta e restituisce l'esito. Annota sempre il passaggio nel registro."""
    note_esistenti = quaderno.leggi_note(config)
    proposta, motivi = _leggi_proposta(contenuto)
    if proposta is not None:
        motivi = regole.controlla(proposta, note_esistenti)

    if motivi:
        registro.annota(config, adesso, origine, None, motivi)
        return Esito(accettata=False, id_nota=None, percorso=None, motivi=motivi)

    id_nota = quaderno.prossimo_id(note_esistenti, config.cifre_numero_nota)
    conferma = proposta.get("conferma_di")
    nota = Nota(
        id=id_nota,
        data=proposta["data"].strip(),
        fonte=proposta["fonte"].strip(),
        autore=proposta["autore"].strip(),
        tipo=proposta["tipo"].strip(),
        natura=proposta["natura"].strip(),
        testo=proposta["testo"].strip(),
        conferma_di=conferma.strip() if conferma is not None else None,
    )
    config.cartella_note.mkdir(parents=True, exist_ok=True)
    percorso = config.cartella_note / f"{id_nota}.md"
    # Modo "x": se il file esistesse già, Python si ferma invece di sovrascriverlo.
    with open(percorso, "x", encoding="utf-8", newline="\n") as f:
        f.write(nota.in_markdown())
    registro.annota(config, adesso, origine, id_nota, [])
    return Esito(accettata=True, id_nota=id_nota, percorso=percorso, motivi=[])
