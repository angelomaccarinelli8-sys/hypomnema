"""Il testimone: registra le parole esatte dei messaggi dell'utente.

Claude Code lancia ``hypomnema testimone`` ogni volta che l'utente invia un messaggio,
prima che Claude lo legga (aggancio "UserPromptSubmit" in ``plugin/hooks/hooks.json``).
Il programma riceve il messaggio in formato JSON e lo aggiunge in fondo al file del
testimone, una riga JSON per messaggio. Il file si apre solo in aggiunta.

Lo sportello usa poi questo file per controllare che la ``citazione`` di una nota
con autore "utente" sia davvero una frase dell'utente.

Formato del file (una riga per messaggio)::

    {"quando": "2026-01-15T10:00:00+01:00", "testo": "il testo esatto del messaggio"}
    {"quando": "2026-01-15T10:01:00+01:00", "testo": "> riga riportata\nmio commento", "righe_citate": [1]}
    {"quando": "2026-01-15T10:02:00+01:00", "privato": "messaggio privato, non registrato"}

"righe_citate" (facoltativo) elenca i numeri delle righe, contando da 1, che iniziano con il
segno di citazione (di base ">"): l'utente le ha marcate come parole riportate da altri.
"""

import json
import re
from dataclasses import dataclass, replace
from pathlib import Path
from datetime import datetime

from hypomnema.configurazione import Configurazione

DICITURA_PRIVATO = "messaggio privato, non registrato"


class ErroreTestimone(Exception):
    """Il messaggio in arrivo o il file del testimone non sono leggibili."""


@dataclass(frozen=True)
class Messaggio:
    quando: str
    testo: str | None  # None per i messaggi privati
    righe_citate: tuple[int, ...] = ()
    # Il codice del messaggio che Claude Code dà a ogni turno, se c'è: lega una risposta al suo messaggio.
    prompt_id: str | None = None
    # La dicitura scritta al posto del testo, per i messaggi non registrati.
    privato: str | None = None


@dataclass(frozen=True)
class Ritrovamento:
    messaggio: Messaggio
    # True se la citazione viene tutta da righe marcate con il segno di citazione.
    riportata: bool


def _righe(testo: str) -> list[str]:
    return testo.split("\n")


def righe_marcate(testo: str, segno: str) -> list[int]:
    """I numeri (da 1) delle righe che iniziano con il segno, a parte gli spazi davanti."""
    return [n for n, riga in enumerate(_righe(testo), start=1) if riga.lstrip().startswith(segno)]


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
    voce: dict[str, object] = {"quando": adesso.isoformat(timespec="seconds")}
    if testo.lstrip().startswith(config.prefisso_privato):
        voce["privato"] = DICITURA_PRIVATO
    else:
        voce["testo"] = testo
        citate = righe_marcate(testo, config.segno_citazione)
        if citate:
            voce["righe_citate"] = citate
    if isinstance(dati.get("prompt_id"), str):
        voce["prompt_id"] = dati["prompt_id"]

    config.cartella_quaderno.mkdir(parents=True, exist_ok=True)
    with open(config.file_testimone, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(voce, ensure_ascii=False) + "\n")
    return True


def _voce_valida(riga: str) -> Messaggio | None:
    """La voce di una riga del testimone, oppure None se la riga non ha il formato previsto.

    Una voce valida ha "quando" (testo) e esattamente uno tra "testo" e "privato" (testo).
    Accanto a "testo" può avere "righe_citate": numeri di riga crescenti, da 1 al numero di righe.
    Può avere "prompt_id" (testo).
    """
    try:
        voce = json.loads(riga)
    except json.JSONDecodeError:
        return None
    if not isinstance(voce, dict) or not isinstance(voce.get("quando"), str):
        return None
    if "prompt_id" in voce and not isinstance(voce["prompt_id"], str):
        return None
    messaggio = _voce_senza_prompt_id(voce)
    if messaggio is None or "prompt_id" not in voce:
        return messaggio
    return replace(messaggio, prompt_id=voce["prompt_id"])


def _voce_senza_prompt_id(voce: dict) -> Messaggio | None:
    altri = set(voce) - {"quando", "prompt_id"}
    if altri == {"testo"} and isinstance(voce["testo"], str):
        return Messaggio(quando=voce["quando"], testo=voce["testo"])
    if altri == {"testo", "righe_citate"} and isinstance(voce["testo"], str):
        citate = voce["righe_citate"]
        totale = len(_righe(voce["testo"]))
        if (
            isinstance(citate, list) and citate
            and all(isinstance(n, int) and not isinstance(n, bool) and 1 <= n <= totale for n in citate)
            and citate == sorted(set(citate))
        ):
            return Messaggio(quando=voce["quando"], testo=voce["testo"], righe_citate=tuple(citate))
    if altri == {"privato"} and isinstance(voce["privato"], str):
        return Messaggio(quando=voce["quando"], testo=None, privato=voce["privato"])
    return None


def leggi_messaggi(
    config: Configurazione, file: Path | None = None, di_chi: str = "del testimone"
) -> list[Messaggio]:
    """Tutti i messaggi registrati, nell'ordine in cui sono arrivati.

    Di base legge il file del testimone; ``file`` permette di leggere quello delle risposte.
    """
    file = config.file_testimone if file is None else file
    if not file.is_file():
        return []
    messaggi = []
    try:
        righe = file.read_text(encoding="utf-8").split("\n")
    except UnicodeDecodeError:
        raise ErroreTestimone(
            f"il file {di_chi} non è in UTF-8. Controlla se è stato modificato a mano."
        )
    for numero, riga in enumerate(righe, start=1):
        if not riga.strip():
            continue
        messaggio = _voce_valida(riga)
        if messaggio is None:
            raise ErroreTestimone(
                f"la riga {numero} del file {di_chi} non è valida. "
                "Controlla se il file è stato modificato a mano."
            )
        messaggi.append(messaggio)
    return messaggi


def normalizza(testo: str) -> str:
    """Riduce ogni gruppo di spazi, tabulazioni e a capo a un solo spazio."""
    return " ".join(testo.split())


def _senza_segni(messaggio: Messaggio, segno: str) -> list[str]:
    """Le righe del messaggio, togliendo dalle righe marcate il segno e uno spazio dopo."""
    righe = _righe(messaggio.testo)
    for numero in messaggio.righe_citate:
        riga = righe[numero - 1].lstrip()[len(segno):]
        righe[numero - 1] = riga[1:] if riga.startswith(" ") else riga
    return righe


def _blocchi_marcati(messaggio: Messaggio, righe: list[str]) -> list[str]:
    """I gruppi di righe marcate consecutive, ciascuno unito in un solo testo."""
    blocchi, corrente, precedente = [], [], None
    for numero in messaggio.righe_citate:
        if precedente is not None and numero != precedente + 1:
            blocchi.append("\n".join(corrente))
            corrente = []
        corrente.append(righe[numero - 1])
        precedente = numero
    if corrente:
        blocchi.append("\n".join(corrente))
    return blocchi


def trova_citazione(messaggi: list[Messaggio], citazione: str, segno: str) -> Ritrovamento | None:
    """Il primo messaggio che contiene la citazione parola per parola, oppure None.

    Il confronto è identico (maiuscole, accenti e punteggiatura compresi), a parte gli
    spazi e gli a capo multipli. La citazione deve iniziare e finire a confine di parola:
    "orto" non si trova dentro "contorto". Nelle righe marcate il segno di citazione si può
    omettere. La citazione è "riportata" se si trova tutta dentro righe marcate consecutive.
    """
    cercata = normalizza(citazione)
    if not cercata:
        return None
    schema = re.compile(r"(?<!\w)" + re.escape(cercata) + r"(?!\w)")
    for messaggio in messaggi:
        if messaggio.testo is None:
            continue
        righe = _senza_segni(messaggio, segno)
        if schema.search(normalizza("\n".join(righe))) or schema.search(normalizza(messaggio.testo)):
            blocchi = _blocchi_marcati(messaggio, righe) + _blocchi_marcati(messaggio, _righe(messaggio.testo))
            riportata = any(schema.search(normalizza(b)) for b in blocchi)
            return Ritrovamento(messaggio=messaggio, riportata=riportata)
    return None
