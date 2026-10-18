"""Il registro degli ingressi: ogni passaggio dallo sportello, accettato o rifiutato.

Il file si apre solo in aggiunta: nessuna riga viene mai modificata o tolta.
"""

import re
import time
from datetime import datetime

from hypomnema import aggiunta
from hypomnema.configurazione import Configurazione

INTESTAZIONE = (
    "# Registro degli ingressi\n"
    "\n"
    "Ogni riga è un passaggio dallo sportello. Questo file si allunga soltanto.\n"
    "\n"
)


# Le sole due forme di riga che "annota" scrive. Servono a "cambiati" e "controlla"
# per riconoscere le righe dello sportello.
_QUANDO = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2}|Z)?"
RIGA_ACCETTATA = re.compile(rf"- {_QUANDO} \| ACCETTATA \| nota (\d+(?:\.\d+)?) \| da: [^\n]*")
RIGA_RIFIUTATA = re.compile(rf"- {_QUANDO} \| RIFIUTATA \| da: [^\n]* \| motivi: [^\n]*")

# Tutti i caratteri che possono far andare a capo un testo.
A_CAPO = re.compile(r"\r\n|[\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029]")
SEGNO_A_CAPO = "⏎"


class RegistroToccato(Exception):
    """Il registro non finisce con un a capo: qualcuno l'ha toccato a mano."""


def controlla_fine(config: Configurazione) -> None:
    """Se il registro esiste, deve finire con un a capo, come lo lascia sempre lo sportello.

    Altrimenti la prossima riga dello sportello si attaccherebbe a quella scritta a mano.
    Lo sportello non ripara il registro: si ferma e lo dice.
    """
    if config.file_registro.exists() and not config.file_registro.read_bytes().endswith(b"\n"):
        raise RegistroToccato(
            f"il registro è stato toccato a mano: non finisce con un a capo ({config.file_registro}). "
            "Non ho scritto niente, né la nota né la riga nel registro. Controlla l'ultima riga del "
            "registro e sistemala tu: lo sportello non lo ripara da solo."
        )


def su_una_riga(testo: str) -> str:
    """Sostituisce ogni a capo con il segno ⏎: un passaggio non può mai occupare più righe."""
    return A_CAPO.sub(SEGNO_A_CAPO, testo)


def annota(
    config: Configurazione,
    adesso: datetime,
    origine: str,
    id_nota: str | None,
    motivi: list[str],
) -> None:
    quando = adesso.isoformat(timespec="seconds")
    # Nome del file e motivi possono contenere testo della proposta: senza questa pulizia
    # un "a capo" permetterebbe di aggiungere al registro righe false.
    origine = su_una_riga(origine)
    motivi = [su_una_riga(m) for m in motivi]
    if id_nota is not None:
        riga = f"- {quando} | ACCETTATA | nota {id_nota} | da: {origine}\n"
    else:
        riga = f"- {quando} | RIFIUTATA | da: {origine} | motivi: {' / '.join(motivi)}\n"

    config.cartella_quaderno.mkdir(parents=True, exist_ok=True)
    _intestazione(config.file_registro)
    # Una sola scrittura in aggiunta: anche se un'altra macchina scrive intanto (il blocco non passa
    # da una macchina all'altra), le due righe non si sovrappongono mai.
    aggiunta.aggiungi(config.file_registro, riga)


# Quanto si aspetta che un altro passaggio finisca di scrivere l'intestazione di un registro nuovo.
ATTESA_INTESTAZIONE = 2.0


def _intestazione(file) -> None:
    """Un registro nuovo nasce con la sua intestazione, una volta sola anche con due scrittori insieme."""
    try:
        # Apertura esclusiva: se due passaggi creano il registro insieme, uno solo scrive l'intestazione.
        with open(file, "x", encoding="utf-8", newline="\n") as f:
            f.write(INTESTAZIONE)
        return
    except FileExistsError:
        pass
    # L'altro passaggio ha appena creato il file: si aspetta che l'intestazione ci sia, prima di aggiungere.
    scadenza = time.monotonic() + ATTESA_INTESTAZIONE
    while file.stat().st_size < len(INTESTAZIONE.encode("utf-8")) and time.monotonic() < scadenza:
        time.sleep(0.02)
