"""Lettura del file di configurazione ``hypomnema.toml``.

Ordine di ricerca del file:
1. il percorso passato con ``--config``;
2. il percorso nella variabile d'ambiente ``HYPOMNEMA_CONFIG``;
3. ``hypomnema.toml`` nella cartella corrente.
"""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

NOME_FILE = "hypomnema.toml"
VARIABILE_AMBIENTE = "HYPOMNEMA_CONFIG"


# Le righe di hypomnema.toml del repository, citate nei messaggi d'errore per dire
# esattamente cosa aggiungere. Non sono valori di riserva: se manca, il programma si ferma.
RIGHE_DI_ESEMPIO = {
    "cartella": 'cartella = "quaderno"',
    "cartella_note": 'cartella_note = "note"',
    "file_registro": 'file_registro = "registro.md"',
    "file": 'file = "testimone.jsonl"',
    "prefisso_privato": 'prefisso_privato = "#privato"',
    "segno_citazione": 'segno_citazione = ">"',
}


class ErroreConfigurazione(Exception):
    """La configurazione manca o non è valida."""


@dataclass(frozen=True)
class Configurazione:
    cartella_quaderno: Path
    cartella_note: Path
    file_registro: Path
    cifre_numero_nota: int
    testimone_attivo: bool
    file_testimone: Path
    prefisso_privato: str
    segno_citazione: str


def trova(percorso: str | None = None) -> Path:
    if percorso:
        return Path(percorso)
    da_ambiente = os.environ.get(VARIABILE_AMBIENTE)
    if da_ambiente:
        return Path(da_ambiente)
    return Path.cwd() / NOME_FILE


def carica(percorso: str | None = None) -> Configurazione:
    file = trova(percorso)
    if not file.is_file():
        raise ErroreConfigurazione(
            f"non trovo il file di configurazione «{file}». "
            f"Lancia il comando dalla cartella che contiene {NOME_FILE}, "
            f"oppure indica il file con --config o con la variabile {VARIABILE_AMBIENTE}."
        )
    try:
        # "utf-8-sig" accetta anche il segno invisibile (BOM) che alcuni programmi Windows,
        # come PowerShell 5.1, mettono all'inizio dei file salvati in UTF-8.
        dati = tomllib.loads(file.read_text(encoding="utf-8-sig"))
    except UnicodeDecodeError:
        raise ErroreConfigurazione(f"il file «{file}» non è salvato in UTF-8: salvalo in UTF-8 e riprova.")
    except tomllib.TOMLDecodeError as errore:
        raise ErroreConfigurazione(f"il file «{file}» non è scritto correttamente: {errore}")

    sezione = dati.get("quaderno")
    if not isinstance(sezione, dict):
        raise ErroreConfigurazione(f"nel file «{file}» manca la sezione [quaderno].")

    testimone = dati.get("testimone")
    if not isinstance(testimone, dict):
        raise ErroreConfigurazione(
            f"nel file «{file}» manca la sezione [testimone]: copiala dal file hypomnema.toml "
            "del repository (con attivo = false il testimone resta spento)."
        )

    def testo(chiave: str, origine: dict = sezione) -> str:
        valore = origine.get(chiave)
        if not isinstance(valore, str) or not valore.strip():
            nome_sezione = "[testimone]" if origine is testimone else "[quaderno]"
            raise ErroreConfigurazione(
                f"nel file «{file}» manca l'impostazione «{chiave}» della sezione {nome_sezione} "
                f"(deve essere un testo). Aggiungi alla sezione {nome_sezione} questa riga, "
                f"come nel file hypomnema.toml del repository:  {RIGHE_DI_ESEMPIO[chiave]}"
            )
        return valore

    def dentro_il_quaderno(chiave: str, origine: dict = sezione) -> str:
        valore = testo(chiave, origine)
        # Si controllano entrambe le forme, Windows e macOS/Linux, perché il file può viaggiare.
        come_windows = PureWindowsPath(valore)
        if come_windows.anchor or PurePosixPath(valore).is_absolute() or ".." in come_windows.parts:
            raise ErroreConfigurazione(
                f"nel file «{file}» l'impostazione «{chiave}» deve indicare un posto dentro la "
                f"cartella del quaderno, per esempio  {RIGHE_DI_ESEMPIO[chiave]}  : niente percorsi "
                "completi (come C:/... o /home/...) e niente «..». Per spostare tutto il quaderno "
                "cambia l'impostazione «cartella»."
            )
        return valore

    cifre = sezione.get("cifre_numero_nota")
    if not isinstance(cifre, int) or isinstance(cifre, bool) or cifre < 1:
        raise ErroreConfigurazione(
            f"nel file «{file}» l'impostazione «cifre_numero_nota» deve essere un numero intero maggiore di zero."
        )

    attivo = testimone.get("attivo")
    if not isinstance(attivo, bool):
        raise ErroreConfigurazione(
            f"nel file «{file}» l'impostazione «attivo» della sezione [testimone] "
            "deve essere true (acceso) oppure false (spento)."
        )

    base = file.resolve().parent
    quaderno = base / testo("cartella")
    return Configurazione(
        cartella_quaderno=quaderno,
        cartella_note=quaderno / dentro_il_quaderno("cartella_note"),
        file_registro=quaderno / dentro_il_quaderno("file_registro"),
        cifre_numero_nota=cifre,
        testimone_attivo=attivo,
        file_testimone=quaderno / dentro_il_quaderno("file", testimone),
        prefisso_privato=testo("prefisso_privato", testimone).strip(),
        segno_citazione=testo("segno_citazione", testimone).strip(),
    )
