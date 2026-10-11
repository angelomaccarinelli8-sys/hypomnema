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
    # True nella configurazione per la chat di Claude, dove il testimone non esiste.
    in_chat: bool
    # Il testimone delle risposte di Claude (sezione [risposte], facoltativa: se manca è spento).
    sezione_risposte: bool
    risposte_attive: bool
    file_risposte: Path | None
    ometti_codice: bool
    file_testimone: Path
    prefisso_privato: str
    segno_citazione: str
    # La copia dell'archivio della chat (sezione [archivio], facoltativa, solo per la chat).
    file_archivio: Path | None = None
    file_diario_chat: Path | None = None
    archivio_ometti_codice: bool = True
    copia_ogni: int | None = None


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

    # Facoltativa: c'è solo nella configurazione per la chat. Senza, tutto resta come prima.
    modalita = testimone.get("modalita")
    if modalita is not None and modalita != "chat":
        raise ErroreConfigurazione(
            f"nel file «{file}» l'impostazione «modalita» della sezione [testimone] può valere solo "
            '"chat" (configurazione per la chat di Claude); altrimenti va tolta.'
        )
    in_chat = modalita == "chat"
    if in_chat and attivo:
        raise ErroreConfigurazione(
            f"nel file «{file}» c'è modalita = \"chat\" ma il testimone è acceso: nella chat di Claude "
            "il testimone non esiste, quindi serve attivo = false."
        )

    # Facoltativa: senza la sezione [risposte] il testimone delle risposte è spento.
    risposte = dati.get("risposte")
    if risposte is not None and not isinstance(risposte, dict):
        raise ErroreConfigurazione(f"nel file «{file}» [risposte] deve essere una sezione.")
    risposte_attive = ometti_codice = False
    file_risposte_nome = None
    if risposte is not None:
        for chiave, spiegazione in (("attivo", "true (acceso) oppure false (spento)"),
                                    ("ometti_codice", "true (blocchi di codice omessi) oppure false (registrati interi)")):
            if not isinstance(risposte.get(chiave), bool):
                raise ErroreConfigurazione(
                    f"nel file «{file}» l'impostazione «{chiave}» della sezione [risposte] deve essere {spiegazione}."
                )
        risposte_attive, ometti_codice = risposte["attivo"], risposte["ometti_codice"]
        file_risposte_nome = risposte.get("file")
        come_windows = PureWindowsPath(file_risposte_nome) if isinstance(file_risposte_nome, str) else None
        if (
            come_windows is None or not file_risposte_nome.strip() or come_windows.anchor
            or PurePosixPath(file_risposte_nome).is_absolute() or ".." in come_windows.parts
        ):
            raise ErroreConfigurazione(
                f"nel file «{file}» l'impostazione «file» della sezione [risposte] deve indicare un "
                'posto dentro la cartella del quaderno, per esempio  file = "risposte.jsonl"  .'
            )
        if risposte_attive and in_chat:
            raise ErroreConfigurazione(
                f"nel file «{file}» il testimone delle risposte è acceso, ma nella chat di Claude non "
                "esiste: con modalita = \"chat\" serve [risposte] attivo = false."
            )
        if risposte_attive and not attivo:
            raise ErroreConfigurazione(
                f"nel file «{file}» il testimone delle risposte è acceso ma quello dell'utente è spento: "
                "le risposte si registrano solo insieme ai messaggi, perché serve sapere se il messaggio "
                "era privato. Accendi anche [testimone] attivo = true, oppure spegni [risposte]."
            )

    # Facoltativa e solo nella configurazione per la chat: la copia dell'archivio della chat.
    archivio = dati.get("archivio")
    if archivio is not None:
        if not isinstance(archivio, dict):
            raise ErroreConfigurazione(f"nel file «{file}» [archivio] deve essere una sezione.")
        if not in_chat:
            raise ErroreConfigurazione(
                f"nel file «{file}» c'è la sezione [archivio], che serve solo nella chat di Claude: "
                'va insieme a modalita = "chat" nella sezione [testimone].'
            )
        for chiave in ("file", "file_diario"):
            valore = archivio.get(chiave)
            come_windows = PureWindowsPath(valore) if isinstance(valore, str) else None
            if (
                come_windows is None or not valore.strip() or come_windows.anchor
                or PurePosixPath(valore).is_absolute() or ".." in come_windows.parts
            ):
                raise ErroreConfigurazione(
                    f"nel file «{file}» l'impostazione «{chiave}» della sezione [archivio] deve indicare un "
                    "posto dentro la cartella del quaderno, per esempio  "
                    + ('file = "archivio-chat.jsonl"' if chiave == "file" else 'file_diario = "diario-chat.jsonl"')
                )
        if not isinstance(archivio.get("ometti_codice"), bool):
            raise ErroreConfigurazione(
                f"nel file «{file}» l'impostazione «ometti_codice» della sezione [archivio] deve essere "
                "true (blocchi di codice omessi) oppure false (registrati interi)."
            )
        copia_ogni = archivio.get("copia_ogni")
        if not isinstance(copia_ogni, int) or isinstance(copia_ogni, bool) or copia_ogni < 1:
            raise ErroreConfigurazione(
                f"nel file «{file}» l'impostazione «copia_ogni» della sezione [archivio] deve essere un "
                "numero intero maggiore di zero (ogni quanti scambi copiare dall'archivio)."
            )

    base = file.resolve().parent
    quaderno = base / testo("cartella")
    return Configurazione(
        cartella_quaderno=quaderno,
        cartella_note=quaderno / dentro_il_quaderno("cartella_note"),
        file_registro=quaderno / dentro_il_quaderno("file_registro"),
        cifre_numero_nota=cifre,
        testimone_attivo=attivo,
        in_chat=in_chat,
        sezione_risposte=risposte is not None,
        risposte_attive=risposte_attive,
        file_risposte=quaderno / file_risposte_nome if file_risposte_nome else None,
        ometti_codice=ometti_codice,
        file_testimone=quaderno / dentro_il_quaderno("file", testimone),
        prefisso_privato=testo("prefisso_privato", testimone).strip(),
        segno_citazione=testo("segno_citazione", testimone).strip(),
        file_archivio=quaderno / archivio["file"] if archivio is not None else None,
        file_diario_chat=quaderno / archivio["file_diario"] if archivio is not None else None,
        archivio_ometti_codice=archivio["ometti_codice"] if archivio is not None else True,
        copia_ogni=archivio["copia_ogni"] if archivio is not None else None,
    )
