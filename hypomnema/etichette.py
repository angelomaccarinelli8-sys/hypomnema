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
        if chiave not in ("chi", "cosa"):
            raise ErroreEtichette(f"il file delle etichette «{file}» non prevede «{chiave}»: ci sono solo chi e "
                                  "cosa. Non ho scritto niente.")
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
    return Etichette(chi=liste["chi"], cosa=liste["cosa"])


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


def separa(valore: str) -> tuple[str, ...]:
    """Le etichette di un campo come «who: Anna, Marco»."""
    return tuple(parte.strip() for parte in valore.split(","))
