"""La nota: com'è fatta, come si scrive in Markdown e come si rilegge.

Dalla versione 0.5.0 le note nuove si scrivono con la struttura in inglese::

    # Note 0001

    - date: 2026-01-10
    - source: chat of 10 January 2026
    - author: user
    - knowledge: stated
    - kind: fact

    ## Text

    Il testo della nota, anche su più righe (le parole restano nella loro lingua).

    ## Context written by Claude

    Sezione facoltativa, solo nelle note dell'utente.

Le note scritte prima (``# Nota``, ``- data:``, ``## Testo``, ``## Contesto scritto da Claude``,
valori come «utente», «dichiarata», «discorso aperto») si leggono come prima e non si riscrivono
mai: chi legge riceve sempre i valori in inglese.
"""

from dataclasses import dataclass

TITOLO_TESTO = "## Text"
# Sezione facoltativa, dopo il testo: ciò che Claude aggiunge alle parole dell'utente.
TITOLO_CONTESTO = "## Context written by Claude"
# I titoli delle note scritte prima della 0.5.0, letti per sempre.
TITOLO_TESTO_ITALIANO = "## Testo"
TITOLO_CONTESTO_ITALIANO = "## Contesto scritto da Claude"
TITOLI_TESTO = (TITOLO_TESTO, TITOLO_TESTO_ITALIANO)
TITOLI_CONTESTO = (TITOLO_CONTESTO, TITOLO_CONTESTO_ITALIANO)

# I campi d'intestazione: il nome inglese (quello che si scrive), il nome italiano (che si legge
# per sempre) e l'attributo della nota. Ordine fisso; i campi facoltativi compaiono solo se presenti.
CAMPI = (
    ("date", "data", "data"),
    ("source", "fonte", "fonte"),
    ("author", "autore", "autore"),
    ("knowledge", "tipo", "tipo"),
    ("kind", "natura", "natura"),
    ("priority", "priorità", "priorita"),
    ("confirms", "conferma_di", "conferma_di"),
    ("corrects", "corregge", "corregge"),
    ("done", "done", "done"),
    ("remind", "riprendere_il", "riprendere_il"),
    ("quote", "citazione", "citazione"),
    ("from_reply", "da_risposta", "da_risposta"),
    ("verification", "verifica", "verifica"),
)
CAMPI_SEMPRE_PRESENTI = ("data", "fonte", "autore", "tipo", "natura")
ATTRIBUTO = {nome: attributo for inglese, italiano, attributo in CAMPI for nome in (inglese, italiano)}

# I valori italiani delle note vecchie e delle proposte, con il loro valore inglese.
VALORI_ITALIANI = {
    "autore": {"utente": "user"},
    "tipo": {"dichiarata": "stated", "osservata": "observed", "dedotta": "inferred"},
    "natura": {"fatto": "fact", "decisione": "decision", "discorso aperto": "open"},
    "priorita": {"alta": "high", "normale": "normal", "bassa": "low"},
    "da_risposta": {"sì": "yes"},
}


def in_inglese(attributo: str, valore: str) -> str:
    return VALORI_ITALIANI.get(attributo, {}).get(valore, valore)


class NotaIlleggibile(Exception):
    """Un file del quaderno non ha il formato previsto."""


@dataclass(frozen=True)
class Nota:
    id: str
    data: str
    fonte: str
    autore: str  # user o claude
    tipo: str  # stated, observed o inferred
    natura: str  # fact, idea, decision, open o todo
    testo: str
    conferma_di: str | None = None
    # Il numero della nota che questa corregge ("era sbagliata").
    corregge: str | None = None
    # I numeri delle note che questa chiude: open, todo o promemoria ("è fatto", "è risolto").
    done: tuple[str, ...] | None = None
    # Promemoria: la data (AAAA-MM-GG) in cui riprendere la nota.
    riprendere_il: str | None = None
    citazione: str | None = None
    contesto: str | None = None
    # "yes" in una nota di Claude che salva un pezzo di una sua risposta.
    da_risposta: str | None = None
    # Scritta dallo sportello, non da Claude: dice se l'autore è stato verificato dal testimone.
    verifica: str | None = None
    # high, normal o low: solo nelle note dell'utente.
    priorita: str | None = None

    def in_markdown(self) -> str:
        righe = [f"# Note {self.id}", ""]
        for inglese, _, attributo in CAMPI:
            valore = getattr(self, attributo)
            if valore is not None:
                if attributo == "done":
                    valore = ", ".join(valore)
                righe.append(f"- {inglese}: {valore}")
        righe += ["", TITOLO_TESTO, "", self.testo, ""]
        if self.contesto is not None:
            righe += [TITOLO_CONTESTO, "", self.contesto, ""]
        return "\n".join(righe)


def numeri(valore: str) -> tuple[str, ...]:
    """I numeri di un campo come «done: 0012, 0015»."""
    return tuple(parte.strip() for parte in valore.split(","))


def da_markdown(id_nota: str, contenuto: str) -> Nota:
    righe = contenuto.split("\n")
    inizio_testo = next((i for i, riga in enumerate(righe) if riga in TITOLI_TESTO), None)
    if inizio_testo is None:
        raise NotaIlleggibile(f"nella nota {id_nota} manca la sezione «{TITOLO_TESTO}»")

    campi: dict[str, object] = {}
    for riga in righe[:inizio_testo]:
        if not riga.startswith("- "):
            continue
        chiave, separatore, valore = riga[2:].partition(": ")
        if separatore and chiave in ATTRIBUTO:
            attributo = ATTRIBUTO[chiave]
            campi[attributo] = numeri(valore) if attributo == "done" else in_inglese(attributo, valore)

    mancanti = [c for c in CAMPI_SEMPRE_PRESENTI if c not in campi]
    if mancanti:
        raise NotaIlleggibile(f"nella nota {id_nota} mancano: {', '.join(mancanti)}")

    # Il titolo del contesto è quello del formato della nota: una nota vecchia con nel testo la
    # riga inglese (o viceversa) non viene spezzata.
    titolo_contesto = TITOLI_CONTESTO[TITOLI_TESTO.index(righe[inizio_testo])]
    corpo = righe[inizio_testo + 1:]
    contesto = None
    if titolo_contesto in corpo:
        inizio_contesto = corpo.index(titolo_contesto)
        contesto = "\n".join(corpo[inizio_contesto + 1:]).strip()
        corpo = corpo[:inizio_contesto]
    testo = "\n".join(corpo).strip()
    return Nota(id=id_nota, testo=testo, contesto=contesto, **campi)


def chiuse(note: list[Nota]) -> dict[str, str]:
    """Per ogni nota chiusa con «done», il numero della prima nota che l'ha chiusa."""
    chiusura: dict[str, str] = {}
    for nota in sorted(note, key=lambda n: (int(n.id), n.id)):
        for numero in nota.done or ():
            chiusura.setdefault(numero, nota.id)
    return chiusura
