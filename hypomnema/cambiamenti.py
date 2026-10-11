"""Quali file del quaderno sono cambiati dopo una proposta. Solo lettura.

Serve nella chat di Claude: il quaderno vive in una copia nel computer di lavoro della chat e,
dopo ogni passaggio dallo sportello, Claude riporta sul computer dell'utente solo i file
cambiati. Si usa così:

    hypomnema istantanea > prima.json      # prima della proposta
    hypomnema proponi proposta.json
    hypomnema cambiati prima.json          # dopo: i file da riportare

"cambiati" controlla anche che sia successo solo ciò che lo sportello sa fare: creare note
nuove, annotate come ACCETTATA nelle righe nuove del registro, e allungare il registro con righe
nella forma dello sportello (e con la sua intestazione, se il registro è nuovo). Una riga scritta
a mano ma con la forma giusta non si può distinguere: il controllo esclude il testo libero.
Qualunque altro cambiamento (un file sparito, riscritto, o scritto a mano) è un errore, e
allora non si riporta niente.
"""

import hashlib
import json
from dataclasses import dataclass

from hypomnema.configurazione import Configurazione
from hypomnema.quaderno import NOME_FILE_NOTA
from hypomnema.registro import INTESTAZIONE, RIGA_ACCETTATA, RIGA_RIFIUTATA


class ErroreCambiamenti(Exception):
    """L'istantanea non è valida, oppure il quaderno è cambiato in un modo non permesso."""

    def __init__(self, problemi: list[str]):
        super().__init__(" / ".join(problemi))
        self.problemi = problemi


@dataclass(frozen=True)
class Cambiamento:
    percorso: str  # relativo alla cartella del quaderno, con "/"
    tipo: str  # "creato" oppure "allungato"


def _impronta(dati: bytes) -> str:
    return hashlib.sha256(dati).hexdigest()


def _file_del_quaderno(config: Configurazione) -> dict[str, bytes]:
    quaderno = config.cartella_quaderno
    if not quaderno.is_dir():
        return {}
    return {
        p.relative_to(quaderno).as_posix(): p.read_bytes()
        for p in sorted(quaderno.rglob("*"))
        if p.is_file()
    }


def istantanea(config: Configurazione) -> dict:
    """Dimensione e impronta (SHA-256) di ogni file del quaderno."""
    return {
        "file": {
            percorso: {"byte": len(dati), "sha256": _impronta(dati)}
            for percorso, dati in _file_del_quaderno(config).items()
        }
    }


def leggi_istantanea(contenuto: bytes) -> dict[str, tuple[int, str]]:
    non_valida = ErroreCambiamenti([
        "il file dell'istantanea non è valido: rifallo con «hypomnema istantanea» prima della proposta."
    ])
    try:
        dati = json.loads(contenuto.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise non_valida
    if not isinstance(dati, dict) or set(dati) != {"file"} or not isinstance(dati["file"], dict):
        raise non_valida
    file = {}
    for percorso, voce in dati["file"].items():
        if (
            not isinstance(voce, dict) or set(voce) != {"byte", "sha256"}
            or not isinstance(voce["byte"], int) or isinstance(voce["byte"], bool) or voce["byte"] < 0
            or not isinstance(voce["sha256"], str)
        ):
            raise non_valida
        file[percorso] = (voce["byte"], voce["sha256"])
    return file


def _accettate_nel_registro(
    registro: str, aggiunte: dict[str, bytes], cambiamenti: list[Cambiamento], problemi: list[str]
) -> set[str]:
    """Controlla il pezzo aggiunto al registro; restituisce i numeri delle note accettate."""
    if registro not in aggiunte:
        return set()
    try:
        testo = aggiunte[registro].decode("utf-8")
    except UnicodeDecodeError:
        problemi.append(f"il file «{registro}» è stato allungato con caratteri che non sono UTF-8.")
        return set()
    creato = any(c.percorso == registro and c.tipo == "creato" for c in cambiamenti)
    if creato:
        if not testo.startswith(INTESTAZIONE):
            problemi.append(f"il file «{registro}» è nuovo ma non comincia con l'intestazione del registro.")
            return set()
        testo = testo[len(INTESTAZIONE):]
    if not testo.endswith("\n"):
        problemi.append(f"il file «{registro}» non finisce con un a capo, come fa lo sportello.")
        return set()
    accettate = set()
    for riga in testo[:-1].split("\n"):
        accettata = RIGA_ACCETTATA.fullmatch(riga)
        if accettata:
            accettate.add(accettata.group(1))
        elif not RIGA_RIFIUTATA.fullmatch(riga):
            problemi.append(f"nel file «{registro}» c'è una riga nuova che non è dello sportello: «{riga}».")
    return accettate


def cambiati(config: Configurazione, prima: dict[str, tuple[int, str]]) -> list[Cambiamento]:
    """I file creati o allungati rispetto all'istantanea; ErroreCambiamenti se è successo altro."""
    dopo = _file_del_quaderno(config)
    problemi = [f"il file «{p}» c'era e ora non c'è più." for p in sorted(prima) if p not in dopo]

    cambiamenti: list[Cambiamento] = []
    aggiunte: dict[str, bytes] = {}
    for percorso, dati in dopo.items():
        if percorso not in prima:
            cambiamenti.append(Cambiamento(percorso, "creato"))
            aggiunte[percorso] = dati
            continue
        byte, impronta = prima[percorso]
        if len(dati) == byte and _impronta(dati) == impronta:
            continue
        if len(dati) > byte and _impronta(dati[:byte]) == impronta:
            cambiamenti.append(Cambiamento(percorso, "allungato"))
            aggiunte[percorso] = dati[byte:]
            if byte > 0 and dati[byte - 1:byte] != b"\n":
                problemi.append(
                    f"il pezzo aggiunto al file «{percorso}» non comincia all'inizio di una riga: "
                    "prima il file non finiva con un a capo (era stato toccato a mano)."
                )
        else:
            problemi.append(f"il file «{percorso}» è stato cambiato in modo diverso da un'aggiunta in fondo.")

    quaderno = config.cartella_quaderno
    registro = config.file_registro.relative_to(quaderno).as_posix()
    cartella_note = config.cartella_note.relative_to(quaderno).as_posix()
    accettate = _accettate_nel_registro(registro, aggiunte, cambiamenti, problemi)

    note_create = set()
    for cambiamento in cambiamenti:
        if cambiamento.percorso == registro:
            continue
        cartella, _, nome = cambiamento.percorso.rpartition("/")
        corrispondenza = NOME_FILE_NOTA.match(nome)
        if (
            cambiamento.tipo == "creato" and cartella == cartella_note and corrispondenza
            and corrispondenza.group(1) in accettate
        ):
            note_create.add(corrispondenza.group(1))
        else:
            problemi.append(
                f"il file «{cambiamento.percorso}» ({cambiamento.tipo}) non l'ha scritto lo sportello: "
                "lo sportello crea solo note annotate come ACCETTATA nel registro e allunga il registro."
            )
    for numero in sorted(accettate - note_create):
        problemi.append(f"il registro dice che la nota {numero} è stata accettata, ma la nota non è stata creata.")

    if problemi:
        raise ErroreCambiamenti(problemi)
    return cambiamenti
