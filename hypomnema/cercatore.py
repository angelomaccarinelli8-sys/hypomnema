"""Il cercatore: trova le note che contengono una parola. Solo lettura.

La ricerca è per parola esatta: non distingue maiuscole e minuscole, e una parola è delimitata
da qualunque segno che non sia una lettera o una cifra (spazi, punteggiatura, ma anche il
trattino basso, il punto, il trattino e la barra delle parole composte): "orto" trova
"orto_balcone.py", ma "caffè" non trova "caffèlatte".

Dalla 0.6.0 si cerca nelle storie (vedi ``versioni``): una nota si trova se la parola è in una
qualunque delle sue versioni, nel testo, nel contesto scritto da Claude o nel motivo di un
cambiamento. Le note trovate vanno dalla più recente (numero più alto) alla più vecchia. Le note la
cui ultima versione è chiusa non si mostrano, a meno di chiederle tutte (``tutte=True``, cioè
``search --all``).

Ogni nota si porta dietro le note che la confermano (``confirms``), e una nota che conferma
un'altra dice sempre com'è quella nota oggi, anche se è chiusa o è stata cambiata.
"""

import re

from hypomnema import quaderno as quaderno_su_disco
from hypomnema.configurazione import Configurazione
from hypomnema.versioni import Quaderno, Storia, Versione, ultima_o_motivo
from hypomnema.nota import ordine


def schema_parola(parola: str) -> re.Pattern:
    """La parola (o le parole) così com'è, delimitata da segni che non sono lettere o cifre."""
    return re.compile(r"(?<![^\W_])" + re.escape(parola) + r"(?![^\W_])", re.IGNORECASE)


def dal_piu_recente(storie: list[Storia]) -> list[Storia]:
    return sorted(storie, key=lambda s: ordine(s.base), reverse=True)


def _contiene(versione: Versione, schema: re.Pattern) -> bool:
    nota = versione.contenuto
    return any(t is not None and schema.search(t) for t in (nota.testo, nota.contesto, versione.motivo))


def leggi(config: Configurazione) -> Quaderno:
    return Quaderno(quaderno_su_disco.leggi_note(config))


def cerca(quaderno: Quaderno | Configurazione, parola: str, tutte: bool = False) -> list[Storia]:
    if isinstance(quaderno, Configurazione):
        quaderno = leggi(quaderno)
    parola = parola.strip()
    if not parola:
        raise ValueError("serve una parola da cercare.")
    schema = schema_parola(parola)
    return dal_piu_recente([
        s for s in quaderno.elenco()
        if any(_contiene(v, schema) for v in s.versioni) and (tutte or not s.chiusa)
    ])


def confermata_da(quaderno: Quaderno) -> dict[str, list[Storia]]:
    """Per ogni storia, le storie che la confermano (``confirms``), dalla più recente."""
    conferme: dict[str, list[Storia]] = {}
    for storia in quaderno.elenco():
        numero = storia.ultima.contenuto.conferma_di
        confermata = quaderno.storia_di(numero) if numero is not None else None
        if confermata is not None and confermata is not storia:
            conferme.setdefault(confermata.base, []).append(storia)
    return {b: dal_piu_recente(s) for b, s in conferme.items()}


def rimando(quaderno: Quaderno, numero: str, segno: str) -> str:
    """Com'è oggi la nota a cui si rimanda: «nota ✓I0005.1 (chiusa)», anche se è una versione vecchia."""
    trovato = quaderno.risolvi(numero, "confirms")
    if trovato.storia is None:
        return f"nota {numero} (non c'è nel quaderno)"
    ultima = trovato.storia.ultima
    chiusa = " (chiusa)" if ultima.chiusa else ""
    if ultima_o_motivo(trovato) is None:
        return f"nota {ultima.etichetta(segno)}{chiusa}"
    return f"nota {trovato.versione.etichetta(segno)}, versione vecchia: l'ultima è {ultima.etichetta(segno)}{chiusa}"


# L'ordine delle priorità: prima le alte. Una nota senza priorità vale «normal».
ORDINE_PRIORITA = {"high": 0, "normal": 1, "low": 2}


def priorita_in_vigore(storia: Storia) -> str:
    """La priorità dell'ultima versione (nelle catene vecchie, l'ultima che ne ha una)."""
    return storia.ultima.contenuto.priorita or "normal"


# Le voci dei cambiamenti (in inglese nel file) come le legge l'utente.
VOCI_ITALIANE = (
    ("text corrected", "testo corretto"),
    ("kind ", "natura "),
    ("priority ", "priorità "),
    ("remind ", "promemoria "),
    ("closed", "chiusa"),
    ("reopened", "riaperta"),
)


def in_italiano(voce: str) -> str:
    for inglese, italiano in VOCI_ITALIANE:
        if voce.startswith(inglese):
            return italiano + voce[len(inglese):]
    return voce


def prima_riga(testo: str) -> str:
    righe = testo.split("\n")
    return righe[0] + (" …" if len(righe) > 1 else "")


def su_una_riga(testo: str) -> str:
    return " ⏎ ".join(testo.split("\n"))


def descrivi_cambio(storia: Storia, versione: Versione, breve: bool) -> str:
    """Che cosa ha cambiato una versione, in italiano: «priorità normal → high. Motivo: «…»»."""
    if versione.numero == 0:
        return "creata"
    taglia = prima_riga if breve else su_una_riga
    voci = []
    for voce in versione.cambi:
        if voce == "reopened":
            perche = f", perché «{taglia(versione.motivo)}»" if versione.motivo else ""
            voci.append(f"riaperta il {versione.data}{perche}")
        elif voce == "text corrected" and not breve:
            precedente = storia.versioni[storia.versioni.index(versione) - 1].contenuto
            voci.append(f"testo corretto (prima: «{prima_riga(precedente.testo)}»)")
        else:
            voci.append(in_italiano(voce))
    descrizione = ", ".join(voci) or "nessun cambiamento scritto"
    if versione.motivo and "reopened" not in versione.cambi and not breve:
        descrizione += f". Motivo: «{taglia(versione.motivo)}»"
    return descrizione


def righe_della_storia(storia: Storia, segno: str, breve: bool) -> list[str]:
    """Una riga per versione, dalla più vecchia: codice, data, chi, che cosa è cambiato."""
    larghezza = max(len(v.etichetta(segno)) for v in storia.versioni)
    return [
        f"{v.etichetta(segno).ljust(larghezza)} {v.data} · {v.autore}: {descrivi_cambio(storia, v, breve)}"
        for v in storia.versioni
    ]
