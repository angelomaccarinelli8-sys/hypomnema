"""L'albero delle etichette: ramo (COSA) → sotto-rami (argomenti) → note. Solo lettura. Dalla 0.10.0 (I0213).

I sotto-rami stanno in ``etichette.toml`` (vedi ``etichette``) e si calcolano al momento della lettura, come le COSA
dal testo: nessun file si scrive. Due modi di calcolarli, per due usi (decisione di Angelo del 21/10):

- **per vedere** (``tree`` e il grafo ad albero): dal testo dell'ultima versione, con le parti integrate;
- **per decidere** (la regola dello sportello e le catene della revisione): dal **testo proprio** della nota, cioè il
  testo della prima versione o della sua ultima correzione, senza le parti aggiunte con ``integrates``. Così una nota
  che riceve integrazioni non si allarga a tutto il ramo.

Una catena di integrazione si mostra come un solo filo: la nota che contiene le altre in testa, poi le note integrate in
lei, dalla più recente integrazione (``I0005.2 ← I0002 ← I0001``).
"""

from hypomnema import etichette
from hypomnema.nota import ordine
from hypomnema.versioni import TESTO_CORRETTO, Quaderno, Storia

SENZA_ARGOMENTO = "senza argomento"


def testo_proprio(storia: Storia) -> str:
    """Il testo della prima versione, o della sua ultima correzione: mai le parti aggiunte con integrates."""
    testo = storia.versioni[0].contenuto.testo
    for versione in storia.versioni[1:]:
        if TESTO_CORRETTO in versione.cambi:
            testo = versione.contenuto.testo
    return testo


def sotto_rami_propri(storia: Storia, lista) -> tuple[tuple[str, str], ...]:
    """I sotto-rami per decidere: dal testo proprio, con le COSA dell'ultima versione."""
    return etichette.sotto_rami(testo_proprio(storia), storia.ultima.contenuto.cosa, lista)


def sotto_rami_visti(storia: Storia, lista) -> tuple[tuple[str, str], ...]:
    """I sotto-rami per vedere: dal testo dell'ultima versione, con le parti integrate."""
    nota = storia.ultima.contenuto
    return etichette.sotto_rami(nota.testo, nota.cosa, lista)


def viva(storia: Storia) -> bool:
    """Aperta: non chiusa, non annullata, non integrata in un'altra nota."""
    return not storia.chiusa and not storia.annullata and storia.integrata_in is None


def integrate_in(quaderno: Quaderno, storia: Storia) -> list[Storia]:
    """Le note integrate direttamente in questa, dalla più recente integrazione."""
    dentro = [s for s in quaderno.elenco() if s.integrata_in is not None and s.integrata_in.base == storia.base]
    return sorted(dentro, key=lambda s: s.integrata_in.numero, reverse=True)


def catena(quaderno: Quaderno, storia: Storia) -> list[Storia]:
    """La nota e tutte quelle integrate in lei (anche in più passaggi), in ordine di filo."""
    filo = [storia]
    for dentro in integrate_in(quaderno, storia):
        if dentro not in filo:
            filo += [s for s in catena(quaderno, dentro) if s not in filo]
    return filo


def rami_in_ordine(quaderno: Quaderno, lista) -> list[str]:
    """Le COSA: quelle della lista, poi quelle usate nelle note ma non più nella lista, in ordine alfabetico."""
    ordine = list(lista.cosa) if lista is not None else []
    usate = {c for s in quaderno.elenco() for c in (s.ultima.contenuto.cosa or ())}
    return ordine + sorted(usate - set(ordine))


def albero(quaderno: Quaderno, lista, tutte: bool = False) -> list[tuple[str, list[tuple[str, list[Storia]]]]]:
    """[(COSA, [(sotto-ramo, note in testa a una catena)])], con «senza argomento» per ultimo, solo se ha note.

    Le note integrate non stanno da sole: sono nella catena della nota che le contiene. Senza ``tutte`` si lasciano
    fuori le note chiuse (tranne le decisioni) e le annullate, come nella ricerca.
    """
    teste = [s for s in quaderno.elenco() if s.integrata_in is None and (tutte or not s.nascosta)]
    risultato = []
    for ramo in rami_in_ordine(quaderno, lista):
        nel_ramo = [s for s in teste if ramo in (s.ultima.contenuto.cosa or ())]
        sotto = []
        for nome, _ in (lista.sotto_rami_di(ramo) if lista is not None else ()):
            sotto.append((nome, [s for s in nel_ramo if (ramo, nome) in sotto_rami_visti(s, lista)]))
        senza = [s for s in nel_ramo if not any(r == ramo for r, _ in sotto_rami_visti(s, lista))]
        if senza:
            sotto.append((SENZA_ARGOMENTO, senza))
        risultato.append((ramo, [(nome, sorted(note, key=lambda s: ordine(s.base), reverse=True))
                                 for nome, note in sotto]))
    return risultato


# La regola dell'integrazione (pezzo 2, I0213): per le idee lo sportello rifiuta, per i fatti dà solo un suggerimento
# (decisione di Angelo del 21/10). Decisioni, domande aperte e cose da fare restano fuori.
NATURE_DELLA_REGOLA = ("idea", "fact")


def gia_nel_sotto_ramo(note_esistenti, lista, autore: str, natura: str, testo: str,
                       cosa_a_mano: tuple[str, ...] | None) -> list[tuple[Storia, tuple[str, str]]]:
    """Le note vive dello stesso autore e dello stesso tipo che hanno un sotto-ramo in comune con la nota nuova (dal
    testo proprio), dalla più recente, con il primo sotto-ramo in comune. Vuoto senza sotto-rami nella lista."""
    if lista is None or not lista.rami or natura not in NATURE_DELLA_REGOLA:
        return []
    cosa, _ = etichette.cosa_finali(cosa_a_mano, etichette.trova_nel_testo(testo, lista))
    nuovi = etichette.sotto_rami(testo, cosa, lista)
    if not nuovi:
        return []
    quaderno = Quaderno(note_esistenti)
    etichette.con_cosa_dal_testo(quaderno, lista)
    trovate = []
    for storia in reversed(quaderno.elenco()):
        nota = storia.ultima.contenuto
        if not viva(storia) or nota.autore != autore or nota.natura != natura:
            continue
        comuni = [r for r in sotto_rami_propri(storia, lista) if r in nuovi]
        if comuni:
            trovate.append((storia, comuni[0]))
    return trovate
