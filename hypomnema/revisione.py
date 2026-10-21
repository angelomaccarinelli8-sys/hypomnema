"""La revisione del quaderno (comando «review»): che cosa conviene guardare. Solo lettura.

Ogni segnalazione viene da una regola fissa, e dice che cosa si può fare senza farlo. Il programma
non capisce il senso delle parole: dove servirebbe (una nota che dice «è fatta», una data scritta a
parole) segnala soltanto, e decide l'utente.

1. **Ramo**: due o più note vecchie cambiano (``corrects`` o ``done``) la stessa versione. Le note
   nuove non possono, perché si cambia sempre l'ultima versione.
2. **Ferma**: un ``open`` o un ``todo`` aperto la cui ultima versione è più vecchia di N giorni
   (impostazione ``giorni`` della sezione ``[revisione]``, di base 30). Dalla 0.7.0 le versioni che
   cambiano solo le etichette non contano: mettere le etichette non riazzera i giorni.
3. **Promemoria scaduto**: la data è arrivata e la nota è ancora aperta.
4. **Nominata**: il numero di un ``open`` o ``todo`` aperto compare (con o senza lettera e versione,
   non dentro una data) nel testo, nel contesto o nel motivo di una nota successiva: forse dice che
   è fatta.
5. **Senza data**: un ``open`` o ``todo`` aperto senza ``remind`` che nel testo ha «ricordamelo»,
   «ricordami», «remind me», «tra/fra … giorni/settimane/mesi» o «in … days/weeks».
6. **Catena vecchia non permessa oggi**: una nota vecchia cambiava ciò che oggi non avrebbe il permesso
   di cambiare (Claude che corregge il testo dell'utente, o che fa smettere un open di essere open).
   Resta nella storia ma non vale: lo dice la revisione, e decide l'utente.
7. **Integrabile** (dalla 0.9.0, decisione di Angelo del 21/10): due note dello stesso autore, con almeno una COSA
   in comune, e il testo o il contesto di una delle due nomina l'altra (anche di tipo diverso: un'idea che finisce in
   una decisione). Si propone di integrare la più vecchia nella più recente; decide l'utente.
   **Dalla 0.10.0 a catena** (decisione di Angelo del 21/10): per una COSA con sotto-rami, le note vive dello stesso
   autore e dello stesso tipo nello stesso sotto-ramo (dal testo proprio, vedi ``albero``) vanno tutte nella più recente,
   una proposta per nota, dalla più vecchia; una nota in due sotto-rami va solo nel primo, nell'ordine del file. Per le
   COSA senza sotto-rami resta la regola della 0.9.0, ma il rimando conta solo nel **testo** (non più nel contesto di
   Claude, che nomina altre note per riferimento) e anche lì a catena: le note legate tra loro, anche attraverso altre,
   vanno tutte nella più recente.

Dalla 0.9.0 ogni segnalazione che ha una regola fissa porta anche una **proposta pronta** (``proposta``), da completare
con le parole dell'utente: il programma non le inventa (``text`` e ``source`` restano vuoti, e lo sportello rifiuta
una proposta finché non sono scritti).
"""

import re
from dataclasses import dataclass
from datetime import date

from hypomnema import albero, promemoria
from hypomnema.cercatore import in_italiano
from hypomnema.nota import ordine
from hypomnema.versioni import Quaderno, Storia, Versione

DA_RIPRENDERE = re.compile(
    r"(?<!\w)(?:ricordamelo|ricordami|remind me"
    r"|(?:tra|fra)\s+\S+\s+(?:giorni|giorno|settimane|settimana|mesi|mese)"
    r"|in\s+\S+\s+(?:days|day|weeks|week))(?!\w)",
    re.IGNORECASE,
)
NATURE_DA_SEGUIRE = ("open", "todo")


@dataclass(frozen=True)
class Segnalazione:
    storia: Storia
    testo: str
    # Dalla 0.9.0: la proposta pronta, da completare (vedi sopra), oppure None.
    proposta: dict | None = None


def _proposta(oggi: date, **campi) -> dict:
    """Una proposta dell'utente da completare: «source» e (se serve) «text» vuoti, che scrive l'utente."""
    return {"date": oggi.isoformat(), "source": "", "author": "user", "knowledge": "stated", **campi}


def _vive(storia: Storia) -> bool:
    return not storia.chiusa and not storia.annullata and storia.integrata_in is None


def _giorno(data: str) -> date:
    return date.fromisoformat(data[:10])


def _numero_nominato(numeri: list[str]) -> re.Pattern:
    """Uno dei numeri, anche con la lettera del codice davanti o una versione dopo, ma non in una data."""
    scelta = "|".join(re.escape(n) for n in sorted(numeri, key=len, reverse=True))
    return re.compile(rf"(?<![\w.\-/])(?:[^\W\d_]{{1,2}}|✓[^\W\d_])?(?:{scelta})(?:\.\d+)?(?![\w/\-]|\.\d)")


def _numeri_della_storia(storia: Storia) -> list[str]:
    numeri = {storia.base}
    for versione in storia.versioni:
        numeri.add(versione.origine.id)
    return sorted(numeri, key=ordine)


def _successive(quaderno: Quaderno, storia: Storia) -> list[tuple[Storia, Versione]]:
    """Le versioni di altre note venute dopo: delle note più recenti, o versioni nuove dal giorno della nota."""
    nata = _giorno(storia.versioni[0].data)
    elenco = []
    for altra in quaderno.elenco():
        if altra is storia:
            continue
        for versione in altra.versioni:
            if ordine(altra.base) > ordine(storia.base) or (versione.numero > 0 and _giorno(versione.data) >= nata):
                elenco.append((altra, versione))
    return elenco


def rivedi(quaderno: Quaderno, oggi: date, giorni: int, segno: str, lista=None) -> list[Segnalazione]:
    segnalazioni: list[Segnalazione] = []
    da_seguire = [s for s in quaderno.elenco() if not s.chiusa and not s.annullata and s.integrata_in is None
                  and s.ultima.contenuto.natura in NATURE_DA_SEGUIRE]

    for versione, note in sorted(quaderno.rami, key=lambda r: ordine(r[0].id)):
        storia = quaderno.storie[versione.base]
        segnalazioni.append(Segnalazione(storia, (
            f"ramo: le note vecchie {', '.join(n.id for n in note)} cambiano tutte la versione "
            f"{versione.etichetta(segno)}. Vale l'ultima ({storia.ultima.etichetta(segno)}); se un'altra diceva "
            f"qualcosa che serve ancora, si può riportarla con corrects: {storia.base} o updates: {storia.base}."
        )))

    for storia in da_seguire:
        fermo = (oggi - _giorno(storia.data_del_contenuto)).days
        if fermo > giorni:
            come = "aperta" if storia.ultima.contenuto.natura == "open" else "da fare"
            segnalazioni.append(Segnalazione(storia, (
                f"{come} da {fermo} giorni (ultima versione del {storia.data_del_contenuto[:10]}). Si può chiudere "
                f"(done: {storia.base}), cambiare (updates: {storia.base}) o lasciarla com'è."
            ), _proposta(oggi, done=storia.base, text="")))

    for voce in promemoria.scaduti(quaderno, oggi):
        segnalazioni.append(Segnalazione(voce.storia, (
            f"promemoria scaduto il {voce.giorno}, ancora aperto. Si può chiudere (done: {voce.storia.base}) "
            f"o spostare (updates: {voce.storia.base} con remind)."
        ), _proposta(oggi, done=voce.storia.base, text="")))

    for storia in da_seguire:
        schema = _numero_nominato(_numeri_della_storia(storia))
        gia = set()
        for altra, versione in _successive(quaderno, storia):
            testi = (versione.contenuto.testo, versione.contenuto.contesto, versione.motivo, versione.contesto)
            if versione.numero > 0 and "text corrected" not in versione.cambi:
                # Una versione che non cambia il testo lo copia: contano solo il suo motivo e il suo contesto.
                testi = (versione.motivo, versione.contesto)
            if altra.base not in gia and any(t is not None and schema.search(t) for t in testi):
                gia.add(altra.base)
                segnalazioni.append(Segnalazione(storia, (
                    f"nominata nella nota {versione.etichetta(segno)} ({versione.data[:10]}). Leggila: se dice che "
                    f"è fatta o risolta, si può chiudere con done: {storia.base}."
                ), _proposta(oggi, done=storia.base, text="")))

    for storia in da_seguire:
        contenuto = storia.ultima.contenuto
        trovato = DA_RIPRENDERE.search(contenuto.testo) if contenuto.riprendere_il is None else None
        if trovato:
            segnalazioni.append(Segnalazione(storia, (
                f"nel testo c'è «{trovato.group(0)}» ma la nota non ha la data del promemoria. Si può "
                f"aggiungere con updates: {storia.base} e remind."
            ), _proposta(oggi, updates=storia.base, remind="", text="")))
    for storia in quaderno.elenco():
        for versione in storia.versioni:
            if not versione.bloccati:
                continue
            campo = ("done" if "closed" in versione.bloccati
                     else "corrects" if "text corrected" in versione.bloccati else "updates")
            segnalazioni.append(Segnalazione(storia, (
                f"catena vecchia non permessa oggi: nella nota {versione.origine.id} ({versione.autore}, "
                f"{versione.data[:10]}) non vale «{', '.join(in_italiano(v) for v in versione.bloccati)}». Resta "
                f"nella storia; se il cambiamento va fatto, lo decide l'utente ({campo}: {storia.base})."
            )))
    segnalazioni += _integrabili(quaderno, segno, oggi, lista)
    return segnalazioni


def _integrabili(quaderno: Quaderno, segno: str, oggi: date, lista=None) -> list[Segnalazione]:
    """Le note integrabili (regola 7), a catena: ogni nota si propone una volta sola, dentro la più recente del suo
    gruppo. Prima i sotto-rami, poi le COSA senza sotto-rami."""
    vive = [s for s in quaderno.elenco() if _vive(s)]
    gruppi: list[tuple[list[Storia], str]] = []
    prese: set[str] = set()

    # (a) Le COSA con sotto-rami: stesso sotto-ramo, stesso autore, stesso tipo.
    for ramo, sotto in (lista.rami if lista is not None else ()):
        for nome, _ in sotto:
            insieme: dict[tuple[str, str], list[Storia]] = {}
            for storia in vive:
                if storia.base not in prese and (ramo, nome) in albero.sotto_rami_propri(storia, lista):
                    nota = storia.ultima.contenuto
                    insieme.setdefault((nota.autore, nota.natura), []).append(storia)
            for note in insieme.values():
                if len(note) > 1:
                    prese.update(s.base for s in note)
                    gruppi.append((note, f"stesso autore, stesso tipo e stesso sotto-ramo ({ramo}/{nome})"))

    # (b) Le COSA senza sotto-rami: la regola della 0.9.0, con il rimando nel testo, a catena.
    def senza_sotto_rami(storia: Storia) -> set[str]:
        return {c for c in (storia.ultima.contenuto.cosa or ()) if lista is None or not lista.sotto_rami_di(c)}
    restanti = [s for s in vive if s.base not in prese and senza_sotto_rami(s)]
    schemi = {s.base: _numero_nominato(_numeri_della_storia(s)) for s in restanti}

    def nomina(chi: Storia, chi_e_nominata: Storia) -> bool:
        return bool(schemi[chi_e_nominata.base].search(chi.ultima.contenuto.testo))

    legami: dict[str, set[str]] = {s.base: set() for s in restanti}
    comuni_di: dict[frozenset, list[str]] = {}
    for i, vecchia in enumerate(restanti):
        for recente in restanti[i + 1:]:
            comuni = sorted(senza_sotto_rami(vecchia) & senza_sotto_rami(recente),
                            key=lambda c: list(recente.ultima.contenuto.cosa).index(c))
            if (vecchia.ultima.contenuto.autore == recente.ultima.contenuto.autore and comuni
                    and (nomina(recente, vecchia) or nomina(vecchia, recente))):
                legami[vecchia.base].add(recente.base)
                legami[recente.base].add(vecchia.base)
                comuni_di[frozenset((vecchia.base, recente.base))] = comuni
    viste: set[str] = set()
    for storia in restanti:
        if storia.base in viste or not legami[storia.base]:
            continue
        componente, da_vedere = set(), [storia.base]
        while da_vedere:
            base = da_vedere.pop()
            if base not in componente:
                componente.add(base)
                da_vedere += legami[base]
        viste |= componente
        note = [s for s in restanti if s.base in componente]
        cosa = sorted({c for coppia, comuni in comuni_di.items() if coppia <= componente for c in comuni},
                      key=lambda c: (lista.cosa.index(c) if lista is not None and c in lista.cosa else len(c), c))
        gruppi.append((note, f"stesso autore, stessa COSA ({', '.join(cosa)}) e nel testo una nomina l'altra"
                             + (" (anche attraverso altre note)" if len(note) > 2 else "")))

    segnalazioni = []
    for note, perche in sorted(gruppi, key=lambda g: ordine(g[0][0].base)):
        recente = note[-1]
        for vecchia in note[:-1]:
            segnalazioni.append(Segnalazione(vecchia, (
                f"integrabile nella nota {recente.ultima.etichetta(segno)}: {perche}. Si può integrare con integrates: "
                f"{recente.base} e from_note: {vecchia.base} (il testo resta com'è); oppure lasciarle separate."
            ), _proposta(oggi, integrates=recente.base, from_note=vecchia.base)))
    return segnalazioni
