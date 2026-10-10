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
10. il file non è JSON valido, non contiene una sola nota, o non è in UTF-8.

Tutti i motivi trovati vengono elencati insieme, sempre nello stesso ordine.

## Da idea a decisione

Un'idea resta un'idea. Quando l'utente la conferma esplicitamente, si propone una **nuova** nota:
`natura: decisione`, `autore: utente`, `tipo: dichiarata`, `conferma_di: <numero dell'idea>`.
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
