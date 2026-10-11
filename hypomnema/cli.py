"""Riga di comando di Hypomnema.

    python -m hypomnema proponi proposta.json   # passa una nota allo sportello
    python -m hypomnema proponi -               # legge la nota dall'ingresso standard
    python -m hypomnema cerca parola            # cerca le note che contengono la parola
    python -m hypomnema testimone               # registra un messaggio (lo lancia Claude Code)
    python -m hypomnema stato                   # dice se il testimone è acceso e l'ultimo messaggio
    python -m hypomnema impostazioni-claude     # le regole che l'avviabile passa a Claude Code

Codici di uscita: 0 = tutto bene, 1 = nota rifiutata, 2 = errore di uso o di configurazione.
Il comando "testimone" non esce mai con 2: per Claude Code vorrebbe dire bloccare il
messaggio dell'utente. In caso di errore esce con 1 e lo scrive sull'uscita degli errori.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import TextIO

from hypomnema import __version__, avvio, cercatore, configurazione, registro, sportello, testimone
from hypomnema.nota import Nota, NotaIlleggibile

ORIGINE_DIRETTA = "(ingresso diretto)"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hypomnema",
        description="Hypomnema: Claude propone le note, i programmi decidono se entrano.",
    )
    parser.add_argument("--version", action="version", version=f"hypomnema {__version__}")
    parser.add_argument(
        "--config",
        help="percorso del file hypomnema.toml (altrimenti HYPOMNEMA_CONFIG o la cartella corrente)",
    )
    comandi = parser.add_subparsers(dest="comando", required=True, metavar="comando")

    proponi = comandi.add_parser("proponi", help="passa una nota allo sportello")
    proponi.add_argument("file", help="file JSON con la nota proposta, oppure - per leggerla dall'ingresso standard")

    cerca = comandi.add_parser("cerca", help="cerca le note che contengono una parola")
    cerca.add_argument("parola", help="la parola (o le parole) da cercare, così come sono")

    registra = comandi.add_parser(
        "testimone", help="registra un messaggio dell'utente (lo lancia Claude Code a ogni messaggio)"
    )
    registra.add_argument(
        "file", nargs="?", default="-",
        help="file JSON con il messaggio, come lo manda Claude Code (di base: ingresso standard)",
    )

    comandi.add_parser(
        "stato", help="dice se il testimone è acceso, dov'è il quaderno e l'ultimo messaggio registrato"
    )
    comandi.add_parser(
        "impostazioni-claude",
        help="scrive le regole che vietano a Claude di modificare quaderno e configurazione (per l'avviabile)",
    )
    return parser


def _descrivi(nota: Nota) -> list[str]:
    righe = [
        f"--- Nota {nota.id} ---",
        f"data: {nota.data}",
        f"fonte: {nota.fonte}",
        f"autore: {nota.autore}",
        f"tipo: {nota.tipo}",
        f"natura: {nota.natura}",
    ]
    if nota.conferma_di is not None:
        righe.append(f"conferma di: nota {nota.conferma_di}")
    if nota.citazione is not None:
        righe.append(f"citazione: {nota.citazione}")
    if nota.verifica is not None:
        righe.append(f"verifica: {nota.verifica}")
    righe.append("testo:")
    righe += _rientrato(nota.testo)
    if nota.contesto is not None:
        righe.append("contesto scritto da Claude:")
        righe += _rientrato(nota.contesto)
    return righe


def _proponi(argomenti, config, adesso: datetime, uscita: TextIO) -> int:
    if argomenti.file == "-":
        dati = sys.stdin.buffer.read()
        origine = ORIGINE_DIRETTA
    else:
        file = Path(argomenti.file)
        if not file.is_file():
            print(f"ERRORE: non trovo il file «{file}».", file=uscita)
            return 2
        dati = file.read_bytes()
        origine = file.name
    esito = sportello.ricevi(dati, origine, config, adesso)

    if esito.accettata:
        relativo = esito.percorso.relative_to(config.cartella_quaderno).as_posix()
        print(f"ACCETTATA: la nota {esito.id_nota} è stata salvata nel quaderno ({relativo}).", file=uscita)
        print("Il passaggio è annotato nel registro.", file=uscita)
        return 0
    print("RIFIUTATA: la nota non è stata salvata.", file=uscita)
    print("Motivi:", file=uscita)
    for motivo in esito.motivi:
        # Come nel registro: un motivo sta su una riga, così nessuna riga falsa
        # (per esempio un finto "ACCETTATA") può comparire nella risposta che legge Claude.
        print(f"- {registro.su_una_riga(motivo)}", file=uscita)
    print("Il passaggio è annotato nel registro.", file=uscita)
    return 1


def _cerca(argomenti, config, uscita: TextIO) -> int:
    parola = argomenti.parola.strip()
    if not parola:
        print("ERRORE: serve una parola da cercare.", file=uscita)
        return 2
    trovate = cercatore.cerca(config, parola)
    if not trovate:
        print(f"Nessuna nota contiene «{parola}».", file=uscita)
        return 0
    if len(trovate) == 1:
        print(f"Trovata 1 nota con «{parola}».", file=uscita)
    else:
        print(f"Trovate {len(trovate)} note con «{parola}».", file=uscita)
    for nota in trovate:
        print("", file=uscita)
        for riga in _descrivi(nota):
            print(riga, file=uscita)
    return 0


def _rientrato(testo: str) -> list[str]:
    return [f"  {riga}" if riga else "" for riga in testo.split("\n")]


def _stato(argomenti, config, uscita: TextIO) -> int:
    """Solo lettura: non crea e non modifica niente."""
    righe = [
        f"Configurazione: {configurazione.trova(argomenti.config).resolve()}",
        f"Quaderno: {config.cartella_quaderno}",
    ]
    if config.testimone_attivo:
        righe.append("Testimone: ACCESO (registra le parole esatte di ogni messaggio dell'utente).")
    else:
        righe.append(
            "Testimone: SPENTO (nella configurazione attivo = false): i messaggi non vengono registrati "
            "e le note con autore «utente» saranno marcate «autore non verificato»."
        )
    righe.append(f"File del testimone: {config.file_testimone}")
    messaggi = testimone.leggi_messaggi(config)
    righe.append(f"Messaggi registrati: {len(messaggi)}")
    if not messaggi:
        righe.append("Ultimo messaggio registrato: nessuno.")
    elif messaggi[-1].testo is None:
        righe.append(f"Ultimo messaggio registrato: {messaggi[-1].quando} ({testimone.DICITURA_PRIVATO}).")
    else:
        righe.append(f"Ultimo messaggio registrato: {messaggi[-1].quando}")
        righe.append("Testo dell'ultimo messaggio:")
        righe += _rientrato(messaggi[-1].testo)
    for riga in righe:
        print(riga, file=uscita)
    return 0


def _impostazioni_claude(argomenti, config, uscita: TextIO) -> int:
    try:
        impostazioni = avvio.impostazioni_claude(config, configurazione.trova(argomenti.config))
    except avvio.ErroreAvvio as errore:
        print(f"ERRORE: {errore}", file=uscita)
        return 2
    # Solo caratteri ASCII: il testo passa intatto anche dalla riga di comando di Windows.
    print(json.dumps(impostazioni, ensure_ascii=True), file=uscita)
    return 0


def _testimone(argomenti, adesso: datetime, errori: TextIO) -> int:
    # Su successo non scrive niente: per Claude Code, ciò che esce qui finirebbe nella chat.
    try:
        config = configurazione.carica(argomenti.config)
        if argomenti.file == "-":
            dati = sys.stdin.buffer.read()
        else:
            dati = Path(argomenti.file).read_bytes()
        testimone.registra(config, adesso, dati)
    except (configurazione.ErroreConfigurazione, testimone.ErroreTestimone, OSError) as errore:
        print(f"ERRORE del testimone: {errore} Il messaggio NON è stato registrato.", file=errori)
        return 1
    return 0


def main(
    argv: list[str] | None = None,
    adesso: datetime | None = None,
    uscita: TextIO | None = None,
    errori: TextIO | None = None,
) -> int:
    """Punto d'ingresso. ``adesso``, ``uscita`` ed ``errori`` servono ai test per avere risultati ripetibili."""
    # Sempre UTF-8: chi legge l'uscita (Claude, Git Bash) si aspetta UTF-8, anche su Windows
    # dove Python userebbe altrimenti la vecchia codifica di sistema. Nella finestra della
    # console non cambia niente: lì Python scrive già correttamente.
    if uscita is None:
        uscita = sys.stdout
        if hasattr(uscita, "reconfigure"):
            uscita.reconfigure(encoding="utf-8", errors="replace")
    if errori is None:
        errori = sys.stderr
        if hasattr(errori, "reconfigure"):
            errori.reconfigure(encoding="utf-8", errors="replace")
    try:
        argomenti = _parser().parse_args(argv)
    except SystemExit as uscita_argparse:
        # Un comando scritto male esce con 2; per il testimone vorrebbe dire bloccare il messaggio.
        elenco = sys.argv[1:] if argv is None else argv
        if uscita_argparse.code == 2 and "testimone" in elenco:
            return 1
        raise
    adesso = adesso or datetime.now().astimezone()
    if argomenti.comando == "testimone":
        return _testimone(argomenti, adesso, errori)
    try:
        config = configurazione.carica(argomenti.config)
    except configurazione.ErroreConfigurazione as errore:
        print(f"ERRORE: {errore}", file=uscita)
        return 2
    try:
        if argomenti.comando == "proponi":
            return _proponi(argomenti, config, adesso, uscita)
        if argomenti.comando == "stato":
            return _stato(argomenti, config, uscita)
        if argomenti.comando == "impostazioni-claude":
            return _impostazioni_claude(argomenti, config, uscita)
        return _cerca(argomenti, config, uscita)
    except NotaIlleggibile as errore:
        print(f"ERRORE: il quaderno contiene un file non valido: {errore}. "
              "Controlla se è stato modificato a mano.", file=uscita)
        return 2
    except testimone.ErroreTestimone as errore:
        print(f"ERRORE: {errore}", file=uscita)
        return 2
