"""Punto d'ingresso del testimone per l'aggancio di Claude Code.

Claude Code lo lancia a ogni messaggio dell'utente (vedi ``.claude/settings.json``) con il
percorso completo, per esempio ``py "C:/.../hypomnema/aggancio_testimone.py"``: così funziona
qualunque sia la cartella corrente e qualunque sia la shell (Git Bash o PowerShell).

Usa ``hypomnema.toml`` accanto a questo file, oppure quello indicato dalla variabile
d'ambiente ``HYPOMNEMA_CONFIG``.
"""

import os
import sys
from pathlib import Path

CARTELLA = Path(__file__).resolve().parent
sys.path.insert(0, str(CARTELLA))

from hypomnema.cli import main  # noqa: E402

if __name__ == "__main__":
    argomenti = ["testimone"]
    if not os.environ.get("HYPOMNEMA_CONFIG"):
        argomenti = ["--config", str(CARTELLA / "hypomnema.toml"), *argomenti]
    sys.exit(main(argomenti))
