"""Le etichette CHI e COSA: la lista che scrive l'utente, nel file ``etichette.toml`` del quaderno. Dalla 0.7.0.

Una nota può avere fino a due etichette CHI (persone: ``who``) e fino a due etichette COSA (progetti o
argomenti: ``about``), scelte da una lista corta e fissa scritta dall'utente::

    chi = ["Anna", "Marco"]
    cosa = ["orto", "bilancio"]

Il file sta nella cartella del quaderno, così lo leggono tutte e due le configurazioni dello stesso
quaderno (``hypomnema.toml`` di Claude Code e ``hypomnema-chat.toml`` della chat) e le liste non possono
diventare diverse. Se il file manca, nessuna nota può avere etichette. Se è scritto male, il comando che
ne ha bisogno si ferma con un errore chiaro senza scrivere niente. Claude non lo scrive mai: lo scrive
l'utente (un modello commentato è ``esempi/etichette.toml``).

Nelle proposte il confronto è esatto: «Orto» non è «orto».

Dalla 0.8.0 lo sportello aggiunge da solo le etichette COSA che trova nel testo della nota
(``trova_nel_testo``): parola intera, come la ricerca, senza badare alle maiuscole, scritte come nella
lista, una volta sola e senza limite di numero. Le CHI restano solo proposte a mano. Per questo il file
si legge a ogni proposta (oltre che per un filtro e per il comando ``labels``).

Dalla 0.10.0 una COSA può avere dei **sotto-rami** (gli argomenti), ognuno con le sue parole, in una tabella
``[rami.<COSA>]`` (decisione di Angelo del 21/10, I0213)::

    [rami.orto]
    pomodori = ["pomodori", "pomodoro"]
    irrigazione = ["irrigazione", "goccia"]

Il nome del sotto-ramo non conta come parola: contano solo le parole della lista. Le parole si cercano come le COSA
(parola intera, maiuscole indifferenti), solo nel testo della nota, e una nota prende un sotto-ramo solo se ha già la
COSA del ramo (``sotto_rami``). Un file senza ``[rami]`` funziona come prima.
"""

import re
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python 3.10 (vedi configurazione)
    from hypomnema import _tomli as tomllib

NOME_FILE = "etichette.toml"
# I due campi della lista, con il campo della proposta e della nota che ci corrisponde.
CAMPI = (("chi", "who"), ("cosa", "about"))
CAMPI_INVERSI = tuple((nota, lista) for lista, nota in CAMPI)
MASSIMO_PER_NOTA = 2


class ErroreEtichette(Exception):
    """Il file delle etichette è scritto male."""


@dataclass(frozen=True)
class Etichette:
    chi: tuple[str, ...]
    cosa: tuple[str, ...]
    # Dalla 0.10.0: per ogni COSA con sotto-rami, (COSA, ((sotto-ramo, parole), ...)), nell'ordine del file.
    rami: tuple[tuple[str, tuple[tuple[str, tuple[str, ...]], ...]], ...] = ()

    def sotto_rami_di(self, cosa: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """I sotto-rami di una COSA, con le loro parole (vuoto se non ne ha)."""
        return next((sotto for ramo, sotto in self.rami if ramo == cosa), ())

    def ammesse(self, campo: str) -> tuple[str, ...]:
        """Le etichette ammesse per il campo della nota (``who`` o ``about``)."""
        return self.chi if campo == "who" else self.cosa


def file_di(cartella_quaderno: Path) -> Path:
    return cartella_quaderno / NOME_FILE


def problema_di(etichetta: str) -> str | None:
    """Che cosa non va in un'etichetta (in italiano, per l'utente), oppure None."""
    if not etichetta:
        return "è vuota"
    if etichetta != etichetta.strip():
        return "ha spazi all'inizio o alla fine"
    if "," in etichetta:
        return "contiene una virgola (la virgola separa le etichette)"
    if "\n" in etichetta or "\r" in etichetta:
        return "va a capo"
    return None


def leggi(cartella_quaderno: Path) -> Etichette | None:
    """La lista delle etichette, oppure None se il file non c'è."""
    file = file_di(cartella_quaderno)
    if not file.is_file():
        return None
    try:
        dati = tomllib.loads(file.read_text(encoding="utf-8-sig"))
    except UnicodeDecodeError:
        raise ErroreEtichette(f"il file delle etichette «{file}» non è salvato in UTF-8: salvalo in UTF-8. "
                              "Non ho scritto niente.")
    except tomllib.TOMLDecodeError as errore:
        raise ErroreEtichette(f"il file delle etichette «{file}» non è scritto correttamente: {errore}. "
                              "Non ho scritto niente.")
    for chiave in dati:
        if chiave not in ("chi", "cosa", "rami"):
            raise ErroreEtichette(f"il file delle etichette «{file}» non prevede «{chiave}»: ci sono solo chi, cosa "
                                  "e le tabelle [rami.<cosa>]. Non ho scritto niente.")
    liste = {}
    for chiave, _ in CAMPI:
        valore = dati.get(chiave, [])
        if not isinstance(valore, list) or not all(isinstance(v, str) for v in valore):
            raise ErroreEtichette(
                f"nel file delle etichette «{file}» «{chiave}» deve essere una lista di testi tra virgolette, per "
                f'esempio  {chiave} = ["{"Anna" if chiave == "chi" else "orto"}"]  . Non ho scritto niente.'
            )
        viste = set()
        for etichetta in valore:
            problema = problema_di(etichetta)
            if problema is None and etichetta in viste:
                problema = "è ripetuta"
            if problema is not None:
                raise ErroreEtichette(f"nel file delle etichette «{file}» l'etichetta «{etichetta}» di «{chiave}» "
                                      f"{problema}. Non ho scritto niente.")
            viste.add(etichetta)
        liste[chiave] = tuple(valore)
    return Etichette(chi=liste["chi"], cosa=liste["cosa"], rami=_rami(dati.get("rami", {}), liste["cosa"], file))


def _rami(dati, cosa: tuple[str, ...], file: Path) -> tuple:
    """Le tabelle [rami.<COSA>] (dalla 0.10.0), controllate: errore chiaro se sono scritte male."""
    def errore(testo: str) -> ErroreEtichette:
        return ErroreEtichette(f"nel file delle etichette «{file}» {testo}. Non ho scritto niente.")
    if not isinstance(dati, dict):
        raise errore("«rami» deve essere una tabella per ogni COSA, per esempio  [rami.orto]  e sotto le righe "
                     'pomodori = ["pomodori", "pomodoro"]')
    rami = []
    for ramo, sotto in dati.items():
        if ramo not in cosa:
            raise errore(f"la tabella [rami.{ramo}] non corrisponde a nessuna COSA della lista (le COSA sono: "
                         f"{', '.join(cosa) if cosa else 'nessuna'})")
        if not isinstance(sotto, dict):
            raise errore(f"[rami.{ramo}] deve avere una riga per sotto-ramo, per esempio  pomodori = "
                         '["pomodori", "pomodoro"]')
        parole_del_ramo: dict[str, str] = {}
        elenco = []
        for nome, parole in sotto.items():
            problema = problema_di(nome)
            if problema is not None:
                raise errore(f"il sotto-ramo «{nome}» di [rami.{ramo}] {problema}")
            if not isinstance(parole, list) or not all(isinstance(p, str) for p in parole):
                raise errore(f"il sotto-ramo «{nome}» di [rami.{ramo}] deve essere una lista di parole tra virgolette, "
                             f'per esempio  {nome} = ["{nome}"]')
            if not parole:
                raise errore(f"il sotto-ramo «{nome}» di [rami.{ramo}] non ha parole: senza parole nessuna nota lo "
                             "prende")
            for parola in parole:
                problema = problema_di(parola)
                if problema is None and parola.casefold() in parole_del_ramo:
                    altro = parole_del_ramo[parola.casefold()]
                    problema = ("è ripetuta" if altro == nome
                                else f"è anche nel sotto-ramo «{altro}»: una parola sta in un sotto-ramo solo")
                if problema is not None:
                    raise errore(f"la parola «{parola}» del sotto-ramo «{nome}» di [rami.{ramo}] {problema}")
                parole_del_ramo[parola.casefold()] = nome
            elenco.append((nome, tuple(parole)))
        rami.append((ramo, tuple(elenco)))
    return tuple(rami)


def sotto_rami(testo: str, cosa_della_nota: tuple[str, ...] | None, lista: "Etichette | None") -> tuple[tuple[str, str], ...]:
    """I sotto-rami di una nota (dalla 0.10.0): (COSA, sotto-ramo) nell'ordine del file, solo per le COSA che la nota
    ha già, quando una parola del sotto-ramo compare nel testo (parola intera, come le COSA)."""
    if lista is None or not cosa_della_nota:
        return ()
    return tuple((ramo, nome) for ramo, sotto in lista.rami if ramo in cosa_della_nota
                 for nome, parole in sotto if any(schema(p).search(testo) for p in parole))


def schema(etichetta: str) -> re.Pattern:
    """L'etichetta come parola intera, come la ricerca (``cercatore.schema_parola``): delimitata da segni che
    non sono lettere o cifre, senza badare alle maiuscole; tra le parole di un'etichetta va bene qualsiasi
    spazio o a capo."""
    parole = r"\s+".join(re.escape(p) for p in etichetta.split())
    return re.compile(r"(?<![^\W_])" + parole + r"(?![^\W_])", re.IGNORECASE)


def trova_nel_testo(testo: str, lista: Etichette | None) -> tuple[str, ...]:
    """Le etichette COSA della lista che compaiono nel testo, scritte come nella lista e nel suo ordine."""
    if lista is None:
        return ()
    return tuple(e for e in lista.cosa if schema(e).search(testo))


def cosa_finali(a_mano: tuple[str, ...] | None, trovate: tuple[str, ...]) -> tuple[tuple[str, ...] | None,
                                                                                     tuple[str, ...] | None]:
    """Le COSA della nota (prima quelle a mano, poi quelle trovate nel testo, senza doppioni) e quelle
    messe dallo sportello (le trovate che non erano già a mano)."""
    a_mano = a_mano or ()
    dal_testo = tuple(e for e in trovate if e not in a_mano)
    finali = a_mano + dal_testo
    return (finali or None), (dal_testo or None)


def cosa_a_mano(nota) -> tuple[str, ...]:
    """Le COSA proposte a mano: quelle della nota meno quelle messe dallo sportello."""
    dal_testo = nota.cosa_dal_testo or ()
    return tuple(e for e in (nota.cosa or ()) if e not in dal_testo)


# Quante parole mostrare prima e dopo l'etichetta trovata, nel comando «matches» (dalla 0.8.0).
PAROLE_INTORNO = 4


def pezzo_di_frase(testo: str, etichetta: str) -> str | None:
    """Il punto del testo dove l'etichetta si trova (la prima volta): fino a PAROLE_INTORNO parole prima e
    dopo, la parola trovata tra parentesi quadre, su una riga. None se non si trova."""
    trovato = schema(etichetta).search(testo)
    if trovato is None:
        return None
    prima = testo[:trovato.start()]
    dopo = testo[trovato.end():]
    # Il pezzo attaccato alla parola (per esempio «l'» in «l'orto») resta con lei.
    parole_prima = prima.split()
    attaccato = "" if not prima or prima[-1].isspace() else parole_prima.pop()
    parole_dopo = dopo.split()
    seguito = "" if not dopo or dopo[0].isspace() else parole_dopo.pop(0)
    inizio = ("… " if len(parole_prima) > PAROLE_INTORNO else "") + " ".join(parole_prima[-PAROLE_INTORNO:])
    fine = " ".join(parole_dopo[:PAROLE_INTORNO]) + (" …" if len(parole_dopo) > PAROLE_INTORNO else "")
    centro = f"{attaccato}[{' '.join(trovato.group(0).split())}]{seguito}"
    return " ".join(parte for parte in (inizio, centro, fine) if parte)


def con_cosa_dal_testo(quaderno, lista: Etichette | None) -> None:
    """Le COSA dal testo calcolate al momento della lettura, per tutte le versioni di tutte le note (dalla 0.9.0).

    Per ogni versione: quelle proposte a mano più quelle trovate oggi nel suo testo con la lista di oggi. Le note
    vecchie prendono subito un'etichetta aggiunta alla lista; nessun file si scrive o si cambia.
    """
    from dataclasses import replace
    if lista is None:
        return
    for storia in quaderno.elenco():
        for i, versione in enumerate(storia.versioni):
            nota = versione.contenuto
            cosa, dal_testo = cosa_finali(cosa_a_mano(nota), trova_nel_testo(nota.testo, lista))
            if (cosa, dal_testo) != (nota.cosa, nota.cosa_dal_testo):
                storia.versioni[i] = replace(versione, contenuto=replace(nota, cosa=cosa, cosa_dal_testo=dal_testo))


def separa(valore: str) -> tuple[str, ...]:
    """Le etichette di un campo come «who: Anna, Marco»."""
    return tuple(parte.strip() for parte in valore.split(","))
