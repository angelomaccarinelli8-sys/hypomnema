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

Il file si legge solo quando serve: una proposta con etichette, un filtro, il comando ``labels``.
Il confronto è esatto: «Orto» non è «orto».
"""

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


def separa(valore: str) -> tuple[str, ...]:
    """Le etichette di un campo come «who: Anna, Marco»."""
    return tuple(parte.strip() for parte in valore.split(","))
