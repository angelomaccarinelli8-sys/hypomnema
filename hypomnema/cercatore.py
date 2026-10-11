"""Il cercatore: trova le note che contengono una parola. Solo lettura.

La ricerca è per parola esatta: non distingue maiuscole e minuscole,
ma "caffè" non trova "caffèlatte". Si cerca nel testo delle note e nel contesto scritto da Claude.
"""

import re

from hypomnema import quaderno
from hypomnema.configurazione import Configurazione
from hypomnema.nota import Nota


def cerca(config: Configurazione, parola: str) -> list[Nota]:
    parola = parola.strip()
    if not parola:
        raise ValueError("serve una parola da cercare.")
    schema = re.compile(r"(?<!\w)" + re.escape(parola) + r"(?!\w)", re.IGNORECASE)
    return [
        n for n in quaderno.leggi_note(config)
        if schema.search(n.testo) or (n.contesto is not None and schema.search(n.contesto))
    ]
