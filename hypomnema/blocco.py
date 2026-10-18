"""Il blocco del quaderno: un passaggio alla volta, anche da due macchine. Dalla 0.6.1.

Sullo stesso quaderno possono scrivere insieme Claude Code (con il plugin, su Windows) e la chat di
Claude collegata al computer (su una macchina Linux che vede la stessa cartella). Senza un blocco
due passaggi quasi contemporanei possono leggere una nota appena creata ma non ancora scritta,
scrivere due volte l'intestazione del registro, o controllare la stessa chiusura due volte.

Il blocco è il blocco del sistema operativo (``fcntl.flock`` su Linux e macOS, ``msvcrt.locking``
su Windows) sul file ``.sportello.lock`` nella cartella del quaderno. Il file si crea vuoto la
prima volta e non si cancella mai, e nessuno ci scrive dentro: il blocco lo toglie il sistema
quando il passaggio finisce, anche se il programma si interrompe, quindi non resta mai un blocco
da togliere a mano.

- Lo sportello e il comando ``archive`` (che scrivono) prendono il blocco per tutto il passaggio:
  lettura del quaderno, regole, file nuovi e righe in fondo.
- I comandi che leggono soltanto lo prendono solo se il file c'è già, così un quaderno vuoto resta
  vuoto.
- Se il quaderno è occupato si aspetta al massimo ``ATTESA_BLOCCO`` secondi. Poi chi scrive si
  ferma senza aver scritto niente (``QuadernoOccupato``); chi legge soltanto va avanti senza blocco,
  così un passaggio fermo a metà non ferma mai la lettura.
- Il file del blocco non si legge mai: su Windows il blocco è obbligatorio (chi legge la parte
  bloccata riceve un errore), per questo si blocca un byte lontanissimo dalla fine del file, che
  resta vuoto. Nessun comando lo legge: ``snapshot`` e ``changed`` lo saltano.
- Se il disco non permette i blocchi (alcune cartelle condivise) si va avanti senza: restano
  l'apertura esclusiva delle note, che non sovrascrive mai, e ``check``.
"""

import errno
import os
import time
from contextlib import contextmanager
from pathlib import Path

NOME_FILE = ".sportello.lock"
# Quanto si aspetta un altro passaggio: una regola, non un'impostazione (un passaggio dura
# una frazione di secondo).
ATTESA_BLOCCO = 10.0
PAUSA = 0.05

# Gli errori che vogliono dire «il file è bloccato da un altro»: si riprova.
_OCCUPATO = {errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK, getattr(errno, "EDEADLOCK", errno.EDEADLK)}


class QuadernoOccupato(Exception):
    """Un altro passaggio tiene il quaderno da più di ATTESA_BLOCCO secondi."""


# Su Windows si blocca un solo byte, molto oltre la fine del file vuoto: Windows lo permette, e chi
# legge il file (vuoto) non tocca mai la parte bloccata.
POSIZIONE_WINDOWS = 1 << 30

if os.name == "nt":
    import msvcrt

    def _prova(f) -> None:
        f.seek(POSIZIONE_WINDOWS)
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)

    def _lascia(f) -> None:
        f.seek(POSIZIONE_WINDOWS)
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl

    def _prova(f) -> None:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _lascia(f) -> None:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def file_del_blocco(cartella_quaderno: Path) -> Path:
    return cartella_quaderno / NOME_FILE


def _prendi(f, attesa: float) -> bool:
    """True se il blocco è preso, False se il disco non permette i blocchi."""
    scadenza = time.monotonic() + attesa
    while True:
        try:
            _prova(f)
            return True
        except OSError as errore:
            if errore.errno not in _OCCUPATO:
                return False
            if time.monotonic() >= scadenza:
                raise QuadernoOccupato(
                    f"il quaderno è occupato da un altro passaggio da più di {attesa:g} secondi: non ho "
                    "scritto niente. Riprova tra poco; se succede sempre, controlla che non ci sia un "
                    "programma Hypomnema fermo a metà."
                ) from errore
            time.sleep(PAUSA)


@contextmanager
def blocco(cartella_quaderno: Path, crea: bool, attesa: float | None = None):
    """Tiene il quaderno per un passaggio. ``crea``: crea il file del blocco se manca (chi scrive)."""
    attesa = ATTESA_BLOCCO if attesa is None else attesa
    file = file_del_blocco(cartella_quaderno)
    if not crea and not file.is_file():
        yield
        return
    if crea:
        cartella_quaderno.mkdir(parents=True, exist_ok=True)
    # Modo "a": se il file c'è non lo tocca, se manca lo crea vuoto. Non ci si scrive mai.
    try:
        f = open(file, "a+b")
    except OSError:
        if crea:
            raise
        # Chi legge soltanto, in una cartella dove non si può aprire il file, legge senza blocco.
        yield
        return
    try:
        try:
            preso = _prendi(f, attesa)
        except QuadernoOccupato:
            if crea:
                raise
            preso = False  # chi legge soltanto non si ferma: legge senza blocco
        try:
            yield
        finally:
            if preso:
                _lascia(f)
    finally:
        f.close()
