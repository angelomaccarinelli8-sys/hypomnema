"""Ciò che serve al plugin e all'avviabile per usare il quaderno in uso, fuori dal programma.

- La configurazione e il quaderno stanno in ``~/Hypomnema`` (su Windows ``%USERPROFILE%\\Hypomnema``),
  fuori dal plugin: un aggiornamento del plugin non li tocca mai.
- ``prepara`` (aggancio SessionStart, comando ``avvio``): la prima volta crea la configurazione dal
  modello e avvisa l'utente; a ogni sessione avvisa se il quaderno è dentro il programma, in una
  cartella sincronizzata o se i testimoni sono in pausa.
- ``protetto`` (aggancio PreToolUse, comando ``protezione``): un plugin non può portare regole di
  permesso, quindi è l'aggancio a fermare gli strumenti di Claude sui file del quaderno.
- ``impostazioni_claude``: le stesse regole come impostazioni di Claude Code, per l'avviabile.
"""

import os
import shutil
from pathlib import Path, PurePath, PureWindowsPath

from hypomnema import configurazione, testimone
from hypomnema.configurazione import Configurazione

# La cartella del programma: quella che contiene il pacchetto hypomnema (nel plugin installato,
# la copia che Claude Code tiene nella sua cache).
CARTELLA_PROGRAMMA = Path(__file__).resolve().parent.parent
MODELLO = CARTELLA_PROGRAMMA / "windows" / "hypomnema-uso.toml"

# Le variabili con cui Windows indica le cartelle di OneDrive, sincronizzate su internet.
VARIABILI_ONEDRIVE = ("OneDrive", "OneDriveConsumer", "OneDriveCommercial")


def configurazione_di_base() -> Path:
    """~/Hypomnema/hypomnema.toml (su Windows %USERPROFILE%\\Hypomnema\\hypomnema.toml)."""
    return Path.home() / "Hypomnema" / "hypomnema.toml"


def _dentro(percorso: Path, cartella: Path) -> bool:
    a = os.path.normcase(os.path.abspath(percorso))
    b = os.path.normcase(os.path.abspath(cartella))
    return a == b or a.startswith(b.rstrip("\\/") + os.sep)


def quaderno_nel_programma(config: Configurazione) -> bool:
    return _dentro(config.cartella_quaderno.resolve(), CARTELLA_PROGRAMMA)


def cartella_sincronizzata(config: Configurazione) -> str | None:
    """La cartella di OneDrive che contiene il quaderno, se c'è."""
    for nome in VARIABILI_ONEDRIVE:
        cartella = os.environ.get(nome)
        if cartella and _dentro(config.cartella_quaderno.resolve(), Path(cartella)):
            return cartella
    return None


def prepara(file_config: Path) -> list[str]:
    """Gli avvisi per l'utente a inizio sessione. La prima volta crea la configurazione."""
    avvisi = []
    if not file_config.exists():
        file_config.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(MODELLO, file_config)
        avvisi.append(
            f"Hypomnema: è la prima volta. Ho creato la configurazione «{file_config}» con il testimone "
            "dei tuoi messaggi e quello delle risposte di Claude ACCESI: da ora registrano tutto quello "
            "che scrivi in Claude Code, in ogni progetto, nel quaderno accanto alla configurazione. "
            "Un messaggio che comincia con #privato non viene registrato; per una pausa scrivi "
            "/hypomnema:pause (o /hypomnema:pausa) e per riprendere /hypomnema:resume (o /hypomnema:riprendi); per spegnerli metti attivo = false "
            "nella configurazione."
        )
    try:
        config = configurazione.carica(str(file_config))
    except configurazione.ErroreConfigurazione as errore:
        return avvisi + [f"Hypomnema: la configurazione non va bene, i testimoni non registrano: {errore}"]
    if quaderno_nel_programma(config):
        avvisi.append(
            f"Hypomnema, ATTENZIONE: il quaderno «{config.cartella_quaderno}» è dentro la cartella del "
            "programma, che un aggiornamento sostituisce. I testimoni non registrano finché non cambi "
            f"«cartella» in «{file_config}»."
        )
    sincronizzata = cartella_sincronizzata(config)
    if sincronizzata:
        avvisi.append(
            f"Hypomnema, ATTENZIONE: il quaderno «{config.cartella_quaderno}» è dentro OneDrive "
            f"(«{sincronizzata}»): viene copiato su internet. Se non lo vuoi, cambia «cartella» in «{file_config}»."
        )
    if config.testimone_attivo:
        try:
            pausa = testimone.in_pausa(testimone.leggi_messaggi(config))
        except testimone.ErroreTestimone as errore:
            avvisi.append(f"Hypomnema: il file del testimone non si legge: {errore}")
            pausa = None
        if pausa is not None:
            avvisi.append(f"Hypomnema: i testimoni sono in pausa dal {pausa.quando}. "
                          "Per riprendere scrivi /hypomnema:resume (o /hypomnema:riprendi).")
    return avvisi


def protetto(file_config: Path, percorso: str) -> bool:
    """True se il percorso è il file di configurazione o un file del quaderno."""
    try:
        config = configurazione.carica(str(file_config))
    except configurazione.ErroreConfigurazione:
        return False
    bersaglio = Path(percorso)
    return _dentro(bersaglio, file_config) or _dentro(bersaglio, config.cartella_quaderno)


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
    if quaderno_nel_programma(config):
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
