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

    ## Contesto scritto da Claude

    Sezione facoltativa, solo nelle note dell'utente.
"""

from dataclasses import dataclass

TITOLO_TESTO = "## Testo"
# Sezione facoltativa, dopo il testo: ciò che Claude aggiunge alle parole dell'utente.
TITOLO_CONTESTO = "## Contesto scritto da Claude"

# Ordine fisso dei campi di intestazione nel file Markdown.
# "conferma_di", "citazione" e "verifica" compaiono solo se presenti.
CAMPI_SEMPRE_PRESENTI = ("data", "fonte", "autore", "tipo", "natura")
CAMPI_INTESTAZIONE = CAMPI_SEMPRE_PRESENTI + ("conferma_di", "citazione", "da_risposta", "verifica")


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
    contesto: str | None = None
    # "sì" in una nota di Claude che salva un pezzo di una sua risposta.
    da_risposta: str | None = None
    # Scritta dallo sportello, non da Claude: dice se l'autore è stato verificato dal testimone.
    verifica: str | None = None

    def in_markdown(self) -> str:
        righe = [f"# Nota {self.id}", ""]
        for campo in CAMPI_INTESTAZIONE:
            valore = getattr(self, campo)
            if valore is not None:
                righe.append(f"- {campo}: {valore}")
        righe += ["", TITOLO_TESTO, "", self.testo, ""]
        if self.contesto is not None:
            righe += [TITOLO_CONTESTO, "", self.contesto, ""]
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

    corpo = righe[inizio_testo + 1:]
    contesto = None
    if TITOLO_CONTESTO in corpo:
        inizio_contesto = corpo.index(TITOLO_CONTESTO)
        contesto = "\n".join(corpo[inizio_contesto + 1:]).strip()
        corpo = corpo[:inizio_contesto]
    testo = "\n".join(corpo).strip()
    return Nota(id=id_nota, testo=testo, contesto=contesto, **campi)
