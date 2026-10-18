"""Riga di comando di Hypomnema.

    python -m hypomnema proponi proposta.json   # passa una nota allo sportello
    python -m hypomnema proponi -               # legge la nota dall'ingresso standard
    python -m hypomnema cerca parola            # cerca le note che contengono la parola (con le note collegate)
    python -m hypomnema promemoria              # le note con «riprendere_il» arrivato o passato
    python -m hypomnema recap                   # dove eravamo rimasti: promemoria, discorsi aperti, decisioni, diario
    python -m hypomnema revisione               # che cosa conviene guardare nel quaderno (solo lettura)
    python -m hypomnema testimone               # registra un messaggio (lo lancia Claude Code)
    python -m hypomnema stato                   # dice se il testimone è acceso e l'ultimo messaggio
    python -m hypomnema impostazioni-claude     # le regole che l'avviabile passa a Claude Code
    python -m hypomnema istantanea > prima.json # chat: fotografa il quaderno prima di una proposta
    python -m hypomnema cambiati prima.json     # chat: i file da riportare sul computer dell'utente
    python -m hypomnema controlla               # note e registro corrispondono? righe estranee?
    python -m hypomnema confronta FILE1 FILE2   # due file identici byte per byte? (non serve configurazione)
    python -m hypomnema risposte                # registra una risposta di Claude (lo lancia Claude Code)
    python -m hypomnema impronta FILE           # l'impronta di un file, come per i blocchi di codice omessi
    python -m hypomnema diario PAROLA           # cerca nei messaggi e nelle risposte (--intorno: con i vicini)
    python -m hypomnema avvio                   # inizio sessione (lo lancia Claude Code): prima volta e avvisi
    python -m hypomnema archivio copia.json     # chat: aggiunge la copia dell'archivio della chat (solo aggiunta)
    python -m hypomnema protezione              # ferma gli strumenti di Claude sul quaderno (lo lancia Claude Code)

Anche il comando "risposte", come "testimone", non esce mai con 2: per Claude Code, alla fine
di una risposta, il codice 2 vorrebbe dire costringere Claude a continuare.

Codici di uscita: 0 = tutto bene, 1 = nota rifiutata, 2 = errore di uso o di configurazione.
Il comando "testimone" non esce mai con 2: per Claude Code vorrebbe dire bloccare il
messaggio dell'utente. In caso di errore esce con 1 e lo scrive sull'uscita degli errori.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import TextIO

from hypomnema import (
    __version__, archivio, avvio, blocco, cambiamenti, cercatore, configurazione, controllo, diario, promemoria, registro,
    revisione, risposte, sportello, testimone,
)
from hypomnema.nota import NotaIlleggibile, base_di
from hypomnema.versioni import LEGENDA, Quaderno, Storia

ORIGINE_DIRETTA = "(ingresso diretto)"

# Dalla versione 0.5.0 i comandi hanno il nome inglese; quello italiano vale per sempre.
INGLESE = {
    "proponi": "propose", "cerca": "search", "promemoria": "reminders", "testimone": "witness",
    "stato": "status", "istantanea": "snapshot", "cambiati": "changed", "controlla": "check",
    "confronta": "compare", "risposte": "replies", "impronta": "fingerprint", "diario": "diary",
    "archivio": "archive", "avvio": "start", "protezione": "protect", "impostazioni-claude": "claude-settings",
    "revisione": "review",
}
# Gli agganci di Claude Code: non devono mai uscire con il codice 2 per un comando scritto male.
AGGANCI = ("witness", "replies", "start", "protect")
# I comandi che leggono il quaderno: aspettano che un passaggio dello sportello finisca (vedi blocco).
LETTURA = ("search", "reminders", "recap", "review", "check", "snapshot", "changed", "status", "diary")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hypomnema",
        description="Hypomnema: Claude propone le note, i programmi decidono se entrano.",
    )
    parser.add_argument("--version", action="version", version=f"hypomnema {__version__}")
    parser.add_argument(
        "--config",
        help="percorso del file hypomnema.toml (altrimenti HYPOMNEMA_CONFIG o la cartella corrente)",
    )
    comandi = parser.add_subparsers(dest="comando", required=True, metavar="comando")

    proponi = comandi.add_parser("propose", aliases=["proponi"], help="passa una nota allo sportello")
    proponi.add_argument("file", help="file JSON con la nota proposta, oppure - per leggerla dall'ingresso standard")

    cerca = comandi.add_parser("search", aliases=["cerca"], help="cerca le note che contengono una parola")
    cerca.add_argument("parola", help="la parola (o le parole) da cercare, così come sono")
    cerca.add_argument("--all", "--tutte", dest="tutte", action="store_true",
                       help="mostra anche le note chiuse, con la loro storia")
    comandi.add_parser(
        "reminders", aliases=["promemoria"], help="elenca le note con «riprendere_il» arrivato o già passato, dal più vecchio"
    )
    comandi.add_parser(
        "recap", help="dove eravamo rimasti: promemoria scaduti, discorsi aperti, ultime decisioni, ultimo diario"
    )
    comandi.add_parser(
        "review", aliases=["revisione"],
        help="che cosa conviene guardare nel quaderno: rami, note ferme, promemoria scaduti, note nominate (solo lettura)",
    )

    registra = comandi.add_parser(
        "witness", aliases=["testimone"], help="registra un messaggio dell'utente (lo lancia Claude Code a ogni messaggio)"
    )
    registra.add_argument(
        "file", nargs="?", default="-",
        help="file JSON con il messaggio, come lo manda Claude Code (di base: ingresso standard)",
    )

    comandi.add_parser(
        "status", aliases=["stato"], help="dice se il testimone è acceso, dov'è il quaderno e l'ultimo messaggio registrato"
    )
    comandi.add_parser(
        "snapshot", aliases=["istantanea"], help="scrive dimensione e impronta di ogni file del quaderno (prima di una proposta)"
    )
    cambiati = comandi.add_parser(
        "changed", aliases=["cambiati"], help="elenca i file del quaderno creati o allungati rispetto a un'istantanea"
    )
    cambiati.add_argument("file", help="il file dell'istantanea fatta prima della proposta")
    comandi.add_parser(
        "check", aliases=["controlla"],
        help="controlla che note e registro corrispondano e che il registro abbia solo righe dello sportello",
    )
    confronta = comandi.add_parser("compare", aliases=["confronta"], help="dice se due file sono identici, byte per byte")
    confronta.add_argument("file1")
    confronta.add_argument("file2")

    registra_risposta = comandi.add_parser(
        "replies", aliases=["risposte"], help="registra una risposta di Claude (lo lancia Claude Code alla fine di ogni risposta)"
    )
    registra_risposta.add_argument(
        "file", nargs="?", default="-",
        help="file JSON con la risposta, come lo manda Claude Code (di base: ingresso standard)",
    )
    calcola_impronta = comandi.add_parser(
        "fingerprint", aliases=["impronta"], help="scrive l'impronta di un file (o di un testo, con -), come per i blocchi di codice omessi"
    )
    calcola_impronta.add_argument("file", help="il file, oppure - per leggere il testo dall'ingresso standard")
    cerca_diario = comandi.add_parser(
        "diary", aliases=["diario"], help="cerca una parola nei messaggi dell'utente e nelle risposte di Claude"
    )
    cerca_diario.add_argument("parola", nargs="?", help="la parola (o le parole) da cercare, così come sono")
    cerca_diario.add_argument("--last", "--ultimi", dest="ultimi", type=int, metavar="N",
                              help="senza parola: mostra gli ultimi N messaggi del diario")
    cerca_diario.add_argument(
        "--around", "--intorno", dest="intorno", action="store_true",
        help="mostra anche il messaggio subito prima e subito dopo"
    )
    copia_archivio = comandi.add_parser(
        "archive", aliases=["archivio"], help="chat: aggiunge ai file del quaderno la copia dei messaggi presa dall'archivio della chat"
    )
    copia_archivio.add_argument("file", help="file JSON con l'indirizzo della chat e i messaggi")
    comandi.add_parser(
        "start", aliases=["avvio"], help="inizio sessione (lo lancia Claude Code): crea la configurazione la prima volta e avvisa"
    )
    comandi.add_parser(
        "protect", aliases=["protezione"], help="ferma gli strumenti di Claude sui file del quaderno (lo lancia Claude Code)"
    )
    comandi.add_parser(
        "claude-settings", aliases=["impostazioni-claude"],
        help="scrive le regole che vietano a Claude di modificare quaderno e configurazione (per l'avviabile)",
    )
    return parser


def _descrivi(storia: Storia, quaderno: Quaderno, segno: str, conferme, titolo: str = "") -> list[str]:
    """L'ultima versione di una nota per intero, poi la sua storia."""
    ultima = storia.ultima
    nota = ultima.contenuto
    righe = [
        f"--- Nota {ultima.etichetta(segno)}{titolo} ---",
        f"data: {nota.data}",
        f"fonte: {nota.fonte}",
        f"autore: {nota.autore}",
        f"tipo: {nota.tipo}",
        f"natura: {nota.natura}",
    ]
    if ultima.chiusa:
        righe.append(f"stato: chiusa ({ultima.data})")
    if nota.priorita is not None:
        righe.append(f"priorità: {nota.priorita}")
    if nota.conferma_di is not None:
        righe.append(f"conferma di: {cercatore.rimando(quaderno, nota.conferma_di, segno)}")
    if nota.corregge is not None:
        righe.append(f"corregge: nota {nota.corregge}")
    if nota.done is not None:
        righe.append("chiude: " + ", ".join(f"nota {n}" for n in nota.done))
    if nota.riprendere_il is not None:
        righe.append(f"riprendere il: {nota.riprendere_il}")
    if conferme.get(storia.base):
        righe.append("confermata da: " + ", ".join(f"nota {s.ultima.etichetta(segno)}" for s in conferme[storia.base]))
    if nota.citazione is not None:
        righe.append(f"citazione: {nota.citazione}")
    if nota.da_risposta is not None:
        righe.append(f"da una risposta di Claude: {nota.da_risposta}")
    if nota.verifica is not None:
        righe.append(f"verifica: {nota.verifica}")
    righe.append("testo:")
    righe += _rientrato(nota.testo)
    if nota.contesto is not None:
        righe.append("contesto scritto da Claude:")
        righe += _rientrato(nota.contesto)
    if len(storia.versioni) > 1:
        righe.append("storia (dalla più vecchia):")
        righe += [f"  {riga}" for riga in cercatore.righe_della_storia(storia, segno, breve=False)]
    return righe


def _proponi(argomenti, config, adesso: datetime, uscita: TextIO) -> int:
    if argomenti.file == "-":
        dati = sys.stdin.buffer.read()
        origine = ORIGINE_DIRETTA
    else:
        file = Path(argomenti.file)
        if not file.is_file():
            print(f"ERRORE: non trovo il file «{file}».", file=uscita)
            return 2
        dati = file.read_bytes()
        origine = file.name
    esito = sportello.ricevi(dati, origine, config, adesso)

    for id_nota, percorso in esito.scritte:
        relativo = percorso.relative_to(config.cartella_quaderno).as_posix()
        cosa = f"la versione {id_nota} della nota {base_di(id_nota)}" if "." in id_nota else f"la nota {id_nota}"
        print(f"ACCETTATA: {cosa} è stata salvata nel quaderno ({relativo}).", file=uscita)
    if esito.accettata:
        print("Il passaggio è annotato nel registro.", file=uscita)
        return 0
    print("RIFIUTATA: la nota non è stata salvata." if not esito.scritte
          else "RIFIUTATA: il resto del cambiamento non è stato salvato.", file=uscita)
    print("Motivi:", file=uscita)
    for motivo in esito.motivi:
        # Come nel registro: un motivo sta su una riga, così nessuna riga falsa
        # (per esempio un finto "ACCETTATA") può comparire nella risposta che legge Claude.
        print(f"- {registro.su_una_riga(motivo)}", file=uscita)
    print("Il passaggio è annotato nel registro.", file=uscita)
    return 1


def _mostra_con_collegate(storia: Storia, quaderno: Quaderno, segno: str, conferme, gia_mostrate: set[str],
                          uscita: TextIO) -> None:
    """La nota con la sua storia, e subito sotto, rientrate, le note che la confermano."""
    print("", file=uscita)
    for riga in _descrivi(storia, quaderno, segno, conferme):
        print(riga, file=uscita)
    gia_mostrate.add(storia.base)
    for collegata in conferme.get(storia.base, []):
        print("", file=uscita)
        legame = f"conferma la nota {storia.base}"
        if collegata.base in gia_mostrate:
            print(f"    (nota {collegata.ultima.etichetta(segno)}, che {legame}: già mostrata sopra)", file=uscita)
            continue
        for riga in _descrivi(collegata, quaderno, segno, conferme, f" ({legame})"):
            print(f"    {riga}" if riga else "", file=uscita)
        gia_mostrate.add(collegata.base)


def _cerca(argomenti, config, uscita: TextIO) -> int:
    parola = argomenti.parola.strip()
    if not parola:
        print("ERRORE: serve una parola da cercare.", file=uscita)
        return 2
    archivio_note = cercatore.leggi(config)
    trovate = cercatore.cerca(archivio_note, parola, tutte=argomenti.tutte)
    nascoste = 0 if argomenti.tutte else len(cercatore.cerca(archivio_note, parola, tutte=True)) - len(trovate)
    if not trovate:
        aperta = " aperta" if nascoste else ""
        print(f"Nessuna nota{aperta} contiene «{parola}».", file=uscita)
    elif len(trovate) == 1:
        print(f"Trovata 1 nota con «{parola}».", file=uscita)
    else:
        print(f"Trovate {len(trovate)} note con «{parola}» (dalla più recente).", file=uscita)
    if nascoste:
        quante = ("1 nota chiusa non mostrata: aggiungi --all per vederla" if nascoste == 1
                  else f"{nascoste} note chiuse non mostrate: aggiungi --all per vederle")
        print(f"({quante}.)", file=uscita)
    conferme = cercatore.confermata_da(archivio_note)
    gia_mostrate: set[str] = set()
    for storia in trovate:
        _mostra_con_collegate(storia, archivio_note, config.segno_chiusa, conferme, gia_mostrate, uscita)
    if trovate:
        print("", file=uscita)
        print(f"Legenda: {LEGENDA.format(segno=config.segno_chiusa)}", file=uscita)
    return 0


def _promemoria(config, adesso: datetime, uscita: TextIO) -> int:
    """Solo lettura: i promemoria scaduti, dal più vecchio."""
    archivio_note = cercatore.leggi(config)
    oggi = adesso.date()
    scaduti = promemoria.scaduti(archivio_note, oggi)
    in_arrivo = promemoria.in_arrivo(archivio_note, oggi)
    if not scaduti:
        print(f"Nessun promemoria scaduto al {oggi.isoformat()}.", file=uscita)
    else:
        quanti = "1 promemoria scaduto" if len(scaduti) == 1 else f"{len(scaduti)} promemoria scaduti"
        print(f"{quanti} al {oggi.isoformat()} (dal più vecchio).", file=uscita)
        conferme = cercatore.confermata_da(archivio_note)
        gia_mostrate: set[str] = set()
        for voce in scaduti:
            print("", file=uscita)
            print(f"=== Da riprendere il {voce.giorno} ===", file=uscita)
            _mostra_con_collegate(voce.storia, archivio_note, config.segno_chiusa, conferme, gia_mostrate, uscita)
    if in_arrivo:
        altri = "1 promemoria ha" if in_arrivo == 1 else f"{in_arrivo} promemoria hanno"
        print("", file=uscita)
        print(f"({altri} una data non ancora arrivata.)", file=uscita)
    return 0


def _prima_riga(testo: str | None, dicitura: str | None = None) -> str:
    if testo is None:
        return f"({dicitura})"
    return cercatore.prima_riga(testo)


ETICHETTA_PRIORITA = {"high": "[alta] ", "normal": "", "low": "[bassa] "}


def _riga_recap(storia: Storia, inizio: str, quaderno: Quaderno, segno: str, conferme) -> list[str]:
    ultima = storia.ultima
    priorita = ETICHETTA_PRIORITA[cercatore.priorita_in_vigore(storia)]
    righe = [f"- [{ultima.etichetta(segno)}] {priorita}{inizio}: {_prima_riga(ultima.contenuto.testo)}"]
    # La storia dalla versione più recente alla più vecchia, come il quaderno.
    for versione in reversed(storia.versioni[1:]):
        righe.append(f"    ↳ {versione.etichetta(segno)} {versione.data} · {versione.autore}: "
                     f"{cercatore.descrivi_cambio(storia, versione, breve=True)}")
    if ultima.contenuto.conferma_di is not None:
        righe.append(f"    ↳ conferma la {cercatore.rimando(quaderno, ultima.contenuto.conferma_di, segno)}")
    for collegata in conferme.get(storia.base, []):
        chiusa = " (chiusa)" if collegata.chiusa else ""
        righe.append(f"    ↳ confermata dalla nota {collegata.ultima.etichetta(segno)}{chiusa}: "
                     f"{_prima_riga(collegata.ultima.contenuto.testo)}")
    return righe


def _recap(config, adesso: datetime, uscita: TextIO) -> int:
    """Solo lettura, con regole fisse: dove eravamo rimasti, in poche righe.

    In ogni blocco vengono prima le note a priorità alta, poi normale, poi bassa; a parità di
    priorità, i promemoria dal più vecchio e il resto dal più recente (per numero di nota). Vale
    l'ultima versione di ogni nota, per quello che è adesso: le chiuse non ci sono, tranne le decisioni
    (una questione chiusa come decisione compare tra le decisioni, con il suo ✓).
    """
    archivio_note = cercatore.leggi(config)
    conferme = cercatore.confermata_da(archivio_note)
    segno = config.segno_chiusa
    oggi = adesso.date()

    def per_priorita(elenco: list[Storia]) -> list[Storia]:
        # sorted è stabile: a parità di priorità resta l'ordine di partenza.
        return sorted(elenco, key=lambda s: cercatore.ORDINE_PRIORITA[cercatore.priorita_in_vigore(s)])

    righe = [f"Dove eravamo rimasti (recap del {oggi.isoformat()}).", ""]

    scaduti = promemoria.scaduti(archivio_note, oggi)
    scaduti = sorted(scaduti, key=lambda voce: cercatore.ORDINE_PRIORITA[cercatore.priorita_in_vigore(voce.storia)])
    if scaduti:
        righe.append(f"Promemoria scaduti: {len(scaduti)} (prima la priorità alta, poi dal più vecchio)")
        for voce in scaduti:
            righe += _riga_recap(voce.storia, f"da riprendere il {voce.giorno}", archivio_note, segno, conferme)
    else:
        righe.append("Promemoria scaduti: nessuno.")

    for titolo, natura, quanti, nessuno, uno_in_piu, tanti_in_piu in (
        ("Discorsi aperti", "open", config.recap_discorsi_aperti, "nessuno",
         "1 discorso aperto più vecchio non mostrato", "{} discorsi aperti più vecchi non mostrati"),
        ("Cose da fare", "todo", config.recap_todo, "nessuna",
         "1 cosa da fare più vecchia non mostrata", "{} cose da fare più vecchie non mostrate"),
        ("Ultime decisioni", "decision", config.recap_decisioni, "nessuna",
         "1 decisione più vecchia non mostrata", "{} decisioni più vecchie non mostrate"),
    ):
        scelte = per_priorita(cercatore.dal_piu_recente(
            [s for s in archivio_note.elenco() if s.ultima.contenuto.natura == natura and not s.nascosta]))
        righe.append("")
        if not scelte:
            righe.append(f"{titolo}: {nessuno}.")
            continue
        mostrate = scelte[:quanti]
        righe.append(f"{titolo}: {len(mostrate)} di {len(scelte)} (prima la priorità alta, poi dal più recente)")
        for storia in mostrate:
            righe += _riga_recap(storia, storia.ultima.data, archivio_note, segno, conferme)
        resto = len(scelte) - len(mostrate)
        if resto:
            righe.append(f"({uno_in_piu if resto == 1 else tanti_in_piu.format(resto)})")

    voci = diario.voci(config)
    righe.append("")
    if not voci:
        righe.append("Ultime voci del diario: nessuna.")
    else:
        mostrate = voci[-config.recap_voci_diario:]
        righe.append(f"Ultime voci del diario: {len(mostrate)} di {len(voci)} (la conversazione registrata, non le note)")
        for voce in mostrate:
            righe.append(f"- {voce.quando} · {voce.chi}: {_prima_riga(voce.testo, voce.dicitura)}")
        righe.append(f"(per leggerle intere: diary --last {len(mostrate)})")
    righe += ["", f"Legenda: {LEGENDA.format(segno=segno)}"]

    for riga in righe:
        print(riga, file=uscita)
    return 0


def _revisione(config, adesso: datetime, uscita: TextIO) -> int:
    """Solo lettura: che cosa conviene guardare. 0 = niente, 1 = qualcosa da guardare."""
    archivio_note = cercatore.leggi(config)
    oggi = adesso.date()
    segnalazioni = revisione.rivedi(archivio_note, oggi, config.giorni_revisione, config.segno_chiusa)
    if not segnalazioni:
        print(f"Revisione del quaderno ({oggi.isoformat()}): niente da segnalare.", file=uscita)
        return 0
    quante = "1 cosa da guardare" if len(segnalazioni) == 1 else f"{len(segnalazioni)} cose da guardare"
    print(f"Revisione del quaderno ({oggi.isoformat()}): {quante}. Non è stato cambiato niente.", file=uscita)
    for voce in segnalazioni:
        print(f"- {voce.storia.ultima.etichetta(config.segno_chiusa)}: {voce.testo}", file=uscita)
    print("", file=uscita)
    print(f"Legenda: {LEGENDA.format(segno=config.segno_chiusa)}", file=uscita)
    return 1


def _rientrato(testo: str) -> list[str]:
    return [f"  {riga}" if riga else "" for riga in testo.split("\n")]


def _stato(argomenti, config, uscita: TextIO) -> int:
    """Solo lettura: non crea e non modifica niente."""
    righe = [
        f"Configurazione: {configurazione.trova(argomenti.config).resolve()}",
        f"Quaderno: {config.cartella_quaderno}",
    ]
    pausa = testimone.in_pausa(testimone.leggi_messaggi(config)) if config.testimone_attivo else None
    if pausa is not None:
        righe.append(
            f"Testimone: IN PAUSA dal {pausa.quando} (comando /hypomnema:pause): i messaggi e le risposte "
            "non vengono registrati e le note con autore «user» saranno marcate «author not verified "
            "(witnesses paused)». Per riprendere: /hypomnema:resume (o /hypomnema:riprendi)."
        )
    elif config.testimone_attivo:
        righe.append("Testimone: ACCESO (registra le parole esatte di ogni messaggio dell'utente).")
    elif config.in_chat:
        righe.append(
            "Testimone: NON C'È (configurazione per la chat di Claude): i messaggi arrivano solo a Claude "
            "e le note con autore «user» saranno marcate «author not verified (chat, no witness)»."
        )
    else:
        righe.append(
            "Testimone: SPENTO (nella configurazione attivo = false): i messaggi non vengono registrati "
            "e le note con autore «user» saranno marcate «author not verified (witness off)»."
        )
    righe.append(f"File del testimone: {config.file_testimone}")
    messaggi = testimone.leggi_messaggi(config)
    righe.append(f"Messaggi registrati: {len(messaggi)}")
    if not messaggi:
        righe.append("Ultimo messaggio registrato: nessuno.")
    elif messaggi[-1].testo is None:
        righe.append(f"Ultimo messaggio registrato: {messaggi[-1].quando} ({messaggi[-1].privato or testimone.DICITURA_PRIVATO}).")
    else:
        righe.append(f"Ultimo messaggio registrato: {messaggi[-1].quando}")
        righe.append("Testo dell'ultimo messaggio:")
        righe += _rientrato(messaggi[-1].testo)
    if config.sezione_risposte:
        righe += _stato_risposte(config)
    if config.file_archivio is not None:
        righe += _stato_archivio(config)
    for riga in righe:
        print(riga, file=uscita)
    return 0


def _stato_archivio(config) -> list[str]:
    messaggi, risposte_copiate = archivio.leggi_messaggi(config), archivio.leggi_risposte(config)
    righe = [
        f"Archivio della chat: {len(messaggi)} messaggi dell'utente e {len(risposte_copiate)} risposte di Claude "
        f"copiati da Claude (da copiare ogni {config.copia_ogni} scambi e alla chiusura).",
        f"File dell'archivio: {config.file_archivio}",
        f"File del diario della chat: {config.file_diario_chat}",
    ]
    tutti = sorted(messaggi + risposte_copiate, key=lambda m: datetime.fromisoformat(m.quando))
    if tutti:
        righe.append(f"Ultimo copiato: {tutti[-1].quando} (chat {tutti[-1].chat})")
    else:
        righe.append("Ultimo copiato: nessuno.")
    return righe


def _archivio(argomenti, config, uscita: TextIO) -> int:
    file = Path(argomenti.file)
    if not file.is_file():
        print(f"ERRORE: non trovo il file «{file}».", file=uscita)
        return 2
    esito = archivio.copia(config, file.read_bytes())

    def quanti(n: int, uno: str, tanti: str) -> str:
        return f"{n} {uno if n == 1 else tanti}"

    print(f"Copiati dall'archivio della chat: {quanti(esito.utente, 'messaggio', 'messaggi')} dell'utente, "
          f"{quanti(esito.claude, 'risposta', 'risposte')} di Claude.", file=uscita)
    if esito.privati or esito.risposte_private:
        print(f"Privati, solo data e ora: {quanti(esito.privati, 'messaggio', 'messaggi')} dell'utente, "
              f"{quanti(esito.risposte_private, 'risposta', 'risposte')}.", file=uscita)
    if esito.avvisi_tolti:
        print(f"Avvisi tecnici <system-reminder> tolti dai messaggi dell'utente: {esito.avvisi_tolti}.", file=uscita)
    if esito.gia_presenti:
        print(f"Già presenti (stessa chat, stesso turno), non duplicati: {esito.gia_presenti}.", file=uscita)
    if esito.diversi:
        if esito.diversi == 1:
            quali, toccati = "1 già presente ha", "non l'ho toccato"
        else:
            quali, toccati = f"{esito.diversi} già presenti hanno", "non li ho toccati"
        print(f"ATTENZIONE: {quali} un testo diverso da quello arrivato ora: {toccati}.", file=uscita)
    return 0


def _stato_risposte(config) -> list[str]:
    if config.risposte_attive:
        codice = "con i blocchi di codice omessi" if config.ometti_codice else "con i blocchi di codice interi"
        righe = [f"Testimone delle risposte: ACCESO (registra le risposte di Claude, {codice})."]
    else:
        righe = ["Testimone delle risposte: SPENTO (nella sezione [risposte] attivo = false)."]
    registrate = risposte.leggi_risposte(config)
    righe += [f"File delle risposte: {config.file_risposte}", f"Risposte registrate: {len(registrate)}"]
    if not registrate:
        righe.append("Ultima risposta registrata: nessuna.")
    elif registrate[-1].testo is None:
        righe.append(f"Ultima risposta registrata: {registrate[-1].quando} ({registrate[-1].privato}).")
    else:
        righe.append(f"Ultima risposta registrata: {registrate[-1].quando}")
    return righe


def _istantanea(config, uscita: TextIO) -> int:
    """Solo lettura: scrive l'istantanea sull'uscita (si salva con > prima.json)."""
    print(json.dumps(cambiamenti.istantanea(config), ensure_ascii=True, sort_keys=True), file=uscita)
    return 0


def _cambiati(argomenti, config, uscita: TextIO) -> int:
    """Solo lettura: elenca i file da riportare, o si rifiuta se è successo altro."""
    file = Path(argomenti.file)
    if not file.is_file():
        print(f"ERRORE: non trovo il file dell'istantanea «{file}».", file=uscita)
        return 2
    try:
        elenco = cambiamenti.cambiati(config, cambiamenti.leggi_istantanea(file.read_bytes()))
    except cambiamenti.ErroreCambiamenti as errore:
        print("ERRORE: il quaderno non è cambiato solo come fa lo sportello. "
              "Non riportare niente sul computer dell'utente.", file=uscita)
        for problema in errore.problemi:
            print(f"- {registro.su_una_riga(problema)}", file=uscita)
        return 2
    if not elenco:
        print("Nessun file del quaderno è cambiato: non c'è niente da riportare.", file=uscita)
        return 0
    print(f"File del quaderno da riportare sul computer dell'utente: {len(elenco)}", file=uscita)
    for cambiamento in elenco:
        print(f"- {registro.su_una_riga(cambiamento.percorso)} ({cambiamento.tipo})", file=uscita)
    return 0


def _controlla(config, uscita: TextIO) -> int:
    """Solo lettura: segnala, non ripara. 0 = in ordine, 1 = qualcosa non corrisponde."""
    esito = controllo.controlla(config)
    if esito.in_ordine:
        quante = "1 nota" if esito.note == 1 else f"{esito.note} note"
        if esito.versioni:
            quante += " e 1 versione" if esito.versioni == 1 else f" e {esito.versioni} versioni"
        if esito.note + esito.versioni == 0:
            print("Quaderno in ordine: nessuna nota.", file=uscita)
        elif esito.note + esito.versioni == 1:
            print(f"Quaderno in ordine: {quante}, con la sua riga ACCETTATA nel registro.", file=uscita)
        else:
            print(f"Quaderno in ordine: {quante}, tutte con la loro riga ACCETTATA nel registro.", file=uscita)
        return 0
    print("ATTENZIONE: note e registro non corrispondono.", file=uscita)
    if esito.senza_intestazione:
        print("- il registro non comincia con la sua intestazione.", file=uscita)
    for numero, riga in esito.righe_estranee:
        print(f"- registro, riga {numero}: «{registro.su_una_riga(riga)}» non è una riga dello sportello.",
              file=uscita)
    if esito.senza_a_capo_finale:
        print("- il registro non finisce con un a capo: lo sportello non scriverà finché non è sistemato.",
              file=uscita)
    for nome, numero in esito.archivio_rovinate:
        print(f"- {nome}, riga {numero}: non ha la forma di una riga dell'archivio della chat.", file=uscita)
    for nome, numero, prima in esito.archivio_doppioni:
        print(f"- {nome}, riga {numero}: stessa chat e stesso turno della riga {prima} (doppione).", file=uscita)
    for numero in esito.senza_riga:
        print(f"- nota {numero}: la nota c'è, ma nel registro manca la sua riga ACCETTATA.", file=uscita)
    for numero in esito.senza_nota:
        print(f"- nota {numero}: il registro dice ACCETTATA, ma la nota non c'è.", file=uscita)
    print("Non è stato riparato niente: decide l'utente.", file=uscita)
    return 1


def _confronta(argomenti, uscita: TextIO) -> int:
    """Solo lettura. 0 = identici, 1 = diversi, 2 = un file manca."""
    contenuti = []
    for nome in (argomenti.file1, argomenti.file2):
        file = Path(nome)
        if not file.is_file():
            print(f"ERRORE: non trovo il file «{file}».", file=uscita)
            return 2
        contenuti.append(file.read_bytes())
    primo, secondo = contenuti
    if primo == secondo:
        print(f"UGUALI: «{argomenti.file1}» e «{argomenti.file2}» sono identici byte per byte "
              f"({len(primo)} byte).", file=uscita)
        return 0
    posizione = next((i for i, (a, b) in enumerate(zip(primo, secondo)) if a != b), min(len(primo), len(secondo)))
    print(f"DIVERSI: «{argomenti.file1}» ({len(primo)} byte) e «{argomenti.file2}» ({len(secondo)} byte) "
          f"non sono uguali: la prima differenza è al byte {posizione + 1}.", file=uscita)
    return 1


def _impostazioni_claude(argomenti, config, uscita: TextIO) -> int:
    try:
        impostazioni = avvio.impostazioni_claude(config, configurazione.trova(argomenti.config))
    except avvio.ErroreAvvio as errore:
        print(f"ERRORE: {errore}", file=uscita)
        return 2
    # Solo caratteri ASCII: il testo passa intatto anche dalla riga di comando di Windows.
    print(json.dumps(impostazioni, ensure_ascii=True), file=uscita)
    return 0


def _avvio(argomenti, uscita: TextIO) -> int:
    """Aggancio SessionStart: avvisi all'utente (systemMessage) e a Claude. Esce sempre con 0."""
    file_config = configurazione.trova(argomenti.config)
    try:
        avvisi = avvio.prepara(file_config)
    except OSError as errore:
        avvisi = [f"Hypomnema: non riesco a preparare la configurazione «{file_config}»: {errore}"]
    if avvisi:
        testo = "\n".join(avvisi)
        print(json.dumps({
            "systemMessage": testo,
            "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": testo},
        }, ensure_ascii=False), file=uscita)
    return 0


def _protezione(argomenti, errori: TextIO) -> int:
    """Aggancio PreToolUse: 2 ferma lo strumento, 0 lo lascia passare."""
    try:
        dati = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
        ingresso = dati.get("tool_input") or {}
        percorso = ingresso.get("file_path") or ingresso.get("notebook_path")
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return 0
    if not isinstance(percorso, str) or not percorso:
        return 0
    if avvio.protetto(configurazione.trova(argomenti.config), percorso):
        print(f"Hypomnema: «{percorso}» fa parte del quaderno o della sua configurazione, e Claude non lo "
              "modifica mai con i suoi strumenti. Le note entrano solo dallo sportello (proponi).", file=errori)
        return 2
    return 0


def _quaderno_nel_programma(config, errori: TextIO, cosa: str) -> bool:
    if avvio.quaderno_nel_programma(config):
        print(f"ERRORE del testimone{cosa}: il quaderno «{config.cartella_quaderno}» è dentro la cartella del "
              "programma, che un aggiornamento sostituisce: non registro niente. Cambia «cartella» nella "
              "configurazione.", file=errori)
        return True
    return False


def _risposte(argomenti, adesso: datetime, errori: TextIO) -> int:
    # Come il testimone: niente a schermo e mai il codice 2 (costringerebbe Claude a continuare).
    try:
        config = configurazione.carica(argomenti.config)
        if config.risposte_attive and _quaderno_nel_programma(config, errori, " delle risposte"):
            return 1
        if argomenti.file == "-":
            dati = sys.stdin.buffer.read()
        else:
            dati = Path(argomenti.file).read_bytes()
        risposte.registra(config, adesso, dati)
    except (configurazione.ErroreConfigurazione, testimone.ErroreTestimone, OSError) as errore:
        print(f"ERRORE del testimone delle risposte: {errore} La risposta NON è stata registrata.", file=errori)
        return 1
    return 0


def _impronta(argomenti, uscita: TextIO) -> int:
    """Solo lettura, senza configurazione."""
    if argomenti.file == "-":
        dati, nome = sys.stdin.buffer.read(), "testo"
    else:
        file = Path(argomenti.file)
        if not file.is_file():
            print(f"ERRORE: non trovo il file «{file}».", file=uscita)
            return 2
        dati, nome = file.read_bytes(), f"«{file}»"
    print(f"Impronta di {nome}: {risposte.impronta(dati)} ({len(dati)} byte).", file=uscita)
    return 0


def _diario(argomenti, config, uscita: TextIO) -> int:
    """Solo lettura: i messaggi e le risposte che contengono la parola, in ordine di tempo."""
    parola = (argomenti.parola or "").strip()
    if not parola and argomenti.ultimi is None:
        print("ERRORE: serve una parola da cercare (oppure --ultimi N).", file=uscita)
        return 2
    if not parola:
        if argomenti.ultimi < 1:
            print("ERRORE: --ultimi vuole un numero maggiore di zero.", file=uscita)
            return 2
        tutte = diario.voci(config)
        if not tutte:
            print("Il diario è vuoto: non c'è nessun messaggio registrato.", file=uscita)
            return 0
        ultimi = tutte[-argomenti.ultimi:]
        print(f"Gli ultimi {len(ultimi)} messaggi del diario (la conversazione registrata, non le note):", file=uscita)
        for voce in ultimi:
            _stampa_voce(voce, "", uscita)
        return 0
    tutte, trovate = diario.cerca(config, parola)
    if not tutte:
        print("Il diario è vuoto: non c'è nessun messaggio registrato.", file=uscita)
        return 0
    if not trovate:
        print(f"Nessun messaggio del diario contiene «{parola}».", file=uscita)
        return 0
    quanti = "Trovato 1 messaggio" if len(trovate) == 1 else f"Trovati {len(trovate)} messaggi"
    print(f"{quanti} con «{parola}» nel diario (la conversazione registrata, non le note).",
          file=uscita)
    da_mostrare = sorted({j for i in trovate for j in ((i - 1, i, i + 1) if argomenti.intorno else (i,))
                          if 0 <= j < len(tutte)})
    precedente = None
    for posizione in da_mostrare:
        if argomenti.intorno and precedente is not None and posizione != precedente + 1:
            print("", file=uscita)
            print("[...]", file=uscita)
        precedente = posizione
        segno = " (trovato)" if argomenti.intorno and posizione in trovate else ""
        _stampa_voce(tutte[posizione], segno, uscita)
    return 0


def _stampa_voce(voce, segno: str, uscita: TextIO) -> None:
    # Le righe dei testimoni di Claude Code non hanno indicazione; quelle copiate dall'archivio dicono da dove vengono.
    fonte = f" · {voce.fonte}" if voce.fonte else ""
    print("", file=uscita)
    print(f"--- {voce.quando} · {voce.chi}{fonte}{segno} ---", file=uscita)
    for riga in _rientrato(voce.testo if voce.testo is not None else f"({voce.dicitura})"):
        print(riga, file=uscita)


def _testimone(argomenti, adesso: datetime, errori: TextIO) -> int:
    # Su successo non scrive niente: per Claude Code, ciò che esce qui finirebbe nella chat.
    try:
        config = configurazione.carica(argomenti.config)
        if config.testimone_attivo and _quaderno_nel_programma(config, errori, ""):
            return 1
        if argomenti.file == "-":
            dati = sys.stdin.buffer.read()
        else:
            dati = Path(argomenti.file).read_bytes()
        testimone.registra(config, adesso, dati)
    except (configurazione.ErroreConfigurazione, testimone.ErroreTestimone, OSError) as errore:
        print(f"ERRORE del testimone: {errore} Il messaggio NON è stato registrato.", file=errori)
        return 1
    return 0


def main(
    argv: list[str] | None = None,
    adesso: datetime | None = None,
    uscita: TextIO | None = None,
    errori: TextIO | None = None,
) -> int:
    """Punto d'ingresso. ``adesso``, ``uscita`` ed ``errori`` servono ai test per avere risultati ripetibili."""
    # Sempre UTF-8: chi legge l'uscita (Claude, Git Bash) si aspetta UTF-8, anche su Windows
    # dove Python userebbe altrimenti la vecchia codifica di sistema. Nella finestra della
    # console non cambia niente: lì Python scrive già correttamente.
    # Anche l'a capo è sempre lo stesso, «\n»: su Windows Python scriverebbe «\r\n». Così l'uscita è
    # identica byte per byte su ogni sistema.
    if uscita is None:
        uscita = sys.stdout
        if hasattr(uscita, "reconfigure"):
            uscita.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    if errori is None:
        errori = sys.stderr
        if hasattr(errori, "reconfigure"):
            errori.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    try:
        argomenti = _parser().parse_args(argv)
    except SystemExit as uscita_argparse:
        # Un comando scritto male esce con 2; per il testimone vorrebbe dire bloccare il messaggio.
        elenco = sys.argv[1:] if argv is None else argv
        # Lo stesso per gli altri agganci: mai il codice 2 per sbaglio (per la protezione vorrebbe dire
        # fermare uno strumento).
        if uscita_argparse.code == 2 and any(INGLESE.get(c, c) in AGGANCI for c in elenco):
            return 1
        raise
    adesso = adesso or datetime.now().astimezone()
    comando = INGLESE.get(argomenti.comando, argomenti.comando)
    if comando == "witness":
        return _testimone(argomenti, adesso, errori)
    if comando == "replies":
        return _risposte(argomenti, adesso, errori)
    if comando == "start":
        return _avvio(argomenti, uscita)
    if comando == "protect":
        return _protezione(argomenti, errori)
    if comando == "compare":
        return _confronta(argomenti, uscita)
    if comando == "fingerprint":
        return _impronta(argomenti, uscita)
    try:
        config = configurazione.carica(argomenti.config)
    except configurazione.ErroreConfigurazione as errore:
        print(f"ERRORE: {errore}", file=uscita)
        return 2
    try:
        if comando in LETTURA:
            # Chi legge aspetta che un passaggio dello sportello finisca: non vede mai una nota a metà.
            with blocco.blocco(config.cartella_quaderno, crea=False):
                return _esegui(comando, argomenti, config, adesso, uscita)
        return _esegui(comando, argomenti, config, adesso, uscita)
    except NotaIlleggibile as errore:
        print(f"ERRORE: il quaderno contiene un file non valido: {errore}. "
              "Controlla se è stato modificato a mano.", file=uscita)
        return 2
    except (testimone.ErroreTestimone, registro.RegistroToccato, blocco.QuadernoOccupato) as errore:
        print(f"ERRORE: {errore}", file=uscita)
        return 2


def _esegui(comando, argomenti, config, adesso: datetime, uscita: TextIO) -> int:
    if comando == "propose":
        return _proponi(argomenti, config, adesso, uscita)
    if comando == "status":
        return _stato(argomenti, config, uscita)
    if comando == "snapshot":
        return _istantanea(config, uscita)
    if comando == "changed":
        return _cambiati(argomenti, config, uscita)
    if comando == "check":
        return _controlla(config, uscita)
    if comando == "diary":
        return _diario(argomenti, config, uscita)
    if comando == "archive":
        return _archivio(argomenti, config, uscita)
    if comando == "reminders":
        return _promemoria(config, adesso, uscita)
    if comando == "recap":
        return _recap(config, adesso, uscita)
    if comando == "review":
        return _revisione(config, adesso, uscita)
    if comando == "claude-settings":
        return _impostazioni_claude(argomenti, config, uscita)
    return _cerca(argomenti, config, uscita)
