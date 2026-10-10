"""Lettura del quaderno: elenco delle note salvate e numero della prossima."""

import re

from hypomnema.configurazione import Configurazione
from hypomnema.nota import Nota, da_markdown

NOME_FILE_NOTA = re.compile(r"^(\d+)\.md$")


def leggi_note(config: Configurazione) -> list[Nota]:
    """Tutte le note del quaderno, in ordine di numero."""
    if not config.cartella_note.is_dir():
        return []
    trovate = []
    for file in config.cartella_note.iterdir():
        corrispondenza = NOME_FILE_NOTA.match(file.name)
        if corrispondenza and file.is_file():
            id_nota = corrispondenza.group(1)
            contenuto = file.read_text(encoding="utf-8")
            trovate.append(da_markdown(id_nota, contenuto))
    trovate.sort(key=lambda n: (int(n.id), n.id))
    return trovate


def prossimo_id(note: list[Nota], cifre: int) -> str:
    ultimo = max((int(n.id) for n in note), default=0)
    return str(ultimo + 1).zfill(cifre)
