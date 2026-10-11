"""Il confronto tra note e registro: ogni nota ha la sua riga ACCETTATA e viceversa. Solo lettura.

Serve a inizio sessione, per accorgersi di un salvataggio rimasto a metà (per esempio una chat
chiusa tra la scrittura del registro e quella della nota) o di un file toccato a mano. Segnala
soltanto: non ripara niente, perché il registro si allunga soltanto e la decisione è dell'utente.
"""

from dataclasses import dataclass

from hypomnema.configurazione import Configurazione
from hypomnema.quaderno import NOME_FILE_NOTA
from hypomnema.registro import RIGA_ACCETTATA


@dataclass(frozen=True)
class Esito:
    note: int  # quante note ci sono nel quaderno
    senza_riga: list[str]  # note senza riga ACCETTATA nel registro
    senza_nota: list[str]  # righe ACCETTATA del registro senza la nota


def controlla(config: Configurazione) -> Esito:
    note = set()
    if config.cartella_note.is_dir():
        for file in config.cartella_note.iterdir():
            corrispondenza = NOME_FILE_NOTA.match(file.name)
            if corrispondenza and file.is_file():
                note.add(corrispondenza.group(1))

    accettate = set()
    if config.file_registro.is_file():
        testo = config.file_registro.read_bytes().decode("utf-8", errors="replace")
        for riga in testo.split("\n"):
            corrispondenza = RIGA_ACCETTATA.fullmatch(riga)
            if corrispondenza:
                accettate.add(corrispondenza.group(1))

    def in_ordine(numeri: set[str]) -> list[str]:
        return sorted(numeri, key=lambda n: (int(n), n))

    return Esito(
        note=len(note),
        senza_riga=in_ordine(note - accettate),
        senza_nota=in_ordine(accettate - note),
    )
