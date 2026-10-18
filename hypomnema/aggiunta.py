"""Scrivere in fondo a un file con una sola scrittura in aggiunta, decisa dal sistema. Dalla 0.6.1.

Il registro, i file dei testimoni e quelli dell'archivio si allungano soltanto. Quando due programmi
scrivono sullo stesso quaderno da due macchine diverse (Claude Code su Windows e la chat collegata al
computer su Linux) il blocco del quaderno non passa da una macchina all'altra: resta la scrittura in
aggiunta, che deve essere una sola operazione, così il sistema mette ogni riga in fondo al file e due
righe non si sovrappongono mai.

- Su Linux e macOS: ``os.open`` con ``O_APPEND`` e una sola ``os.write``.
- Su Windows: Python porterebbe il file alla fine e poi scriverebbe, in due tempi; qui invece il file
  si apre con il solo permesso di aggiungere (``FILE_APPEND_DATA``), e allora è Windows stesso a
  scrivere ogni volta in fondo, in un'operazione sola.

Il testo è sempre UTF-8, con gli a capo così come sono (``\\n``): stessi byte da ogni sistema.
"""

import os
from pathlib import Path

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _kernel32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                                      wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    _kernel32.CreateFileW.restype = wintypes.HANDLE
    _kernel32.WriteFile.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.DWORD,
                                    ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
    _kernel32.WriteFile.restype = wintypes.BOOL
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL

    _FILE_APPEND_DATA = 0x0004
    _CONDIVISO = 0x1 | 0x2 | 0x4  # altri possono leggere, scrivere e rinominare intanto
    _OPEN_ALWAYS = 4  # se il file manca lo crea
    _FILE_ATTRIBUTE_NORMAL = 0x80
    _NON_VALIDO = wintypes.HANDLE(-1).value

    def _aggiungi(file: Path, dati: bytes) -> None:
        maniglia = _kernel32.CreateFileW(str(file), _FILE_APPEND_DATA, _CONDIVISO, None, _OPEN_ALWAYS,
                                         _FILE_ATTRIBUTE_NORMAL, None)
        if maniglia == _NON_VALIDO or maniglia is None:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            scritti = wintypes.DWORD(0)
            if not _kernel32.WriteFile(maniglia, dati, len(dati), ctypes.byref(scritti), None):
                raise ctypes.WinError(ctypes.get_last_error())
            if scritti.value != len(dati):
                raise OSError(f"scrittura in aggiunta incompleta su «{file}»")
        finally:
            _kernel32.CloseHandle(maniglia)
else:
    def _aggiungi(file: Path, dati: bytes) -> None:
        descrittore = os.open(file, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            if os.write(descrittore, dati) != len(dati):
                raise OSError(f"scrittura in aggiunta incompleta su «{file}»")
        finally:
            os.close(descrittore)


def aggiungi(file: Path, testo: str) -> None:
    """Aggiunge il testo in fondo al file (creandolo se manca), con una sola scrittura."""
    _aggiungi(Path(file), testo.encode("utf-8"))
