"""Le versioni: ogni nota è una storia di versioni (0049, 0049.1, 0049.2…). Solo lettura.

Dalla 0.6.0 ogni cambiamento di una nota (correzione del testo, natura, priorità, promemoria,
chiusura, riapertura) è un file nuovo con il punto, scritto dallo sportello. Le note di prima non
si riscrivono: si leggono con le stesse regole, come versioni «virtuali»:

- una nota vecchia con ``corrects: X`` è la versione successiva della storia di X; si mostra come
  ``0001.1 (nota 0002)``; la sua natura, priorità e data di promemoria valgono da lì in poi (se non
  ne ha una sua, resta quella di prima);
- una nota vecchia con ``done: X`` è la versione chiusa della storia di X (una volta sola per
  storia), con il suo testo come motivo; la natura chiusa è la sua se è decision, fact o idea,
  altrimenti resta quella di prima. Se è essa stessa un todo o un promemoria, se conferma un'idea
  (``confirms``) o se un'altra nota la corregge, resta anche una nota a sé, perché non si perda;
- le versioni virtuali di una storia sono numerate per numero di nota, prima delle versioni vere.

Il codice di una versione è la lettera della sua natura davanti al numero (F fact, I idea,
D decision, O open, T todo), con un segno davanti se è chiusa (di base ✓): ✓T0049.3. La lettera
si mostra soltanto: nei rimandi si scrive il numero.
"""

import re
from dataclasses import dataclass, replace

from hypomnema.nota import Nota, base_di, ordine, versione_di

LETTERE = {"fact": "F", "idea": "I", "decision": "D", "open": "O", "todo": "T"}
SEGNO_CHIUSA = "✓"
LEGENDA = "F fatto · I idea · D decisione · O aperta · T da fare · {segno} chiusa"
# Che cosa può diventare una questione quando si chiude (come nella 0.5.0).
NATURE_DOPO_LA_CHIUSURA = ("decision", "fact", "idea")
CHIUSA = "closed"
RIAPERTA = "reopened"
TESTO_CORRETTO = "text corrected"

FORMA_NUMERO = re.compile(r"^\d+(?:\.\d+)?$")
# Un numero con davanti una lettera o un segno, per esempio «T0049» o «✓T0049.3».
FORMA_CODICE = re.compile(r"^[^\d\s]+(\d+(?:\.\d+)?)$")


@dataclass(frozen=True)
class Versione:
    base: str  # il numero della nota, per esempio «0049»
    numero: int  # 0 per la nota stessa, poi 1, 2…
    # La nota com'è in questa versione: testo e campi in vigore. Il suo id è quello della versione.
    contenuto: Nota
    chiusa: bool
    # Il file da cui viene la versione: la versione stessa, oppure la nota vecchia (versione virtuale).
    origine: Nota
    # Il cambiamento: quando, chi, che cosa (voci in inglese), perché.
    data: str
    fonte: str
    autore: str
    cambi: tuple[str, ...] = ()
    motivo: str | None = None

    @property
    def id(self) -> str:
        return self.base if self.numero == 0 else f"{self.base}.{self.numero}"

    @property
    def virtuale(self) -> bool:
        return self.origine.id != self.id

    def codice(self, segno: str = SEGNO_CHIUSA) -> str:
        return (segno if self.chiusa else "") + LETTERE.get(self.contenuto.natura, "?") + self.id

    def etichetta(self, segno: str = SEGNO_CHIUSA) -> str:
        """Il codice, e per una versione virtuale il numero vero: «T0001.1 (nota 0002)»."""
        return self.codice(segno) + (f" (nota {self.origine.id})" if self.virtuale else "")


@dataclass
class Storia:
    base: str
    versioni: list[Versione]

    @property
    def id(self) -> str:
        return self.base

    @property
    def ultima(self) -> Versione:
        return self.versioni[-1]

    @property
    def chiusa(self) -> bool:
        return self.ultima.chiusa

    def natura_prima_della_chiusura(self) -> str:
        """La natura dell'ultima versione aperta prima della chiusura in corso."""
        for versione in reversed(self.versioni):
            if not versione.chiusa:
                return versione.contenuto.natura
        return self.versioni[0].contenuto.natura

    def prossima_versione(self) -> str:
        return f"{self.base}.{max(v.numero for v in self.versioni) + 1}"


def differenze(prima: Nota, dopo: Nota) -> list[str]:
    """Le voci di un cambiamento tra due versioni, in inglese e in ordine fisso."""
    cambi = []
    if (dopo.testo, dopo.contesto) != (prima.testo, prima.contesto):
        cambi.append(TESTO_CORRETTO)
    if dopo.natura != prima.natura:
        cambi.append(f"kind {prima.natura} → {dopo.natura}")
    if (dopo.priorita or "normal") != (prima.priorita or "normal"):
        cambi.append(f"priority {prima.priorita or 'normal'} → {dopo.priorita or 'normal'}")
    if dopo.riprendere_il != prima.riprendere_il:
        cambi.append(f"remind {prima.riprendere_il} → {dopo.riprendere_il}" if prima.riprendere_il
                     else f"remind {dopo.riprendere_il}")
    return cambi


@dataclass(frozen=True)
class Rimando:
    storia: Storia | None
    versione: Versione | None
    motivo: str | None  # il motivo del rifiuto, se il rimando non vale


class Quaderno:
    """Le storie del quaderno, con i numeri vecchi che portano a una versione."""

    def __init__(self, note: list[Nota]):
        self.storie: dict[str, Storia] = {}
        # Il numero di una nota vecchia diventata versione → le versioni che è diventata.
        self.alias: dict[str, list[Versione]] = {}
        # Le versioni (anche virtuali) che due o più note vecchie hanno cambiato: (versione, note).
        self.rami: list[tuple[Versione, list[Nota]]] = []
        self._costruisci(note)

    # --- costruzione ---

    def _costruisci(self, note: list[Nota]) -> None:
        vecchie = {n.id: n for n in note if "." not in n.id}
        file_versioni: dict[str, list[Nota]] = {}
        for n in note:
            if "." in n.id:
                file_versioni.setdefault(base_di(n.id), []).append(n)

        def bersaglio_valido(nota: Nota) -> str | None:
            return nota.corregge if nota.corregge in vecchie and nota.corregge != nota.id else None

        def radice(numero: str) -> str:
            # Lo sportello di prima accettava solo correzioni di note che esistevano già, quindi la catena
            # finisce; se qualcuno ha scritto a mano un giro, la radice è la nota più vecchia del giro.
            cammino = [numero]
            while (successiva := bersaglio_valido(vecchie[cammino[-1]])) is not None:
                if successiva in cammino:
                    return min(cammino[cammino.index(successiva):], key=ordine)
                cammino.append(successiva)
            return cammino[-1]

        corrette = {n.corregge for n in vecchie.values() if bersaglio_valido(n)}
        basi = []
        for numero, nota in vecchie.items():
            if bersaglio_valido(nota) is not None and radice(numero) != numero:
                continue
            chiude = any(t in vecchie for t in nota.done or ())
            # Una nota vecchia che chiude resta anche una nota a sé se è ancora una cosa da fare, se
            # conferma un'idea o se qualcuno la corregge: altrimenti si perderebbe.
            resta_da_fare = nota.natura == "todo" or nota.riprendere_il is not None
            if not chiude or resta_da_fare or nota.conferma_di is not None or numero in corrette:
                basi.append(numero)

        # Gli avvenimenti di ogni storia: (nota vecchia, "corregge" o "chiude", bersaglio).
        avvenimenti: dict[str, list[tuple[Nota, str, str]]] = {b: [] for b in basi}
        for numero in sorted(vecchie, key=ordine):
            nota = vecchie[numero]
            bersaglio = bersaglio_valido(nota)
            if bersaglio is not None and radice(numero) != numero:
                storia = radice(numero)
                if storia in avvenimenti:
                    avvenimenti[storia].append((nota, "corregge", bersaglio))
            # Una chiusura sola per storia: il bersaglio è la nota più recente chiusa in quella storia.
            per_storia: dict[str, str] = {}
            for chiusa in nota.done or ():
                if chiusa in vecchie and radice(chiusa) in avvenimenti and radice(chiusa) != numero:
                    storia = radice(chiusa)
                    per_storia[storia] = max(per_storia.get(storia, chiusa), chiusa, key=ordine)
            for storia, chiusa in per_storia.items():
                avvenimenti[storia].append((nota, "chiude", chiusa))

        for base in sorted(basi, key=ordine):
            self.storie[base] = self._storia(vecchie[base], avvenimenti[base], file_versioni.pop(base, []))
        # Versioni vere di una nota che non c'è più (file toccati a mano): una storia a parte.
        for base, files in sorted(file_versioni.items(), key=lambda c: ordine(c[0])):
            primo = sorted(files, key=lambda n: ordine(n.id))
            self.storie[base] = self._storia(replace(primo[0], id=base), [], primo[1:])

    def _storia(self, nota: Nota, avvenimenti, files: list[Nota]) -> Storia:
        prima = Versione(nota.id, 0, nota, nota.stato == CHIUSA, nota, nota.data, nota.fonte, nota.autore)
        storia = Storia(nota.id, [prima])
        cambiate: dict[str, list[Nota]] = {}
        for vecchia, come, bersaglio in avvenimenti:
            precedente = storia.ultima
            numero = precedente.numero + 1
            vid = f"{nota.id}.{numero}"
            p = precedente.contenuto
            if come == "corregge":
                contenuto = replace(
                    vecchia, id=vid, corregge=None, done=None,
                    priorita=vecchia.priorita or p.priorita,
                    riprendere_il=vecchia.riprendere_il or p.riprendere_il,
                    conferma_di=vecchia.conferma_di or p.conferma_di,
                    stato=CHIUSA if precedente.chiusa else None,
                )
                versione = Versione(nota.id, numero, contenuto, precedente.chiusa, vecchia, vecchia.data,
                                    vecchia.fonte, vecchia.autore, tuple(differenze(p, contenuto)))
            else:
                natura = vecchia.natura if vecchia.natura in NATURE_DOPO_LA_CHIUSURA else p.natura
                contenuto = replace(p, id=vid, natura=natura, stato=CHIUSA)
                versione = Versione(nota.id, numero, contenuto, True, vecchia, vecchia.data, vecchia.fonte,
                                    vecchia.autore, (CHIUSA, *differenze(p, contenuto)), vecchia.testo)
            cambiate.setdefault(bersaglio, []).append(vecchia)
            storia.versioni.append(versione)
            self.alias.setdefault(vecchia.id, []).append(versione)
        for chiave, chi in cambiate.items():
            if len(chi) > 1:
                versione = next(v for v in storia.versioni if v.origine.id == chiave or v.id == chiave)
                self.rami.append((versione, chi))
        for file in sorted(files, key=lambda n: ordine(n.id)):
            cambio = file.cambio
            storia.versioni.append(Versione(
                nota.id, versione_di(file.id), file, file.stato == CHIUSA, file,
                cambio.data if cambio else file.data, cambio.fonte if cambio else file.fonte,
                cambio.autore if cambio else file.autore,
                tuple(cambio.cambio.split("; ")) if cambio else (), cambio.motivo if cambio else None,
            ))
        return storia

    # --- lettura ---

    def elenco(self) -> list[Storia]:
        """Le storie in ordine di numero."""
        return [self.storie[b] for b in sorted(self.storie, key=ordine)]

    def storia_di(self, numero: str) -> Storia | None:
        """La storia a cui appartiene un numero: della nota, di una versione o di una nota vecchia."""
        if numero in self.storie:
            return self.storie[numero]
        if numero in self.alias:
            return self.storie[self.alias[numero][0].base]
        base = base_di(numero)
        return self.storie.get(base) if "." in numero else None

    def risolvi(self, rimando: str, campo: str) -> Rimando:
        """Il rimando di una proposta: «0049» = l'ultima versione; «0049.1» o «0002» = quella versione."""
        rimando = rimando.strip()
        codice = FORMA_CODICE.match(rimando)
        if codice:
            return Rimando(None, None, f"write only the number in «{campo}»: «{codice.group(1)}», not «{rimando}» "
                                       "(the letter of the code is only shown, it is not part of the number).")
        if not FORMA_NUMERO.match(rimando):
            return Rimando(None, None, f"«{campo}» must contain a note number, for example «0012».")
        if rimando in self.storie:
            storia = self.storie[rimando]
            return Rimando(storia, storia.ultima, None)
        if rimando in self.alias:
            versioni = self.alias[rimando]
            if len({v.base for v in versioni}) > 1:
                quali = " and ".join(v.id for v in versioni)
                return Rimando(None, None, f"note «{rimando}» is an old closing note: it is version {quali}. "
                                           f"Write in «{campo}» the number of the note to change.")
            return Rimando(self.storie[versioni[0].base], versioni[0], None)
        storia = self.storie.get(base_di(rimando)) if "." in rimando else None
        if storia is not None:
            for versione in storia.versioni:
                if versione.id == rimando:
                    return Rimando(storia, versione, None)
        return Rimando(None, None, f"note «{rimando}» named in «{campo}» does not exist in the notebook.")


def ultima_o_motivo(rimando: Rimando, segno: str = SEGNO_CHIUSA) -> str | None:
    """Si cambia sempre l'ultima versione: il motivo del rifiuto se il rimando è a una versione vecchia."""
    if rimando.versione is None or rimando.versione is rimando.storia.ultima:
        return None
    ultima = rimando.storia.ultima
    vecchia = rimando.versione.id + (f" (note {rimando.versione.origine.id})" if rimando.versione.virtuale else "")
    return (f"{vecchia} is not the last version of {rimando.storia.base}: the last is {ultima.codice(segno)}. "
            f"Changes are made only to the last version (write «{rimando.storia.base}»).")
