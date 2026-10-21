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

Dalla 0.9.0 ogni segnalazione che ha una regola fissa porta anche una **proposta pronta** (``proposta``), da completare
con le parole dell'utente: il programma non le inventa (``text`` e ``source`` restano vuoti, e lo sportello rifiuta
una proposta finché non sono scritti).
"""

import re
from dataclasses import dataclass
from datetime import date

from hypomnema import promemoria
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


def rivedi(quaderno: Quaderno, oggi: date, giorni: int, segno: str) -> list[Segnalazione]:
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
    segnalazioni += _integrabili(quaderno, segno, oggi)
    return segnalazioni


def _integrabili(quaderno: Quaderno, segno: str, oggi: date) -> list[Segnalazione]:
    """Le coppie di note integrabili (regola 7): la più vecchia si propone dentro la più recente."""
    vive = [s for s in quaderno.elenco() if _vive(s)]
    schemi = {s.base: _numero_nominato(_numeri_della_storia(s)) for s in vive}

    def nomina(chi: Storia, chi_e_nominata: Storia) -> bool:
        nota = chi.ultima.contenuto
        return any(t is not None and schemi[chi_e_nominata.base].search(t) for t in (nota.testo, nota.contesto))

    segnalazioni = []
    for i, vecchia in enumerate(vive):
        for recente in vive[i + 1:]:
            a, b = recente.ultima.contenuto, vecchia.ultima.contenuto
            comuni = [c for c in (a.cosa or ()) if c in (b.cosa or ())]
            if a.autore != b.autore or not comuni or not (nomina(recente, vecchia) or nomina(vecchia, recente)):
                continue
            segnalazioni.append(Segnalazione(vecchia, (
                f"integrabile nella nota {recente.ultima.etichetta(segno)}: stesso autore, stessa COSA "
                f"({', '.join(comuni)}) e una delle due nomina l'altra. Si può integrare con integrates: {recente.base} "
                f"e from_note: {vecchia.base} (il testo resta com'è); oppure lasciarle separate."
            ), _proposta(oggi, integrates=recente.base, from_note=vecchia.base)))
    return segnalazioni
