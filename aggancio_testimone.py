"""Punto d'ingresso dei due testimoni per gli agganci di Claude Code.

Senza argomenti lancia il testimone dei messaggi dell'utente (aggancio UserPromptSubmit); con
l'argomento ``risposte`` quello delle risposte di Claude (aggancio Stop).

Claude Code lo lancia a ogni messaggio dell'utente (vedi ``plugin/hooks/hooks.json``) con il
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
    comando = sys.argv[1] if len(sys.argv) > 1 else "testimone"
    if comando not in ("testimone", "risposte"):
        # Mai il codice 2: per Claude Code bloccherebbe il messaggio o la fine della risposta.
        print(f"ERRORE: comando sconosciuto «{comando}».", file=sys.stderr)
        sys.exit(1)
    argomenti = [comando]
    if not os.environ.get("HYPOMNEMA_CONFIG"):
        argomenti = ["--config", str(CARTELLA / "hypomnema.toml"), *argomenti]
    sys.exit(main(argomenti))
