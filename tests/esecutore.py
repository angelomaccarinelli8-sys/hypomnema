"""Esegue un esempio della cartella ``esempi/`` in un quaderno vuoto e temporaneo.

Ogni esempio ha un file ``comandi.txt`` (un comando per riga, come si scriverebbe
dopo ``hypomnema``) e una cartella ``atteso/`` con:
- ``uscita.txt``: ciò che il programma deve scrivere a schermo;
- ``quaderno/``: come deve risultare il quaderno alla fine (note, registro, testimone).

Se l'esempio ha una cartella ``quaderno-iniziale/``, il quaderno parte come quella copia
(per esempio per mostrare un quaderno con una nota senza la sua riga nel registro).

Se l'esempio ha un suo ``hypomnema.toml`` si usa quello (per esempio per accendere
il testimone); altrimenti la configurazione di prova qui sotto, con il testimone spento.
Nei comandi, ``istantanea > FILE`` salva l'uscita in un file della cartella di prova (come la
shell) e ``cambiati FILE`` lo rilegge da lì. ``proponi FILE`` e ``testimone FILE`` usano file della
cartella dell'esempio:
``testimone FILE`` simula un messaggio dell'utente come lo manderebbe Claude Code, e
``risposte FILE`` una risposta di Claude alla fine del turno; ``impronta FILE`` usa un file
della cartella dell'esempio.

I percorsi della cartella temporanea (che cambiano da computer a computer, per esempio
nell'uscita di ``stato``) vengono scritti come ``<cartella di prova>/...``, e quelli della
cartella dell'esempio come ``<esempio>/...``, con le barre "/" anche su Windows.
``confronta A B`` confronta due file della cartella dell'esempio.

Se l'esempio ha anche un ``hypomnema-chat.toml`` (dalla 0.6.1, la chat collegata al computer), il
file va accanto a ``hypomnema.toml`` e le righe che cominciano con ``chat:`` usano quello: due
configurazioni, lo stesso quaderno.

Per avere risultati ripetibili l'ora di ogni comando è fissa:
il primo comando avviene il 15 gennaio 2026 alle 10:00 (ora italiana),
ogni comando successivo un minuto dopo.
"""

import io
import re
import shlex
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from hypomnema.cli import INGLESE, main

RADICE = Path(__file__).resolve().parent.parent
CARTELLA_ESEMPI = RADICE / "esempi"
ORA_DI_PARTENZA = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone(timedelta(hours=1)))

CONFIG_DI_PROVA = """\
[quaderno]
cartella = "quaderno"
cartella_note = "note"
file_registro = "registro.md"
cifre_numero_nota = 4

[testimone]
attivo = false
file = "testimone.jsonl"
prefisso_privato = "#privato"
segno_citazione = ">"
"""


CARTELLA_DI_PROVA = "<cartella di prova>"


def fuso_disponibile(nome: str = "Europe/Rome") -> bool:
    """C'è la tabella dei fusi orari su questo computer? (Su Windows di solito no.)"""
    import zoneinfo
    try:
        zoneinfo.ZoneInfo(nome)
        return True
    except (zoneinfo.ZoneInfoNotFoundError, ValueError, OSError):
        return False


def per_questo_computer(testo: str) -> str:
    """Una configurazione per le prove, così com'è.

    Nella 0.6.1, su un computer senza la tabella dei fusi orari, qui si toglieva la riga «fuso = …».
    Dalla 0.7.0 non serve più: per i fusi europei vale la regola dell'ora legale scritta nel programma
    (``fuso_europeo``), e gli esempi usano Europe/Rome. Resta il nome, usato da molte prove.
    """
    return testo


# La riga di «status» sul fuso cambia da computer a computer (dalla 0.7.0): negli esempi si scrive sempre
# come con la tabella dei fusi. Le due frasi sono provate a parte (test_difetti).
def fuso_come_con_la_tabella(testo: str) -> str:
    from hypomnema.cli import FUSO_CON_REGOLA, FUSO_CON_TABELLA
    return testo.replace(FUSO_CON_REGOLA, FUSO_CON_TABELLA)


def modello_chat(cartella: Path) -> Path:
    """Il modello della configurazione della chat, scritto in ``cartella`` per questo computer."""
    file = cartella / "hypomnema-chat.toml"
    file.write_text(per_questo_computer((RADICE / "chat" / "hypomnema-chat.toml").read_text(encoding="utf-8")),
                    encoding="utf-8", newline="\n")
    return file


def senza_cartella_di_prova(testo: str, lavoro: Path, esempio: Path | None = None) -> str:
    for cartella, etichetta in ((lavoro, CARTELLA_DI_PROVA), (esempio, "<esempio>")):
        if cartella is None:
            continue
        radice = str(cartella.resolve())
        schema = re.compile(re.escape(radice) + r"[^\s«»]*")
        testo = schema.sub(lambda m: etichetta + m.group(0)[len(radice):].replace("\\", "/"), testo)
    return testo


def elenco_esempi() -> list[Path]:
    return sorted(p for p in CARTELLA_ESEMPI.iterdir() if (p / "comandi.txt").is_file())


def esegui(esempio: Path, lavoro: Path) -> str:
    """Esegue i comandi dell'esempio con un quaderno in ``lavoro``; restituisce l'uscita."""
    config = lavoro / "hypomnema.toml"
    proprio = esempio / "hypomnema.toml"
    testo_config = proprio.read_text(encoding="utf-8") if proprio.is_file() else CONFIG_DI_PROVA
    config.write_text(per_questo_computer(testo_config), encoding="utf-8")
    config_chat = lavoro / "hypomnema-chat.toml"
    if (esempio / "hypomnema-chat.toml").is_file():
        config_chat.write_text(per_questo_computer((esempio / "hypomnema-chat.toml").read_text(encoding="utf-8")),
                               encoding="utf-8")
    iniziale = esempio / "quaderno-iniziale"
    if iniziale.is_dir():
        shutil.copytree(iniziale, lavoro / "quaderno")
    comandi = (esempio / "comandi.txt").read_text(encoding="utf-8").splitlines()
    uscita = io.StringIO()
    for numero, riga in enumerate(c for c in comandi if c.strip()):
        con_config = config
        parti = shlex.split(riga)
        if parti[0] == "chat:":
            con_config, parti = config_chat, parti[1:]
        destinazione = None
        if ">" in parti:
            # Come nella shell: l'uscita del comando va nel file, dentro la cartella di prova.
            destinazione = lavoro / parti[parti.index(">") + 1]
            parti = parti[:parti.index(">")]
        # I comandi si possono scrivere con il nome inglese o con quello italiano.
        nome = INGLESE.get(parti[0], parti[0])
        if nome in ("propose", "witness", "replies", "fingerprint", "archive"):
            argomenti = [parti[0], str(esempio / parti[1])]
        elif nome == "changed":
            argomenti = [parti[0], str(lavoro / parti[1])]
        elif nome == "compare":
            argomenti = [parti[0], *(str(esempio.resolve() / p) for p in parti[1:])]
        else:
            argomenti = parti
        uscita.write(f"$ hypomnema {riga}\n")
        uscita_comando = io.StringIO() if destinazione else uscita
        codice = main(
            ["--config", str(con_config), *argomenti],
            adesso=ORA_DI_PARTENZA + timedelta(minutes=numero),
            uscita=uscita_comando,
            errori=uscita,
        )
        if destinazione:
            destinazione.write_text(uscita_comando.getvalue(), encoding="utf-8")
        uscita.write(f"[codice di uscita: {codice}]\n\n")
    return fuso_come_con_la_tabella(senza_cartella_di_prova(uscita.getvalue(), lavoro, esempio))


def file_di(cartella: Path) -> dict[str, str]:
    """Tutti i file di una cartella, come {percorso relativo: contenuto}.

    Il file del blocco (``.sportello.lock``, dalla 0.6.1) non conta: è sempre vuoto e nasce con la
    prima scrittura; lo controllano le prove di ``test_chat_diretta``.
    """
    if not cartella.is_dir():
        return {}
    return {
        p.relative_to(cartella).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(cartella.rglob("*"))
        if p.is_file() and p.name != ".sportello.lock"
    }


CARTELLA_SKILL = RADICE / "skills" / "hypomnema"


def testo_della_skill() -> str:
    """Tutti i file della skill (dalla 0.7.0 divisa in più file): SKILL.md e poi gli altri, in ordine di nome."""
    file = [CARTELLA_SKILL / "SKILL.md", *sorted(p for p in CARTELLA_SKILL.glob("*.md") if p.name != "SKILL.md")]
    return "\n".join(f.read_text(encoding="utf-8") for f in file)
