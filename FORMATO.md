# Formato delle note (bozza da approvare)

## La proposta: cosa Claude passa allo sportello

Una proposta è **una sola nota** scritta in JSON, salvata in UTF-8.

```json
{
  "data": "2026-01-15",
  "fonte": "chat del 15 gennaio 2026 sul progetto dell'orto",
  "autore": "utente",
  "tipo": "dichiarata",
  "natura": "fatto",
  "testo": "L'orto è sul balcone esposto a sud."
}
```

| Campo | Obbligatorio | Valori ammessi | Significato |
|---|---|---|---|
| `data` | sì | `AAAA-MM-GG`, oppure `AAAA-MM-GGThh:mm`, oppure `AAAA-MM-GGThh:mm:ss` | Quando la cosa è stata detta o osservata. |
| `fonte` | sì | testo su una riga | Da dove viene: quale chat, oppure "dal libro …", "dalla spiegazione di Claude …", "mio pensiero". |
| `autore` | sì | `utente`, `claude` | Chi l'ha detta. |
| `tipo` | sì | `osservata`, `dichiarata`, `dedotta` | Quanto è certa: vista, detta esplicitamente, oppure ricavata ragionando. |
| `natura` | sì | `idea`, `decisione`, `fatto`, `discorso aperto` | Che cosa è. |
| `testo` | sì | testo, anche su più righe | Con `autore: utente`: **le parole esatte dell'utente**, copiate da un suo messaggio. Con `autore: claude`: le parole di Claude. |
| `contesto` | no; **solo** con `autore: utente` | testo, anche su più righe | Ciò che Claude aggiunge alle parole dell'utente (spiegazioni, di cosa si parlava). Mostrato come "Contesto scritto da Claude". |
| `citazione` | no; **solo** con `autore: claude` | testo, anche su più righe | Le parole esatte dell'utente su cui Claude basa la sua nota. |
| `conferma_di` | no | numero di una nota esistente, per esempio `"0001"` | Solo per una decisione che conferma un'idea già nel quaderno. |
| `da_risposta` | no; **solo** con `autore: claude`, mai insieme a `citazione` | `"sì"` | Il `testo` è un pezzo di una risposta di Claude («Salva questa risposta di Claude»). Con il testimone delle risposte acceso, lo sportello lo cerca nelle risposte registrate. |

Le parole dell'utente e quelle di Claude non stanno mai nello stesso campo: in una nota
dell'utente sono `testo` (utente) e `contesto` (Claude); in una nota di Claude sono `testo`
(Claude) e `citazione` (utente).

I valori vanno scritti esattamente così, in minuscolo. Gli spazi all'inizio e alla fine vengono tolti.

## Le regole dello sportello

La nota viene **rifiutata** se:

1. manca un campo obbligatorio, oppure è vuoto;
2. c'è un campo non previsto (per esempio un errore di battitura come `fnte`) o un campo ripetuto;
3. un campo non è un testo tra virgolette;
4. un campo diverso da `testo`, `contesto` e `citazione` va a capo;
5. la data non esiste o non è nel formato indicato;
6. `autore`, `tipo` o `natura` hanno un valore non ammesso;
7. è una **decisione** scritta da **Claude**: le decisioni le prende solo l'utente;
8. è una **decisione** non **dichiarata** (una decisione non si osserva e non si deduce: la dice l'utente);
9. ha `conferma_di` ma non è una decisione, oppure la nota indicata non esiste, oppure non è un'idea;
10. il file non è JSON valido, non contiene una sola nota, o non è in UTF-8;
11. ha `autore: utente` e il campo `citazione` (le sue parole vanno in `testo`), oppure ha
    `autore: claude` e il campo `contesto` (in una nota di Claude è tutto già di Claude);
12. `testo` o `contesto` contengono la riga `## Contesto scritto da Claude`, riservata al
    formato della nota;
13. con il testimone acceso, ha `autore: utente` e il `testo` non si trova parola per parola in
    nessun messaggio registrato (vale anche per le decisioni, che sono sempre dell'utente);
14. con il testimone acceso, è una nota di Claude con una `citazione` che non si trova parola
    per parola in nessun messaggio registrato.

Tutti i motivi trovati vengono elencati insieme, sempre nello stesso ordine.

## Il testimone

Il testimone è un programma che registra le parole esatte di ogni messaggio dell'utente,
prima che Claude lo legga. Così lo sportello non deve fidarsi di Claude quando una nota dice
`autore: utente`: confronta il `testo` con i messaggi registrati (e, nelle note di Claude, la
`citazione`). Qui sotto "citazione" vuol dire il pezzo da cercare, in entrambi i casi.

**Testo incollato.** Un testo incollato dall'utente in un messaggio conta come portato da lui:
non c'è nessuna regola che lo distingua dal testo scritto. Da dove viene lo dice la `fonte`.

**Confronto (da confermare).** La citazione deve comparire **identica** dentro **un solo** messaggio:
stesse parole, stesse maiuscole, stessi accenti, stessa punteggiatura. Unica tolleranza: gli spazi,
le tabulazioni e gli a capo multipli contano come un solo spazio, e quelli all'inizio e alla fine
non contano. La citazione deve iniziare e finire a confine di parola: `ucchine` non si trova
dentro `zucchine`.

**Il segno `>` (facoltativo).** Le righe di un messaggio che iniziano con il segno di citazione
(di base `>`, regolabile con `segno_citazione`; contano anche gli spazi prima del segno) sono
parole riportate da altri. Il testimone registra il messaggio identico e in più annota i numeri
di quelle righe (`righe_citate`). Nel confronto il segno all'inizio di una riga marcata, e uno
spazio dopo, si possono omettere. Se la citazione si trova tutta dentro un gruppo di righe
marcate consecutive, la nota porta la dicitura "citazione riportata dall'utente"; se prende
anche righe non marcate ("citazione mista") viene verificata come le altre, senza dicitura.

**Testimone spento.** Le note con `autore: utente` vengono accettate senza controllo,
ma sono marcate in modo visibile come non verificate (vedi sotto).

**Messaggi privati.** Un messaggio che inizia con il prefisso privato (di base `#privato`) non
viene registrato: il testimone annota solo data e ora. Le sue parole non si possono citare.

Il file del testimone (`testimone.jsonl` nel quaderno) ha una riga JSON per messaggio:

```
{"quando": "2026-01-15T10:00:00+01:00", "testo": "Ho deciso: da lunedì annaffio l'orto alle sei."}
{"quando": "2026-01-15T10:01:00+01:00", "testo": "Un passo:\n> Un orto non si finisce mai.", "righe_citate": [2]}
{"quando": "2026-01-15T10:02:00+01:00", "privato": "messaggio privato, non registrato"}
```

`righe_citate` compare solo se almeno una riga è marcata; le righe si contano da 1.

## La riga «verifica»

Lo sportello, e solo lo sportello, aggiunge alla nota salvata una riga `verifica`
(una proposta che contiene `verifica` viene rifiutata come campo non previsto):

| Situazione | Riga scritta nella nota |
|---|---|
| Testimone acceso, nota dell'utente, testo trovato | `- verifica: testo trovato nel messaggio del <data e ora del messaggio>` |
| Testimone acceso, nota di Claude, citazione trovata | `- verifica: citazione trovata nel messaggio del <data e ora del messaggio>` |
| Testimone acceso, trovato tutto in righe marcate con `>` | `- verifica: citazione riportata dall'utente, trovata nel messaggio del <data e ora>` |
| Testimone spento, `autore: utente` | `- verifica: autore non verificato (testimone spento)` |
| Testimone spento, nota di Claude con citazione | `- verifica: citazione non verificata (testimone spento)` |
| Chat di Claude (`modalita = "chat"`), `autore: utente` | `- verifica: autore non verificato (chat, senza testimone)` |
| Chat di Claude (`modalita = "chat"`), nota di Claude con citazione | `- verifica: citazione non verificata (chat, senza testimone)` |
| Testimoni in pausa (`/hypomnema:pausa`), `autore: utente` | `- verifica: autore non verificato (testimoni in pausa)` |
| Testimoni in pausa, nota di Claude con citazione o con `da_risposta` | `- verifica: citazione non verificata (testimoni in pausa)` oppure `- verifica: risposta non verificata (testimoni in pausa)` |
| Nota di Claude con `da_risposta`, testimone delle risposte acceso, testo trovato | `- verifica: testo trovato nella risposta di Claude del <data e ora>` |
| Nota di Claude con `da_risposta`, testimone delle risposte spento | `- verifica: risposta non verificata (registro delle risposte spento)` |
| Nota di Claude con `da_risposta`, chat di Claude | `- verifica: risposta non verificata (chat, senza testimone)` |
| Nota di Claude senza citazione e senza `da_risposta` | nessuna riga |

Nel file della nota la `citazione` (note di Claude) è scritta su una riga sola (spazi e a capo
ridotti a uno); il `testo` e il `contesto` restano come sono, anche su più righe.

## Il testimone delle risposte

Se la sezione `[risposte]` della configurazione è accesa, il file delle risposte (`risposte.jsonl`
nel quaderno) ha una riga JSON per ogni risposta di Claude:

```
{"quando": "2026-01-15T10:01:00+01:00", "testo": "Il testo della risposta.", "prompt_id": "…"}
{"quando": "2026-01-15T10:03:00+01:00", "privato": "risposta a un messaggio privato, non registrata"}
```

`prompt_id` compare se Claude Code lo passa; dal compito 7 il testimone dei messaggi lo registra
anche accanto ai messaggi dell'utente. Con `ometti_codice = true` ogni blocco di codice diventa
`[blocco di codice di N righe omesso, impronta XXXXXXXXXXXX]`: l'impronta sono le prime 12 cifre
esadecimali dello SHA-256 delle righe del blocco, ciascuna seguita da un a capo.

Con `da_risposta`, il testo della nota viene cercato nelle risposte con le stesse regole del
testimone dei messaggi (identico a parte spazi e a capo multipli, dentro una sola risposta).

## Da idea a decisione

Un'idea resta un'idea. Quando l'utente la conferma esplicitamente, si propone una **nuova** nota:
`natura: decisione`, `autore: utente`, `tipo: dichiarata`, `conferma_di: <numero dell'idea>`
e come `testo` le parole esatte con cui l'utente conferma (eventuali spiegazioni in `contesto`).
L'idea originale non viene toccata: il quaderno conserva sia l'idea sia la decisione.

## La nota salvata nel quaderno

Ogni nota accettata riceve il numero successivo (`0001`, `0002`, ...) e diventa un file
`note/<numero>.md`, leggibile da una persona:

```markdown
# Nota 0002

- data: 2026-01-15T10:05
- fonte: chat del 15 gennaio 2026 sul progetto dell'orto
- autore: utente
- tipo: dichiarata
- natura: decisione
- conferma_di: 0001
- verifica: testo trovato nel messaggio del 2026-01-15T10:04:30+01:00

## Testo

sì, da domani annaffio la mattina presto

## Contesto scritto da Claude

Conferma dell'idea 0001: annaffiare la mattina presto invece che la sera.
```

La sezione "Contesto scritto da Claude" compare solo se la nota ha un `contesto`.

Il file si crea una volta sola: il programma non sovrascrive mai una nota esistente.

## Il registro degli ingressi

Il file `registro.md` del quaderno riceve una riga per ogni passaggio dallo sportello,
accettato o rifiutato. Si apre solo in aggiunta.

```
- 2026-01-15T10:00:00+01:00 | ACCETTATA | nota 0001 | da: 1-idea.json
- 2026-01-15T10:01:00+01:00 | RIFIUTATA | da: nota.json | motivi: manca il campo «fonte»: ogni nota deve dire da dove viene.
```

L'ora è quella del computer al momento del passaggio. `da:` è il nome del file proposto,
oppure `(ingresso diretto)` se la nota arriva dall'ingresso standard.
Se il registro esiste e non finisce con un "a capo" (qualcuno l'ha toccato a mano), lo sportello
non scrive niente, né la nota né la riga, e risponde con un errore: la sua riga si attaccherebbe a
quella scritta a mano. Non ripara il registro da solo. `controlla` mostra le righe che non hanno la
forma di una riga dello sportello, con il loro numero.

Ogni passaggio occupa sempre una sola riga: se il nome del file o un motivo contengono un
"a capo" (per esempio un nome di campo inventato), al suo posto viene scritto il segno ⏎.
Lo stesso vale per i motivi di rifiuto mostrati a schermo: ogni motivo sta su una riga.
