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
    python -m hypomnema etichette               # le etichette CHI e COSA, con quante note ha ognuna
    python -m hypomnema cerca --cosa orto       # anche search e recap filtrano per etichette (--chi, --cosa)
    python -m hypomnema albero --cosa orto      # ramo → sotto-rami → note, con le catene di integrazione

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
    __version__, albero, archivio, avvio, blocco, cambiamenti, cercatore, configurazione, controllo, diario, etichette,
    fuso_del_sistema, grafo, promemoria, registro, revisione, risposte, schemi, sportello, testimone,
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
    "revisione": "review", "etichette": "labels", "riscontri": "matches", "schemi": "patterns", "grafo": "graph",
    "albero": "tree",
}
# Gli agganci di Claude Code: non devono mai uscire con il codice 2 per un comando scritto male.
AGGANCI = ("witness", "replies", "start", "protect")
# I comandi che leggono il quaderno: aspettano che un passaggio dello sportello finisca (vedi blocco).
LETTURA = ("search", "reminders", "recap", "review", "check", "snapshot", "changed", "status", "diary", "labels",
           "matches", "patterns", "graph", "tree")


def _filtri(comando: argparse.ArgumentParser) -> None:
    """I filtri per etichette (dalla 0.7.0): si possono ripetere e devono valere tutti."""
    comando.add_argument("--who", "--chi", dest="chi", action="append", default=[], metavar="ETICHETTA",
                         help="solo le note con questa etichetta CHI (si può ripetere: devono valere tutte)")
    comando.add_argument("--about", "--cosa", dest="cosa", action="append", default=[], metavar="ETICHETTA",
                         help="solo le note con questa etichetta COSA (si può ripetere: devono valere tutte)")


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
    cerca.add_argument("parola", nargs="?",
                       help="la parola (o le parole) da cercare, così come sono (con un filtro si può omettere)")
    cerca.add_argument("--all", "--tutte", dest="tutte", action="store_true",
                       help="mostra anche le note chiuse, con la loro storia")
    _filtri(cerca)
    comandi.add_parser(
        "reminders", aliases=["promemoria"], help="elenca le note con «riprendere_il» arrivato o già passato, dal più vecchio"
    )
    recap = comandi.add_parser(
        "recap", help="dove eravamo rimasti: promemoria scaduti, discorsi aperti, ultime decisioni, ultimo diario"
    )
    _filtri(recap)
    comandi.add_parser(
        "labels", aliases=["etichette"], help="le etichette CHI e COSA della lista, con quante note ha ognuna"
    )
    riscontri = comandi.add_parser(
        "matches", aliases=["riscontri"],
        help="per ogni COSA messa dallo sportello, dove l'ha trovata nel testo; e le COSA a mano che nel testo non ci "
             "sono (solo lettura)",
    )
    riscontri.add_argument("--about", "--cosa", dest="cosa", action="append", default=[], metavar="ETICHETTA",
                           help="solo queste etichette COSA (si può ripetere)")
    schemi_parser = comandi.add_parser(
        "patterns", aliases=["schemi"],
        help="le sequenze di parole tipiche di ogni tipo di nota, dalle note dell'utente (solo lettura)",
    )
    schemi_parser.add_argument("--all", "--tutti", dest="tutti", action="store_true",
                               help="mostra tutte le sequenze tipiche, non solo le più frequenti")
    schemi_parser.add_argument("--measure", "--misura", dest="misura", action="store_true",
                               help="quante volte gli schemi indovinano il tipo: sulle stesse note e a turno")
    disegna = comandi.add_parser(
        "graph", aliases=["grafo"],
        help="scrive una pagina HTML con il grafo del taccuino (note, etichette, rimandi), fuori dal quaderno",
    )
    disegna.add_argument("file", help="il file .html da scrivere, fuori dalla cartella del quaderno")
    pianta = comandi.add_parser(
        "tree", aliases=["albero"],
        help="l'albero delle etichette: ramo (COSA) → sotto-rami → note, con le catene di integrazione (solo lettura)",
    )
    pianta.add_argument("--about", "--cosa", dest="cosa", action="append", default=[], metavar="ETICHETTA",
                        help="solo questo ramo (si può ripetere)")
    pianta.add_argument("--all", "--tutte", dest="tutte", action="store_true",
                        help="mostra anche le note chiuse e annullate")
    rivedi = comandi.add_parser(
        "review", aliases=["revisione"],
        help="che cosa conviene guardare nel quaderno: rami, note ferme, promemoria scaduti, note nominate (solo lettura)",
    )
    rivedi.add_argument("--proposals", "--proposte", dest="proposte", action="store_true",
                        help="mostra anche le proposte pronte, da completare e passare allo sportello una alla volta")

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


def _legenda(quaderno: Quaderno, segno: str) -> str:
    """La legenda dei codici; «C annullata» solo se nel quaderno c'è una nota annullata (dalla 0.9.0)."""
    annullate = any(v.annullata for s in quaderno.elenco() for v in s.versioni)
    return LEGENDA.format(segno=segno) + (" · C annullata" if annullate else "")


def _leggi(config, uscita: TextIO) -> Quaderno:
    """Il quaderno per un comando che legge; se etichette.toml è scritto male, una riga di avviso e si va avanti."""
    quaderno = cercatore.leggi(config)
    if quaderno.avviso:
        print(quaderno.avviso, file=uscita)
    return quaderno


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
    if ultima.annullata:
        righe.append(f"stato: annullata ({ultima.data})")
    if storia.integrata_in is not None:
        righe.append(f"stato: integrata nella nota {storia.integrata_in.etichetta(segno)} "
                     f"({storia.integrata_in.data}): il suo testo è in fondo a quella nota")
    if nota.priorita is not None:
        righe.append(f"priorità: {nota.priorita}")
    if nota.chi is not None:
        righe.append(f"chi: {', '.join(nota.chi)}")
    if nota.cosa is not None:
        righe.append(f"cosa: {', '.join(nota.cosa)}")
    if nota.cosa_dal_testo:
        righe.append(f"etichette dal testo (messe dallo sportello): cosa {', '.join(nota.cosa_dal_testo)}")
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
        _stampa_suggerimento(esito, uscita)
        return 0
    print("RIFIUTATA: la nota non è stata salvata." if not esito.scritte
          else "RIFIUTATA: il resto del cambiamento non è stato salvato.", file=uscita)
    print("Motivi:", file=uscita)
    for motivo in esito.motivi:
        # Come nel registro: un motivo sta su una riga, così nessuna riga falsa
        # (per esempio un finto "ACCETTATA") può comparire nella risposta che legge Claude.
        print(f"- {registro.su_una_riga(motivo)}", file=uscita)
    print("Il passaggio è annotato nel registro.", file=uscita)
    _stampa_suggerimento(esito, uscita)
    return 1


# Come si dice il tipo nel suggerimento: «suona come una decisione».
COME_SUONA = {"decision": "una decisione", "idea": "un'idea", "todo": "una cosa da fare",
              "open": "una questione aperta", "fact": "un fatto"}


def _stampa_suggerimento(esito, uscita: TextIO) -> None:
    """Dalla 0.9.0: il tipo che suona meglio secondo gli schemi dell'utente; dalla 0.10.0 il fatto che c'è già nello
    stesso sotto-ramo. Solo suggerimenti: non cambiano niente."""
    if esito.integrazione is not None:
        numero, sotto = esito.integrazione
        print(f"SUGGERIMENTO (non cambia niente): there is already fact {numero} in this sub-branch ({sotto}): is this "
              f"an integration? («integrates»: «{numero}»)", file=uscita)
    if esito.suggerimento is None:
        return
    tipo, trovate, proposto = esito.suggerimento
    citate = ", ".join(f"«{s}»" for s in trovate)
    print(f"SUGGERIMENTO (non cambia niente): suona come {COME_SUONA[tipo]} ({tipo}: {citate}). È giusto il tipo "
          f"{proposto}? Per cambiarlo serve updates.", file=uscita)


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


def _descrivi_filtro(argomenti) -> str:
    """«chi: Anna e cosa: orto»."""
    parti = [f"chi: {e}" for e in argomenti.chi] + [f"cosa: {e}" for e in argomenti.cosa]
    return ", ".join(parti[:-1]) + " e " + parti[-1] if len(parti) > 1 else parti[0]


def _controlla_filtro(argomenti, config, quaderno: Quaderno, uscita: TextIO) -> bool:
    """Un'etichetta del filtro deve essere nella lista, o almeno in una nota (tolta poi dalla lista)."""
    if not (argomenti.chi or argomenti.cosa):
        return True
    lista = etichette.leggi(config.cartella_quaderno)
    usate = _etichette_usate(quaderno)
    for campo, nome, scelte in (("who", "CHI", argomenti.chi), ("about", "COSA", argomenti.cosa)):
        ammesse = lista.ammesse(campo) if lista is not None else ()
        for scelta in scelte:
            if scelta in ammesse or scelta in usate[campo]:
                continue
            if lista is None:
                print(f"ERRORE: in questo quaderno non ci sono etichette (manca il file {etichette.NOME_FILE} nella "
                      f"cartella «{config.cartella_quaderno}»), e nessuna nota ha l'etichetta {nome} «{scelta}».", file=uscita)
            else:
                elenco = ", ".join(ammesse) if ammesse else "nessuna"
                print(f"ERRORE: l'etichetta {nome} «{scelta}» non è nella lista (le etichette {nome} sono: {elenco}) "
                      "e nessuna nota la usa. Il confronto è esatto: maiuscole e minuscole contano.", file=uscita)
            return False
    return True


def _etichette_usate(quaderno: Quaderno) -> dict[str, set[str]]:
    usate = {"who": set(), "about": set()}
    for storia in quaderno.elenco():
        usate["who"].update(storia.ultima.contenuto.chi or ())
        usate["about"].update(storia.ultima.contenuto.cosa or ())
    return usate


def _cerca(argomenti, config, uscita: TextIO) -> int:
    parola = (argomenti.parola or "").strip()
    filtro = bool(argomenti.chi or argomenti.cosa)
    if not parola and not filtro:
        print("ERRORE: serve una parola da cercare (oppure un filtro: --chi, --cosa).", file=uscita)
        return 2
    archivio_note = _leggi(config, uscita)
    if not _controlla_filtro(argomenti, config, archivio_note, uscita):
        return 2
    trovate = cercatore.cerca(archivio_note, parola, argomenti.tutte, argomenti.chi, argomenti.cosa)
    nascoste = 0 if argomenti.tutte else len(
        cercatore.cerca(archivio_note, parola, True, argomenti.chi, argomenti.cosa)) - len(trovate)
    if not filtro:
        cosa = f"con «{parola}»"
    elif parola:
        cosa = f"con «{parola}» e le etichette {_descrivi_filtro(argomenti)}"
    else:
        cosa = f"con le etichette {_descrivi_filtro(argomenti)}"
    if not trovate:
        aperta = " aperta" if nascoste else ""
        if filtro:
            print(f"Nessuna nota{aperta} {cosa}.", file=uscita)
        else:
            print(f"Nessuna nota{aperta} contiene «{parola}».", file=uscita)
    elif len(trovate) == 1:
        print(f"Trovata 1 nota {cosa}.", file=uscita)
    else:
        print(f"Trovate {len(trovate)} note {cosa} (dalla più recente).", file=uscita)
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
        print(f"Legenda: {_legenda(archivio_note, config.segno_chiusa)}", file=uscita)
    return 0


def _promemoria(config, adesso: datetime, uscita: TextIO) -> int:
    """Solo lettura: i promemoria scaduti, dal più vecchio."""
    archivio_note = _leggi(config, uscita)
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


def _etichette_in_riga(storia: Storia) -> str:
    """« · chi: Anna · cosa: orto», solo se la nota ha etichette (dalla 0.7.0)."""
    nota = storia.ultima.contenuto
    parti = []
    if nota.chi:
        parti.append(f"chi: {', '.join(nota.chi)}")
    if nota.cosa:
        parti.append(f"cosa: {', '.join(nota.cosa)}")
    return "".join(f" · {parte}" for parte in parti)


def _riga_recap(storia: Storia, inizio: str, quaderno: Quaderno, segno: str, conferme) -> list[str]:
    ultima = storia.ultima
    priorita = ETICHETTA_PRIORITA[cercatore.priorita_in_vigore(storia)]
    righe = [f"- [{ultima.etichetta(segno)}] {priorita}{inizio}: {_prima_riga(ultima.contenuto.testo)}"
             f"{_etichette_in_riga(storia)}"]
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


def _recap(argomenti, config, adesso: datetime, uscita: TextIO) -> int:
    """Solo lettura, con regole fisse: dove eravamo rimasti, in poche righe.

    In ogni blocco vengono prima le note a priorità alta, poi normale, poi bassa. A parità di
    priorità, i promemoria dal più vecchio (per data del promemoria); il resto (dalla 0.7.0) dal giorno
    dell'ultima versione più recente, senza contare le versioni che cambiano solo le etichette, e a parità
    di giorno dal numero più alto. Vale l'ultima versione di ogni nota, per quello che è adesso: le chiuse
    non ci sono, tranne le decisioni (una questione chiusa come decisione compare tra le decisioni, con il
    suo ✓). Con un filtro per etichette (--chi, --cosa) restano solo le note che le hanno tutte, e il diario,
    che non ha etichette, non si mostra.
    """
    archivio_note = _leggi(config, uscita)
    if not _controlla_filtro(argomenti, config, archivio_note, uscita):
        return 2
    filtro = bool(argomenti.chi or argomenti.cosa)
    conferme = cercatore.confermata_da(archivio_note)
    segno = config.segno_chiusa
    oggi = adesso.date()

    def per_priorita(elenco: list[Storia]) -> list[Storia]:
        # sorted è stabile: a parità di priorità resta l'ordine di partenza.
        return sorted(elenco, key=lambda s: cercatore.ORDINE_PRIORITA[cercatore.priorita_in_vigore(s)])

    def filtrate(elenco: list[Storia]) -> list[Storia]:
        return cercatore.filtra(elenco, argomenti.chi, argomenti.cosa)

    solo = f", solo le note con le etichette {_descrivi_filtro(argomenti)}" if filtro else ""
    righe = [f"Dove eravamo rimasti (recap del {oggi.isoformat()}{solo}).", ""]

    scaduti = promemoria.scaduti(archivio_note, oggi)
    if filtro:
        tenute = set(id(s) for s in filtrate([v.storia for v in scaduti]))
        scaduti = [v for v in scaduti if id(v.storia) in tenute]
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
        scelte = per_priorita(cercatore.per_data(filtrate(
            [s for s in archivio_note.elenco() if s.ultima.contenuto.natura == natura and not s.nascosta])))
        righe.append("")
        if not scelte:
            righe.append(f"{titolo}: {nessuno}.")
            continue
        mostrate = scelte[:quanti]
        righe.append(f"{titolo}: {len(mostrate)} di {len(scelte)} (prima la priorità alta, poi dal più recente)")
        for storia in mostrate:
            righe += _riga_recap(storia, storia.data_del_contenuto, archivio_note, segno, conferme)
        resto = len(scelte) - len(mostrate)
        if resto:
            righe.append(f"({uno_in_piu if resto == 1 else tanti_in_piu.format(resto)})")

    # Il blocco del diario: non c'è con voci_diario = 0 (dalla 0.7.0), e con un filtro si dice perché manca.
    if filtro:
        righe += ["", "Ultime voci del diario: non mostrate (il diario non ha etichette)."]
    elif config.recap_voci_diario:
        voci = diario.voci(config)
        righe.append("")
        if not voci:
            righe.append("Ultime voci del diario: nessuna.")
        else:
            mostrate = voci[-config.recap_voci_diario:]
            righe.append(f"Ultime voci del diario: {len(mostrate)} di {len(voci)} (la conversazione registrata, "
                         "non le note)")
            for voce in mostrate:
                righe.append(f"- {voce.quando} · {voce.chi}: {_prima_riga(voce.testo, voce.dicitura)}")
            righe.append(f"(per leggerle intere: diary --last {len(mostrate)})")
    righe += ["", f"Legenda: {_legenda(archivio_note, segno)}"]

    for riga in righe:
        print(riga, file=uscita)
    return 0


def _etichette(config, uscita: TextIO) -> int:
    """Solo lettura: le etichette della lista, con quante note (ultima versione) ha ognuna."""
    lista = etichette.leggi(config.cartella_quaderno)
    archivio_note = _leggi(config, uscita)
    storie = archivio_note.elenco()

    def aperta(storia: Storia) -> bool:
        nota = storia.ultima.contenuto
        return not storia.chiusa and (nota.natura in ("open", "todo") or nota.riprendere_il is not None)

    righe = []
    if lista is None:
        righe.append(f"Nessuna etichetta: nella cartella del quaderno non c'è il file {etichette.NOME_FILE}, quindi "
                     "nessuna nota può averne. Lo scrive l'utente (un modello commentato è esempi/etichette.toml).")
    for campo, attributo, nome in (("who", "chi", "CHI"), ("about", "cosa", "COSA")):
        if lista is None:
            continue
        righe.append(f"Etichette {nome}:" if lista.ammesse(campo) else f"Etichette {nome}: nessuna nella lista.")
        for etichetta in lista.ammesse(campo):
            con = [s for s in storie if etichetta in (getattr(s.ultima.contenuto, attributo) or ())]
            aperte = sum(1 for s in con if aperta(s))
            quante = "1 nota" if len(con) == 1 else f"{len(con)} note"
            if con:
                quante += " (1 aperta)" if aperte == 1 else f" ({aperte} aperte)"
            if con and campo == "about":
                # Dalla 0.8.0: quante le ha messe lo sportello dal testo e quante sono state proposte a mano.
                dal_testo = sum(1 for s in con if etichetta in (s.ultima.contenuto.cosa_dal_testo or ()))
                a_mano = len(con) - dal_testo
                quante += f": {dal_testo} dal testo, {a_mano} {'proposta' if a_mano == 1 else 'proposte'}"
            righe.append(f"- {etichetta}: {quante}")
    usate = _etichette_usate(archivio_note)
    fuori = [(nome, e) for campo, nome in (("who", "CHI"), ("about", "COSA"))
             for e in sorted(usate[campo]) if lista is None or e not in lista.ammesse(campo)]
    if fuori:
        righe.append("Etichette usate in qualche nota ma non nella lista: "
                     + ", ".join(f"{nome} «{e}»" for nome, e in fuori) + ".")
    elif lista is not None:
        righe.append("Etichette usate in qualche nota ma non nella lista: nessuna.")
    righe.append("(Si contano le note per la loro ultima versione; «aperte»: open, todo e promemoria non chiusi; "
                 "le COSA «dal testo» le ha messe lo sportello.)")
    for riga in righe:
        print(riga, file=uscita)
    return 0


def _revisione(argomenti, config, adesso: datetime, uscita: TextIO) -> int:
    """Solo lettura: che cosa conviene guardare. 0 = niente, 1 = qualcosa da guardare."""
    archivio_note = _leggi(config, uscita)
    oggi = adesso.date()
    segnalazioni = revisione.rivedi(archivio_note, oggi, config.giorni_revisione, config.segno_chiusa)
    if not segnalazioni:
        print(f"Revisione del quaderno ({oggi.isoformat()}): niente da segnalare.", file=uscita)
        return 0
    quante = "1 cosa da guardare" if len(segnalazioni) == 1 else f"{len(segnalazioni)} cose da guardare"
    print(f"Revisione del quaderno ({oggi.isoformat()}): {quante}. Non è stato cambiato niente.", file=uscita)
    for voce in segnalazioni:
        print(f"- {voce.storia.ultima.etichetta(config.segno_chiusa)}: {voce.testo}", file=uscita)
    proposte = [v for v in segnalazioni if v.proposta is not None] if argomenti.proposte else []
    if proposte:
        print("", file=uscita)
        print(f"Proposte pronte: {len(proposte)}. Non sono state passate allo sportello: ognuna va completata con "
              "«source» e, dove c'è, «text» (le parole dell'utente, mai inventate), e poi proposta una alla volta "
              "con propose. Se manca qualcosa lo sportello la rifiuta.", file=uscita)
        for numero, voce in enumerate(proposte, start=1):
            print(f"Proposta {numero} ({voce.storia.ultima.etichetta(config.segno_chiusa)}):", file=uscita)
            print(json.dumps(voce.proposta, ensure_ascii=False), file=uscita)
    print("", file=uscita)
    print(f"Legenda: {_legenda(archivio_note, config.segno_chiusa)}", file=uscita)
    return 1


def _rientrato(testo: str) -> list[str]:
    return [f"  {riga}" if riga else "" for riga in testo.split("\n")]


def _stato(argomenti, config, adesso: datetime, uscita: TextIO) -> int:
    """Solo lettura: non crea e non modifica niente."""
    righe = [
        f"Configurazione: {configurazione.trova(argomenti.config).resolve()}",
        f"Quaderno: {config.cartella_quaderno}",
        fuso_del_sistema.scegli(config, adesso).descrizione,
        _riga_etichette(config),
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


def _riscontri(argomenti, config, uscita: TextIO) -> int:
    """Solo lettura (dalla 0.8.0): i riscontri delle etichette COSA, per costruire la tabella dei riscontri.

    Una riga per caso, in ordine fisso: per etichetta (nell'ordine della lista, poi quelle fuori lista in
    ordine alfabetico), poi per numero di nota. Per ogni COSA messa dallo sportello: il codice della nota,
    l'etichetta e il pezzo di frase dove l'ha trovata. Per ogni COSA proposta a mano che nel testo non c'è:
    il codice, l'etichetta e «a mano, non nel testo». Non giudica e non cambia niente.
    """
    lista = etichette.leggi(config.cartella_quaderno)
    archivio_note = _leggi(config, uscita)
    storie = archivio_note.elenco()
    segno = config.segno_chiusa
    usate = sorted({e for s in storie for e in (s.ultima.contenuto.cosa or ())} - set(lista.cosa if lista else ()))
    ordine = [*(lista.cosa if lista else ()), *usate]
    if argomenti.cosa:
        sconosciute = [e for e in argomenti.cosa if e not in ordine]
        if sconosciute:
            print(f"ERRORE: l'etichetta COSA «{sconosciute[0]}» non è nella lista e nessuna nota la usa. Il confronto "
                  "è esatto: maiuscole e minuscole contano.", file=uscita)
            return 2
        ordine = [e for e in ordine if e in argomenti.cosa]
    righe = []
    for etichetta in ordine:
        for storia in storie:
            nota = storia.ultima.contenuto
            if etichetta not in (nota.cosa or ()):
                continue
            codice = storia.ultima.etichetta(segno)
            if etichetta in (nota.cosa_dal_testo or ()):
                pezzo = etichette.pezzo_di_frase(nota.testo, etichetta)
                righe.append(f"- {codice} · {etichetta} · dal testo: «{pezzo}»")
            elif etichette.pezzo_di_frase(nota.testo, etichetta) is None:
                righe.append(f"- {codice} · {etichetta} · a mano, non nel testo")
    quante = "1 riga" if len(righe) == 1 else f"{len(righe)} righe"
    print(f"Riscontri delle etichette COSA: {quante} (solo lettura: non giudica e non cambia niente).", file=uscita)
    print("«dal testo»: messa dallo sportello, con il pezzo di frase dove l'ha trovata (tra [ ] la parola); "
          "«a mano, non nel testo»: proposta a mano, e nel testo non c'è.", file=uscita)
    for riga in righe:
        print(riga, file=uscita)
    return 0


def _schemi(argomenti, config, uscita: TextIO) -> int:
    """Solo lettura (dalla 0.9.0): gli schemi del modo di parlare dell'utente, e se si chiede la misura."""
    note = schemi.note_dell_utente(_leggi(config, uscita))
    conti = schemi.Conti.da(note)
    print(f"Schemi del modo di parlare dell'utente: {len(note)} note dell'utente (prima versione di ogni nota; le note "
          "di Claude non contano).", file=uscita)
    print(f"Una sequenza di 2 o 3 parole è tipica di un tipo se compare in almeno {schemi.MIN_NOTE} note di quel tipo "
          f"e almeno il {schemi.QUOTA:.0%} delle sue note è di quel tipo.", file=uscita)
    for tipo in schemi.TIPI:
        trovati = conti.schemi(tipo)
        mostrati = trovati if argomenti.tutti else trovati[:schemi.DA_MOSTRARE]
        quante = "1 nota" if conti.note_per_tipo[tipo] == 1 else f"{conti.note_per_tipo[tipo]} note"
        elenco = ", ".join(f"«{s}» {n}" for s, n in mostrati) or "nessuno schema"
        resto = len(trovati) - len(mostrati)
        altri = f" (e altri {resto}: --all per vederli)" if resto else ""
        print(f"- {tipo} ({quante}): {elenco}{altri}", file=uscita)
    if argomenti.misura:
        print("", file=uscita)
        for titolo, a_turno in (("sulle stesse note (ottimista: gli schemi vengono anche dalla nota da indovinare)",
                                 False),
                                ("a turno (onesta: ogni nota tolta dal calcolo prima di indovinarla)", True)):
            m = schemi.misura(note, a_turno)
            print(f"Misura {titolo}: {m.note} note, tipo giusto {m.giuste}, nessuno schema {m.senza}, "
                  f"tipo sbagliato {m.note - m.giuste - m.senza}.", file=uscita)
        print("È una prova, non una garanzia: il tipo lo sceglie sempre chi propone.", file=uscita)
    return 0


def _grafo(argomenti, config, uscita: TextIO) -> int:
    """Solo lettura sul quaderno (dalla 0.9.0): scrive la pagina del grafo in un file fuori dal quaderno.

    Sovrascrive solo un file che è già una pagina del grafo di Hypomnema: un altro file non lo tocca.
    """
    file = Path(argomenti.file).resolve()
    if config.cartella_quaderno.resolve() in (file, *file.parents):
        print("ERRORE: la pagina del grafo non va dentro la cartella del quaderno: scegli un file fuori.", file=uscita)
        return 2
    if file.exists():
        try:
            inizio = file.read_text(encoding="utf-8")[:200]
        except (OSError, UnicodeDecodeError):
            inizio = ""
        if grafo.SEGNO_PAGINA not in inizio:
            print(f"ERRORE: il file «{file}» c'è già e non è una pagina del grafo di Hypomnema: non lo tocco. Scegli "
                  "un altro nome.", file=uscita)
            return 2
    archivio_note = _leggi(config, uscita)
    try:
        lista = etichette.leggi(config.cartella_quaderno)
    except etichette.ErroreEtichette:
        lista = None  # l'avviso l'ha già dato _leggi
    testo = grafo.pagina(archivio_note, lista, config.segno_chiusa)
    file.write_text(testo, encoding="utf-8", newline="\n")
    note = len(archivio_note.elenco())
    print(f"Grafo del taccuino scritto in «{file}»: {note} note, {len(grafo.collegamenti(archivio_note))} rimandi. "
          "Aprilo con il browser. Il quaderno non è stato toccato.", file=uscita)
    return 0


def _albero(argomenti, config, uscita: TextIO) -> int:
    """Solo lettura (dalla 0.10.0): l'albero delle etichette, ramo → sotto-rami → note."""
    archivio_note = _leggi(config, uscita)
    try:
        lista = etichette.leggi(config.cartella_quaderno)
    except etichette.ErroreEtichette:
        lista = None  # l'avviso l'ha già dato _leggi
    rami = albero.albero(archivio_note, lista, argomenti.tutte)
    if not rami:
        print(f"L'albero è vuoto: nessuna nota ha un'etichetta COSA (la lista è nel file {etichette.NOME_FILE} della "
              "cartella del quaderno).", file=uscita)
        return 0
    nomi = [r for r, _ in rami]
    for scelta in argomenti.cosa:
        if scelta not in nomi:
            print(f"ERRORE: la COSA «{scelta}» non è nella lista e nessuna nota la usa (le COSA sono: "
                  f"{', '.join(nomi)}). Il confronto è esatto: maiuscole e minuscole contano.", file=uscita)
            return 2
    if argomenti.cosa:
        rami = [(r, sotto) for r, sotto in rami if r in argomenti.cosa]
    segno = config.segno_chiusa
    quanti = "1 ramo" if len(rami) == 1 else f"{len(rami)} rami"
    print(f"Albero del taccuino: {quanti}. Non è stato cambiato niente.", file=uscita)
    for ramo, sotto in rami:
        teste = {s.base for _, note in sotto for s in note}
        print("", file=uscita)
        print(f"{ramo} · {len(teste)} {'nota' if len(teste) == 1 else 'note'}", file=uscita)
        for nome, note in sotto:
            print(f"  {nome} · {len(note)}" if note else f"  {nome} · nessuna nota", file=uscita)
            for storia in note:
                filo = albero.catena(archivio_note, storia)
                codici = " ← ".join(s.ultima.codice(segno) for s in filo)
                print(f"    {codici}  {_prima_riga(storia.ultima.contenuto.testo)}", file=uscita)
    nascoste = 0 if argomenti.tutte else sum(
        1 for s in archivio_note.elenco() if s.integrata_in is None and s.nascosta
        and set(argomenti.cosa or nomi) & set(s.ultima.contenuto.cosa or ()))
    if nascoste:
        quante = "1 nota chiusa o annullata non mostrata" if nascoste == 1 \
            else f"{nascoste} note chiuse o annullate non mostrate"
        print("", file=uscita)
        print(f"({quante}: aggiungi --all per vederle.)", file=uscita)
    print("", file=uscita)
    print(f"Legenda: {_legenda(archivio_note, segno)} · ← integrata nella nota a sinistra", file=uscita)
    return 0


def _riga_etichette(config) -> str:
    """La lista delle etichette (dalla 0.8.0): letta bene? Se è scritta male lo dice, senza fermarsi."""
    try:
        lista = etichette.leggi(config.cartella_quaderno)
    except etichette.ErroreEtichette as errore:
        return f"Etichette: ERRORE in {etichette.NOME_FILE}: {errore} Finché non è corretto lo sportello non salva niente."
    if lista is None:
        return f"Etichette: nessun file {etichette.NOME_FILE} (nessuna etichetta)."
    return (f"Etichette: {etichette.NOME_FILE} letto bene: {len(lista.chi)} CHI, {len(lista.cosa)} COSA. Lo sportello "
            "aggiunge da solo le COSA che trova nel testo; le CHI si propongono a mano.")


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
        adesso = configurazione.nel_fuso(config, adesso)
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
        adesso = configurazione.nel_fuso(config, adesso)
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
    adesso = configurazione.nel_fuso(config, adesso)
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
    except (testimone.ErroreTestimone, registro.RegistroToccato, blocco.QuadernoOccupato,
            etichette.ErroreEtichette) as errore:
        print(f"ERRORE: {errore}", file=uscita)
        return 2


def _esegui(comando, argomenti, config, adesso: datetime, uscita: TextIO) -> int:
    if comando == "propose":
        return _proponi(argomenti, config, adesso, uscita)
    if comando == "status":
        return _stato(argomenti, config, adesso, uscita)
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
        return _recap(argomenti, config, adesso, uscita)
    if comando == "labels":
        return _etichette(config, uscita)
    if comando == "matches":
        return _riscontri(argomenti, config, uscita)
    if comando == "patterns":
        return _schemi(argomenti, config, uscita)
    if comando == "graph":
        return _grafo(argomenti, config, uscita)
    if comando == "tree":
        return _albero(argomenti, config, uscita)
    if comando == "review":
        return _revisione(argomenti, config, adesso, uscita)
    if comando == "claude-settings":
        return _impostazioni_claude(argomenti, config, uscita)
    return _cerca(argomenti, config, uscita)
