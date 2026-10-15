"""Il cercatore: trova le note che contengono una parola. Solo lettura.

La ricerca è per parola esatta: non distingue maiuscole e minuscole, e una parola è delimitata
da qualunque segno che non sia una lettera o una cifra (spazi, punteggiatura, ma anche il
trattino basso, il punto, il trattino e la barra delle parole composte): "orto" trova
"orto_balcone.py", ma "caffè" non trova "caffèlatte". Si cerca nel testo delle note e nel
contesto scritto da Claude. Le note trovate vanno dalla più recente (numero più alto) alla
più vecchia.

Ogni nota si porta dietro le note collegate: quelle che la correggono (``corregge``), che la
confermano (``conferma_di``) e che la segnano come fatta (``done``), anche a catena (la
correzione di una correzione), dalla più recente alla più vecchia.
"""

import re
from dataclasses import dataclass

from hypomnema import quaderno
from hypomnema.configurazione import Configurazione
from hypomnema.nota import Nota

# Il campo che collega una nota a un'altra, e come si legge il legame.
LEGAMI = (
    ("corregge", "corregge la nota", "corretta da"),
    ("conferma_di", "conferma la nota", "confermata da"),
    ("done", "segna come fatta la nota", "segnata come fatta da"),
)


@dataclass(frozen=True)
class Collegata:
    nota: Nota
    # Per esempio "corregge la nota 0001".
    legame: str


def schema_parola(parola: str) -> re.Pattern:
    """La parola (o le parole) così com'è, delimitata da segni che non sono lettere o cifre."""
    return re.compile(r"(?<![^\W_])" + re.escape(parola) + r"(?![^\W_])", re.IGNORECASE)


def dal_piu_recente(note: list[Nota]) -> list[Nota]:
    return sorted(note, key=lambda n: (int(n.id), n.id), reverse=True)


def cerca(config: Configurazione, parola: str) -> list[Nota]:
    parola = parola.strip()
    if not parola:
        raise ValueError("serve una parola da cercare.")
    schema = schema_parola(parola)
    return dal_piu_recente([
        n for n in quaderno.leggi_note(config)
        if schema.search(n.testo) or (n.contesto is not None and schema.search(n.contesto))
    ])


def legami_diretti(note: list[Nota]) -> dict[str, list[Collegata]]:
    """Per ogni numero di nota, le note che la nominano in corregge, conferma_di o done."""
    diretti: dict[str, list[Collegata]] = {}
    for nota in note:
        for campo, come, _ in LEGAMI:
            bersaglio = getattr(nota, campo)
            if bersaglio is not None:
                diretti.setdefault(bersaglio, []).append(Collegata(nota, f"{come} {bersaglio}"))
    return diretti


def collegate(id_nota: str, diretti: dict[str, list[Collegata]]) -> list[Collegata]:
    """Tutte le note collegate a una nota, anche a catena, dalla più recente alla più vecchia."""
    trovate: dict[str, Collegata] = {}
    da_guardare = [id_nota]
    while da_guardare:
        corrente = da_guardare.pop()
        for collegata in diretti.get(corrente, []):
            if collegata.nota.id not in trovate and collegata.nota.id != id_nota:
                trovate[collegata.nota.id] = collegata
                da_guardare.append(collegata.nota.id)
    return sorted(trovate.values(), key=lambda c: (int(c.nota.id), c.nota.id), reverse=True)


def righe_dei_legami(id_nota: str, diretti: dict[str, list[Collegata]]) -> list[str]:
    """Le righe «corretta da: nota …», «confermata da: nota …» di una nota (solo i legami diretti)."""
    righe = []
    for campo, _, letto in LEGAMI:
        numeri = sorted((c.nota.id for c in diretti.get(id_nota, []) if getattr(c.nota, campo) == id_nota),
                        key=lambda n: (int(n), n), reverse=True)
        if numeri:
            righe.append(f"{letto}: " + ", ".join(f"nota {n}" for n in numeri))
    return righe
