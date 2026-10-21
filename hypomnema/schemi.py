"""Gli schemi del modo di parlare dell'utente: le sequenze di parole tipiche di ogni tipo di nota. Dalla 0.9.0.

Traduce lo script di sola lettura del 21/10/2026 (``schemi_del_taccuino.py``, decisione D0210): gli schemi non si
inventano, si ricavano dall'uso. Solo lettura, regole fisse, niente modelli linguistici: stessi ingressi, stesso
risultato. Gli schemi si ricalcolano dal quaderno ogni volta (nessun file salvato): crescono con il taccuino.

Le regole, tutte qui:

- si guardano solo le note dell'utente (autore ``user``), ognuna con la sua **prima versione** (il tipo e il testo
  di quando è nata): le note di Claude sono il modo di parlare di Claude, non dell'utente;
- il testo si porta in minuscolo e si spezza in parole (``PAROLA``: lettere, lettere accentate italiane, apostrofo);
- di ogni nota si prendono le sequenze di 2 e 3 parole consecutive (``LUNGHEZZE``), ognuna una volta sola;
- una sequenza è **tipica** di un tipo se compare in almeno ``MIN_NOTE`` note di quel tipo, se almeno la ``QUOTA``
  delle note in cui compare è di quel tipo, e se non è una coppia «vuota» (``VUOTE``: una parola grammaticale e una
  parola piena, come «di casa», «il punto»);
- il tipo che **suona** una nota: per ogni tipo, quante delle sue sequenze sono tipiche di quel tipo; vince il tipo
  con più punti, a parità nell'ordine fisso ``TIPI``; con zero punti nessuno.
"""

import re
from collections import Counter
from dataclasses import dataclass

# --- Le soglie e le regole fisse (dello script del 21/10; si cambiano solo qui) ---
# Una sequenza è tipica di un tipo se compare in almeno MIN_NOTE note di quel tipo…
MIN_NOTE = 2
# …e se almeno QUOTA delle note in cui compare sono di quel tipo (0.6 = 60%).
QUOTA = 0.6
# Le sequenze: di 2 e di 3 parole consecutive.
LUNGHEZZE = (2, 3)
# Che cosa è una parola: lettere minuscole, lettere accentate italiane e apostrofo (il testo si porta in minuscolo).
PAROLA = re.compile(r"[a-zàèéìòù']+")
# Le coppie «vuote»: una parola grammaticale e una parola piena (come nello script, parola per parola).
VUOTE = re.compile(r"(di|a|e|il|la|lo|le|i|che|per|in|un|una|non|è|da|con|su) \S+"
                   r"|\S+ (di|a|e|il|la|lo|le|i|che|per|in|un|una|da|con|su)")
# L'ordine dei tipi: decide a parità di punti.
TIPI = ("decision", "idea", "todo", "open", "fact")
# Quante sequenze mostra il comando «patterns» per ogni tipo (senza --all), come lo script.
DA_MOSTRARE = 12
# Quante sequenze trovate cita al massimo il suggerimento dello sportello.
NEL_SUGGERIMENTO = 3


def sequenze(testo: str) -> frozenset[str]:
    """Le sequenze di 2 e 3 parole di un testo, ognuna una volta sola."""
    parole = PAROLA.findall(testo.lower())
    return frozenset(" ".join(parole[i:i + n]) for n in LUNGHEZZE for i in range(len(parole) - n + 1))


@dataclass(frozen=True)
class NotaDellUtente:
    base: str
    tipo: str
    sequenze: frozenset[str]


def note_dell_utente(quaderno) -> list[NotaDellUtente]:
    """Le note dell'utente, ognuna con il tipo e il testo della sua prima versione."""
    note = []
    for storia in quaderno.elenco():
        prima = storia.versioni[0].contenuto
        if prima.autore == "user":
            note.append(NotaDellUtente(storia.base, prima.natura, sequenze(prima.testo)))
    return note


@dataclass
class Conti:
    """In quante note di ogni tipo compare ogni sequenza, e in quante note in tutto."""
    per_tipo: dict[str, Counter]
    tutte: Counter
    note_per_tipo: Counter

    @classmethod
    def da(cls, note: list[NotaDellUtente]) -> "Conti":
        conti = cls({t: Counter() for t in TIPI}, Counter(), Counter())
        for nota in note:
            conti.aggiungi(nota, +1)
        return conti

    def aggiungi(self, nota: NotaDellUtente, quanto: int) -> None:
        self.note_per_tipo[nota.tipo] += quanto
        for sequenza in nota.sequenze:
            self.per_tipo.setdefault(nota.tipo, Counter())[sequenza] += quanto
            self.tutte[sequenza] += quanto

    def tipica(self, sequenza: str, tipo: str) -> bool:
        nel_tipo = self.per_tipo.get(tipo, Counter())[sequenza]
        tutte = self.tutte[sequenza]
        return (nel_tipo >= MIN_NOTE and tutte > 0 and nel_tipo / tutte >= QUOTA
                and VUOTE.fullmatch(sequenza) is None)

    def schemi(self, tipo: str) -> list[tuple[str, int]]:
        """Le sequenze tipiche di un tipo, dalla più frequente; a parità in ordine alfabetico."""
        trovate = [(s, n) for s, n in self.per_tipo.get(tipo, Counter()).items() if n > 0 and self.tipica(s, tipo)]
        return sorted(trovate, key=lambda c: (-c[1], c[0]))

    def punti(self, seq: frozenset[str]) -> dict[str, list[str]]:
        """Per ogni tipo, le sequenze del testo tipiche di quel tipo (in ordine alfabetico)."""
        return {t: sorted(s for s in seq if self.tipica(s, t)) for t in TIPI}


def suona_come(conti: Conti, seq: frozenset[str]) -> tuple[str | None, dict[str, list[str]]]:
    """Il tipo con più punti (a parità nell'ordine TIPI), o None se nessuna sequenza è tipica."""
    punti = conti.punti(seq)
    migliore = max(TIPI, key=lambda t: len(punti[t]))  # max tiene il primo a parità: l'ordine di TIPI
    return (migliore if punti[migliore] else None), punti


def suggerimento(conti: Conti, testo: str, tipo_proposto: str) -> tuple[str, list[str]] | None:
    """Un altro tipo che suona meglio di quello proposto: (tipo, sequenze trovate), o None.

    Solo se un altro tipo ha **più** punti del tipo proposto (decisione di Angelo del 21/10): a parità niente.
    """
    if tipo_proposto not in TIPI:
        return None
    punti = conti.punti(sequenze(testo))
    altri = [t for t in TIPI if t != tipo_proposto]
    migliore = max(altri, key=lambda t: len(punti[t]))
    if len(punti[migliore]) > len(punti[tipo_proposto]):
        return migliore, punti[migliore][:NEL_SUGGERIMENTO]
    return None


@dataclass(frozen=True)
class Misura:
    note: int
    giuste: int
    senza: int


def misura(note: list[NotaDellUtente], a_turno: bool) -> Misura:
    """Quante volte gli schemi indovinano il tipo. ``a_turno``: ogni nota tolta dal calcolo prima di indovinarla."""
    conti = Conti.da(note)
    giuste = senza = 0
    for nota in note:
        if a_turno:
            conti.aggiungi(nota, -1)
        tipo, _ = suona_come(conti, nota.sequenze)
        if a_turno:
            conti.aggiungi(nota, +1)
        if tipo is None:
            senza += 1
        elif tipo == nota.tipo:
            giuste += 1
    return Misura(len(note), giuste, senza)
