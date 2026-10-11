"""Esegue un esempio della cartella ``esempi/`` in un quaderno vuoto e temporaneo.

Ogni esempio ha un file ``comandi.txt`` (un comando per riga, come si scriverebbe
dopo ``hypomnema``) e una cartella ``atteso/`` con:
- ``uscita.txt``: ciò che il programma deve scrivere a schermo;
- ``quaderno/``: come deve risultare il quaderno alla fine (note, registro, testimone).

Se l'esempio ha un suo ``hypomnema.toml`` si usa quello (per esempio per accendere
il testimone); altrimenti la configurazione di prova qui sotto, con il testimone spento.
Nei comandi, ``proponi FILE`` e ``testimone FILE`` usano file della cartella dell'esempio:
``testimone FILE`` simula un messaggio dell'utente come lo manderebbe Claude Code.

I percorsi della cartella temporanea (che cambiano da computer a computer, per esempio
nell'uscita di ``stato``) vengono scritti come ``<cartella di prova>/...``, con le barre
"/" anche su Windows.

Per avere risultati ripetibili l'ora di ogni comando è fissa:
il primo comando avviene il 15 gennaio 2026 alle 10:00 (ora italiana),
ogni comando successivo un minuto dopo.
"""

import io
import re
import shlex
from datetime import datetime, timedelta, timezone
from pathlib import Path

from hypomnema.cli import main

RADICE = Path(__file__).resolve().parent.parent
CARTELLA_ESEMPI = RADICE / "esempi"
ORA_DI_PARTENZA = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone(timedelta(hours=1)))

CONFIG_DI_PROVA = """\
[quaderno]
cartella = "quaderno"
cartella_note = "note"
file_registro = "registro.md"
cifre_numero_nota = 4

[testimone]
attivo = false
file = "testimone.jsonl"
prefisso_privato = "#privato"
segno_citazione = ">"
"""


CARTELLA_DI_PROVA = "<cartella di prova>"


def senza_cartella_di_prova(testo: str, lavoro: Path) -> str:
    radice = str(lavoro.resolve())
    schema = re.compile(re.escape(radice) + r"[^\s«»]*")
    return schema.sub(lambda m: CARTELLA_DI_PROVA + m.group(0)[len(radice):].replace("\\", "/"), testo)


def elenco_esempi() -> list[Path]:
    return sorted(p for p in CARTELLA_ESEMPI.iterdir() if (p / "comandi.txt").is_file())


def esegui(esempio: Path, lavoro: Path) -> str:
    """Esegue i comandi dell'esempio con un quaderno in ``lavoro``; restituisce l'uscita."""
    config = lavoro / "hypomnema.toml"
    proprio = esempio / "hypomnema.toml"
    testo_config = proprio.read_text(encoding="utf-8") if proprio.is_file() else CONFIG_DI_PROVA
    config.write_text(testo_config, encoding="utf-8")
    comandi = (esempio / "comandi.txt").read_text(encoding="utf-8").splitlines()
    uscita = io.StringIO()
    for numero, riga in enumerate(c for c in comandi if c.strip()):
        parti = shlex.split(riga)
        if parti[0] in ("proponi", "testimone"):
            argomenti = [parti[0], str(esempio / parti[1])]
        else:
            argomenti = parti
        uscita.write(f"$ hypomnema {riga}\n")
        codice = main(
            ["--config", str(config), *argomenti],
            adesso=ORA_DI_PARTENZA + timedelta(minutes=numero),
            uscita=uscita,
            errori=uscita,
        )
        uscita.write(f"[codice di uscita: {codice}]\n\n")
    return senza_cartella_di_prova(uscita.getvalue(), lavoro)


def file_di(cartella: Path) -> dict[str, str]:
    """Tutti i file di una cartella, come {percorso relativo: contenuto}."""
    if not cartella.is_dir():
        return {}
    return {
        p.relative_to(cartella).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(cartella.rglob("*"))
        if p.is_file()
    }
