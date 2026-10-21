# Formato delle note

Dalla versione 0.5.0 la struttura è in inglese (nomi dei campi, valori, motivi di rifiuto) e il
contenuto resta nella sua lingua. I nomi e i valori italiani delle versioni precedenti valgono per
sempre, nelle proposte e nelle note già salvate: vedi «Nomi italiani» in fondo a questa sezione.

Dalla versione 0.6.0 **ogni cambiamento di una nota è una versione nuova**: un file nuovo con il
punto (`0049.1.md`, `0049.2.md`), che contiene tutta la nota con il cambiamento applicato e in fondo
un blocco «Change» (vedi «Le versioni»). Ogni nota ha un **codice**, con la lettera della sua natura
davanti al numero: `T0049.2`, e `✓T0049.3` se è chiusa (vedi «Il codice della nota»). Tutte le regole
del quaderno sono raccolte in «Le regole del quaderno», in fondo.

## La proposta: cosa Claude passa allo sportello

Una proposta è **una sola nota** scritta in JSON, salvata in UTF-8.

```json
{
  "date": "2026-01-15",
  "source": "chat del 15 gennaio 2026 sul progetto dell'orto",
  "author": "user",
  "knowledge": "stated",
  "kind": "fact",
  "text": "L'orto è sul balcone esposto a sud."
}
```

| Campo | Obbligatorio | Valori ammessi | Significato |
|---|---|---|---|
| `date` | sì | `AAAA-MM-GG`, oppure `AAAA-MM-GGThh:mm`, oppure `AAAA-MM-GGThh:mm:ss` | Quando la cosa è stata detta o osservata. |
| `source` | sì | testo su una riga | Da dove viene: quale chat, oppure "dal libro …", "dalla spiegazione di Claude …", "mio pensiero". |
| `author` | sì | `user`, `claude` | Chi l'ha detta. |
| `knowledge` | sì | `stated`, `observed`, `inferred` | Come si sa: detta esplicitamente, vista, oppure ricavata ragionando. |
| `kind` | sì (no in un cambiamento) | `fact`, `idea`, `decision`, `open`, `todo` | Che cosa è: un fatto, un'idea, una decisione, una questione aperta, una cosa da fare. In un cambiamento (`corrects`, `updates`, `done`, `reopens`) dice che cosa diventa la nota; se manca, la natura non cambia. |
| `text` | sì | testo, anche su più righe | Con `author: user`: **le parole esatte dell'utente**, copiate da un suo messaggio. Con `author: claude`: le parole di Claude. In un cambiamento è ciò che è stato detto adesso: il testo nuovo con `corrects`, il motivo con `updates`, `done` e `reopens`. |
| `context` | no; **solo** con `author: user` | testo, anche su più righe | Ciò che Claude aggiunge alle parole dell'utente (spiegazioni, di cosa si parlava). Mostrato come "Context written by Claude". Dalla 0.7.0 anche nei cambiamenti dell'utente (`updates`, `done`, `reopens`), accanto al motivo: va nel blocco del cambiamento. |
| `quote` | no; **solo** con `author: claude` | testo, anche su più righe | Le parole esatte dell'utente su cui Claude basa la sua nota. |
| `confirms` | no | numero di una nota esistente, per esempio `"0001"` | Solo per una decisione che conferma un'idea già nel quaderno. |
| `corrects` | no | numero di una nota esistente, per esempio `"0007"` | Corregge il **testo** della nota: crea la sua versione successiva, con il `text` della proposta come testo nuovo. Insieme si possono cambiare `kind`, `priority` e `remind`. |
| `updates` | no | numero di una nota esistente | Cambia natura (`kind`), priorità (`priority`), promemoria (`remind`) o etichette (`who`, `about`) senza toccare il testo: crea la versione successiva; il `text` è il motivo. |
| `reopens` | no | numero di una nota chiusa | Riapre la nota: crea una versione non chiusa; il `text` è il motivo. Se `kind` manca, torna la natura che la nota aveva prima della chiusura. |
| `remind` | no | solo il giorno: `AAAA-MM-GG` | Promemoria: il giorno in cui riprendere la nota. Il comando `reminders` elenca quelli arrivati o passati. |
| `done` | no | uno o più numeri di note esistenti, separati da virgole: `"0012"` oppure `"0012, 0015"` | Chiude le note indicate: questioni aperte (`open`), cose da fare (`todo`) o promemoria (con `remind`). Crea una versione chiusa per ciascuna, con lo stesso motivo (il `text`). Vedi «Chiudere e riaprire». |
| `priority` | no; **solo** con `author: user` | `high`, `normal`, `low` | La priorità; senza, vale `normal`. Si cambia con `updates`. |
| `who` | no (dalla 0.7.0) | una o due etichette CHI, separate da virgola: `"Anna"`, `"Anna, Marco"` | Le persone di cui parla la nota, dalla lista `chi` di `etichette.toml`. Vedi «Le etichette». |
| `about` | no (dalla 0.7.0) | una o due etichette COSA, separate da virgola | I progetti o gli argomenti, dalla lista `cosa` di `etichette.toml`. |
| `from_reply` | no; **solo** con `author: claude`, mai insieme a `quote` | `"yes"` | Il `text` è un pezzo di una risposta di Claude («Salva questa risposta di Claude»). Con il testimone delle risposte acceso, lo sportello lo cerca nelle risposte registrate. |

`corrects`, `updates`, `done` e `reopens` sono i **cambiamenti**: una proposta ne usa uno solo e non
crea una nota nuova, ma la versione successiva della nota indicata. In un rimando si scrive solo il
numero, senza la lettera del codice: `"0049"` vuol dire l'ultima versione, `"0049.1"` quella versione
precisa (va bene solo se è l'ultima). Il numero di una nota scritta prima della 0.6.0 che è diventata
una versione (per esempio una vecchia correzione) vale come quella versione.

Le parole dell'utente e quelle di Claude non stanno mai nello stesso campo: in una nota
dell'utente sono `text` (utente) e `context` (Claude); in una nota di Claude sono `text`
(Claude) e `quote` (utente).

I valori vanno scritti esattamente così, in minuscolo. Gli spazi all'inizio e alla fine vengono tolti.

**Nomi italiani.** Nelle proposte si possono usare anche i nomi e i valori di prima: `data`,
`fonte`, `autore` (`utente`), `tipo` (`dichiarata`, `osservata`, `dedotta`), `natura` (`fatto`,
`idea`, `decisione`, `discorso aperto`), `testo`, `contesto`, `citazione`, `conferma_di`,
`corregge`, `aggiorna` (per `updates`), `riapre` (per `reopens`), `riprendere_il`, `da_risposta` (`sì`),
`priorità` (`alta`, `normale`, `bassa`), e dalla 0.7.0 `chi` (per `who`) e `cosa` (per `about`).
Lo sportello li porta all'inglese e la nota nuova si scrive in inglese. Lo stesso campo non può
comparire due volte, nemmeno con i due nomi (per esempio `data` e `date`).

## Le regole dello sportello

La nota viene **rifiutata** se (i motivi sono scritti in inglese, perché li legge Claude):

1. manca un campo obbligatorio, oppure è vuoto;
2. c'è un campo non previsto (per esempio un errore di battitura come `fnte`) o un campo ripetuto
   (anche con il nome italiano e quello inglese);
3. un campo non è un testo tra virgolette;
4. un campo diverso da `text`, `context` e `quote` va a capo;
5. la data non esiste o non è nel formato indicato;
6. `author`, `knowledge`, `kind` o `priority` hanno un valore non ammesso (per esempio `choice`);
7. è una **decisione** scritta da **Claude**: le decisioni le prende solo l'utente;
8. è una **decisione** non **stated** (una decisione non si osserva e non si deduce: la dice l'utente);
9. ha `confirms` ma non è una decisione, oppure la nota indicata non esiste, non è all'ultima
   versione, oppure non è un'idea;
10. il file non è JSON valido, non contiene una sola nota, o non è in UTF-8;
11. ha `author: user` e il campo `quote` (le sue parole vanno in `text`), oppure ha
    `author: claude` e il campo `context` (in una nota di Claude è tutto già di Claude);
12. `text` o `context` contengono la riga `## Context written by Claude` (o quella italiana
    `## Contesto scritto da Claude`) oppure `## Change`, riservate al formato della nota;
13. con il testimone acceso, ha `author: user` e il `text` non si trova parola per parola in
    nessun messaggio registrato (vale anche per le decisioni e per i motivi dei cambiamenti);
14. con il testimone acceso, è una nota di Claude con una `quote` che non si trova parola
    per parola in nessun messaggio registrato;
15. ha `remind` con una data che non esiste o che non è solo un giorno (`AAAA-MM-GG`);
16. ha `priority` ma `author: claude` (Claude può proporre una priorità solo nel testo di una sua idea);
17. usa più di un cambiamento (`corrects`, `updates`, `done`, `reopens`), oppure un cambiamento
    insieme a `confirms`;
18. un rimando non è un numero (per esempio ha la lettera del codice, `T0049`), non esiste, oppure
    non è l'ultima versione della nota: il motivo dice qual è l'ultima;
19. `corrects` cambia il testo di una nota dell'utente ma non ha `author: user`, oppure il testo
    nuovo è uguale a quello di prima;
20. `updates` non cambia niente, oppure `updates`, `done` o `reopens` hanno `context` o
    `from_reply` (appartengono al testo di una nota);
21. `done` è scritto male, ripete una nota (anche con due numeri della stessa nota), chiude una nota
    già chiusa (il motivo dice di usare `reopens`) o che non si può chiudere (un `fact`, una
    `decision` o un'`idea` senza `remind`), ha `priority` o `remind`, oppure farebbe diventare la nota
    `todo` o `open`;
22. chiude o riapre un `open`, o fa smettere a una nota di essere `open`, ma non ha `author: user`;
23. `reopens` indica una nota che non è chiusa;
24. cambia la natura in `decision` senza `author: user`, cambia la natura di una decisione o di una
    nota dell'utente senza `author: user`, oppure fa diventare decisione un'idea (per questo c'è
    `confirms`).

Tutti i motivi trovati vengono elencati insieme, sempre nello stesso ordine.

## Il testimone

Il testimone è un programma che registra le parole esatte di ogni messaggio dell'utente,
prima che Claude lo legga. Così lo sportello non deve fidarsi di Claude quando una nota dice
`author: user`: confronta il `text` con i messaggi registrati (e, nelle note di Claude, la
`quote`). Qui sotto "citazione" vuol dire il pezzo da cercare, in entrambi i casi.

**Testo incollato.** Un testo incollato dall'utente in un messaggio conta come portato da lui:
non c'è nessuna regola che lo distingua dal testo scritto. Da dove viene lo dice la `source`.

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
marcate consecutive, la nota porta la dicitura "quote reported by the user"; se prende
anche righe non marcate ("citazione mista") viene verificata come le altre, senza dicitura.

**Testimone spento.** Le note con `author: user` vengono accettate senza controllo,
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

## La riga «verification»

Lo sportello, e solo lo sportello, aggiunge alla nota salvata una riga `verification` (una proposta
che contiene `verification` o `verifica` viene rifiutata come campo non previsto). Dalla 0.5.0 le
diciture sono in inglese; le note salvate prima hanno la riga `verifica` con la dicitura italiana
di allora («testo trovato nel messaggio del …», «autore non verificato (testimone spento)», …), che
resta com'è.

| Situazione | Riga scritta nella nota |
|---|---|
| Testimone acceso, nota dell'utente, testo trovato | `- verification: text found in the message of <data e ora del messaggio>` |
| Testimone acceso, nota di Claude, citazione trovata | `- verification: quote found in the message of <data e ora del messaggio>` |
| Testimone acceso, trovato tutto in righe marcate con `>` | `- verification: quote reported by the user, found in the message of <data e ora>` |
| Testimone spento, `author: user` | `- verification: author not verified (witness off)` |
| Testimone spento, nota di Claude con citazione | `- verification: quote not verified (witness off)` |
| Chat di Claude (`modalita = "chat"`), `author: user` | `- verification: author not verified (chat, no witness)` |
| Chat di Claude (`modalita = "chat"`), nota di Claude con citazione | `- verification: quote not verified (chat, no witness)` |
| Chat con l'archivio (`[archivio]`), `author: user`, testo trovato nella copia dell'archivio | `- verification: text matched in the chat archive <indirizzo>, message of turn <numero> (<data e ora>, copied by Claude)` |
| Chat con l'archivio, nota di Claude con citazione trovata nell'archivio, o con `from_reply` trovata nel diario della chat | `- verification: quote matched in the chat archive …` oppure `- verification: text matched in the chat archive …, reply of turn …` |
| Testimoni in pausa (`/hypomnema:pause`), `author: user` | `- verification: author not verified (witnesses paused)` |
| Testimoni in pausa, nota di Claude con citazione o con `from_reply` | `- verification: quote not verified (witnesses paused)` oppure `- verification: reply not verified (witnesses paused)` |
| Nota di Claude con `from_reply`, testimone delle risposte acceso, testo trovato | `- verification: text found in Claude's reply of <data e ora>` |
| Nota di Claude con `from_reply`, testimone delle risposte spento | `- verification: reply not verified (replies witness off)` |
| Nota di Claude con `from_reply`, chat di Claude | `- verification: reply not verified (chat, no witness)` |
| Nota di Claude senza citazione e senza `from_reply` | nessuna riga |

«Matched» (riscontrato sull'archivio della chat) non è mai «verified»: verificato vale solo per il
testimone di Claude Code.

Nel file della nota la `quote` (note di Claude) è scritta su una riga sola (spazi e a capo
ridotti a uno); il `text` e il `context` restano come sono, anche su più righe.

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

Con `from_reply`, il testo della nota viene cercato nelle risposte con le stesse regole del
testimone dei messaggi (identico a parte spazi e a capo multipli, dentro una sola risposta).

## L'archivio della chat

Nella configurazione per la chat, la sezione `[archivio]` accende la copia dall'archivio della chat.
Il comando `archive <file.json>` (o `archivio`) riceve da Claude la copia come la dà lo strumento dell'archivio:
l'indirizzo della chat, il fuso orario a parte e, per ogni messaggio, il numero del turno, la data e
l'ora al minuto, chi parla e il testo
(`{"chat": "https://…", "fuso": "UTC+02:00", "messaggi": [{"turno": 12, "quando": "Fri 2026-10-09 17:46", "chi": "utente"|"claude", "testo": "…"}]}`).
Li aggiunge solo in aggiunta e senza doppioni: un messaggio è già presente se ha lo stesso indirizzo
e lo stesso numero di turno (l'ora al minuto non basta: due messaggi nello stesso minuto si
confonderebbero). La data e l'ora si scrivono con il fuso (`2026-10-09T17:46:00+02:00`).

```
archivio-chat.jsonl  {"quando": "…", "chat": "https://…", "turno": 12, "testo": "…", "origine": "copiato dall'archivio della chat da Claude"}
diario-chat.jsonl    {"quando": "…", "chat": "https://…", "turno": 13, "testo": "…", "origine": "copiato dall'archivio della chat da Claude"}
```

Lo strumento che rilegge la chat scrive `<`, `>` e `&` come `&lt;`, `&gt;` e `&amp;`. Claude copia il
testo così com'è; il programma, prima di tutto il resto e con una regola fissa, riporta `&lt;` a `<`,
`&gt;` a `>` e infine `&amp;` a `&` (in quest'ordine, così `&amp;lt;` diventa `&lt;`). Vale per i
messaggi dell'utente e per le risposte di Claude. Limite: un `&lt;` scritto davvero diventa `<`.

Dai messaggi dell'utente si tolgono, con una regola fissa, gli avvisi tecnici dell'app: ogni blocco
da `<system-reminder>` a `</system-reminder>`, poi gli spazi e gli a capo rimasti all'inizio e alla
fine. Si fa prima di controllare il prefisso privato. Un segno di avviso senza la sua coppia ferma
la copia con un errore. Le risposte di Claude restano come sono.

I messaggi che cominciano con il prefisso privato diventano `"privato": "messaggio privato, non
copiato"`, e la risposta che li segue `"privato": "risposta a un messaggio privato, non copiata"` (la risposta segue il messaggio
dell'utente con il numero di turno più alto, non più alto del suo).
Nelle risposte i blocchi di codice sono sostituiti dalla loro impronta se `ometti_codice = true`.
Lo sportello cerca il testo delle note dell'utente nell'archivio con le stesse regole del testimone;
se non lo trova la nota resta non verificata, non viene rifiutata.

## Le versioni

Ogni cambiamento di una nota (`corrects`, `updates`, `done`, `reopens`) è una **versione nuova**: lo
sportello scrive un file nuovo, `note/<numero>.<versione>.md`, e una riga nel registro
(`ACCETTATA | nota 0049.1`). I file di prima non cambiano mai. La versione nuova contiene tutto:
l'intestazione e il testo dell'ultima versione, copiati e con il cambiamento applicato, la riga
`- status: closed` se è chiusa, e in fondo il blocco del cambiamento:

```markdown
# Note 0006.1

- date: 2026-01-10
- source: chat del 10 gennaio 2026
- author: user
- knowledge: stated
- kind: todo
- priority: high
- remind: 2026-01-20
- verification: author not verified (witness off)

## Text

Seminare il basilico.

## Change

- date: 2026-01-15
- source: chat del 15 gennaio 2026
- author: user
- knowledge: stated
- change: priority normal → high
- verification: author not verified (witness off)

### Reason

Il basilico è urgente, sta finendo la stagione buona.
```

- `change` elenca che cosa cambia, separato da `; `: `text corrected`, `kind todo → decision`,
  `priority normal → high`, `remind 2026-01-20` (oppure `remind 2026-01-20 → 2026-01-25`),
  `who → Anna` (oppure `who Anna → Anna, Marco`), `about → orto`, `closed`, `reopened`.
- `### Reason` è il motivo: il `text` della proposta, cioè le parole di chi ha chiesto il cambiamento
  (verificate dal testimone come ogni nota dell'utente). In una correzione del testo non c'è: le
  parole nuove sono il testo stesso, e l'intestazione (data, fonte, autore, knowledge, verifica)
  diventa quella della correzione.
- Dalla 0.7.0, in un `updates`, `done` o `reopens` dell'utente, dopo `### Reason` può esserci
  `### Context written by Claude`: la spiegazione di Claude, tenuta a parte dalle parole dell'utente.
  Il testo e il contesto di una proposta non possono contenere quella riga.
- Una nota di Claude può avere nel blocco anche `quote`, le parole dell'utente su cui si basa.
- Si cambia sempre l'**ultima** versione; un rimando a una versione vecchia è rifiutato.
- Il numero delle note nuove è il primo numero intero dopo il più alto: le versioni non contano e
  i buchi non si riempiono.

Il blocco `## Change` si legge solo nei file con il punto: una nota vecchia che ha quella riga nel
testo resta com'è.

## Il codice della nota

Ogni nota si mostra con un codice: la lettera della natura della sua **ultima** versione davanti al
numero, e un segno davanti se è chiusa.

| Lettera | Natura |
|---|---|
| F | fatto (`fact`) |
| I | idea (`idea`) |
| D | decisione (`decision`) |
| O | aperta (`open`) |
| T | da fare (`todo`) |
| ✓ | chiusa (davanti alla lettera) |

Per esempio `T0049.2` (una cosa da fare, alla versione 2) e `✓T0049.3` (chiusa). La lettera si mostra
soltanto: non fa parte del numero, e in un rimando di una proposta si scrive solo il numero
(`"0049"`): un rimando con la lettera è rifiutato con un motivo che dice come scriverlo. Chi ha un
terminale che non mostra `✓` può scegliere un altro segno nella sezione facoltativa `[codici]`
(`chiusa = "x"` dà `xT0049.3`). Il recap, la ricerca e la revisione finiscono con la legenda
`Legenda: F fatto · I idea · D decisione · O aperta · T da fare · ✓ chiusa`.

## Le note di prima delle versioni

Le note salvate prima della 0.6.0 non si riscrivono: si leggono con le stesse regole delle versioni.

- Una nota vecchia con `corrects: X` è la versione successiva della nota X, e si mostra con il suo
  numero vero accanto: `T0001.1 (nota 0002)`. Il suo testo e la sua natura valgono da lì in poi (una
  vecchia correzione che cambiava natura conta come cambio di natura); priorità e `remind` valgono se
  ce li ha, altrimenti restano quelli di prima.
- Una nota vecchia con `done` è la versione **chiusa** di ogni nota che chiude (una volta sola per
  nota, anche se ne chiude anche la correzione), con il suo testo come motivo. La natura chiusa è la
  sua se è `decision`, `fact` o `idea`; altrimenti resta quella di prima.
- Se la nota vecchia che chiude è essa stessa un `todo` o un promemoria, se conferma un'idea
  (`confirms`) o se un'altra nota la corregge, resta **anche** una nota a sé: così non si perde.
- **Le regole di oggi valgono anche per le catene vecchie.** Una nota vecchia che oggi non sarebbe
  permessa resta nella storia, ma non cambia ciò che oggi non avrebbe il permesso di cambiare:
  - se Claude correggeva il testo di una nota dell'utente, il testo che vale resta quello dell'utente;
  - se Claude faceva smettere un `open` di essere `open` (lo chiudeva, o lo correggeva con un'altra
    natura), l'`open` resta `open`;
  - vale lo stesso per gli altri cambi di natura non permessi (regola 12).

  La storia dice che cosa non vale: «non applicato (catena vecchia non permessa oggi): …», e la
  revisione la segnala. Nessuna regola nuova fa sparire qualcosa dell'utente per mano di Claude.
- Le versioni vecchie di una nota sono numerate per numero di nota, prima delle versioni nuove.
- Due note vecchie che correggono (o chiudono) la stessa versione formano un **ramo**: vale la più
  recente, e la revisione lo segnala. Con le note nuove non può succedere.
- Il numero vecchio vale nei rimandi come la versione che è diventata (`0002` = `0001.1`).

Esempio: la 0001 è un `todo`, la 0002 la corregge, la 0003 (un `fact`) chiude con `done: 0001, 0002`.
È una storia sola: `T0001`, `T0001.1 (nota 0002)`, `✓F0001.2 (nota 0003)`. Il recap non la mostra;
`search terriccio --all` la mostra una volta, con la sua storia.

## La ricerca

Il cercatore (`search`) trova una nota se la parola è in una qualunque delle sue versioni: nel testo,
nel contesto scritto da Claude o nel motivo di un cambiamento. Di ogni nota mostra l'ultima versione
intera e poi la sua storia, una riga per versione dalla più vecchia: codice, data, chi, che cosa è
cambiato e il motivo (per una correzione del testo, anche la prima riga del testo di prima; per una
chiusura e una riapertura «chiusa il …, perché «…»» e «riaperta il …, perché «…»»). Sotto la nota, rientrate di quattro spazi, compaiono le note
che la confermano (`confirms`); una nota che conferma un'altra dice com'è quella nota oggi, anche se è
chiusa o se la conferma riguarda una versione vecchia («conferma di: nota I0005.1 (nota 0008),
versione vecchia: l'ultima è I0005.2»). Una nota già comparsa più sopra si indica con una riga sola.

Le note trovate vanno dalla più recente alla più vecchia, cioè dal numero più alto: è l'ordine in
cui sono entrate nel quaderno, non il campo `date`. Le note chiuse non si mostrano, tranne le
decisioni (vedi «Chiudere e riaprire»): l'uscita dice quante sono state nascoste («1 nota chiusa non mostrata: aggiungi --all per
vederla.»), e `search <parola> --all` (o `--tutte`) le mostra, con la loro storia.

La ricerca è per parola esatta, senza distinzione di maiuscole; una parola è delimitata da
qualunque segno che non sia una lettera o una cifra, compresi il trattino basso, il punto, il
trattino e la barra: `orto` trova `orto_balcone.py`. Il diario segue la stessa regola.

## Chiudere e riaprire

Chiusa e aperta sono **stati** di una nota, non note a parte.

- `done` chiude un `open`, un `todo` o un promemoria (una nota con `remind`): crea la versione chiusa
  di ogni nota indicata, con lo stesso motivo (`text`). Il `kind` facoltativo dice che cosa è
  diventata la questione (`decision`, `fact` o `idea`); se manca, la natura resta.
- `reopens` riapre una nota chiusa: crea una versione aperta, con il motivo. Se `kind` manca, torna
  la natura di prima della chiusura.
- Un `open` lo chiude e lo riapre solo l'utente (`author: user`); `todo` e promemoria li possono
  chiudere e riaprire anche Claude.
- `fact`, `decision` e `idea` senza `remind` non si chiudono: si correggono (`corrects`), si
  cambiano (`updates`), e le idee si confermano (`confirms`).

Il recap e la ricerca leggono ogni nota per quello che è **adesso**, cioè la sua ultima versione. Si
nascondono solo le note chiuse che non sono decisioni: le cose da fare o da decidere ormai risolte
(`todo`, `open` e promemoria chiusi, anche diventati fatti o idee); `search --all` le mostra. Una
questione chiusa come decisione **è una decisione**: compare in «Ultime decisioni» e nella ricerca,
con il suo codice (`✓D0049.3`). Il ✓ dice che la questione è risolta, non che va nascosta.

## La priorità

`priority` (`high`, `normal`, `low`) è facoltativa e solo dell'utente. Vale la priorità dell'ultima
versione; si cambia con `updates`. Senza priorità vale `normal`. Il recap la usa per l'ordine,
dentro ogni blocco.

## I promemoria

Un promemoria è una nota con `remind`; vale la data dell'ultima versione (si sposta con `updates`).
Il comando `reminders` mostra quelli scaduti: la data è uguale o precedente a oggi (la data del
computer) e l'ultima versione non è chiusa. Vanno dal più vecchio al più recente; a parità di data
decide il numero della nota.

## Il recap

Il comando `recap` («dove eravamo rimasti») mostra, con regole fisse, una riga per nota (codice
dell'ultima versione, priorità `[alta]` o `[bassa]` se c'è, data dell'ultima versione, prima riga del
testo, con `…` se il testo continua) e sotto, con `↳`, una riga per ogni versione dopo la prima, **dalla
più recente alla più vecchia**, come il quaderno (che cosa è cambiato; per una chiusura e una
riapertura anche il motivo), e le conferme. Vale l'ultima versione di ogni nota, per quello che è
adesso: le note chiuse non compaiono, tranne le decisioni (una questione chiusa come decisione compare
in «Ultime decisioni», con `✓`).

1. i promemoria scaduti, tutti;
2. gli ultimi discorsi aperti (`kind: open`);
3. le ultime cose da fare (`kind: todo`);
4. le ultime decisioni;
5. le ultime voci del diario, nell'ordine in cui sono state dette, con la prima riga del testo.

Nei blocchi 1-4 vengono prima le note a priorità alta, poi le normali, poi le basse. A parità di
priorità, i promemoria dal più vecchio (per data del promemoria, poi per numero). Il resto, dalla
0.7.0, dal **giorno dell'ultima versione** più recente, senza contare le versioni che cambiano solo le
etichette, e a parità di giorno dal numero di nota più alto (prima della 0.7.0: solo per numero di
nota). La data sulla riga è quella dello stesso giorno. In fondo c'è la legenda dei codici.

Quante voci mostrare per i blocchi 2, 3, 4 e 5 si regola nella sezione facoltativa `[recap]`
(`discorsi_aperti`, `todo`, `decisioni`, numeri interi maggiori di zero; `voci_diario`, zero o più:
con 0, dalla 0.7.0, il blocco del diario non compare). Se la sezione o un'impostazione mancano
valgono 5, 5, 5 e 10. Se le voci sono di più, il recap dice quante non ha mostrato.

Con un filtro per etichette (`--who`/`--chi`, `--about`/`--cosa`, vedi «Le etichette») i blocchi 1-4
hanno solo le note con tutte quelle etichette, la prima riga lo dice, e al posto del diario c'è
«Ultime voci del diario: non mostrate (il diario non ha etichette).». Ogni riga di una nota con
etichette finisce con ` · chi: … · cosa: …`.

## Le etichette

Dalla 0.7.0 una nota può avere fino a due etichette CHI (`who`: persone) e fino a due COSA (`about`:
progetti o argomenti) proposte a mano. L'intestazione le mostra dopo la priorità: `- who: Anna, Marco`,
`- about: orto`.

**Dalla 0.8.0 lo sportello aggiunge da solo le COSA trovate nel testo.**
- Per ogni etichetta di `cosa`, nell'ordine della lista, cerca nel `text` della nota (non in `context`
  né in `quote`) la parola intera, con la regola di `search`: una parola finisce dove c'è un segno che
  non è una lettera o una cifra (spazio, punteggiatura, apostrofo, trattino, trattino basso, punto,
  barra); maiuscole e minuscole non contano; gli accenti sì; tra le parole di un'etichetta va bene
  qualsiasi spazio o a capo.
- Ogni etichetta trovata si aggiunge scritta come nella lista, una volta sola, senza limite di numero.
- `about` è l'elenco finale: prima quelle proposte a mano, poi quelle trovate, senza doppioni. La riga
  `- labels from text: about orto, gioco` (dopo `about`) elenca quelle messe dallo sportello e non
  proposte a mano. Una copia della 0.7.0 salta la riga e legge `about` come sempre.
- A ogni versione nuova (`corrects`, `updates`, `done`, `reopens`) le COSA dello sportello si
  ricalcolano dal testo della versione, con la lista di adesso: seguono il testo. Quelle proposte a mano
  non si toccano (le cambia solo `updates`). Le CHI non si cercano mai nel testo. Il tipo (`kind`) non si
  tocca.
- Il permesso «Claude può mettere etichette a una nota dell'utente solo se non ne ha» conta solo quelle
  proposte a mano.
- **Dalla 0.9.0 le COSA dal testo si calcolano anche al momento della lettura** (recap, search, labels, matches,
  review, patterns), per tutte le versioni di tutte le note, anche quelle scritte prima: quelle proposte a mano più
  quelle trovate oggi nel testo con la lista di oggi. Un'etichetta aggiunta alla lista vale subito per tutte le note
  che la nominano; nessun file si scrive (niente versioni di sole etichette). Se `etichette.toml` è scritto male, i
  comandi che leggono vanno avanti senza le COSA dal testo, con una prima riga «Attenzione: etichette.toml è scritto
  male (…)»; lo sportello invece si ferma, come nella 0.8.0.
- **`matches`** (`riscontri`), in sola lettura: per ogni COSA messa dallo sportello, una riga con il
  codice della nota, l'etichetta e il pezzo di frase dove l'ha trovata (fino a 4 parole prima e dopo,
  la parola tra `[ ]`); per ogni COSA proposta a mano che nel testo non c'è, una riga «a mano, non nel
  testo». Ordine fisso: per etichetta (nell'ordine della lista, poi quelle fuori lista in ordine
  alfabetico), poi per numero di nota. `--about`/`--cosa` per una sola etichetta.

- **La lista** è il file `etichette.toml` nella cartella del quaderno, scritto dall'utente (Claude non
  lo scrive mai; un modello commentato è `esempi/etichette.toml`):
  `chi = ["Anna", "Marco"]` e `cosa = ["orto", "bilancio"]`, liste di testi su una riga, senza virgole,
  senza spazi all'inizio o alla fine, senza doppioni. Lo leggono tutte le configurazioni dello stesso
  quaderno. Si legge solo quando serve (una proposta con etichette, un filtro, `labels`); se è scritto
  male il comando si ferma con un errore e non scrive niente, nemmeno nel registro. `check` lo ignora.
- **Senza il file**, nessuna nota può avere etichette: «there are no labels in this notebook…».
- Dalla 0.8.0 il file si legge a **ogni** proposta (per le COSA dal testo): se è scritto male lo
  sportello non salva niente finché non è corretto. `status` ha la riga «Etichette: …» che dice se è
  letto bene, senza fermarsi.
- **Regole dello sportello:** ogni etichetta dev'essere nella lista, uguale lettera per lettera; al
  massimo due per campo; nessuna ripetuta, nessuna vuota. Le etichette si cambiano solo con `updates`
  (non con `corrects`, `done`, `reopens`); le versioni le copiano.
- **Chi le cambia:** l'utente sempre; Claude sulle sue note sempre; Claude su una nota dell'utente solo
  se non ha ancora etichette («only the user can change the labels of one of the user's notes once they
  are set»).
- **Una versione che cambia solo le etichette** non conta per l'ordine del recap e per i giorni della
  revisione.
- **Filtri:** `search` e `recap` accettano `--who` (`--chi`) e `--about` (`--cosa`), anche più volte:
  devono valere tutti, sull'ultima versione. Con un filtro `search` può fare a meno della parola.
  Un'etichetta che non è nella lista e che nessuna nota usa è un errore (codice 2).
- **`labels`** (`etichette`): per ogni etichetta della lista quante note la hanno (ultima versione) e
  quante sono aperte (open, todo e promemoria non chiusi); per le COSA anche quante dal testo e quante
  proposte (dalla 0.8.0); poi le etichette usate in qualche nota ma non più nella lista.

## Gli schemi del modo di parlare (dalla 0.9.0)

Il comando `patterns` (`schemi`), in sola lettura, ricava dal quaderno le sequenze di parole tipiche di ogni tipo di
nota, con le regole fisse dello script del 21/10/2026 (decisione D0210), scritte in un posto solo (`hypomnema/schemi.py`):

- si guardano solo le note dell'utente, ognuna con la sua prima versione (tipo e testo di quando è nata); le note di
  Claude non contano;
- il testo si porta in minuscolo e si spezza in parole fatte di lettere (anche à è é ì ò ù) e apostrofi; di ogni nota
  si prendono le sequenze di 2 e 3 parole consecutive, ognuna una volta sola;
- una sequenza è tipica di un tipo se compare in almeno 2 note di quel tipo e almeno il 60% delle note in cui compare
  è di quel tipo, e non è una coppia «vuota»: una parola grammaticale (di, a, e, il, la, lo, le, i, che, per, in, un,
  una, non, è, da, con, su) seguita da una parola, o una parola seguita da una di quelle (tranne non, è);
- il tipo che suona un testo è quello con più sequenze tipiche; a parità vale l'ordine decision, idea, todo, open,
  fact; con nessuna, nessuno.

Gli schemi si ricalcolano dal quaderno ogni volta: nessun file salvato. `patterns` mostra le 12 più frequenti per tipo
(`--all` tutte, a parità in ordine alfabetico); `--measure` (`--misura`) dice quante volte gli schemi indovinano il
tipo delle note dell'utente, sulle stesse note (ottimista) e a turno (ogni nota tolta dal calcolo prima di indovinarla:
il numero onesto).

**Il suggerimento dello sportello.** Per una nota nuova dell'utente (non per i cambiamenti), se un altro tipo ha più
sequenze tipiche del tipo proposto (gli schemi del quaderno di prima della proposta), `propose` stampa in fondo una
riga «SUGGERIMENTO (non cambia niente): suona come una decisione (decision: «d'ora in poi»). È giusto il tipo idea? …».
A parità niente. Il suggerimento non entra nella nota né nel registro, non cambia il codice di uscita e non blocca.

## La revisione

Il comando `review` (o `revisione`) dice che cosa conviene guardare nel quaderno. È solo lettura:
ogni riga ha il codice della nota e dice che cosa si può fare, senza farlo. Esce con 0 se non trova
niente, con 1 se c'è qualcosa da guardare. Le regole sono fisse:

1. **ramo**: due o più note vecchie correggono (o chiudono) la stessa versione;
2. **ferma**: un `open` o un `todo` aperto la cui ultima versione è più vecchia di N giorni (sezione
   facoltativa `[revisione]`, `giorni`, di base 30);
3. **promemoria scaduto** e ancora aperto;
4. **nominata**: il numero di un `open` o `todo` aperto (anche con la lettera o la versione, non
   dentro una data come `2026-01-15`) compare nel testo, nel contesto o nel motivo di una nota venuta
   dopo: forse dice che è fatta;
5. **senza data**: un `open` o `todo` aperto senza `remind` che nel testo ha «ricordamelo»,
   «ricordami», «remind me», «tra (o fra) … giorni/giorno/settimane/settimana/mesi/mese» oppure
   «in … days/day/weeks/week»;
6. **catena vecchia non permessa oggi**: una nota vecchia cambiava ciò che oggi non avrebbe il
   permesso di cambiare (vedi «Le note di prima delle versioni»): resta nella storia ma non vale, e la
   riga dice con quale proposta l'utente può fare il cambiamento, se lo vuole.

Il programma non capisce il senso delle parole: non sa se una nota dice «è fatta» o «è superata», e
non legge le date scritte a parole. Per questo segnala soltanto, e decide l'utente.

## Da idea a decisione

Un'idea resta un'idea. Quando l'utente la conferma esplicitamente, si propone una **nuova** nota:
`kind: decision`, `author: user`, `knowledge: stated`, `confirms: <numero dell'idea>`
e come `text` le parole esatte con cui l'utente conferma (eventuali spiegazioni in `context`).
L'idea originale non viene toccata: il quaderno conserva sia l'idea sia la decisione.

## La nota salvata nel quaderno

Ogni nota nuova accettata riceve il numero successivo (`0001`, `0002`, ...) e diventa un file
`note/<numero>.md`, leggibile da una persona (le versioni sono i file con il punto, vedi «Le
versioni»):

```markdown
# Note 0002

- date: 2026-01-15T10:05
- source: chat del 15 gennaio 2026 sul progetto dell'orto
- author: user
- knowledge: stated
- kind: decision
- confirms: 0001
- verification: text found in the message of 2026-01-15T10:04:30+01:00

## Text

sì, da domani annaffio la mattina presto

## Context written by Claude

Conferma dell'idea 0001: annaffiare la mattina presto invece che la sera.
```

La sezione "Context written by Claude" compare solo se la nota ha un `context`. I campi
d'intestazione hanno quest'ordine: `date`, `source`, `author`, `knowledge`, `kind`, `status`, `priority`,
`who`, `about`, `confirms`, `corrects`, `done`, `remind`, `quote`, `from_reply`, `verification`; quelli facoltativi
compaiono solo se presenti.

Le note salvate prima della 0.5.0 hanno il formato italiano (`# Nota 0002`, `- data:`, `- fonte:`,
`- autore: utente`, `- tipo: dichiarata`, `- natura: decisione`, `## Testo`,
`## Contesto scritto da Claude`, `- verifica: …`): il programma le legge come prima, con i valori
portati all'inglese (`utente` → `user`, `discorso aperto` → `open`, …), e non le riscrive mai.

Il file si crea una volta sola: il programma non sovrascrive mai una nota esistente.

## Date e ore: il fuso orario

Le date e le ore che scrive il programma (righe del registro, data delle versioni, file dei testimoni)
e il giorno di «oggi» (recap, promemoria, revisione) seguono questa regola (dalla 0.7.0; decisione di
Angelo: il fuso del taccuino viene dal sistema operativo dell'utente):

1. **Sul computer dell'utente** vale sempre l'ora del sistema operativo, anche se la configurazione
   ha la riga `fuso` (`[quaderno]`, facoltativa, dalla 0.6.1). Se la riga dice un fuso diverso dal
   sistema, `status` lo segnala, ma non blocca.
2. Il computer dell'utente legge il **nome** del fuso del sistema e lo aggiunge in fondo al file
   `fuso-del-sistema.jsonl` del quaderno quando è diverso dall'ultima riga (o il file manca), a inizio
   sessione (`start`) e a ogni proposta. Una riga per volta, solo in aggiunta, con una sola scrittura:
   `{"quando": "2026-10-20T09:12:00+02:00", "fuso": "Europe/Rome", "dal_sistema": "Windows: W. Europe
   Standard Time, regione IT"}`. Vale l'ultima riga valida; le righe rovinate si saltano. Una
   configurazione per la chat non lo scrive mai. Il file non è una nota: `check` lo ignora.
3. **Su una macchina in UTC** (la chat collegata al computer, le sessioni in cloud) vale, in
   quest'ordine: la riga `fuso` della configurazione; l'ultima riga del file del quaderno; UTC. Un fuso
   che su quella macchina non si trova (nome sbagliato, tabella dei fusi mancante) si salta.

**Macchina in UTC**, regola fissa: il nome del fuso del sistema è `UTC`, `Etc/UTC`, `Etc/Universal`,
`Universal`, `Zulu`, `Etc/Zulu`, `UCT`, `GMT`, `Etc/GMT` (e le sue forme `+0`, `-0`, `0`) o `Greenwich`;
oppure il nome non si legge e la differenza dall'ora universale è zero. Ogni altro nome è il computer
dell'utente.

**Il nome del fuso del sistema** si legge, su Windows, dal registro (`TimeZoneKeyName` e la regione in
`Control Panel\International\Geo\Name`) e si traduce con la tabella ufficiale di Unicode CLDR
(`hypomnema/_cldr/windowsZones.xml`, copia non modificata): «W. Europe Standard Time» con la regione `IT`
è `Europe/Rome`, senza regione `Europe/Berlin` (stesse ore). Su macOS e Linux: la variabile `TZ`, poi
dove punta `/etc/localtime`, poi `/etc/timezone`.

`status` dice sempre quale fuso vale, su una riga: «Fuso orario: Europe/Rome, dal sistema operativo
(…).», «Fuso orario: Europe/Rome, dal file fuso-del-sistema.jsonl del quaderno (scritto il … dal
computer dell'utente): questa macchina è in UTC.», «Fuso orario: Europe/Zurich, scritto nella
configurazione: questa macchina è in UTC.» oppure «Fuso orario: UTC, quello di questa macchina: …» con il
motivo.

## Il registro degli ingressi

Il file `registro.md` del quaderno riceve una riga per ogni passaggio dallo sportello,
accettato o rifiutato. Si apre solo in aggiunta.

```
- 2026-01-15T10:00:00+01:00 | ACCETTATA | nota 0001 | da: 1-idea.json
- 2026-01-15T10:01:00+01:00 | RIFIUTATA | da: nota.json | motivi: the field «source» is missing: every note must say where it comes from.
- 2026-01-15T10:02:00+01:00 | ACCETTATA | nota 0001.1 | da: 2-chiusura.json
```

Una versione ha la sua riga come una nota; una chiusura di più note (`done: 0012, 0015`) ha una riga
per ogni versione chiusa.

L'ora è quella del computer al momento del passaggio. `da:` è il nome del file proposto,
oppure `(ingresso diretto)` se la nota arriva dall'ingresso standard.
Se il registro esiste e non finisce con un "a capo" (qualcuno l'ha toccato a mano), lo sportello
non scrive niente, né la nota né la riga, e risponde con un errore: la sua riga si attaccherebbe a
quella scritta a mano. Non ripara il registro da solo. `check` mostra le righe che non hanno la
forma di una riga dello sportello, con il loro numero.

**Un passaggio alla volta (dalla 0.6.1).** Sullo stesso quaderno possono scrivere insieme Claude
Code (con il plugin) e la chat collegata al computer. Per tutto il passaggio (lettura del quaderno,
regole, nota, riga del registro) lo sportello tiene il blocco del sistema operativo su un file vuoto;
lo stesso fa il comando `archive`. Dalla 0.7.0 il file sta nella cartella temporanea del computer,
`<cartella temporanea>/hypomnema-blocchi/<impronta del percorso del quaderno>.lock`, e non più nel
quaderno; il `.sportello.lock` lasciato nel quaderno dalla 0.6.1 non si usa più, il programma non lo
tocca e `snapshot` e `changed` continuano a saltarlo (si può cancellare a mano o mettere nel
`.gitignore`). I comandi che
leggono aspettano che il passaggio finisca, al massimo 10 secondi, poi leggono lo stesso: un passaggio
fermo a metà non ferma mai la lettura. Il file del blocco non lo legge nessun comando (su Windows il
blocco è obbligatorio, e chi leggesse la parte bloccata riceverebbe un errore). Il file si crea vuoto alla prima scrittura e non si
cancella mai; il blocco lo toglie il sistema alla fine del passaggio, anche se il programma si
interrompe. Se il quaderno è occupato per più di 10 secondi lo sportello si ferma con «ERRORE: il
quaderno è occupato da un altro passaggio…» senza scrivere niente. Se il disco non permette i
blocchi si va avanti senza: la nota si crea comunque con apertura esclusiva (mai sovrascritta) e
`check` segnala ogni nota senza la sua riga.

**Tra due macchine il blocco non passa** (provato il 18/10/2026 tra Windows e la macchina Linux della
chat). Restano l'apertura esclusiva delle note e delle versioni, la riga del registro aggiunta con una
sola scrittura in aggiunta (anche quelle dei testimoni e dell'archivio; su Windows con il solo
permesso di aggiungere, così è il sistema a scrivere in fondo), la rilettura per un attimo di una nota
appena creata e non ancora scritta, e `check` dopo ogni proposta in chat. Un registro nuovo nasce con
apertura esclusiva, così l'intestazione si scrive una volta sola. `snapshot` e `changed` non contano il file del blocco.

**Sempre gli stessi byte.** Note, versioni, registro e file dei testimoni e dell'archivio si
scrivono sempre in UTF-8 con l'a capo `\n`, scelti in modo esplicito: su Windows, su Linux e su
macOS lo stesso passaggio dà lo stesso file, byte per byte. Lo stesso vale per l'uscita a schermo dei
comandi.

Ogni passaggio occupa sempre una sola riga: se il nome del file o un motivo contengono un
"a capo" (per esempio un nome di campo inventato), al suo posto viene scritto il segno ⏎.
Lo stesso vale per i motivi di rifiuto mostrati a schermo: ogni motivo sta su una riga.

## Le regole del quaderno

Tutte le regole, in un posto solo. Per ognuna: che cosa dice, chi può usarla, che effetto ha, un
esempio giusto (✔) e uno sbagliato (✘). Gli esempi sono inventati. Le regole segnate con «(Claude)»
il programma non le può controllare, perché servirebbe capire il senso delle parole: le segue
Claude, e la revisione (`review`) ne controlla solo la parte che ha un segno fisso.

### 1. Ogni cambiamento è una versione; si cambia sempre l'ultima

- **Dice:** correzione del testo, cambio di natura, priorità, promemoria, chiusura e riapertura
  creano una versione nuova della nota (`0049.1.md`); niente si riscrive. Si cambia sempre l'ultima
  versione.
- **Chi:** l'utente e Claude, con i limiti delle regole 9-12.
- **Effetto:** lo sportello scrive il file della versione e la sua riga nel registro; un rimando a una
  versione vecchia è rifiutato, e il motivo dice qual è l'ultima.
- ✔ `{"updates": "0049", "priority": "high", "text": "È urgente.", …}` → `0049.1`.
- ✘ `{"corrects": "0049.1", …}` quando l'ultima è `0049.2` → rifiutata: «the last is T0049.2».

### 2. La correzione non chiude

- **Dice:** correggere una nota (`corrects`) cambia il suo testo, non il suo stato: una cosa da fare
  corretta resta da fare, una questione aperta corretta resta aperta.
- **Chi:** chi può correggere quel testo (regola 11).
- **Effetto:** la versione nuova ha lo stesso stato (aperta o chiusa) di prima.
- ✔ «Non il terriccio per agrumi: quello universale.» → `corrects: 0001`, la `T0001.1` resta da fare.
- ✘ Usare `corrects` con il testo «Comprato» per dire che è fatta: per chiudere c'è `done`.

### 3. «Ricordamelo», «tra tre giorni» → `remind` con la data (Claude)

- **Dice:** quando l'utente chiede di ricordargli una cosa, la nota ha il campo `remind` con il giorno
  (Claude lo calcola dalla data della chat: «tra tre giorni» il 15/01 → `2026-01-18`).
- **Chi:** l'utente e Claude.
- **Effetto:** il promemoria compare nel recap e in `reminders` quando arriva la data. La revisione
  segnala gli `open` e i `todo` con queste parole nel testo ma senza `remind`.
- ✔ «Ricordamelo tra tre giorni: travasare il limone.» → `kind: todo`, `remind: 2026-01-18`.
- ✘ La stessa nota senza `remind`: non tornerà mai da sola.

### 4. «Ricordati questa cosa» è un fatto, non una questione aperta (Claude)

- **Dice:** un'informazione da tenere a mente (un programma, un indirizzo, un numero) è un `fact`.
- **Chi:** l'utente e Claude.
- **Effetto:** la nota si trova con la ricerca, ma non resta nel recap come questione da chiudere.
- ✔ «Ricordati: il vivaio è in via dei Tigli 4.» → `kind: fact`.
- ✘ La stessa frase come `kind: open`: resterebbe aperta per sempre.

### 5. `open` è una domanda, `todo` è una cosa da fare (Claude)

- **Dice:** `open` = una domanda o una cosa ancora da decidere; `todo` = una cosa decisa che resta da
  fare.
- **Chi:** l'utente e Claude.
- **Effetto:** il recap li mostra in due blocchi diversi («Discorsi aperti» e «Cose da fare»).
- ✔ «Dove mettiamo la compostiera?» → `open`; «Montare la compostiera.» → `todo`.
- ✘ «Montare la compostiera.» come `open`.

### 6. Una nota = una cosa sola (Claude)

- **Dice:** ogni nota dice una cosa; due cose diventano due note.
- **Chi:** l'utente e Claude.
- **Effetto:** si possono correggere, chiudere e ritrovare una per una.
- ✔ «Il fico va potato a marzo.» e «Il limone va rinvasato.» in due note.
- ✘ «Il fico va potato a marzo e il limone va rinvasato.» in una nota sola: chiudere una delle due
  chiuderebbe anche l'altra.

### 7. Le parole dell'utente si copiano, mai a memoria (Claude)

- **Dice:** il `text` di una nota dell'utente è copiato dal suo messaggio (in chat, dall'archivio
  della chat), mai riscritto a memoria; un messaggio dettato a voce resta con i suoi errori di
  trascrizione.
- **Chi:** Claude, per le note dell'utente.
- **Effetto:** il testimone (o l'archivio) trova le parole e la nota è verificata (o riscontrata).
- ✔ Il messaggio dettato dice «il fico va potato a marzo e non a febraio» → `text` identico, con
  «febraio».
- ✘ Correggere in «febbraio» o riassumere: il testimone non lo trova e la nota è rifiutata (le
  spiegazioni di Claude vanno in `context`).

### 8. La fonte dice in che chat è nata la nota, non di che cosa parla (Claude)

- **Dice:** `source` dice da dove viene la nota (quale chat, quale libro).
- **Chi:** l'utente e Claude.
- **Effetto:** si può risalire alla conversazione.
- ✔ `"source": "chat del 15 gennaio 2026"`.
- ✘ `"source": "il fico"`.

### 9. Chiudere: chi chiude che cosa

- **Dice:** `done` chiude `open`, `todo` e promemoria. Un `open` lo chiude solo l'utente; `todo` e
  promemoria anche Claude. Fatti, decisioni e idee senza `remind` non si chiudono.
- **Chi:** come detto.
- **Effetto:** versione chiusa (`✓`), con il motivo; sparisce dal recap, tranne se è diventata una
  decisione (allora compare in «Ultime decisioni», con `✓D`).
- ✔ Claude: `{"done": "0006", "kind": "fact", "text": "Seminato oggi in tre vasi.", …}` → `✓F0006.2`.
- ✘ Claude chiude un `open` → rifiutata: «only the user can close an open note».

### 10. Riaprire

- **Dice:** `reopens` riapre una nota chiusa, con il motivo; un `open` lo riapre solo l'utente.
- **Chi:** l'utente; Claude per `todo` e promemoria.
- **Effetto:** versione aperta che dice «riaperta il …, perché «…»»; torna nel recap.
- ✔ `{"reopens": "0006", "text": "Le piantine sono morte col gelo.", …}` → `T0006.3`.
- ✘ `reopens` su una nota non chiusa → rifiutata.

### 11. Correggere il testo: chi

- **Dice:** il testo di una nota dell'utente sono le sue parole: lo corregge solo l'utente. Claude
  corregge le sue note; se l'utente corregge una nota di Claude, il testo nuovo è suo.
- **Chi:** come detto.
- **Effetto:** l'intestazione della versione descrive il testo nuovo (chi, quando, verifica).
- ✔ L'utente: «No, il rubinetto perde dalla guarnizione.» → `corrects: 0007`.
- ✘ Claude corregge da solo la `F0007` dell'utente → rifiutata.

### 12. Cambiare la natura: chi

- **Dice:** diventare `decision`, smettere di essere `open` e ogni cambio di natura di una nota
  dell'utente li decide solo l'utente; un'idea diventa decisione solo con `confirms`.
- **Chi:** come detto; Claude può cambiare la natura delle sue note (per esempio un'idea che diventa
  una cosa da fare).
- **Effetto:** versione nuova con la lettera nuova (`O0004` → `T0004.1`).
- ✔ L'utente: `{"updates": "0004", "kind": "todo", "text": "Ho deciso il posto, ora va solo montata."}`.
- ✘ Claude: `{"updates": "0004", "kind": "decision", …}` → rifiutata.

### 13. La priorità è dell'utente

- **Dice:** `priority` (`high`, `normal`, `low`) la mette e la cambia solo l'utente.
- **Chi:** l'utente; Claude può proporla nel testo di una sua idea.
- **Effetto:** il recap mostra prima le note a priorità alta.
- ✔ `{"updates": "0006", "priority": "high", "text": "Il basilico è urgente."}` dell'utente.
- ✘ Una nota di Claude con `priority` → rifiutata.

### 14. Le decisioni sono dell'utente

- **Dice:** una decisione la prende l'utente, con parole sue (`knowledge: stated`).
- **Chi:** l'utente.
- **Effetto:** una nota di Claude non può essere una decisione; una sua idea resta idea finché
  l'utente non la conferma (`confirms`, nota nuova).
- ✔ L'utente: «Sì, la compostiera va sotto il fico.» → `decision`, `confirms: 0005`.
- ✘ Claude salva «Abbiamo deciso: sotto il fico.» come `decision` → rifiutata.

### 15. Come si sa: `knowledge`

- **Dice:** `stated` = detto esplicitamente; `observed` = visto; `inferred` = ricavato ragionando.
  L'incerto resta incerto.
- **Chi:** l'utente e Claude.
- **Effetto:** chi legge sa quanto fidarsi.
- ✔ Claude deduce che il vaso è troppo piccolo → `inferred`.
- ✘ La stessa deduzione come `stated`.

### 16. Il codice della nota; nei rimandi solo il numero

- **Dice:** ogni nota si mostra con la lettera della sua natura e `✓` se è chiusa (`✓T0049.3`); nei
  rimandi si scrive solo il numero.
- **Chi:** tutti.
- **Effetto:** un rimando con la lettera è rifiutato con il modo giusto di scriverlo.
- ✔ `"done": "0049"`.
- ✘ `"done": "T0049"` → rifiutata: «write only the number».

### 17. Testo e contesto separati; la citazione nelle note di Claude

- **Dice:** in una nota dell'utente `text` sono le sue parole e `context` le aggiunte di Claude; in
  una nota di Claude le parole dell'utente vanno in `quote`.
- **Chi:** l'utente e Claude.
- **Effetto:** parole dell'utente e di Claude non si mescolano mai.
- ✔ `text`: «annaffio alle sei», `context`: «Parlava dell'orto sul balcone.»
- ✘ `text`: «L'utente annaffia alle sei.» in una nota dell'utente.

### 18. Testo incollato e segno `>`

- **Dice:** un testo incollato dall'utente conta come suo; da dove viene lo dice `source`. Le righe che
  iniziano con `>` sono parole riportate da altri.
- **Chi:** l'utente.
- **Effetto:** una nota presa tutta da righe con `>` porta la dicitura «quote reported by the user».
- ✔ Un passo di un libro incollato con `>` e `source`: «dal libro …».
- ✘ Lo stesso passo con `source` «chat del 15 gennaio».

### 19. I messaggi privati non si citano

- **Dice:** un messaggio che inizia con `#privato` non viene registrato e non si può citare.
- **Chi:** l'utente decide; Claude rispetta.
- **Effetto:** una nota con quelle parole è rifiutata (il testimone non le trova).
- ✔ Nessuna nota dal messaggio privato.
- ✘ Salvare le parole di un messaggio privato.

### 20. Il diario non è il quaderno

- **Dice:** il diario è la conversazione registrata; il quaderno sono le note scelte. Una cosa trovata
  solo nel diario non è una decisione.
- **Chi:** Claude, quando risponde «cosa ci eravamo detti».
- **Effetto:** dal diario si può proporre una nota, che passa dallo sportello come le altre.
- ✔ «Nel diario del 10 gennaio avevi scritto…: vuoi che lo salvi?»
- ✘ «Avevamo deciso…» citando solo il diario.

### 21. I pezzi delle risposte di Claude: `from_reply`

- **Dice:** per salvare un pezzo di una risposta di Claude si usa `from_reply: yes`, con il testo
  copiato identico dalla risposta.
- **Chi:** Claude, quando l'utente lo chiede.
- **Effetto:** con il testimone delle risposte acceso, lo sportello cerca il testo nelle risposte.
- ✔ «Salva questa risposta» → nota di Claude con `from_reply: yes`.
- ✘ Un riassunto della risposta con `from_reply`.

### 22. La data è quando la cosa è stata detta (Claude)

- **Dice:** `date` è il giorno (e l'ora) in cui la cosa è stata detta o vista, non quello del
  salvataggio.
- **Chi:** l'utente e Claude.
- **Effetto:** le note restano in ordine di tempo anche se salvate dopo.
- ✔ Una cosa detta il 10 gennaio, salvata il 15 → `date: 2026-01-10`.
- ✘ `date: 2026-01-15`.

### 23. Claude non scrive mai nei file del quaderno

- **Dice:** tutto entra dallo sportello (`propose`); Claude non modifica mai i file del quaderno.
- **Chi:** Claude.
- **Effetto:** ogni ingresso ha la sua riga nel registro; nel plugin la protezione ferma gli strumenti
  di Claude sul quaderno.
- ✔ `propose proposta.json`.
- ✘ Aprire `note/0049.md` e cambiarlo a mano.

### 24. La nota-regola

- **Dice:** quando le regole del quaderno cambiano, l'utente salva una decisione «Da questa nota in
  poi…».
- **Chi:** l'utente.
- **Effetto:** chi rilegge il quaderno sa da quando vale la regola nuova.
- ✔ «Da questa nota in poi le spese dell'orto vanno nelle note con la parola "spesa".» → `decision`.
- ✘ Cambiare abitudine senza dirlo: le note vecchie e le nuove non si capiscono più.

### 25. Le etichette vengono dalla lista dell'utente (dalla 0.7.0)

- **Dice:** CHI e COSA si scelgono solo dalla lista di `etichette.toml`, che scrive l'utente. Le COSA
  scritte nel testo le mette lo sportello (dalla 0.8.0); a mano si propongono le CHI e le COSA che nel
  testo non ci sono, al massimo due per campo. Claude sceglie le etichette delle sue note e propone
  quelle delle note dell'utente, dicendole all'utente. Una volta messe a mano, le etichette di una nota
  dell'utente le cambia solo l'utente.
- **Chi:** lo sportello controlla lista, numero e permessi e trova le COSA nel testo; Claude sceglie
  bene le altre (questo il programma non lo può controllare).
- **Effetto:** si legge il quaderno per persona o per progetto (`search --about`, `recap --cosa`,
  `labels`).
- ✔ `"about": "orto"` per «sabato semino il basilico», con `orto` nella lista; niente `about` per
  «sabato semino l'orto»: lo trova lo sportello.
- ✘ Scrivere `etichette.toml` al posto dell'utente; `"about": "Orto"` se la lista dice `orto`; usare
  un'etichetta per dire da quale chat viene la nota (quello è `source`).
