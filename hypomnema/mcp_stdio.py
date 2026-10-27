"""Il trasporto stdio del server MCP (dalla 0.11.0): una richiesta JSON-RPC per riga sull'ingresso standard, una
risposta per riga sull'uscita standard. Lo usano Claude Code (plugin, ``.mcp.json``) e l'app desktop.

Non apre porte di rete e non sa niente di note: passa ogni riga al cuore (``servizio``). Sull'uscita standard
scrive solo risposte del protocollo, nient'altro (una riga in più romperebbe la conversazione con Claude).
"""

from __future__ import annotations

import json
from typing import Iterable, TextIO

from hypomnema import servizio


def servi(taccuino: servizio.Taccuino, righe: Iterable[str], uscita: TextIO) -> None:
    """Risponde a ogni riga finché l'ingresso non finisce (il client chiude: il server si ferma)."""
    for riga in righe:
        if not riga.strip():
            continue
        risposta = servizio.rispondi_al_testo(taccuino, riga)
        if risposta is not None:
            uscita.write(json.dumps(risposta, ensure_ascii=False) + "\n")
            uscita.flush()
