"""Lo sportello: l'unica porta d'ingresso del quaderno.

Riceve una nota proposta in formato JSON (testo UTF-8), la controlla con le regole fisse,
la salva come file Markdown se è completa, e annota sempre il passaggio nel registro.

Una proposta con ``corrects``, ``updates``, ``done`` o ``reopens`` non crea una nota nuova: crea
la versione successiva della nota (``0049.1.md``), una per ogni nota chiusa con ``done``, ognuna
con la sua riga nel registro.
"""

import json
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from hypomnema import (
    archivio as testimone_archivio, blocco, etichette, fuso_del_sistema, quaderno, registro, regole,
    risposte as testimone_risposte, schemi, testimone, versioni,
)
from hypomnema.configurazione import Configurazione
from hypomnema.nota import Cambio, Nota, numeri


@dataclass(frozen=True)
class Esito:
    accettata: bool
    id_nota: str | None
    percorso: Path | None
    motivi: list[str]
    # Tutte le note o versioni scritte: (numero, percorso). Più di una solo con «done» su più note.
    scritte: tuple[tuple[str, Path], ...] = ()
    # Dalla 0.9.0: un altro tipo che suona meglio, dagli schemi del modo di parlare dell'utente: (tipo, sequenze).
    # Solo un suggerimento: non entra nella nota né nel registro e non cambia niente.
    suggerimento: tuple[str, list[str], str] | None = None  # (tipo che suona meglio, sequenze, tipo proposto)


class _CampoDoppio(Exception):
    pass


def _senza_doppioni(coppie: list[tuple[str, object]]) -> dict:
    risultato: dict = {}
    for chiave, valore in coppie:
        if chiave in risultato:
            raise _CampoDoppio(chiave)
        risultato[chiave] = valore
    return risultato


def _leggi_proposta(contenuto: bytes) -> tuple[dict | None, list[str]]:
    try:
        # "utf-8-sig" accetta anche i file con il segno iniziale che aggiungono alcuni programmi Windows.
        testo = contenuto.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None, ["the file is not saved in UTF-8: save it in UTF-8 and try again."]
    try:
        dati = json.loads(testo, object_pairs_hook=_senza_doppioni)
    except _CampoDoppio as errore:
        return None, [f"the field «{errore.args[0]}» appears twice: it must appear only once."]
    except json.JSONDecodeError as errore:
        return None, [
            "the proposal is not valid JSON: check commas, quotes and brackets "
            f"(error at line {errore.lineno}, column {errore.colno})."
        ]
    if not isinstance(dati, dict):
        return None, [
            "the proposal must be a single note, written between braces { } with the note's fields."
        ]
    return dati, []


def _facoltativo(proposta: dict, campo: str) -> str | None:
    valore = proposta.get(campo)
    return valore.strip() if valore is not None else None


def _suggerimento(proposta: dict | None, note_esistenti) -> tuple[str, list[str], str] | None:
    """Per una nota nuova dell'utente: un altro tipo che suona meglio, con gli schemi del quaderno di prima."""
    if (proposta is None or not isinstance(proposta.get("author"), str) or proposta["author"].strip() != "user"
            or not isinstance(proposta.get("text"), str) or not isinstance(proposta.get("kind"), str)
            or any(proposta.get(c) is not None for c in regole.CAMPI_CAMBIAMENTO)):
        return None
    conti = schemi.Conti.da(schemi.note_dell_utente(versioni.Quaderno(note_esistenti)))
    proposto = proposta["kind"].strip()
    trovato = schemi.suggerimento(conti, proposta["text"], proposto)
    return (*trovato, proposto) if trovato is not None else None


def _etichette(proposta: dict, campo: str) -> tuple[str, ...] | None:
    valore = _facoltativo(proposta, campo)
    return etichette.separa(valore) if valore is not None else None


def ricevi(contenuto: bytes, origine: str, config: Configurazione, adesso: datetime) -> Esito:
    """Esamina una proposta e restituisce l'esito. Annota sempre il passaggio nel registro.

    Se il registro è stato toccato a mano (non finisce con un a capo) non scrive niente e solleva
    registro.RegistroToccato. Tiene il blocco del quaderno per tutto il passaggio (vedi ``blocco``);
    se un altro passaggio lo tiene troppo a lungo solleva blocco.QuadernoOccupato senza scrivere.
    """
    scelta = fuso_del_sistema.scegli(config, adesso)
    if scelta.fuso is not None:
        adesso = adesso.astimezone(scelta.fuso)
    # Prima del blocco, così un registro toccato a mano ferma tutto senza creare niente; poi di nuovo
    # dentro il passaggio.
    registro.controlla_fine(config)
    with blocco.blocco(config.cartella_quaderno, crea=True):
        # Sul computer dell'utente: il fuso del sistema nel file del quaderno, se è cambiato (dalla 0.7.0).
        fuso_del_sistema.annota(config, scelta, adesso)
        return _ricevi(contenuto, origine, config, adesso)


def _ricevi(contenuto: bytes, origine: str, config: Configurazione, adesso: datetime) -> Esito:
    registro.controlla_fine(config)
    note_esistenti = quaderno.leggi_note(config)
    messaggi = testimone.leggi_messaggi(config) if config.testimone_attivo else None
    risposte = testimone_risposte.leggi_risposte(config) if config.risposte_attive else None
    in_pausa = messaggi is not None and testimone.in_pausa(messaggi) is not None
    if in_pausa:
        # In pausa i testimoni non registrano: niente verifica, e la nota lo dice
        # («autore non verificato (testimoni in pausa)»).
        messaggi = risposte = None
    # La lista delle etichette, a ogni proposta (dalla 0.8.0 lo sportello mette da solo le COSA trovate nel
    # testo): un file scritto male ferma tutto (etichette.ErroreEtichette) prima di scrivere qualunque cosa,
    # anche nel registro.
    lista = etichette.leggi(config.cartella_quaderno)
    proposta, motivi = _leggi_proposta(contenuto)
    if proposta is not None:
        # I nomi e i valori italiani di prima valgono per sempre: qui diventano inglesi.
        proposta, motivi = regole.in_inglese(proposta)
        motivi += regole.controlla(proposta, note_esistenti, messaggi, config.segno_citazione, risposte,
                                   config.segno_chiusa, lista)

    consiglio = _suggerimento(proposta, note_esistenti)
    if motivi:
        registro.annota(config, adesso, origine, None, motivi)
        return Esito(accettata=False, id_nota=None, percorso=None, motivi=motivi, suggerimento=consiglio)

    id_nota = quaderno.prossimo_id(note_esistenti, config.cifre_numero_nota)
    citazione = _facoltativo(proposta, "quote")
    if citazione is not None:
        # Nel file della nota la citazione sta su una riga: spazi e a capo ridotti a uno.
        citazione = testimone.normalizza(citazione)
    autore = proposta["author"].strip()
    # Senza testo solo l'integrazione di un'altra nota (dalla 0.9.0), che copia il testo di quella nota.
    testo = proposta["text"].strip() if isinstance(proposta.get("text"), str) else ""
    da_risposta = _facoltativo(proposta, "from_reply")
    dicitura = regole.verifica(
        autore, testo, citazione, messaggi, config.segno_citazione, config.in_chat,
        da_risposta=da_risposta is not None, risposte=risposte, in_pausa=in_pausa,
        archivio=testimone_archivio.leggi_messaggi(config) if config.file_archivio else None,
        diario_chat=testimone_archivio.leggi_risposte(config) if config.file_archivio else None,
    ) if testo else None
    campo = next((c for c in regole.CAMPI_CAMBIAMENTO if _facoltativo(proposta, c) is not None), None)
    if campo is not None:
        valori = {k: v.strip() for k, v in proposta.items() if isinstance(v, str)}
        if citazione is not None:
            valori["quote"] = citazione
        return _versioni(config, adesso, origine, note_esistenti, campo, valori, dicitura, lista)
    nota = Nota(
        id=id_nota,
        data=proposta["date"].strip(),
        fonte=proposta["source"].strip(),
        autore=autore,
        tipo=proposta["knowledge"].strip(),
        natura=proposta["kind"].strip(),
        testo=testo,
        priorita=_facoltativo(proposta, "priority"),
        conferma_di=_facoltativo(proposta, "confirms"),
        riprendere_il=_facoltativo(proposta, "remind"),
        citazione=citazione,
        contesto=_facoltativo(proposta, "context"),
        da_risposta=da_risposta,
        verifica=dicitura,
        chi=_etichette(proposta, "who"),
    )
    # Le COSA: quelle proposte a mano, poi quelle che lo sportello trova nel testo (dalla 0.8.0).
    cosa, dal_testo = etichette.cosa_finali(_etichette(proposta, "about"), etichette.trova_nel_testo(testo, lista))
    nota = replace(nota, cosa=cosa, cosa_dal_testo=dal_testo)
    config.cartella_note.mkdir(parents=True, exist_ok=True)
    numero = int(id_nota)
    while True:
        nota = replace(nota, id=str(numero).zfill(config.cifre_numero_nota))
        percorso = config.cartella_note / f"{nota.id}.md"
        try:
            # Modo "x": se il file esiste già, Python si ferma invece di sovrascriverlo.
            with open(percorso, "x", encoding="utf-8", newline="\n") as f:
                f.write(nota.in_markdown())
            break
        except FileExistsError:
            # Un altro passaggio ha appena preso questo numero: si prova il successivo.
            # Finisce sempre, perché i file già presenti sono in numero finito.
            numero += 1
    id_nota = nota.id
    registro.annota(config, adesso, origine, id_nota, [])
    return Esito(accettata=True, id_nota=id_nota, percorso=percorso, motivi=[], scritte=((id_nota, percorso),),
                 suggerimento=consiglio)


def _versioni(config, adesso, origine, note_esistenti, campo, valori, dicitura, lista) -> Esito:
    """Scrive la versione successiva di ogni nota cambiata. Le regole sono già state controllate tutte."""
    elenco = numeri(valori[campo]) if campo == "done" else (valori[campo],)
    archivio_note = versioni.Quaderno(note_esistenti)
    cambio = Cambio(
        data=valori["date"], fonte=valori["source"], autore=valori["author"], tipo=valori["knowledge"], cambio="",
        citazione=None if campo == "corrects" else valori.get("quote"), verifica=dicitura,
        # In una correzione (e in un'integrazione, dalla 0.9.0) le parole nuove sono nel testo stesso: non c'è un
        # motivo a parte.
        motivo=None if campo in ("corrects", "integrates") else valori["text"],
        # In una correzione il contesto descrive il testo nuovo e sta nella nota; negli altri cambiamenti
        # dell'utente (dalla 0.7.0) accompagna il motivo.
        contesto=None if campo == "corrects" else valori.get("context"),
    )
    config.cartella_note.mkdir(parents=True, exist_ok=True)
    scritte = []
    for numero in elenco:
        storia = archivio_note.risolvi(numero, campo).storia
        attuale = storia.ultima.contenuto
        dopo = regole.dopo_il_cambiamento(campo, valori, storia, lista, archivio_note)
        voci = versioni.differenze(attuale, dopo)
        cambio_qui = cambio
        if campo == "integrates":
            # Il testo di prima resta intatto: la voce dice che cosa si è aggiunto in fondo.
            voci = [v for v in voci if v != versioni.TESTO_CORRETTO]
            if "from_note" in valori:
                integrata = archivio_note.risolvi(valori["from_note"], "from_note").storia
                sua = integrata.ultima.contenuto
                voci.insert(0, f"{versioni.INTEGRATA} {integrata.base}")
                cambio_qui = replace(cambio, verifica=None,
                                     da_nota=(integrata.base, sua.data, sua.fonte, sua.autore, sua.verifica))
            else:
                voci.insert(0, versioni.TESTO_AGGIUNTO)
        if campo == "done":
            voci.insert(0, versioni.CHIUSA)
        elif campo == "reopens":
            voci.insert(0, versioni.RIAPERTA)
        elif campo == "cancels":
            voci.insert(0, versioni.ANNULLATA)
        id_versione = storia.prossima_versione()
        nota = replace(
            dopo, id=id_versione, corregge=None, done=None,
            verifica=dicitura if campo == "corrects" else attuale.verifica,
            cambio=replace(cambio_qui, cambio="; ".join(voci)),
        )
        percorso = config.cartella_note / f"{id_versione}.md"
        try:
            # Modo "x": se il file esiste già, Python si ferma invece di sovrascriverlo.
            with open(percorso, "x", encoding="utf-8", newline="\n") as f:
                f.write(nota.in_markdown())
        except FileExistsError:
            # Un altro passaggio ha appena cambiato la stessa nota: questo cambiamento è stato
            # controllato su una versione che non è più l'ultima, quindi non si scrive.
            motivi = [f"version {id_versione} was written by another passage in the meantime: nothing more "
                      "was written. Look at the note again and make a new proposal."]
            registro.annota(config, adesso, origine, None, motivi)
            return Esito(accettata=False, id_nota=None, percorso=None, motivi=motivi, scritte=tuple(scritte))
        registro.annota(config, adesso, origine, id_versione, [])
        scritte.append((id_versione, percorso))
    return Esito(accettata=True, id_nota=scritte[0][0], percorso=scritte[0][1], motivi=[], scritte=tuple(scritte))
