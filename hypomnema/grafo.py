"""Il grafo del taccuino: una pagina HTML da aprire nel browser. Solo lettura. Dalla 0.9.0 (I0204).

Le note sono punti colorati per tipo, le etichette (CHI e COSA) punti grandi; le linee sono i rimandi tra le note
(conferme, chiusure e correzioni delle note vecchie, integrazioni, «nota 0049» scritto nel testo o nel contesto) e,
più chiare, i legami tra una nota e le sue etichette. La pagina è un unico file, con il disegno dentro (SVG), senza
internet e senza librerie.

La disposizione è calcolata con regole fisse: stesso quaderno, stessa pagina, byte per byte.

- le etichette stanno su un cerchio grande, nell'ordine della lista (prima CHI, poi COSA; poi quelle usate nelle note
  ma non più nella lista, in ordine alfabetico);
- una nota con etichette sta tra le sue etichette, a metà strada verso il centro, spostata di poco secondo il suo
  numero (perché due note con le stesse etichette non si coprano);
- una nota senza etichette sta nella parte centrale, su una spirale, in ordine di numero.

Dalla 0.10.0 ``graph --albero`` (``pagina_albero``) dispone lo stesso taccuino ad albero, sempre con regole fisse: ogni
COSA è il centro di un grappolo, i grappoli stanno su un cerchio (nell'ordine della lista, poi le COSA fuori lista in
ordine alfabetico, e per ultimo «senza COSA»); intorno a ogni COSA i suoi sotto-rami e «senza argomento»; intorno a ogni
sotto-ramo le sue note, su una spirale, con le catene di integrazione una accanto all'altra. Una nota sta nel primo
ramo e nel primo sotto-ramo che ha (quelli dell'ultima versione, come ``tree``); verso gli altri suoi sotto-rami ha
una linea chiara. Le CHI non si disegnano.
"""

import html
import math
import re

from hypomnema import albero as albero_delle_etichette
from hypomnema.versioni import LETTERE, Quaderno, Storia

LATO = 1000
CENTRO = LATO / 2
RAGGIO_ETICHETTE = 400
ANGOLO_AUREO = math.pi * (3 - math.sqrt(5))
# Un numero di nota nel testo: anche con la lettera del codice davanti o la versione dopo, mai dentro una data.
NUMERO_NEL_TESTO = re.compile(r"(?<![\w.\-/])(?:[^\W\d_]{1,2}|✓[^\W\d_])?(\d{3,})(?:\.\d+)?(?![\w/\-]|\.\d)")
COLORI = {"fact": "#2f6db3", "idea": "#d08a1e", "decision": "#2e8b57", "open": "#b23a48", "todo": "#7a4fb3"}
NOMI = {"fact": "fatto", "idea": "idea", "decision": "decisione", "open": "aperta", "todo": "da fare"}
SEGNO_PAGINA = "<!-- Hypomnema: grafo del taccuino -->"


def _etichette(quaderno: Quaderno, lista) -> list[tuple[str, str]]:
    """(tipo, etichetta) nell'ordine fisso: la lista, poi quelle usate ma fuori lista in ordine alfabetico."""
    ordine = [("chi", e) for e in (lista.chi if lista else ())] + [("cosa", e) for e in (lista.cosa if lista else ())]
    usate = {("chi", e) for s in quaderno.elenco() for e in (s.ultima.contenuto.chi or ())}
    usate |= {("cosa", e) for s in quaderno.elenco() for e in (s.ultima.contenuto.cosa or ())}
    return ordine + sorted(usate - set(ordine))


def _della_nota(storia: Storia) -> list[tuple[str, str]]:
    nota = storia.ultima.contenuto
    return [("chi", e) for e in (nota.chi or ())] + [("cosa", e) for e in (nota.cosa or ())]


def collegamenti(quaderno: Quaderno) -> list[tuple[str, str, str]]:
    """I rimandi tra le note: (da, a, tipo), senza doppioni, in ordine fisso."""
    trovati = set()

    def aggiungi(da: Storia, numero: str | None, tipo: str) -> None:
        if numero is None:
            return
        a = quaderno.storia_di(numero.strip())
        if a is not None and a is not da:
            trovati.add((da.base, a.base, tipo))

    for storia in quaderno.elenco():
        for versione in storia.versioni:
            origine = versione.origine
            aggiungi(storia, origine.conferma_di, "conferma")
            aggiungi(storia, origine.corregge, "corregge")
            for numero in origine.done or ():
                aggiungi(storia, numero, "chiude")
            if versione.da_nota is not None:
                aggiungi(storia, versione.da_nota[0], "integra")
        nota = storia.ultima.contenuto
        for testo in (nota.testo, nota.contesto):
            for trovato in NUMERO_NEL_TESTO.finditer(testo or ""):
                aggiungi(storia, trovato.group(1), "nomina")
    return sorted(trovati)


def posizioni(quaderno: Quaderno, etichette: list[tuple[str, str]]) -> tuple[dict, dict]:
    """Le posizioni fisse delle etichette e delle note."""
    dove_etichetta = {}
    for i, chiave in enumerate(etichette):
        angolo = 2 * math.pi * i / max(len(etichette), 1) - math.pi / 2
        dove_etichetta[chiave] = (CENTRO + RAGGIO_ETICHETTE * math.cos(angolo),
                                  CENTRO + RAGGIO_ETICHETTE * math.sin(angolo))
    dove_nota = {}
    senza = 0
    for storia in quaderno.elenco():
        proprie = [dove_etichetta[e] for e in _della_nota(storia) if e in dove_etichetta]
        numero = int(storia.base)
        if proprie:
            x = sum(p[0] for p in proprie) / len(proprie)
            y = sum(p[1] for p in proprie) / len(proprie)
            x, y = CENTRO + (x - CENTRO) * 0.55, CENTRO + (y - CENTRO) * 0.55
            r = 14 + (numero % 7) * 6
            x, y = x + r * math.cos(numero * ANGOLO_AUREO), y + r * math.sin(numero * ANGOLO_AUREO)
        else:
            r = 12 * math.sqrt(senza + 1)
            x, y = CENTRO + r * math.cos(senza * ANGOLO_AUREO), CENTRO + r * math.sin(senza * ANGOLO_AUREO)
            senza += 1
        dove_nota[storia.base] = (x, y)
    return dove_etichetta, dove_nota


def pagina(quaderno: Quaderno, lista, segno: str) -> str:
    """La pagina HTML del grafo."""
    etichette = _etichette(quaderno, lista)
    dove_etichetta, dove_nota = posizioni(quaderno, etichette)
    linee = collegamenti(quaderno)
    svg = []
    for storia in quaderno.elenco():
        x, y = dove_nota[storia.base]
        for chiave in _della_nota(storia):
            ex, ey = dove_etichetta[chiave]
            svg.append(f'<line class="legame" x1="{x:.1f}" y1="{y:.1f}" x2="{ex:.1f}" y2="{ey:.1f}"/>')
    for da, a, tipo in linee:
        (x1, y1), (x2, y2) = dove_nota[da], dove_nota[a]
        svg.append(f'<line class="rimando {tipo}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}">'
                   f'<title>{html.escape(da)} {tipo} {html.escape(a)}</title></line>')
    for tipo, etichetta in etichette:
        x, y = dove_etichetta[(tipo, etichetta)]
        svg.append(f'<g class="etichetta {tipo}"><circle cx="{x:.1f}" cy="{y:.1f}" r="16"/>'
                   f'<text x="{x:.1f}" y="{y + 32:.1f}">{html.escape(etichetta)}</text></g>')
    for storia in quaderno.elenco():
        x, y = dove_nota[storia.base]
        nota = storia.ultima.contenuto
        spenta = " spenta" if storia.nascosta else ""
        prima_riga = nota.testo.split("\n")[0]
        svg.append(f'<circle class="nota{spenta}" cx="{x:.1f}" cy="{y:.1f}" r="7" '
                   f'fill="{COLORI.get(nota.natura, "#888888")}"><title>{html.escape(storia.ultima.etichetta(segno))}: '
                   f'{html.escape(prima_riga)}</title></circle>'
                   f'<text class="codice{spenta}" x="{x + 10:.1f}" y="{y + 4:.1f}">'
                   f'{html.escape(storia.ultima.codice(segno))}</text>')
    note = len(quaderno.elenco())
    intro = (f"{note} note, {len(etichette)} etichette, {len(linee)} rimandi. Passa sopra un punto per leggere la nota. Le "
             "note\nchiuse, annullate o integrate sono sbiadite; le etichette CHI hanno il bordo tratteggiato, i rimandi "
             "«nota NNNN»\nscritti nel testo sono tratteggiati. Pagina scritta da Hypomnema in sola lettura: non cambia "
             "il quaderno.")
    return _documento(intro, "Grafo delle note e delle etichette", svg)


def _documento(intro: str, descrizione: str, svg: list[str], stile_in_piu: str = "") -> str:
    """La pagina intera: intestazione, legenda dei tipi e disegno."""
    legenda = " ".join(f'<span><i style="background:{c}"></i>{NOMI[k]} ({LETTERE[k]})</span>' for k, c in COLORI.items())
    return f"""<!doctype html>
{SEGNO_PAGINA}
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Grafo del taccuino</title>
<style>
:root {{ --sfondo: #fbfaf7; --testo: #222; --linea: #9a9a9a; --legame: #d9d6cf; --etichetta: #444; }}
@media (prefers-color-scheme: dark) {{ :root {{ --sfondo: #181818; --testo: #eee; --linea: #8a8a8a;
  --legame: #333; --etichetta: #ccc; }} }}
body {{ margin: 0; padding: 16px; background: var(--sfondo); color: var(--testo);
  font-family: system-ui, sans-serif; }}
h1 {{ font-size: 1.2rem; margin: 0 0 .3rem; }}
p {{ margin: .2rem 0 .6rem; font-size: .9rem; }}
.legenda span {{ margin-right: 1rem; font-size: .85rem; white-space: nowrap; }}
.legenda i {{ display: inline-block; width: .8rem; height: .8rem; border-radius: 50%; margin-right: .3rem; }}
svg {{ width: 100%; max-width: 900px; height: auto; display: block; }}
.legame {{ stroke: var(--legame); stroke-width: 1; }}
.rimando {{ stroke: var(--linea); stroke-width: 1.6; }}
.rimando.nomina {{ stroke-dasharray: 4 3; }}
.etichetta circle {{ fill: var(--sfondo); stroke: var(--etichetta); stroke-width: 2; }}
.etichetta.chi circle {{ stroke-dasharray: 3 2; }}
.etichetta text {{ fill: var(--etichetta); font-size: 14px; text-anchor: middle; }}
.nota.spenta, .codice.spenta {{ opacity: .3; }}
.codice {{ fill: var(--testo); font-size: 10px; }}
{stile_in_piu}</style>
</head>
<body>
<h1>Grafo del taccuino</h1>
<p>{intro}</p>
<div class="legenda">{legenda}</div>
<svg viewBox="0 0 {LATO} {LATO}" role="img" aria-label="{descrizione}">
{chr(10).join(svg)}
</svg>
</body>
</html>
"""


SENZA_COSA = "senza COSA"
# La distanza tra due note vicine nel grafo ad albero: quanto basta per il codice («I0002.1»).
DISTANZA_NOTE = 46


def _grappoli(quaderno: Quaderno, lista) -> list[tuple[str, list[tuple[str, list[Storia]]]]]:
    """[(COSA, [(sotto-ramo, note)])]: ogni nota una volta sola, nel suo primo ramo e sotto-ramo, con le note
    integrate in lei subito dopo; poi le note senza COSA."""
    messe: set[str] = set()
    grappoli = []
    for ramo, sotto in albero_delle_etichette.albero(quaderno, lista, tutte=True):
        rami = []
        for nome, teste in sotto:
            note = []
            for testa in sorted(teste, key=lambda s: int(s.base)):
                if testa.base in messe:
                    continue
                for storia in albero_delle_etichette.catena(quaderno, testa):
                    if storia.base not in messe:
                        messe.add(storia.base)
                        note.append(storia)
            rami.append((nome, note))
        grappoli.append((ramo, rami))
    resto = [s for s in quaderno.elenco() if s.base not in messe]
    if resto:
        grappoli.append((SENZA_COSA, [("", resto)]))
    return grappoli


def posizioni_albero(quaderno: Quaderno, lista) -> tuple[list, dict]:
    """I centri (COSA e sotto-rami, con le loro posizioni) e le posizioni delle note."""
    grappoli = _grappoli(quaderno, lista)
    n = len(grappoli)
    seno = math.sin(math.pi / n) if n > 1 else 1.0
    raggio = 470 * seno / (1 + seno) if n > 1 else 420
    giro = 480 - raggio if n > 1 else 0
    nodi = []  # (tipo, nome, x, y, ramo)
    dove_nota = {}
    for g, (ramo, sotto) in enumerate(grappoli):
        angolo = 2 * math.pi * g / n - math.pi / 2
        cx, cy = CENTRO + giro * math.cos(angolo), CENTRO + giro * math.sin(angolo)
        nodi.append(("ramo", ramo, cx, cy, ramo))
        m = len(sotto)
        anello = raggio * 0.55 if m > 1 or ramo == SENZA_COSA else raggio * 0.45
        spazio = min(raggio * 0.4, anello * math.sin(math.pi / m) * 0.95) if m > 1 else raggio * 0.4
        for j, (nome, note) in enumerate(sotto):
            a = 2 * math.pi * j / m - math.pi / 2
            sx, sy = (cx, cy) if ramo == SENZA_COSA else (cx + anello * math.cos(a), cy + anello * math.sin(a))
            if ramo != SENZA_COSA:
                nodi.append(("sotto", nome, sx, sy, ramo))
            if ramo == SENZA_COSA:
                # Senza COSA: tutto intorno al centro del grappolo, su anelli.
                for i, storia in enumerate(note):
                    fila, posto = divmod(i, 10)
                    r = max(raggio * 0.45, 75) + DISTANZA_NOTE * fila
                    b = 2 * math.pi * posto / min(10, len(note) - fila * 10) + fila * 0.3
                    dove_nota[storia.base] = (sx + r * math.cos(b), sy + r * math.sin(b))
                continue
            # A ventaglio verso l'esterno del grappolo, lontano dalla linea che va alla COSA: file sempre più larghe,
            # con almeno DISTANZA_NOTE tra due note della stessa fila.
            restano, r = list(note), 40.0
            while restano:
                capienza = max(3, int(math.pi * r / DISTANZA_NOTE))
                fila, restano = restano[:capienza], restano[capienza:]
                passo = DISTANZA_NOTE / r
                for posto, storia in enumerate(fila):
                    b = a + (posto - (len(fila) - 1) / 2) * passo
                    dove_nota[storia.base] = (sx + r * math.cos(b), sy + r * math.sin(b))
                r += DISTANZA_NOTE
    return nodi, dove_nota


def pagina_albero(quaderno: Quaderno, lista, segno: str) -> str:
    """La pagina HTML del grafo ad albero (dalla 0.10.0)."""
    nodi, dove_nota = posizioni_albero(quaderno, lista)
    dove_sotto = {(ramo, nome): (x, y) for tipo, nome, x, y, ramo in nodi if tipo == "sotto"}
    dove_ramo = {nome: (x, y) for tipo, nome, x, y, _ in nodi if tipo == "ramo"}
    linee = collegamenti(quaderno)
    svg = []
    for (ramo, nome), (x, y) in dove_sotto.items():
        rx, ry = dove_ramo[ramo]
        svg.append(f'<line class="struttura" x1="{rx:.1f}" y1="{ry:.1f}" x2="{x:.1f}" y2="{y:.1f}"/>')
    for storia in quaderno.elenco():
        x, y = dove_nota[storia.base]
        nota = storia.ultima.contenuto
        propri = list(albero_delle_etichette.sotto_rami_visti(storia, lista))
        propri += [(c, albero_delle_etichette.SENZA_ARGOMENTO) for c in (nota.cosa or ())
                   if not any(r == c for r, _ in propri)]
        for i, chiave in enumerate(propri):
            if chiave in dove_sotto:
                ex, ey = dove_sotto[chiave]
                classe = "legame" if i == 0 else "legame altro"
                svg.append(f'<line class="{classe}" x1="{x:.1f}" y1="{y:.1f}" x2="{ex:.1f}" y2="{ey:.1f}"/>')
    for da, a, tipo in linee:
        (x1, y1), (x2, y2) = dove_nota[da], dove_nota[a]
        svg.append(f'<line class="rimando {tipo}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}">'
                   f'<title>{html.escape(da)} {tipo} {html.escape(a)}</title></line>')
    for tipo, nome, x, y, ramo in nodi:
        if tipo == "ramo":
            # Il cerchio della COSA è grande quanto il suo nome.
            svg.append(f'<g class="ramo"><circle cx="{x:.1f}" cy="{y:.1f}" r="{max(22, 4.2 * len(nome)):.1f}"/>'
                       f'<text x="{x:.1f}" y="{y + 5:.1f}">{html.escape(nome)}</text></g>')
        else:
            # Il nome del sotto-ramo sta di lato: dentro c'è la linea della COSA, fuori le note.
            rx, ry = dove_ramo[ramo]
            a = math.atan2(y - ry, x - rx) + math.pi / 2
            dx, dy = math.cos(a), math.sin(a)
            ancora = "start" if dx > 0.3 else "end" if dx < -0.3 else "middle"
            tx, ty = (x + 16 * dx, y + 4) if ancora != "middle" else (x, y + (52 if dy > 0 else -40))
            svg.append(f'<g class="sotto"><circle cx="{x:.1f}" cy="{y:.1f}" r="11"/>'
                       f'<text x="{tx:.1f}" y="{ty:.1f}" style="text-anchor: {ancora}">{html.escape(nome)}</text></g>')
    for storia in quaderno.elenco():
        x, y = dove_nota[storia.base]
        nota = storia.ultima.contenuto
        spenta = " spenta" if storia.nascosta else ""
        prima_riga = nota.testo.split("\n")[0]
        svg.append(f'<circle class="nota{spenta}" cx="{x:.1f}" cy="{y:.1f}" r="6" '
                   f'fill="{COLORI.get(nota.natura, "#888888")}"><title>{html.escape(storia.ultima.etichetta(segno))}: '
                   f'{html.escape(prima_riga)}</title></circle>'
                   f'<text class="codice{spenta}" x="{x + 8:.1f}" y="{y + 3:.1f}">'
                   f'{html.escape(storia.ultima.codice(segno))}</text>')
    rami = sum(1 for t, nome, *_ in nodi if t == "ramo" and nome != SENZA_COSA)
    intro = (f"{len(quaderno.elenco())} note, {rami} rami, {len(dove_sotto)} sotto-rami, {len(linee)} rimandi. Disposto "
             "ad albero: ogni COSA al centro del suo grappolo, intorno i sotto-rami e le loro note. Le linee chiare "
             "vanno agli altri sotto-rami di una nota; le note chiuse, annullate o integrate sono sbiadite. Passa sopra "
             "un punto per leggere la nota. Pagina scritta da Hypomnema in sola lettura: non cambia il quaderno.")
    stile = (".struttura { stroke: var(--etichetta); stroke-width: 2; }\n"
             ".legame.altro { stroke-dasharray: 2 3; }\n"
             ".ramo circle { fill: var(--sfondo); stroke: var(--etichetta); stroke-width: 3; }\n"
             ".ramo text { fill: var(--etichetta); font-size: 15px; font-weight: 600; text-anchor: middle; }\n"
             ".sotto circle { fill: var(--sfondo); stroke: var(--etichetta); stroke-width: 1.5; }\n"
             ".sotto text { fill: var(--etichetta); font-size: 12px; text-anchor: middle; }\n")
    return _documento(intro, "Albero delle etichette: rami, sotto-rami e note", svg, stile)

