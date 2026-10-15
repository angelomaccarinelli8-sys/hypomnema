"""I promemoria: le note con «riprendere_il» la cui data è arrivata o già passata. Solo lettura.

Un promemoria e le sue correzioni (``corregge``, anche a catena) formano un gruppo, che compare una
volta sola, sotto la prima nota. Regole fisse:

- vale la data della nota più recente del gruppo che ha un suo «riprendere_il» (una correzione
  con una data nuova sposta il promemoria; una correzione senza data lo lascia com'era);
- se una nota segna come fatta («done») una nota del gruppo, il promemoria non è più tra gli scaduti;
- gli scaduti vanno dal più vecchio al più recente; a parità di data decide il numero della nota.
"""

from dataclasses import dataclass
from datetime import date

from hypomnema.nota import Nota


@dataclass(frozen=True)
class Promemoria:
    nota: Nota  # la prima nota del gruppo
    giorno: str  # la data in vigore (AAAA-MM-GG)
    da: Nota  # la nota da cui viene la data in vigore


def _numero(nota: Nota) -> tuple[int, str]:
    return int(nota.id), nota.id


def _radice(nota: Nota, per_numero: dict[str, Nota]) -> Nota:
    # Lo sportello accetta solo correzioni di note che esistono già, quindi la catena finisce;
    # il controllo dei numeri già visti serve se qualcuno ha toccato le note a mano.
    viste = {nota.id}
    while nota.corregge is not None and nota.corregge in per_numero and nota.corregge not in viste:
        nota = per_numero[nota.corregge]
        viste.add(nota.id)
    return nota


def gruppi(note: list[Nota]) -> list[tuple[Promemoria, bool]]:
    """Tutti i promemoria ancora da fare, con la data in vigore; il booleano dice se è chiuso (done)."""
    per_numero = {n.id: n for n in note}
    membri: dict[str, list[Nota]] = {}
    for nota in note:
        membri.setdefault(_radice(nota, per_numero).id, []).append(nota)
    fatte = {n.done for n in note if n.done is not None}
    elenco = []
    for numero, gruppo in membri.items():
        con_data = [n for n in gruppo if n.riprendere_il is not None]
        if not con_data:
            continue
        ultima = max(con_data, key=_numero)
        chiuso = any(n.id in fatte for n in gruppo)
        elenco.append((Promemoria(per_numero[numero], ultima.riprendere_il, ultima), chiuso))
    return elenco


def scaduti(note: list[Nota], oggi: date) -> list[Promemoria]:
    aperti = [p for p, chiuso in gruppi(note) if not chiuso]
    arrivati = [p for p in aperti if date.fromisoformat(p.giorno) <= oggi]
    return sorted(arrivati, key=lambda p: (p.giorno, _numero(p.nota)))


def in_arrivo(note: list[Nota], oggi: date) -> int:
    """Quanti promemoria aperti hanno una data non ancora arrivata."""
    return sum(1 for p, chiuso in gruppi(note) if not chiuso and date.fromisoformat(p.giorno) > oggi)
