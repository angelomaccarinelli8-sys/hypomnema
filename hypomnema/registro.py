"""Il registro degli ingressi: ogni passaggio dallo sportello, accettato o rifiutato.

Il file si apre solo in aggiunta: nessuna riga viene mai modificata o tolta.
"""

import re
from datetime import datetime

from hypomnema.configurazione import Configurazione

INTESTAZIONE = (
    "# Registro degli ingressi\n"
    "\n"
    "Ogni riga è un passaggio dallo sportello. Questo file si allunga soltanto.\n"
    "\n"
)


# Tutti i caratteri che possono far andare a capo un testo.
A_CAPO = re.compile(r"\r\n|[\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029]")
SEGNO_A_CAPO = "⏎"


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
    nuovo = not config.file_registro.exists()
    with open(config.file_registro, "a", encoding="utf-8", newline="\n") as f:
        if nuovo:
            f.write(INTESTAZIONE)
        f.write(riga)
