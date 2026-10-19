"""Le prove di Hypomnema.

Dalla 0.7.0 il fuso orario viene dal sistema operativo (``hypomnema.fuso_del_sistema``). Perché le prove
diano lo stesso risultato su ogni computer, qui il sistema operativo di prova è sempre una macchina in
UTC, come la chat e il cloud: sul computer dell'utente (per esempio Windows con «W. Europe Standard
Time») le prove altrimenti scriverebbero il file del fuso nei quaderni di prova. Le prove del computer
dell'utente sostituiscono a loro volta ``leggi_sistema``.
"""

from hypomnema import fuso_del_sistema

MACCHINA_IN_UTC = fuso_del_sistema.Sistema("Etc/UTC", "prova: macchina in UTC")
fuso_del_sistema.leggi_sistema = lambda: MACCHINA_IN_UTC
