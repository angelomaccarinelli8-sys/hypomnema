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
"""

import html
import math
import re

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
    legenda = " ".join(f'<span><i style="background:{c}"></i>{NOMI[k]} ({LETTERE[k]})</span>' for k, c in COLORI.items())
    note = len(quaderno.elenco())
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
</style>
</head>
<body>
<h1>Grafo del taccuino</h1>
<p>{note} note, {len(etichette)} etichette, {len(linee)} rimandi. Passa sopra un punto per leggere la nota. Le note
chiuse, annullate o integrate sono sbiadite; le etichette CHI hanno il bordo tratteggiato, i rimandi «nota NNNN»
scritti nel testo sono tratteggiati. Pagina scritta da Hypomnema in sola lettura: non cambia il quaderno.</p>
<div class="legenda">{legenda}</div>
<svg viewBox="0 0 {LATO} {LATO}" role="img" aria-label="Grafo delle note e delle etichette">
{chr(10).join(svg)}
</svg>
</body>
</html>
"""
