"""Punto d'ingresso di Hypomnema dentro il plugin di Claude Code.

Gli agganci del plugin (``hooks/hooks.json``) e Claude stesso lanciano questo file con il percorso
del plugin, per esempio  py "${CLAUDE_PLUGIN_ROOT}/programma.py" testimone . I programmi stanno
nella cartella accanto (``hypomnema/``), dentro il plugin: funziona anche dalla copia che Claude
Code tiene nella sua cache quando il plugin è installato.

La configurazione e il quaderno stanno FUORI dal plugin, così un aggiornamento non li tocca mai:
di base ``~/Hypomnema/hypomnema.toml`` (su Windows ``%USERPROFILE%\\Hypomnema\\hypomnema.toml``),
oppure il file indicato da ``--config`` o dalla variabile d'ambiente ``HYPOMNEMA_CONFIG``.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hypomnema.avvio import configurazione_di_base  # noqa: E402
from hypomnema.cli import main  # noqa: E402

if __name__ == "__main__":
    argomenti = sys.argv[1:]
    if "--config" not in argomenti and not os.environ.get("HYPOMNEMA_CONFIG"):
        argomenti = ["--config", str(configurazione_di_base()), *argomenti]
    sys.exit(main(argomenti))
