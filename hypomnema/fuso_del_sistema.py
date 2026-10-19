"""Il fuso orario del taccuino viene dal sistema operativo dell'utente. Dalla 0.7.0.

Il principio (decisione di Angelo, 19/10/2026):

1. **Sul computer dell'utente** vale sempre l'ora del sistema operativo, anche se la configurazione ha
   la riga ``fuso``: se la riga dice un fuso diverso dal sistema, ``status`` lo segnala, ma non blocca.
2. Il computer dell'utente legge anche il **nome** del fuso del sistema (``Europe/Rome``) e, se è
   cambiato, lo aggiunge in fondo al file ``fuso-del-sistema.jsonl`` del quaderno (una riga per volta,
   solo in aggiunta: vale l'ultima riga).
3. **Le macchine in UTC** (la chat collegata al computer, le sessioni in cloud) usano, in quest'ordine:
   la riga ``fuso`` della configurazione, poi l'ultima riga del file del quaderno, poi UTC, detto
   chiaramente da ``status``. Un fuso che lì non si trova (manca la tabella dei fusi) si salta.

**Come si riconosce una macchina in UTC**, con una regola fissa: il nome del fuso del sistema è UTC
(``UTC``, ``Etc/UTC``, ``Etc/Universal``, ``Zulu``, ``Etc/GMT``…; su Windows la chiave ``UTC``), oppure il
nome non si riesce a leggere e la differenza dall'ora universale è zero. Ogni altro nome è il computer
dell'utente. Una configurazione per la chat (``modalita = "chat"``) non scrive mai il file.

**Dove si legge il nome:**

- su Windows, nel registro: la chiave del fuso (``TimeZoneKeyName``, per esempio «W. Europe Standard
  Time») e la regione (``Control Panel\\International\\Geo\\Name``, per esempio ``IT``), tradotte con la
  tabella ufficiale di Unicode CLDR (``_cldr/windowsZones.xml``): «W. Europe Standard Time» con la
  regione ``IT`` è ``Europe/Rome``; senza regione, ``Europe/Berlin`` (stesse ore);
- su macOS e Linux: la variabile ``TZ``, poi dove punta ``/etc/localtime``, poi ``/etc/timezone``.

Per scrivere date e ore sul computer dell'utente non serve la tabella dei fusi: basta l'ora del sistema.
"""

import json
import os
import re
import zoneinfo
from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo
from functools import lru_cache
from pathlib import Path

from hypomnema import aggiunta

NOME_FILE = "fuso-del-sistema.jsonl"
TABELLA_WINDOWS = Path(__file__).resolve().parent / "_cldr" / "windowsZones.xml"
# I nomi che vogliono dire «questa macchina tiene l'ora universale».
NOMI_UTC = frozenset({
    "UTC", "Etc/UTC", "Etc/Universal", "Universal", "Etc/Zulu", "Zulu", "UCT", "Etc/UCT",
    "GMT", "Etc/GMT", "Etc/GMT0", "Etc/GMT+0", "Etc/GMT-0", "GMT0", "GMT+0", "GMT-0", "Etc/Greenwich", "Greenwich",
})


# Un nome della tabella dei fusi: «Europe/Rome», «America/Argentina/Buenos_Aires», «Etc/GMT+1», «UTC».
FORMA_NOME = re.compile(r"[A-Za-z_]+(?:/[A-Za-z0-9_+\-]+)+|[A-Za-z]+")


@dataclass(frozen=True)
class Sistema:
    """Il fuso del sistema operativo: il nome (``Europe/Rome``, o None se non si legge) e da dove viene."""
    nome: str | None
    da_dove: str


@dataclass(frozen=True)
class Riga:
    """Una riga del file del quaderno."""
    quando: str
    fuso: str
    dal_sistema: str


@dataclass(frozen=True)
class Scelta:
    """Il fuso da usare in un comando, e la riga di ``status`` che lo dice."""
    # None: l'ora così com'è (quella del sistema). Altrimenti il fuso in cui portarla.
    fuso: tzinfo | None
    descrizione: str
    # Il computer dell'utente: il suo fuso va scritto nel file del quaderno (se è cambiato).
    computer_dell_utente: bool
    sistema: Sistema


# --- Il nome del fuso del sistema ---

@lru_cache(maxsize=1)
def _tabella_windows() -> dict[tuple[str, str], str]:
    import xml.etree.ElementTree as albero
    tabella = {}
    for voce in albero.parse(TABELLA_WINDOWS).getroot().iter("mapZone"):
        nomi = voce.get("type", "").split()
        if nomi:
            tabella[(voce.get("other"), voce.get("territory"))] = nomi[0]
    return tabella


def da_windows(chiave: str, regione: str | None) -> str | None:
    """Il nome tipo ``Europe/Rome`` di un fuso di Windows, con la regione se la tabella la conosce."""
    tabella = _tabella_windows()
    if regione:
        trovato = tabella.get((chiave, regione.upper()))
        if trovato:
            return trovato
    return tabella.get((chiave, "001"))


def _leggi_registro(radice, percorso: str, valore: str) -> str | None:
    import winreg
    try:
        with winreg.OpenKey(radice, percorso) as chiave:
            letto, _ = winreg.QueryValueEx(chiave, valore)
    except OSError:
        return None
    return letto.strip().rstrip("\x00") if isinstance(letto, str) and letto.strip() else None


def _sistema_windows() -> Sistema:
    import winreg
    chiave = _leggi_registro(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\TimeZoneInformation",
                             "TimeZoneKeyName")
    if chiave is None:
        return Sistema(None, "Windows: la chiave del fuso non si legge")
    regione = _leggi_registro(winreg.HKEY_CURRENT_USER, r"Control Panel\International\Geo", "Name")
    da_dove = f"Windows: {chiave}" + (f", regione {regione}" if regione else "")
    return Sistema(da_windows(chiave, regione), da_dove)


def _nome_da_percorso(percorso: str) -> str | None:
    """«/usr/share/zoneinfo/Europe/Rome» → «Europe/Rome»."""
    _, trovato, dopo = percorso.replace("\\", "/").partition("/zoneinfo/")
    if not trovato or not dopo:
        return None
    for prefisso in ("posix/", "right/"):
        if dopo.startswith(prefisso):
            dopo = dopo[len(prefisso):]
    return dopo


def _sistema_unix(ambiente=os.environ, localtime: str = "/etc/localtime", timezone: str = "/etc/timezone") -> Sistema:
    tz = ambiente.get("TZ")
    if tz:
        valore = tz[1:] if tz.startswith(":") else tz
        nome = _nome_da_percorso(valore) if "/zoneinfo/" in valore else valore
        # Una regola POSIX come «CET-1CEST» non è un nome della tabella: non si sa.
        valido = nome is not None and FORMA_NOME.fullmatch(nome) is not None
        return Sistema(nome if valido else None, f"variabile TZ={tz}")
    if os.path.islink(localtime):
        nome = _nome_da_percorso(os.path.realpath(localtime))
        if nome:
            return Sistema(nome, f"{localtime} → {nome}")
    try:
        nome = Path(timezone).read_text(encoding="utf-8").strip().splitlines()[0].strip()
        if nome:
            return Sistema(nome, f"{timezone}: {nome}")
    except (OSError, IndexError, UnicodeDecodeError):
        pass
    return Sistema(None, "il nome del fuso non si legge")


def leggi_sistema() -> Sistema:
    """Il fuso del sistema operativo di questa macchina. Le prove la sostituiscono (tests/__init__.py)."""
    return _sistema_windows() if os.name == "nt" else _sistema_unix()


def in_utc(sistema: Sistema, adesso: datetime) -> bool:
    """La regola fissa: questa macchina tiene l'ora universale (chat, cloud)?"""
    if sistema.nome is not None:
        return sistema.nome in NOMI_UTC
    return adesso.utcoffset() == timedelta(0)


# --- Il file del quaderno ---

def file_di(cartella_quaderno: Path) -> Path:
    return cartella_quaderno / NOME_FILE


def ultima_riga(cartella_quaderno: Path) -> Riga | None:
    """L'ultima riga valida del file, oppure None. Le righe rovinate si saltano."""
    try:
        testo = file_di(cartella_quaderno).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    for riga in reversed(testo.splitlines()):
        try:
            dati = json.loads(riga)
        except json.JSONDecodeError:
            continue
        if (isinstance(dati, dict) and set(dati) == {"quando", "fuso", "dal_sistema"}
                and all(isinstance(v, str) and v for v in dati.values())):
            return Riga(dati["quando"], dati["fuso"], dati["dal_sistema"])
    return None


def annota(config, scelta: Scelta, adesso: datetime) -> bool:
    """Sul computer dell'utente aggiunge una riga al file se il fuso del sistema è cambiato. True se l'ha scritta.

    Mai nella configurazione per la chat; mai se il nome del fuso non si legge. Non ferma mai il comando:
    se non si può scrivere, si va avanti (``status`` mostra comunque il fuso del sistema).
    """
    nome = scelta.sistema.nome
    if config.in_chat or not scelta.computer_dell_utente or nome is None:
        return False
    if not config.cartella_quaderno.is_dir():
        return False
    ultima = ultima_riga(config.cartella_quaderno)
    if ultima is not None and ultima.fuso == nome:
        return False
    riga = json.dumps({"quando": adesso.isoformat(timespec="seconds"), "fuso": nome,
                       "dal_sistema": scelta.sistema.da_dove}, ensure_ascii=False)
    try:
        aggiunta.aggiungi(file_di(config.cartella_quaderno), riga + "\n")
    except OSError:
        return False
    return True


# --- La scelta del fuso ---

def _zona(nome: str) -> tzinfo | None:
    try:
        return zoneinfo.ZoneInfo(nome)
    except (zoneinfo.ZoneInfoNotFoundError, ValueError, OSError):
        return None


def scegli(config, adesso: datetime, sistema: Sistema | None = None) -> Scelta:
    """Il fuso da usare, con la precedenza del principio (vedi sopra)."""
    sistema = sistema or leggi_sistema()
    scritto = config.nome_fuso
    if not in_utc(sistema, adesso):
        nome = sistema.nome or "nome non letto"
        descrizione = f"Fuso orario: {nome}, dal sistema operativo ({sistema.da_dove})."
        if scritto and scritto != sistema.nome:
            descrizione += (f" Nella configurazione c'è fuso = \"{scritto}\", diverso dal sistema: su questo "
                            "computer vale il sistema.")
        return Scelta(None, descrizione, True, sistema)

    saltati = []
    if scritto:
        zona = _zona(scritto)
        if zona is not None:
            return Scelta(zona, f"Fuso orario: {scritto}, scritto nella configurazione: questa macchina è in UTC.",
                          False, sistema)
        saltati.append(f"fuso = \"{scritto}\" della configurazione non si trova su questa macchina")
    riga = ultima_riga(config.cartella_quaderno)
    if riga is not None:
        zona = _zona(riga.fuso)
        if zona is not None:
            descrizione = (f"Fuso orario: {riga.fuso}, dal file {NOME_FILE} del quaderno (scritto il "
                           f"{riga.quando[:10]} dal computer dell'utente): questa macchina è in UTC.")
            if saltati:
                descrizione += f" ({saltati[0]}.)"
            return Scelta(zona, descrizione, False, sistema)
        saltati.append(f"il file {NOME_FILE} dice {riga.fuso}, ma su questa macchina manca la tabella dei fusi")
    else:
        saltati.append(f"il quaderno non ha ancora il file {NOME_FILE}, che nasce la prima volta che usi "
                       "Hypomnema sul tuo computer")
    return Scelta(None, "Fuso orario: UTC, quello di questa macchina: " + "; ".join(saltati) + ".", False, sistema)


def nel_fuso(config, adesso: datetime) -> datetime:
    """L'ora da scrivere: quella del sistema sul computer dell'utente, il fuso scelto su una macchina in UTC."""
    scelta = scegli(config, adesso)
    return adesso.astimezone(scelta.fuso) if scelta.fuso is not None else adesso
