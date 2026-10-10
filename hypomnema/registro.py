"""Il registro degli ingressi: ogni passaggio dallo sportello, accettato o rifiutato.

Il file si apre solo in aggiunta: nessuna riga viene mai modificata o tolta.
"""

from datetime import datetime

from hypomnema.configurazione import Configurazione

INTESTAZIONE = (
    "# Registro degli ingressi\n"
    "\n"
    "Ogni riga è un passaggio dallo sportello. Questo file si allunga soltanto.\n"
    "\n"
)


def annota(
    config: Configurazione,
    adesso: datetime,
    origine: str,
    id_nota: str | None,
    motivi: list[str],
) -> None:
    quando = adesso.isoformat(timespec="seconds")
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
