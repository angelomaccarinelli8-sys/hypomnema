"""Il diario: i messaggi dell'utente e le risposte di Claude, insieme e in ordine di tempo.

Il diario è la conversazione grezza registrata dai due testimoni; il quaderno sono le note scelte.
Solo lettura. La ricerca segue le regole del cercatore: parola esatta, maiuscole indifferenti.
"""

import re
from dataclasses import dataclass
from datetime import datetime

from hypomnema import archivio, risposte, testimone
from hypomnema.configurazione import Configurazione
from hypomnema.testimone import ErroreTestimone


@dataclass(frozen=True)
class Voce:
    quando: str
    chi: str  # "utente" oppure "claude"
    testo: str | None  # None se non registrato (messaggio privato)
    dicitura: str | None  # perché il testo non c'è
    # Da dove viene, se non dai testimoni di Claude Code: l'archivio della chat, copiato da Claude.
    fonte: str | None = None


def voci(config: Configurazione) -> list[Voce]:
    """Tutto il diario, in ordine di tempo; a parità di ora prima l'utente, poi Claude."""
    elenco = []
    for ordine, (chi, messaggi) in enumerate((
        ("utente", testimone.leggi_messaggi(config)),
        ("claude", risposte.leggi_risposte(config)),
        ("utente", archivio.leggi_messaggi(config)),
        ("claude", archivio.leggi_risposte(config)),
    )):
        for posizione, messaggio in enumerate(messaggi):
            try:
                momento = datetime.fromisoformat(messaggio.quando)
            except ValueError:
                raise ErroreTestimone(
                    f"nel diario c'è una data non valida: «{messaggio.quando}». "
                    "Controlla se i file dei testimoni sono stati modificati a mano."
                )
            fonte = f"archivio della chat {messaggio.chat}, copiato da Claude" if messaggio.chat else None
            voce = Voce(messaggio.quando, chi, messaggio.testo, messaggio.privato, fonte)
            elenco.append(((momento, ordine % 2, ordine, posizione), voce))
    elenco.sort(key=lambda coppia: coppia[0])
    return [voce for _, voce in elenco]


def cerca(config: Configurazione, parola: str) -> tuple[list[Voce], list[int]]:
    """Tutto il diario e le posizioni delle voci che contengono la parola."""
    parola = parola.strip()
    if not parola:
        raise ValueError("serve una parola da cercare.")
    schema = re.compile(r"(?<!\w)" + re.escape(parola) + r"(?!\w)", re.IGNORECASE)
    tutte = voci(config)
    trovate = [i for i, voce in enumerate(tutte) if voce.testo is not None and schema.search(voce.testo)]
    return tutte, trovate
