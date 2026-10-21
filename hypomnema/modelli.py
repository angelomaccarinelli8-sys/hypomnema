"""I modelli delle proposte (comando «template»): per ogni mossa, la proposta vuota con soltanto i campi ammessi.
Solo lettura: non legge e non scrive il quaderno. Dalla 0.10.0 (pezzo 6).

I modelli hanno la data di oggi, autore ``user`` e ``knowledge: stated`` (le note dell'utente sono le più frequenti) e
tutti gli altri valori vuoti: le parole dell'utente non si inventano, e lo sportello rifiuta un campo vuoto. I campi
facoltativi non ci sono: li dice la riga sotto il modello. Le regole restano quelle dello sportello (``regole``).
"""

import json
from datetime import date

# Le mosse, con i nomi italiani come sinonimi (come i comandi).
MOSSE = ("new", "integrates", "updates", "done", "cancels")
NOMI_ITALIANI = {"nuova": "new", "integra": "integrates", "aggiorna": "updates", "chiudi": "done",
                 "annulla": "cancels"}

DESCRIZIONI = {
    "new": "una nota nuova",
    "integrates": "aggiungere in fondo a una nota che c'è già (l'integrazione)",
    "updates": "cambiare tipo, priorità, promemoria o etichette di una nota",
    "done": "chiudere una domanda aperta, una cosa da fare o un promemoria",
    "cancels": "annullare una nota che non vale più (diverso da «fatto»)",
}


def _base(oggi: date) -> dict:
    return {"date": oggi.isoformat(), "source": "", "author": "user", "knowledge": "stated"}


def modelli(mossa: str, oggi: date) -> list[tuple[str, dict]]:
    """Le forme di una mossa: (che cosa fa, proposta vuota)."""
    base = _base(oggi)
    if mossa == "new":
        return [("una nota nuova", {**base, "kind": "", "text": ""})]
    if mossa == "integrates":
        return [("parole nuove in fondo alla nota NNNN (dello stesso autore)", {**base, "integrates": "", "text": ""}),
                ("il testo di un'altra nota in fondo alla nota NNNN, senza «text»",
                 {**base, "integrates": "", "from_note": ""})]
    if mossa == "updates":
        return [("un valore nuovo per la nota NNNN: tieni solo i campi che cambiano tra kind, priority, remind, "
                 "who e about", {**base, "updates": "", "kind": "", "priority": "", "remind": "", "who": "",
                                 "about": "", "text": ""})]
    if mossa == "done":
        return [("chiudere la nota NNNN (o più note: «0012, 0015»), con il motivo in «text»",
                 {**base, "done": "", "text": ""})]
    return [("annullare la nota NNNN, con il motivo in «text»", {**base, "cancels": "", "text": ""})]


FACOLTATIVI = {
    "new": ("Facoltativi: «context» (solo nelle note dell'utente: le aggiunte di Claude), «quote» (solo nelle note di "
            "Claude: le parole dell'utente), «remind» (AAAA-MM-GG), «priority» (solo l'utente), «who» e «about» (dalla "
            "lista delle etichette; le COSA scritte nel testo le mette lo sportello), «confirms» (solo per una "
            "decisione che conferma un'idea)."),
    "integrates": ("Niente altro: niente «kind», «about», «who», «priority», «remind» né «context» (lo sportello li "
                   "rifiuta). Per cambiare il tipo o le etichette serve «updates»."),
    "updates": "Facoltativo: «context» (solo se il cambiamento è dell'utente).",
    "done": ("Facoltativi: «kind» (che cosa è diventata: decision, fact o idea; decision solo l'utente), «context» "
             "(solo se la chiusura è dell'utente)."),
    "cancels": "Facoltativo: «context» (solo se l'annullamento è dell'utente).",
}

VALORI = ("Valori: «author» user o claude; «knowledge» stated, observed o inferred (una decisione è sempre stated); "
          "«kind» fact, idea, decision, open o todo. Nei rimandi solo il numero («0012», mai «I0012»). Per una nota di "
          "Claude: author claude, niente «context» né «priority», le parole dell'utente in «quote».")


def testo(mossa: str | None, oggi: date) -> str:
    """Il testo da stampare per una mossa, o l'elenco delle mosse."""
    if mossa is None:
        righe = ["I modelli delle proposte (template <mossa>):"]
        righe += [f"- {m}: {DESCRIZIONI[m]}" for m in MOSSE]
        righe.append("Per corrects, reopens e confirms vedi FORMATO.md. Non è stato letto né cambiato niente.")
        return "\n".join(righe)
    righe = [f"Modello per «{mossa}»: {DESCRIZIONI[mossa]}. Completa i valori vuoti, poi propose."]
    for che_cosa, proposta in modelli(mossa, oggi):
        righe.append(f"{che_cosa[0].upper()}{che_cosa[1:]}:")
        righe.append(json.dumps(proposta, ensure_ascii=False))
    righe += [FACOLTATIVI[mossa], VALORI]
    return "\n".join(righe)
