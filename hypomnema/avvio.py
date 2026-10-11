"""Ciò che serve all'avviabile: le regole che vietano a Claude di modificare il quaderno in uso.

Il quaderno in uso sta fuori dal repository, quindi il divieto del progetto
(``.claude/settings.json``, che copre solo la cartella ``quaderno/`` di sviluppo) non lo
protegge. L'avviabile chiede queste regole a ``hypomnema impostazioni-claude`` e le passa a
Claude Code con ``--settings``: valgono solo per la sessione aperta dall'avviabile.
"""

from pathlib import Path, PurePath, PureWindowsPath

from hypomnema.configurazione import Configurazione

# La cartella del programma: quella che contiene il pacchetto hypomnema.
CARTELLA_PROGRAMMA = Path(__file__).resolve().parent.parent


class ErroreAvvio(Exception):
    """La configurazione in uso non è adatta all'avviabile."""


def percorso_per_le_regole(percorso: PurePath) -> str:
    """Un percorso assoluto scritto come vogliono le regole di Claude Code.

    "//" all'inizio vuol dire "dalla radice del disco". Su Windows Claude Code scrive i percorsi
    in forma Unix: C:\\Users\\nome diventa /c/Users/nome, quindi la regola usa //c/Users/nome.
    """
    if isinstance(percorso, PureWindowsPath) and len(percorso.drive) == 2:
        return "//" + percorso.drive[0].lower() + percorso.as_posix()[2:]
    return "/" + percorso.as_posix()


def impostazioni_claude(config: Configurazione, file_config: Path) -> dict:
    """Le impostazioni da passare a Claude Code: vietata ogni modifica a quaderno e configurazione."""
    quaderno = config.cartella_quaderno.resolve()
    if quaderno == CARTELLA_PROGRAMMA or CARTELLA_PROGRAMMA in quaderno.parents:
        raise ErroreAvvio(
            f"il quaderno «{quaderno}» è dentro la cartella del programma «{CARTELLA_PROGRAMMA}»: "
            "le note vere devono stare fuori, perché l'aggiornamento del programma non le tocchi mai. "
            f"Cambia l'impostazione «cartella» nel file «{file_config}»."
        )
    return {
        "permissions": {
            "deny": [
                f"Edit({percorso_per_le_regole(quaderno)}/**)",
                f"Edit({percorso_per_le_regole(file_config.resolve())})",
            ]
        }
    }
