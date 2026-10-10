"""Riga di comando di Hypomnema.

    python -m hypomnema proponi proposta.json   # passa una nota allo sportello
    python -m hypomnema proponi -               # legge la nota dall'ingresso standard
    python -m hypomnema cerca parola            # cerca le note che contengono la parola

Codici di uscita: 0 = tutto bene, 1 = nota rifiutata, 2 = errore di uso o di configurazione.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import TextIO

from hypomnema import __version__, cercatore, configurazione, sportello
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
    righe.append("testo:")
    righe += [f"  {riga}" if riga else "" for riga in nota.testo.split("\n")]
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
        print(f"- {motivo}", file=uscita)
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


def main(argv: list[str] | None = None, adesso: datetime | None = None, uscita: TextIO | None = None) -> int:
    """Punto d'ingresso. ``adesso`` e ``uscita`` servono ai test per avere risultati ripetibili."""
    if uscita is None:
        uscita = sys.stdout
        if hasattr(uscita, "reconfigure"):
            uscita.reconfigure(errors="replace")
    argomenti = _parser().parse_args(argv)
    try:
        config = configurazione.carica(argomenti.config)
    except configurazione.ErroreConfigurazione as errore:
        print(f"ERRORE: {errore}", file=uscita)
        return 2
    try:
        if argomenti.comando == "proponi":
            return _proponi(argomenti, config, adesso or datetime.now().astimezone(), uscita)
        return _cerca(argomenti, config, uscita)
    except NotaIlleggibile as errore:
        print(f"ERRORE: il quaderno contiene un file non valido: {errore}. "
              "Controlla se è stato modificato a mano.", file=uscita)
        return 2
