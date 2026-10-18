"""Lettura del quaderno: elenco delle note salvate e numero della prossima.

Le note sono i file ``0049.md``; le loro versioni sono i file con il punto: ``0049.1.md``,
``0049.2.md``.
"""

import re

from hypomnema.configurazione import Configurazione
from hypomnema.nota import Nota, base_di, da_markdown, ordine

NOME_FILE_NOTA = re.compile(r"^(\d+(?:\.\d+)?)\.md$")


def leggi_note(config: Configurazione) -> list[Nota]:
    """Tutte le note e le loro versioni, in ordine di numero (la versione subito dopo la sua nota)."""
    if not config.cartella_note.is_dir():
        return []
    trovate = []
    for file in config.cartella_note.iterdir():
        corrispondenza = NOME_FILE_NOTA.match(file.name)
        if corrispondenza and file.is_file():
            id_nota = corrispondenza.group(1)
            contenuto = file.read_text(encoding="utf-8")
            trovate.append(da_markdown(id_nota, contenuto))
    trovate.sort(key=lambda n: ordine(n.id))
    return trovate


def prossimo_id(note: list[Nota], cifre: int) -> str:
    """Il primo numero intero dopo il più alto: le versioni non contano, i buchi non si riempiono."""
    ultimo = max((int(base_di(n.id)) for n in note), default=0)
    return str(ultimo + 1).zfill(cifre)
