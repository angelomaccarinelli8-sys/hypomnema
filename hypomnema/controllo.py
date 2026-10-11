"""Il confronto tra note e registro: ogni nota ha la sua riga ACCETTATA e viceversa. Solo lettura.

Serve a inizio sessione, per accorgersi di un salvataggio rimasto a metà (per esempio una chat
chiusa tra la scrittura del registro e quella della nota) o di un file toccato a mano. Segnala
soltanto: non ripara niente, perché il registro si allunga soltanto e la decisione è dell'utente.
"""

from dataclasses import dataclass

from hypomnema import archivio
from hypomnema.configurazione import Configurazione
from hypomnema.quaderno import NOME_FILE_NOTA
from hypomnema.registro import INTESTAZIONE, RIGA_ACCETTATA, RIGA_RIFIUTATA


@dataclass(frozen=True)
class Esito:
    note: int  # quante note ci sono nel quaderno
    senza_riga: list[str]  # note senza riga ACCETTATA nel registro
    senza_nota: list[str]  # righe ACCETTATA del registro senza la nota
    senza_intestazione: bool  # il registro c'è ma non comincia con l'intestazione
    righe_estranee: list[tuple[int, str]]  # (numero di riga, testo) che non sono dello sportello
    senza_a_capo_finale: bool  # il registro c'è ma non finisce con un a capo
    # Nei file dell'archivio della chat: (nome del file, riga) rovinate e (nome, riga, riga già vista) doppioni.
    archivio_rovinate: tuple[tuple[str, int], ...] = ()
    archivio_doppioni: tuple[tuple[str, int, int], ...] = ()

    @property
    def in_ordine(self) -> bool:
        return not (self.senza_riga or self.senza_nota or self.senza_intestazione
                    or self.righe_estranee or self.senza_a_capo_finale
                    or self.archivio_rovinate or self.archivio_doppioni)


def controlla(config: Configurazione) -> Esito:
    note = set()
    if config.cartella_note.is_dir():
        for file in config.cartella_note.iterdir():
            corrispondenza = NOME_FILE_NOTA.match(file.name)
            if corrispondenza and file.is_file():
                note.add(corrispondenza.group(1))

    accettate = set()
    senza_intestazione = senza_a_capo_finale = False
    righe_estranee: list[tuple[int, str]] = []
    if config.file_registro.is_file():
        testo = config.file_registro.read_bytes().decode("utf-8", errors="replace")
        senza_a_capo_finale = not testo.endswith("\n")
        righe = testo.split("\n")
        if not senza_a_capo_finale:
            righe = righe[:-1]  # dopo l'ultimo a capo non c'è una riga
        # Le righe dopo l'intestazione; se l'intestazione manca, si guardano tutte.
        primo = 1
        if testo.startswith(INTESTAZIONE):
            primo = INTESTAZIONE.count("\n") + 1
        else:
            senza_intestazione = True
        for numero, riga in enumerate(righe[primo - 1:], start=primo):
            corrispondenza = RIGA_ACCETTATA.fullmatch(riga)
            if corrispondenza:
                accettate.add(corrispondenza.group(1))
            elif not RIGA_RIFIUTATA.fullmatch(riga):
                righe_estranee.append((numero, riga))

    rovinate: list[tuple[str, int]] = []
    doppioni: list[tuple[str, int, int]] = []
    for file in (config.file_archivio, config.file_diario_chat):
        if file is None:
            continue
        coppie, righe_rovinate = archivio.doppioni_e_righe_rovinate(file)
        rovinate += [(file.name, n) for n in righe_rovinate]
        doppioni += [(file.name, n, m) for n, m in coppie]

    def in_ordine(numeri: set[str]) -> list[str]:
        return sorted(numeri, key=lambda n: (int(n), n))

    return Esito(
        note=len(note),
        senza_riga=in_ordine(note - accettate),
        senza_nota=in_ordine(accettate - note),
        senza_intestazione=senza_intestazione,
        righe_estranee=righe_estranee,
        senza_a_capo_finale=senza_a_capo_finale,
        archivio_rovinate=tuple(rovinate),
        archivio_doppioni=tuple(doppioni),
    )
