"""Riga di comando di Hypomnema.

    python -m hypomnema proponi proposta.json   # passa una nota allo sportello
    python -m hypomnema proponi -               # legge la nota dall'ingresso standard
    python -m hypomnema cerca parola            # cerca le note che contengono la parola
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
    __version__, archivio, avvio, cambiamenti, cercatore, configurazione, controllo, diario, registro, risposte,
    sportello, testimone,
)
from hypomnema.nota import Nota, NotaIlleggibile

ORIGINE_DIRETTA = "(ingresso diretto)"


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

    proponi = comandi.add_parser("proponi", help="passa una nota allo sportello")
    proponi.add_argument("file", help="file JSON con la nota proposta, oppure - per leggerla dall'ingresso standard")

    cerca = comandi.add_parser("cerca", help="cerca le note che contengono una parola")
    cerca.add_argument("parola", help="la parola (o le parole) da cercare, così come sono")

    registra = comandi.add_parser(
        "testimone", help="registra un messaggio dell'utente (lo lancia Claude Code a ogni messaggio)"
    )
    registra.add_argument(
        "file", nargs="?", default="-",
        help="file JSON con il messaggio, come lo manda Claude Code (di base: ingresso standard)",
    )

    comandi.add_parser(
        "stato", help="dice se il testimone è acceso, dov'è il quaderno e l'ultimo messaggio registrato"
    )
    comandi.add_parser(
        "istantanea", help="scrive dimensione e impronta di ogni file del quaderno (prima di una proposta)"
    )
    cambiati = comandi.add_parser(
        "cambiati", help="elenca i file del quaderno creati o allungati rispetto a un'istantanea"
    )
    cambiati.add_argument("file", help="il file dell'istantanea fatta prima della proposta")
    comandi.add_parser(
        "controlla",
        help="controlla che note e registro corrispondano e che il registro abbia solo righe dello sportello",
    )
    confronta = comandi.add_parser("confronta", help="dice se due file sono identici, byte per byte")
    confronta.add_argument("file1")
    confronta.add_argument("file2")

    registra_risposta = comandi.add_parser(
        "risposte", help="registra una risposta di Claude (lo lancia Claude Code alla fine di ogni risposta)"
    )
    registra_risposta.add_argument(
        "file", nargs="?", default="-",
        help="file JSON con la risposta, come lo manda Claude Code (di base: ingresso standard)",
    )
    calcola_impronta = comandi.add_parser(
        "impronta", help="scrive l'impronta di un file (o di un testo, con -), come per i blocchi di codice omessi"
    )
    calcola_impronta.add_argument("file", help="il file, oppure - per leggere il testo dall'ingresso standard")
    cerca_diario = comandi.add_parser(
        "diario", help="cerca una parola nei messaggi dell'utente e nelle risposte di Claude"
    )
    cerca_diario.add_argument("parola", nargs="?", help="la parola (o le parole) da cercare, così come sono")
    cerca_diario.add_argument("--ultimi", type=int, metavar="N",
                              help="senza parola: mostra gli ultimi N messaggi del diario")
    cerca_diario.add_argument(
        "--intorno", action="store_true", help="mostra anche il messaggio subito prima e subito dopo"
    )
    copia_archivio = comandi.add_parser(
        "archivio", help="chat: aggiunge ai file del quaderno la copia dei messaggi presa dall'archivio della chat"
    )
    copia_archivio.add_argument("file", help="file JSON con l'indirizzo della chat e i messaggi")
    comandi.add_parser(
        "avvio", help="inizio sessione (lo lancia Claude Code): crea la configurazione la prima volta e avvisa"
    )
    comandi.add_parser(
        "protezione", help="ferma gli strumenti di Claude sui file del quaderno (lo lancia Claude Code)"
    )
    comandi.add_parser(
        "impostazioni-claude",
        help="scrive le regole che vietano a Claude di modificare quaderno e configurazione (per l'avviabile)",
    )
    return parser


def _descrivi(nota: Nota) -> list[str]:
    righe = [
        f"--- Nota {nota.id} ---",
        f"data: {nota.data}",
        f"fonte: {nota.fonte}",
        f"autore: {nota.autore}",
        f"tipo: {nota.tipo}",
        f"natura: {nota.natura}",
    ]
    if nota.conferma_di is not None:
        righe.append(f"conferma di: nota {nota.conferma_di}")
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

    if esito.accettata:
        relativo = esito.percorso.relative_to(config.cartella_quaderno).as_posix()
        print(f"ACCETTATA: la nota {esito.id_nota} è stata salvata nel quaderno ({relativo}).", file=uscita)
        print("Il passaggio è annotato nel registro.", file=uscita)
        return 0
    print("RIFIUTATA: la nota non è stata salvata.", file=uscita)
    print("Motivi:", file=uscita)
    for motivo in esito.motivi:
        # Come nel registro: un motivo sta su una riga, così nessuna riga falsa
        # (per esempio un finto "ACCETTATA") può comparire nella risposta che legge Claude.
        print(f"- {registro.su_una_riga(motivo)}", file=uscita)
    print("Il passaggio è annotato nel registro.", file=uscita)
    return 1


def _cerca(argomenti, config, uscita: TextIO) -> int:
    parola = argomenti.parola.strip()
    if not parola:
        print("ERRORE: serve una parola da cercare.", file=uscita)
        return 2
    trovate = cercatore.cerca(config, parola)
    if not trovate:
        print(f"Nessuna nota contiene «{parola}».", file=uscita)
        return 0
    if len(trovate) == 1:
        print(f"Trovata 1 nota con «{parola}».", file=uscita)
    else:
        print(f"Trovate {len(trovate)} note con «{parola}».", file=uscita)
    for nota in trovate:
        print("", file=uscita)
        for riga in _descrivi(nota):
            print(riga, file=uscita)
    return 0


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
            f"Testimone: IN PAUSA dal {pausa.quando} (comando /hypomnema:pausa): i messaggi e le risposte "
            "non vengono registrati e le note con autore «utente» saranno marcate «autore non verificato "
            "(testimoni in pausa)». Per riprendere: /hypomnema:riprendi."
        )
    elif config.testimone_attivo:
        righe.append("Testimone: ACCESO (registra le parole esatte di ogni messaggio dell'utente).")
    elif config.in_chat:
        righe.append(
            "Testimone: NON C'È (configurazione per la chat di Claude): i messaggi arrivano solo a Claude "
            "e le note con autore «utente» saranno marcate «autore non verificato (chat, senza testimone)»."
        )
    else:
        righe.append(
            "Testimone: SPENTO (nella configurazione attivo = false): i messaggi non vengono registrati "
            "e le note con autore «utente» saranno marcate «autore non verificato»."
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
    if esito.gia_presenti:
        print(f"Già presenti, non duplicati: {esito.gia_presenti}.", file=uscita)
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
        if esito.note == 0:
            print("Quaderno in ordine: nessuna nota.", file=uscita)
        elif esito.note == 1:
            print("Quaderno in ordine: 1 nota, con la sua riga ACCETTATA nel registro.", file=uscita)
        else:
            print(f"Quaderno in ordine: {esito.note} note, tutte con la loro riga ACCETTATA nel registro.",
                  file=uscita)
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
        print(f"- {nome}, riga {numero}: stessa chat e stessa ora della riga {prima} (doppione).", file=uscita)
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
    if uscita is None:
        uscita = sys.stdout
        if hasattr(uscita, "reconfigure"):
            uscita.reconfigure(encoding="utf-8", errors="replace")
    if errori is None:
        errori = sys.stderr
        if hasattr(errori, "reconfigure"):
            errori.reconfigure(encoding="utf-8", errors="replace")
    try:
        argomenti = _parser().parse_args(argv)
    except SystemExit as uscita_argparse:
        # Un comando scritto male esce con 2; per il testimone vorrebbe dire bloccare il messaggio.
        elenco = sys.argv[1:] if argv is None else argv
        # Lo stesso per gli altri agganci: mai il codice 2 per sbaglio (per la protezione vorrebbe dire
        # fermare uno strumento).
        if uscita_argparse.code == 2 and any(c in elenco for c in ("testimone", "risposte", "avvio", "protezione")):
            return 1
        raise
    adesso = adesso or datetime.now().astimezone()
    if argomenti.comando == "testimone":
        return _testimone(argomenti, adesso, errori)
    if argomenti.comando == "risposte":
        return _risposte(argomenti, adesso, errori)
    if argomenti.comando == "avvio":
        return _avvio(argomenti, uscita)
    if argomenti.comando == "protezione":
        return _protezione(argomenti, errori)
    if argomenti.comando == "confronta":
        return _confronta(argomenti, uscita)
    if argomenti.comando == "impronta":
        return _impronta(argomenti, uscita)
    try:
        config = configurazione.carica(argomenti.config)
    except configurazione.ErroreConfigurazione as errore:
        print(f"ERRORE: {errore}", file=uscita)
        return 2
    try:
        if argomenti.comando == "proponi":
            return _proponi(argomenti, config, adesso, uscita)
        if argomenti.comando == "stato":
            return _stato(argomenti, config, uscita)
        if argomenti.comando == "istantanea":
            return _istantanea(config, uscita)
        if argomenti.comando == "cambiati":
            return _cambiati(argomenti, config, uscita)
        if argomenti.comando == "controlla":
            return _controlla(config, uscita)
        if argomenti.comando == "diario":
            return _diario(argomenti, config, uscita)
        if argomenti.comando == "archivio":
            return _archivio(argomenti, config, uscita)
        if argomenti.comando == "impostazioni-claude":
            return _impostazioni_claude(argomenti, config, uscita)
        return _cerca(argomenti, config, uscita)
    except NotaIlleggibile as errore:
        print(f"ERRORE: il quaderno contiene un file non valido: {errore}. "
              "Controlla se è stato modificato a mano.", file=uscita)
        return 2
    except (testimone.ErroreTestimone, registro.RegistroToccato) as errore:
        print(f"ERRORE: {errore}", file=uscita)
        return 2
