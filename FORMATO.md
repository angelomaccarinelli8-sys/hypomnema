# Formato delle note

Dalla versione 0.5.0 la struttura è in inglese (nomi dei campi, valori, motivi di rifiuto) e il
contenuto resta nella sua lingua. I nomi e i valori italiani delle versioni precedenti valgono per
sempre, nelle proposte e nelle note già salvate: vedi «Nomi italiani» in fondo a questa sezione.

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
| `kind` | sì | `fact`, `idea`, `decision`, `open`, `todo` | Che cosa è: un fatto, un'idea, una decisione, una questione aperta, una cosa da fare. |
| `text` | sì | testo, anche su più righe | Con `author: user`: **le parole esatte dell'utente**, copiate da un suo messaggio. Con `author: claude`: le parole di Claude. |
| `context` | no; **solo** con `author: user` | testo, anche su più righe | Ciò che Claude aggiunge alle parole dell'utente (spiegazioni, di cosa si parlava). Mostrato come "Context written by Claude". |
| `quote` | no; **solo** con `author: claude` | testo, anche su più righe | Le parole esatte dell'utente su cui Claude basa la sua nota. |
| `confirms` | no | numero di una nota esistente, per esempio `"0001"` | Solo per una decisione che conferma un'idea già nel quaderno. |
| `corrects` | no | numero di una nota esistente, per esempio `"0007"` | Questa nota corregge quella indicata («era sbagliata»). La nota vecchia resta; il cercatore la mostra sempre con la sua correzione. |
| `remind` | no | solo il giorno: `AAAA-MM-GG` | Promemoria: il giorno in cui riprendere la nota. Il comando `reminders` elenca quelli arrivati o passati. |
| `done` | no | uno o più numeri di note esistenti, separati da virgole: `"0012"` oppure `"0012, 0015"` | Questa nota chiude le note indicate: questioni aperte (`open`), cose da fare (`todo`) o promemoria (con `remind`). Vedi «Chiudere». |
| `priority` | no; **solo** con `author: user` | `high`, `normal`, `low` | La priorità; senza, vale `normal`. Si cambia con una nota nuova che ha `corrects` e la priorità nuova. |
| `from_reply` | no; **solo** con `author: claude`, mai insieme a `quote` | `"yes"` | Il `text` è un pezzo di una risposta di Claude («Salva questa risposta di Claude»). Con il testimone delle risposte acceso, lo sportello lo cerca nelle risposte registrate. |

Le parole dell'utente e quelle di Claude non stanno mai nello stesso campo: in una nota
dell'utente sono `text` (utente) e `context` (Claude); in una nota di Claude sono `text`
(Claude) e `quote` (utente).

I valori vanno scritti esattamente così, in minuscolo. Gli spazi all'inizio e alla fine vengono tolti.

**Nomi italiani.** Nelle proposte si possono usare anche i nomi e i valori di prima: `data`,
`fonte`, `autore` (`utente`), `tipo` (`dichiarata`, `osservata`, `dedotta`), `natura` (`fatto`,
`idea`, `decisione`, `discorso aperto`), `testo`, `contesto`, `citazione`, `conferma_di`,
`corregge`, `riprendere_il`, `da_risposta` (`sì`), `priorità` (`alta`, `normale`, `bassa`).
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
9. ha `confirms` ma non è una decisione, oppure la nota indicata non esiste, oppure non è un'idea;
10. il file non è JSON valido, non contiene una sola nota, o non è in UTF-8;
11. ha `author: user` e il campo `quote` (le sue parole vanno in `text`), oppure ha
    `author: claude` e il campo `context` (in una nota di Claude è tutto già di Claude);
12. `text` o `context` contengono la riga `## Context written by Claude` (o quella italiana
    `## Contesto scritto da Claude`), riservata al formato della nota;
13. con il testimone acceso, ha `author: user` e il `text` non si trova parola per parola in
    nessun messaggio registrato (vale anche per le decisioni, che sono sempre dell'utente);
14. con il testimone acceso, è una nota di Claude con una `quote` che non si trova parola
    per parola in nessun messaggio registrato;
15. ha `corrects` con il numero di una nota che non esiste;
16. ha `remind` con una data che non esiste o che non è solo un giorno (`AAAA-MM-GG`);
17. ha `done` scritto male (non numeri separati da virgole), con un numero ripetuto, con il numero
    di una nota che non esiste, o di una nota che non si può chiudere (un `fact`, una `decision` o
    un'`idea` senza `remind`: quelle si correggono con `corrects`, le idee si confermano con `confirms`);
18. chiude con `done` una nota `open` ma non ha `author: user` (le questioni aperte le chiude solo
    l'utente);
19. ha `done` ed è a sua volta una nota `open` (la nota che chiude dice che cosa è diventata la
    questione: `decision`, `todo`, `fact` o `idea`);
20. chiude con `done` una nota già chiusa: il motivo dice da quale nota è già chiusa;
21. ha `priority` ma `author: claude` (Claude può proporre una priorità solo nel testo di una sua idea).

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

## Note collegate: correzioni, conferme, chiusure

Tre campi collegano una nota a note precedenti: `corrects`, `confirms` e `done`. Il cercatore
(`search`) mostra, sotto ogni nota trovata e rientrate di quattro spazi, **tutte** le note collegate,
anche a catena (la correzione di una correzione), dalla più recente alla più vecchia, anche se non
contengono la parola cercata. Nella nota trovata compaiono le righe `corretta da: nota …`,
`confermata da: nota …` e `chiusa da: nota …`. Una nota collegata che è già comparsa
più sopra si indica con una riga sola: `(nota 0002, che corregge la nota 0001: già mostrata sopra)`.

Le note trovate vanno dalla più recente alla più vecchia, cioè dal numero più alto: è l'ordine in
cui sono entrate nel quaderno, non il campo `date`. Le note chiuse non si mostrano: l'uscita dice
quante sono state nascoste («1 nota chiusa non mostrata: aggiungi --all per vederla.»), e
`search <parola> --all` (o `--tutte`) le mostra, con sotto la nota che le ha chiuse.

La ricerca è per parola esatta, senza distinzione di maiuscole; una parola è delimitata da
qualunque segno che non sia una lettera o una cifra, compresi il trattino basso, il punto, il
trattino e la barra: `orto` trova `orto_balcone.py`. Il diario segue la stessa regola.

## Chiudere: questioni aperte, cose da fare, promemoria

Una nota `open`, `todo` o con `remind` resta aperta finché una **nota nuova** non la chiude con
`done`. Le regole (vedi anche «Le regole dello sportello», 17-20):

- `done` elenca uno o più numeri, separati da virgole;
- il `text` della nota che chiude è il motivo; il suo `kind` dice che cosa è diventata la questione
  (`decision`, `todo`, `fact` o `idea`, mai `open`);
- un `open` lo chiude solo l'utente (`author: user`); `todo` e promemoria li può chiudere anche Claude;
- una nota si chiude una volta sola;
- `fact`, `decision` e `idea` senza `remind` non si chiudono: si correggono (`corrects`), e le idee
  si confermano (`confirms`);
- una questione chiusa che ritorna è un `open` nuovo, senza campi speciali.

Le note chiuse non compaiono nel recap né nella ricerca di base (`search --all` le mostra).

## La priorità

`priority` (`high`, `normal`, `low`) è facoltativa e solo dell'utente. Vale la priorità della nota
o, se la nota è stata corretta (`corrects`, anche a catena), quella della correzione più recente che
ne ha una; senza priorità vale `normal`. Il recap la usa per l'ordine, dentro ogni blocco.

## I promemoria

Un promemoria è una nota con `remind`. Insieme alle sue correzioni (`corrects`, anche a
catena) forma un gruppo, che il comando `reminders` mostra una volta sola, sotto la prima nota:

- vale la data della nota **più recente** del gruppo che ha un suo `remind`: una correzione
  senza data lascia il promemoria com'era, una correzione con una data nuova lo sposta;
- se una nota chiude (`done`) una nota del gruppo, il promemoria non è più tra gli scaduti;
- sono scaduti i promemoria con la data uguale o precedente a oggi (la data del computer), dal più
  vecchio al più recente; a parità di data decide il numero della nota.

## Il recap

Il comando `recap` («dove eravamo rimasti») mostra, con regole fisse, una riga per nota (numero,
priorità `[alta]` o `[bassa]` se c'è, data, prima riga del testo, con `…` se il testo continua) e
sotto, con `↳`, le note collegate. Le note chiuse non compaiono.

1. i promemoria scaduti, tutti;
2. gli ultimi discorsi aperti (`kind: open`);
3. le ultime cose da fare (`kind: todo`);
4. le ultime decisioni;
5. le ultime voci del diario, nell'ordine in cui sono state dette, con la prima riga del testo.

Nei blocchi 1-4 vengono prima le note a priorità alta, poi le normali, poi le basse; a parità di
priorità, i promemoria dal più vecchio e il resto dal più recente.

Quante voci mostrare per i blocchi 2, 3, 4 e 5 si regola nella sezione facoltativa `[recap]`
(`discorsi_aperti`, `todo`, `decisioni`, `voci_diario`, numeri interi maggiori di zero). Se la
sezione o un'impostazione mancano valgono 5, 5, 5 e 10. Se le voci sono di più, il recap dice quante
non ha mostrato.

## Da idea a decisione

Un'idea resta un'idea. Quando l'utente la conferma esplicitamente, si propone una **nuova** nota:
`kind: decision`, `author: user`, `knowledge: stated`, `confirms: <numero dell'idea>`
e come `text` le parole esatte con cui l'utente conferma (eventuali spiegazioni in `context`).
L'idea originale non viene toccata: il quaderno conserva sia l'idea sia la decisione.

## La nota salvata nel quaderno

Ogni nota accettata riceve il numero successivo (`0001`, `0002`, ...) e diventa un file
`note/<numero>.md`, leggibile da una persona:

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
d'intestazione hanno quest'ordine: `date`, `source`, `author`, `knowledge`, `kind`, `priority`,
`confirms`, `corrects`, `done`, `remind`, `quote`, `from_reply`, `verification`; quelli facoltativi
compaiono solo se presenti.

Le note salvate prima della 0.5.0 hanno il formato italiano (`# Nota 0002`, `- data:`, `- fonte:`,
`- autore: utente`, `- tipo: dichiarata`, `- natura: decisione`, `## Testo`,
`## Contesto scritto da Claude`, `- verifica: …`): il programma le legge come prima, con i valori
portati all'inglese (`utente` → `user`, `discorso aperto` → `open`, …), e non le riscrive mai.

Il file si crea una volta sola: il programma non sovrascrive mai una nota esistente.

## Il registro degli ingressi

Il file `registro.md` del quaderno riceve una riga per ogni passaggio dallo sportello,
accettato o rifiutato. Si apre solo in aggiunta.

```
- 2026-01-15T10:00:00+01:00 | ACCETTATA | nota 0001 | da: 1-idea.json
- 2026-01-15T10:01:00+01:00 | RIFIUTATA | da: nota.json | motivi: the field «source» is missing: every note must say where it comes from.
```

L'ora è quella del computer al momento del passaggio. `da:` è il nome del file proposto,
oppure `(ingresso diretto)` se la nota arriva dall'ingresso standard.
Se il registro esiste e non finisce con un "a capo" (qualcuno l'ha toccato a mano), lo sportello
non scrive niente, né la nota né la riga, e risponde con un errore: la sua riga si attaccherebbe a
quella scritta a mano. Non ripara il registro da solo. `check` mostra le righe che non hanno la
forma di una riga dello sportello, con il loro numero.

Ogni passaggio occupa sempre una sola riga: se il nome del file o un motivo contengono un
"a capo" (per esempio un nome di campo inventato), al suo posto viene scritto il segno ⏎.
Lo stesso vale per i motivi di rifiuto mostrati a schermo: ogni motivo sta su una riga.
