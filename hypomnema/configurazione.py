"""Lettura del file di configurazione ``hypomnema.toml``.

Ordine di ricerca del file:
1. il percorso passato con ``--config``;
2. il percorso nella variabile d'ambiente ``HYPOMNEMA_CONFIG``;
3. ``hypomnema.toml`` nella cartella corrente.
"""

import os
from datetime import datetime

try:
    import tomllib
except ImportError:  # Python 3.10: la copia di tomli, da cui è nato tomllib (vedi _tomli/LEGGIMI.md).
    from hypomnema import _tomli as tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

from hypomnema import fuso_del_sistema

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


# Il recap («dove eravamo rimasti»): quante voci mostrare per blocco. La sezione [recap] è
# facoltativa, perché i quaderni di prima della 0.4.0 non la hanno: se manca, valgono questi
# numeri, approvati da Angelo (15/10/2026; «todo» dalla 0.5.0).
RECAP_DI_BASE = {"discorsi_aperti": 5, "todo": 5, "decisioni": 5, "voci_diario": 10}

# La revisione (comando «review»): dopo quanti giorni senza versioni nuove un open o un todo aperto
# si segnala. Sezione facoltativa [revisione], dalla 0.6.0.
GIORNI_REVISIONE_DI_BASE = 30
# Il segno davanti al codice di una nota chiusa (✓T0049.3). Sezione facoltativa [codici], dalla 0.6.0:
# chi ha un terminale che non mostra ✓ può scrivere per esempio chiusa = "x".
SEGNO_CHIUSA_DI_BASE = "✓"


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
    # Quante voci mostra il recap per ogni blocco.
    recap_discorsi_aperti: int = RECAP_DI_BASE["discorsi_aperti"]
    recap_decisioni: int = RECAP_DI_BASE["decisioni"]
    recap_todo: int = RECAP_DI_BASE["todo"]
    recap_voci_diario: int = RECAP_DI_BASE["voci_diario"]
    giorni_revisione: int = GIORNI_REVISIONE_DI_BASE
    segno_chiusa: str = SEGNO_CHIUSA_DI_BASE
    # Il nome del fuso orario dell'impostazione facoltativa «fuso» di [quaderno] (dalla 0.6.1), per
    # esempio "Europe/Rome". Dalla 0.7.0 vale solo sulle macchine in UTC (chat, cloud): sul computer
    # dell'utente vale sempre il sistema operativo (vedi fuso_del_sistema).
    nome_fuso: str | None = None


def nel_fuso(config: "Configurazione", adesso: datetime) -> datetime:
    """L'ora da scrivere: vedi ``fuso_del_sistema``."""
    return fuso_del_sistema.nel_fuso(config, adesso)


def _fuso(file: Path, valore) -> str:
    """Il nome dell'impostazione «fuso». Si controlla solo la forma: se il fuso non si trova, non ferma
    niente (dalla 0.7.0, vedi fuso_del_sistema)."""
    if not isinstance(valore, str) or not valore.strip() or valore != valore.strip():
        raise ErroreConfigurazione(
            f"nel file «{file}» l'impostazione «fuso» deve essere il nome di un fuso orario tra virgolette, "
            'per esempio fuso = "Europe/Rome". Se non serve, toglila: vale l\'ora del sistema operativo.'
        )
    return valore


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

    # Facoltativa: quante voci mostra il recap. Ogni impostazione mancante vale come in RECAP_DI_BASE.
    recap = dati.get("recap", {})
    if not isinstance(recap, dict):
        raise ErroreConfigurazione(f"nel file «{file}» [recap] deve essere una sezione.")
    for chiave in recap:
        if chiave not in RECAP_DI_BASE:
            raise ErroreConfigurazione(
                f"nel file «{file}» la sezione [recap] non prevede «{chiave}»: le impostazioni sono "
                + ", ".join(RECAP_DI_BASE) + "."
            )
        valore = recap[chiave]
        # Il diario si può togliere dal recap (dalla 0.7.0): voci_diario = 0. Gli altri blocchi no.
        minimo = 0 if chiave == "voci_diario" else 1
        if not isinstance(valore, int) or isinstance(valore, bool) or valore < minimo:
            raise ErroreConfigurazione(
                f"nel file «{file}» l'impostazione «{chiave}» della sezione [recap] deve essere un numero "
                + ("intero, zero o più (quante voci mostrare; con 0 il blocco del diario non compare)."
                   if minimo == 0 else "intero maggiore di zero (quante voci mostrare).")
            )
    quanti_recap = {**RECAP_DI_BASE, **recap}

    revisione = dati.get("revisione", {})
    if not isinstance(revisione, dict):
        raise ErroreConfigurazione(f"nel file «{file}» [revisione] deve essere una sezione.")
    for chiave in revisione:
        if chiave != "giorni":
            raise ErroreConfigurazione(f"nel file «{file}» la sezione [revisione] non prevede «{chiave}»: "
                                       "l'impostazione è giorni.")
    giorni = revisione.get("giorni", GIORNI_REVISIONE_DI_BASE)
    if not isinstance(giorni, int) or isinstance(giorni, bool) or giorni < 1:
        raise ErroreConfigurazione(
            f"nel file «{file}» l'impostazione «giorni» della sezione [revisione] deve essere un numero "
            "intero maggiore di zero (dopo quanti giorni segnalare un open o un todo fermo)."
        )

    codici = dati.get("codici", {})
    if not isinstance(codici, dict):
        raise ErroreConfigurazione(f"nel file «{file}» [codici] deve essere una sezione.")
    for chiave in codici:
        if chiave != "chiusa":
            raise ErroreConfigurazione(f"nel file «{file}» la sezione [codici] non prevede «{chiave}»: "
                                       "l'impostazione è chiusa.")
    segno_chiusa = codici.get("chiusa", SEGNO_CHIUSA_DI_BASE)
    if (not isinstance(segno_chiusa, str) or not segno_chiusa.strip() or segno_chiusa != segno_chiusa.strip()
            or any(c.isdigit() or c.isspace() for c in segno_chiusa)):
        raise ErroreConfigurazione(
            f"nel file «{file}» l'impostazione «chiusa» della sezione [codici] deve essere un segno tra "
            'virgolette, senza spazi né cifre (per esempio "✓" oppure "x").'
        )

    nome_fuso = _fuso(file, sezione["fuso"]) if "fuso" in sezione else None

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
        recap_discorsi_aperti=quanti_recap["discorsi_aperti"],
        recap_decisioni=quanti_recap["decisioni"],
        recap_todo=quanti_recap["todo"],
        recap_voci_diario=quanti_recap["voci_diario"],
        giorni_revisione=giorni,
        segno_chiusa=segno_chiusa,
        nome_fuso=nome_fuso,
    )
