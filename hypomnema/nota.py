"""La nota: com'è fatta, come si scrive in Markdown e come si rilegge.

Esempio di file di nota salvato nel quaderno::

    # Nota 0001

    - data: 2026-01-10
    - fonte: chat del 10 gennaio 2026
    - autore: utente
    - tipo: dichiarata
    - natura: fatto

    ## Testo

    Il testo della nota, anche su più righe.
"""

from dataclasses import dataclass

TITOLO_TESTO = "## Testo"

# Ordine fisso dei campi di intestazione nel file Markdown.
# "conferma_di", "citazione" e "verifica" compaiono solo se presenti.
CAMPI_SEMPRE_PRESENTI = ("data", "fonte", "autore", "tipo", "natura")
CAMPI_INTESTAZIONE = CAMPI_SEMPRE_PRESENTI + ("conferma_di", "citazione", "verifica")


class NotaIlleggibile(Exception):
    """Un file del quaderno non ha il formato previsto."""


@dataclass(frozen=True)
class Nota:
    id: str
    data: str
    fonte: str
    autore: str
    tipo: str
    natura: str
    testo: str
    conferma_di: str | None = None
    citazione: str | None = None
    # Scritta dallo sportello, non da Claude: dice se l'autore è stato verificato dal testimone.
    verifica: str | None = None

    def in_markdown(self) -> str:
        righe = [f"# Nota {self.id}", ""]
        for campo in CAMPI_INTESTAZIONE:
            valore = getattr(self, campo)
            if valore is not None:
                righe.append(f"- {campo}: {valore}")
        righe += ["", TITOLO_TESTO, "", self.testo, ""]
        return "\n".join(righe)


def da_markdown(id_nota: str, contenuto: str) -> Nota:
    righe = contenuto.split("\n")
    try:
        inizio_testo = righe.index(TITOLO_TESTO)
    except ValueError:
        raise NotaIlleggibile(f"nella nota {id_nota} manca la sezione «{TITOLO_TESTO}»")

    campi: dict[str, str] = {}
    for riga in righe[:inizio_testo]:
        if not riga.startswith("- "):
            continue
        chiave, separatore, valore = riga[2:].partition(": ")
        if separatore and chiave in CAMPI_INTESTAZIONE:
            campi[chiave] = valore

    mancanti = [c for c in CAMPI_SEMPRE_PRESENTI if c not in campi]
    if mancanti:
        raise NotaIlleggibile(f"nella nota {id_nota} mancano: {', '.join(mancanti)}")

    testo = "\n".join(righe[inizio_testo + 1:]).strip()
    return Nota(id=id_nota, testo=testo, **campi)
