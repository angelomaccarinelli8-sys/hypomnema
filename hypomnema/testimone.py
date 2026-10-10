"""Il testimone: registra le parole esatte dei messaggi dell'utente.

Claude Code lancia ``hypomnema testimone`` ogni volta che l'utente invia un messaggio,
prima che Claude lo legga (aggancio "UserPromptSubmit" in ``.claude/settings.json``).
Il programma riceve il messaggio in formato JSON e lo aggiunge in fondo al file del
testimone, una riga JSON per messaggio. Il file si apre solo in aggiunta.

Lo sportello usa poi questo file per controllare che la ``citazione`` di una nota
con autore "utente" sia davvero una frase dell'utente.

Formato del file (una riga per messaggio)::

    {"quando": "2026-01-15T10:00:00+01:00", "testo": "il testo esatto del messaggio"}
    {"quando": "2026-01-15T10:01:00+01:00", "privato": "messaggio privato, non registrato"}
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime

from hypomnema.configurazione import Configurazione

DICITURA_PRIVATO = "messaggio privato, non registrato"


class ErroreTestimone(Exception):
    """Il messaggio in arrivo o il file del testimone non sono leggibili."""


@dataclass(frozen=True)
class Messaggio:
    quando: str
    testo: str | None  # None per i messaggi privati


def registra(config: Configurazione, adesso: datetime, contenuto: bytes) -> bool:
    """Aggiunge il messaggio al testimone. Restituisce False se il testimone è spento."""
    if not config.testimone_attivo:
        return False
    try:
        dati = json.loads(contenuto.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ErroreTestimone("il messaggio in arrivo non è in formato JSON UTF-8.")
    if not isinstance(dati, dict) or not isinstance(dati.get("prompt"), str):
        raise ErroreTestimone("il messaggio in arrivo non contiene il campo «prompt» con il testo.")

    testo = dati["prompt"]
    voce: dict[str, str] = {"quando": adesso.isoformat(timespec="seconds")}
    if testo.lstrip().startswith(config.prefisso_privato):
        voce["privato"] = DICITURA_PRIVATO
    else:
        voce["testo"] = testo

    config.cartella_quaderno.mkdir(parents=True, exist_ok=True)
    with open(config.file_testimone, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(voce, ensure_ascii=False) + "\n")
    return True


def leggi_messaggi(config: Configurazione) -> list[Messaggio]:
    """Tutti i messaggi registrati, nell'ordine in cui sono arrivati."""
    if not config.file_testimone.is_file():
        return []
    messaggi = []
    righe = config.file_testimone.read_text(encoding="utf-8").split("\n")
    for numero, riga in enumerate(righe, start=1):
        if not riga.strip():
            continue
        try:
            voce = json.loads(riga)
            quando = voce["quando"]
            testo = voce.get("testo")
        except (json.JSONDecodeError, TypeError, KeyError):
            raise ErroreTestimone(
                f"la riga {numero} del file del testimone non è valida. "
                "Controlla se il file è stato modificato a mano."
            )
        messaggi.append(Messaggio(quando=quando, testo=testo))
    return messaggi


def normalizza(testo: str) -> str:
    """Riduce ogni gruppo di spazi, tabulazioni e a capo a un solo spazio."""
    return " ".join(testo.split())


def trova_citazione(messaggi: list[Messaggio], citazione: str) -> Messaggio | None:
    """Il primo messaggio che contiene la citazione parola per parola, oppure None.

    Il confronto è identico (maiuscole, accenti e punteggiatura compresi), a parte gli
    spazi e gli a capo multipli. La citazione deve iniziare e finire a confine di parola:
    "orto" non si trova dentro "contorto".
    """
    cercata = normalizza(citazione)
    if not cercata:
        return None
    schema = re.compile(r"(?<!\w)" + re.escape(cercata) + r"(?!\w)")
    for messaggio in messaggi:
        if messaggio.testo is not None and schema.search(normalizza(messaggio.testo)):
            return messaggio
    return None
