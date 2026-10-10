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
| `fonte` | sì | testo su una riga | Da dove viene (per esempio quale chat). |
| `autore` | sì | `utente`, `claude` | Chi l'ha detta. |
| `tipo` | sì | `osservata`, `dichiarata`, `dedotta` | Quanto è certa: vista, detta esplicitamente, oppure ricavata ragionando. |
| `natura` | sì | `idea`, `decisione`, `fatto`, `discorso aperto` | Che cosa è. |
| `testo` | sì | testo, anche su più righe | Il contenuto della nota. |
| `conferma_di` | no | numero di una nota esistente, per esempio `"0001"` | Solo per una decisione che conferma un'idea già nel quaderno. |
| `citazione` | **sì se `autore` è `utente` e il testimone è acceso**; altrimenti no | testo, anche su più righe | Le parole esatte dell'utente, copiate da un suo messaggio. Vedi «Il testimone». |

I valori vanno scritti esattamente così, in minuscolo. Gli spazi all'inizio e alla fine vengono tolti.

## Le regole dello sportello

La nota viene **rifiutata** se:

1. manca un campo obbligatorio, oppure è vuoto;
2. c'è un campo non previsto (per esempio un errore di battitura come `fnte`) o un campo ripetuto;
3. un campo non è un testo tra virgolette;
4. un campo diverso da `testo` va a capo;
5. la data non esiste o non è nel formato indicato;
6. `autore`, `tipo` o `natura` hanno un valore non ammesso;
7. è una **decisione** scritta da **Claude**: le decisioni le prende solo l'utente;
8. è una **decisione** non **dichiarata** (una decisione non si osserva e non si deduce: la dice l'utente);
9. ha `conferma_di` ma non è una decisione, oppure la nota indicata non esiste, oppure non è un'idea;
10. il file non è JSON valido, non contiene una sola nota, o non è in UTF-8;
11. con il testimone acceso, ha `autore: utente` ma non ha la `citazione`
    (vale anche per le decisioni, che sono sempre dell'utente);
12. con il testimone acceso, ha una `citazione` che non si trova parola per parola in nessun
    messaggio registrato dal testimone (vale per qualunque autore).

Tutti i motivi trovati vengono elencati insieme, sempre nello stesso ordine.

## Il testimone

Il testimone è un programma che registra le parole esatte di ogni messaggio dell'utente,
prima che Claude lo legga. Così lo sportello non deve fidarsi di Claude quando una nota dice
`autore: utente`: confronta la `citazione` con i messaggi registrati.

**Confronto (da confermare).** La citazione deve comparire **identica** dentro **un solo** messaggio:
stesse parole, stesse maiuscole, stessi accenti, stessa punteggiatura. Unica tolleranza: gli spazi,
le tabulazioni e gli a capo multipli contano come un solo spazio, e quelli all'inizio e alla fine
non contano. La citazione deve iniziare e finire a confine di parola: `ucchine` non si trova
dentro `zucchine`.

**Testimone spento.** Le note con `autore: utente` vengono accettate anche senza citazione,
ma sono marcate in modo visibile come non verificate (vedi sotto).

**Messaggi privati.** Un messaggio che inizia con il prefisso privato (di base `#privato`) non
viene registrato: il testimone annota solo data e ora. Le sue parole non si possono citare.

Il file del testimone (`testimone.jsonl` nel quaderno) ha una riga JSON per messaggio:

```
{"quando": "2026-01-15T10:00:00+01:00", "testo": "Ho deciso: da lunedì annaffio l'orto alle sei."}
{"quando": "2026-01-15T10:01:00+01:00", "privato": "messaggio privato, non registrato"}
```

## La riga «verifica»

Lo sportello, e solo lo sportello, aggiunge alla nota salvata una riga `verifica`
(una proposta che contiene `verifica` viene rifiutata come campo non previsto):

| Situazione | Riga scritta nella nota |
|---|---|
| Testimone acceso, citazione trovata | `- verifica: citazione trovata nel messaggio del <data e ora del messaggio>` |
| Testimone spento, `autore: utente` | `- verifica: autore non verificato (testimone spento)` |
| Testimone spento, nota di Claude con citazione | `- verifica: citazione non verificata (testimone spento)` |
| Nota di Claude senza citazione | nessuna riga |

Nel file della nota la citazione è scritta su una riga sola (spazi e a capo ridotti a uno).

## Da idea a decisione

Un'idea resta un'idea. Quando l'utente la conferma esplicitamente, si propone una **nuova** nota:
`natura: decisione`, `autore: utente`, `tipo: dichiarata`, `conferma_di: <numero dell'idea>`
e, con il testimone acceso, la `citazione` delle parole con cui l'utente conferma.
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
- citazione: sì, da domani annaffio la mattina presto
- verifica: citazione trovata nel messaggio del 2026-01-15T10:04:30+01:00

## Testo

D'ora in poi annaffio l'orto la mattina presto invece che la sera.
```

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
