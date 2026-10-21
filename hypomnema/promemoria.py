"""I promemoria: le note con «remind» la cui data è arrivata o già passata. Solo lettura.

Dalla 0.6.0 un promemoria è una storia (vedi ``versioni``) e vale la sua ultima versione. Regole fisse:

- vale la data dell'ultima versione (nelle catene vecchie, quella della correzione più recente che
  ne ha una: una correzione senza data lascia il promemoria com'era);
- se l'ultima versione è chiusa, il promemoria non è più tra gli scaduti;
- gli scaduti vanno dal più vecchio al più recente; a parità di data decide il numero della nota.
"""

from dataclasses import dataclass
from datetime import date

from hypomnema.nota import ordine
from hypomnema.versioni import Quaderno, Storia


@dataclass(frozen=True)
class Promemoria:
    storia: Storia
    giorno: str  # la data in vigore (AAAA-MM-GG)


def aperti(quaderno: Quaderno) -> list[Promemoria]:
    """Tutti i promemoria ancora aperti, con la data in vigore."""
    return [
        Promemoria(s, s.ultima.contenuto.riprendere_il) for s in quaderno.elenco()
        if s.ultima.contenuto.riprendere_il is not None and not s.chiusa and s.integrata_in is None
    ]


def scaduti(quaderno: Quaderno, oggi: date) -> list[Promemoria]:
    arrivati = [p for p in aperti(quaderno) if date.fromisoformat(p.giorno) <= oggi]
    return sorted(arrivati, key=lambda p: (p.giorno, ordine(p.storia.base)))


def in_arrivo(quaderno: Quaderno, oggi: date) -> int:
    """Quanti promemoria aperti hanno una data non ancora arrivata."""
    return sum(1 for p in aperti(quaderno) if date.fromisoformat(p.giorno) > oggi)
