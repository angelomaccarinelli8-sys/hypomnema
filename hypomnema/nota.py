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

Dalla versione 0.6.0 ogni cambiamento di una nota è una versione nuova, in un file con il punto
(``0049.1.md``): intestazione e testo copiati con il cambiamento applicato, ``- status: closed``
se la versione è chiusa, e in fondo il blocco del cambiamento::

    ## Change

    - date: 2026-02-20
    - source: chat del 20 febbraio 2026
    - author: user
    - knowledge: stated
    - change: priority normal → high
    - verification: author not verified (witness off)

    ### Reason

    Il motivo, con le parole di chi ha chiesto il cambiamento.

    ### Context written by Claude

    Dalla 0.7.0, facoltativo e solo nei cambiamenti chiesti dall'utente: la spiegazione di Claude.

Il blocco si legge solo nei file con il punto: una nota vecchia con quella riga nel testo resta com'è.

Dalla 0.7.0 l'intestazione può avere le etichette, dopo la priorità: ``- who: Anna, Marco`` (CHI) e
``- about: orto`` (COSA). Vedi ``etichette``. Dalla 0.8.0 ``about`` comprende anche le COSA trovate nel
testo dallo sportello, che sono elencate anche nella riga ``- labels from text: about orto, bilancio``:
le altre sono state proposte a mano. Una copia della 0.7.0 salta la riga e legge ``about`` come sempre.
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
# Il blocco del cambiamento, solo nelle versioni (file con il punto).
TITOLO_CAMBIO = "## Change"
TITOLO_MOTIVO = "### Reason"
# Dalla 0.7.0: il contesto scritto da Claude in un cambiamento chiesto dall'utente.
TITOLO_CONTESTO_CAMBIO = "### Context written by Claude"

# I campi d'intestazione: il nome inglese (quello che si scrive), il nome italiano (che si legge
# per sempre) e l'attributo della nota. Ordine fisso; i campi facoltativi compaiono solo se presenti.
CAMPI = (
    ("date", "data", "data"),
    ("source", "fonte", "fonte"),
    ("author", "autore", "autore"),
    ("knowledge", "tipo", "tipo"),
    ("kind", "natura", "natura"),
    ("status", "status", "stato"),
    ("priority", "priorità", "priorita"),
    ("who", "chi", "chi"),
    ("about", "cosa", "cosa"),
    ("labels from text", "labels from text", "cosa_dal_testo"),
    ("confirms", "conferma_di", "conferma_di"),
    ("corrects", "corregge", "corregge"),
    ("done", "done", "done"),
    ("remind", "riprendere_il", "riprendere_il"),
    ("quote", "citazione", "citazione"),
    ("from_reply", "da_risposta", "da_risposta"),
    ("verification", "verifica", "verifica"),
)
CAMPI_SEMPRE_PRESENTI = ("data", "fonte", "autore", "tipo", "natura")
# I campi con più valori separati da virgola.
CAMPI_ELENCO = ("done", "chi", "cosa")
# La riga «labels from text» comincia con il tipo di etichetta: per ora solo COSA (about).
PREFISSO_DAL_TESTO = "about "
# I campi del blocco del cambiamento, in ordine fisso.
CAMPI_CAMBIO = (
    ("date", "data"), ("source", "fonte"), ("author", "autore"), ("knowledge", "tipo"),
    ("change", "cambio"), ("quote", "citazione"), ("verification", "verifica"),
)
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


def base_di(id_nota: str) -> str:
    """Il numero della nota senza la versione: «0049.2» → «0049»."""
    return id_nota.partition(".")[0]


def versione_di(id_nota: str) -> int:
    """Il numero della versione: «0049.2» → 2, «0049» → 0."""
    _, punto, versione = id_nota.partition(".")
    return int(versione) if punto else 0


def ordine(id_nota: str) -> tuple[int, int, str]:
    """Per mettere in ordine i numeri delle note e delle versioni."""
    return int(base_di(id_nota)), versione_di(id_nota), id_nota


@dataclass(frozen=True)
class Cambio:
    """Il blocco «## Change» di una versione: chi ha cambiato che cosa, quando e perché."""
    data: str
    fonte: str
    autore: str
    tipo: str
    # Le voci del cambiamento, separate da «; », per esempio «priority normal → high».
    cambio: str
    citazione: str | None = None
    verifica: str | None = None
    # Il motivo: le parole di chi ha chiesto il cambiamento. Manca nelle correzioni del testo,
    # dove le parole nuove sono il testo stesso.
    motivo: str | None = None
    # Dalla 0.7.0: ciò che Claude aggiunge al motivo dell'utente (mai nelle parole dell'utente).
    contesto: str | None = None

    def in_markdown(self) -> list[str]:
        righe = [TITOLO_CAMBIO, ""]
        for inglese, attributo in CAMPI_CAMBIO:
            valore = getattr(self, attributo)
            if valore is not None:
                righe.append(f"- {inglese}: {valore}")
        righe.append("")
        if self.motivo is not None:
            righe += [TITOLO_MOTIVO, "", self.motivo, ""]
        if self.contesto is not None:
            righe += [TITOLO_CONTESTO_CAMBIO, "", self.contesto, ""]
        return righe


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
    # Le etichette (dalla 0.7.0): CHI (who) e COSA (about), al massimo due per campo.
    chi: tuple[str, ...] | None = None
    cosa: tuple[str, ...] | None = None
    # Dalla 0.8.0: le COSA messe dallo sportello perché trovate nel testo (sono anche in «cosa»).
    cosa_dal_testo: tuple[str, ...] | None = None
    # "closed" nelle versioni chiuse; altrimenti None.
    stato: str | None = None
    # Solo nelle versioni: il blocco del cambiamento.
    cambio: Cambio | None = None

    def in_markdown(self) -> str:
        righe = [f"# Note {self.id}", ""]
        for inglese, _, attributo in CAMPI:
            valore = getattr(self, attributo)
            if valore is not None:
                if attributo == "cosa_dal_testo":
                    valore = PREFISSO_DAL_TESTO + ", ".join(valore)
                elif attributo in CAMPI_ELENCO:
                    valore = ", ".join(valore)
                righe.append(f"- {inglese}: {valore}")
        righe += ["", TITOLO_TESTO, "", self.testo, ""]
        if self.contesto is not None:
            righe += [TITOLO_CONTESTO, "", self.contesto, ""]
        if self.cambio is not None:
            righe += self.cambio.in_markdown()
        return "\n".join(righe)


def numeri(valore: str) -> tuple[str, ...]:
    """I numeri di un campo come «done: 0012, 0015»."""
    return tuple(parte.strip() for parte in valore.split(","))


def _cambio(id_nota: str, righe: list[str]) -> Cambio:
    campi: dict[str, str] = {}
    fine = righe.index(TITOLO_MOTIVO) if TITOLO_MOTIVO in righe else len(righe)
    for riga in righe[:fine]:
        if riga.startswith("- "):
            chiave, separatore, valore = riga[2:].partition(": ")
            for inglese, attributo in CAMPI_CAMBIO:
                if separatore and chiave == inglese:
                    campi[attributo] = valore
    mancanti = [c for c in ("data", "fonte", "autore", "tipo", "cambio") if c not in campi]
    if mancanti:
        raise NotaIlleggibile(f"nel cambiamento della nota {id_nota} mancano: {', '.join(mancanti)}")
    resto = righe[fine + 1:]
    contesto = None
    if TITOLO_CONTESTO_CAMBIO in resto:
        inizio = resto.index(TITOLO_CONTESTO_CAMBIO)
        contesto = "\n".join(resto[inizio + 1:]).strip()
        resto = resto[:inizio]
    motivo = "\n".join(resto).strip() if fine < len(righe) else None
    return Cambio(motivo=motivo, contesto=contesto, **campi)


def da_markdown(id_nota: str, contenuto: str) -> Nota:
    righe = contenuto.split("\n")
    cambio = None
    if "." in id_nota and TITOLO_CAMBIO in righe:
        # L'ultima riga «## Change»: il testo copiato da una nota vecchia potrebbe contenerla.
        inizio_cambio = len(righe) - 1 - righe[::-1].index(TITOLO_CAMBIO)
        cambio = _cambio(id_nota, righe[inizio_cambio + 1:])
        righe = righe[:inizio_cambio]
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
            if attributo == "cosa_dal_testo":
                # «about orto, bilancio»: per ora solo le COSA (dalla 0.8.0).
                campi[attributo] = numeri(valore.removeprefix(PREFISSO_DAL_TESTO))
            else:
                campi[attributo] = numeri(valore) if attributo in CAMPI_ELENCO else in_inglese(attributo, valore)

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
    return Nota(id=id_nota, testo=testo, contesto=contesto, cambio=cambio, **campi)
