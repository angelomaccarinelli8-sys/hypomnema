"""Lettura del quaderno: elenco delle note salvate e numero della prossima.

Le note sono i file ``0049.md``; le loro versioni sono i file con il punto: ``0049.1.md``,
``0049.2.md``.
"""

import re
import time

from hypomnema.configurazione import Configurazione
from hypomnema.nota import Nota, NotaIlleggibile, base_di, da_markdown, ordine

NOME_FILE_NOTA = re.compile(r"^(\d+(?:\.\d+)?)\.md$")


def leggi_note(config: Configurazione) -> list[Nota]:
    """Tutte le note e le loro versioni, in ordine di numero (la versione subito dopo la sua nota)."""
    if not config.cartella_note.is_dir():
        return []
    trovate = []
    for file in config.cartella_note.iterdir():
        corrispondenza = NOME_FILE_NOTA.match(file.name)
        if corrispondenza and file.is_file():
            trovate.append(_leggi_nota(corrispondenza.group(1), file))
    trovate.sort(key=lambda n: ordine(n.id))
    return trovate


# Quanto si aspetta una nota appena creata da un altro passaggio e non ancora scritta (dalla 0.6.1).
# Tra due macchine il blocco del quaderno non passa: la nota si crea con apertura esclusiva e poi
# si scrive, e per un attimo il file può essere vuoto o a metà.
ATTESA_NOTA = 1.0


def _leggi_nota(id_nota: str, file) -> Nota:
    scadenza = time.monotonic() + ATTESA_NOTA
    while True:
        try:
            return da_markdown(id_nota, file.read_text(encoding="utf-8"))
        except (NotaIlleggibile, UnicodeDecodeError):
            # Un file davvero rovinato resta rovinato: dopo l'attesa l'errore arriva comunque.
            if time.monotonic() >= scadenza:
                raise
            time.sleep(0.02)


def prossimo_id(note: list[Nota], cifre: int) -> str:
    """Il primo numero intero dopo il più alto: le versioni non contano, i buchi non si riempiono."""
    ultimo = max((int(base_di(n.id)) for n in note), default=0)
    return str(ultimo + 1).zfill(cifre)
