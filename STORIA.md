# Storia delle versioni

Le versioni pubblicate su GitHub, dalla più recente. Ogni versione dice cosa cambia per chi usa
Hypomnema e come aggiornarsi.

## 0.6.0 (prototipo) — versioni e regole

*Da pubblicare: il testo qui sotto è la nota di rilascio proposta.*

- **Ogni cambiamento è una versione nuova.** Correggere il testo, cambiare natura, priorità o data
  del promemoria, chiudere e riaprire non creano più una nota nuova che rimanda alla vecchia: creano
  la versione successiva della stessa nota (`0049.1`, `0049.2`…). Ogni versione è un file vero
  (`note/0049.1.md`) con tutta la nota e in fondo un blocco «Change»: quando, chi, che cosa e perché
  (con le tue parole, se il cambiamento è tuo). Ogni versione ha la sua riga nel registro; i file di
  prima non si toccano mai. Si cambia sempre l'ultima versione.
- **Due campi nuovi** per le proposte: `updates` (in italiano `aggiorna`) cambia natura, priorità o
  promemoria senza toccare il testo; `reopens` (`riapre`) riapre una nota chiusa. `corrects` ora
  corregge il testo, `done` chiude (anche più note: una versione chiusa per ciascuna).
- **Nessuna chiusura definitiva.** Chiusa e aperta sono stati: una nota chiusa si riapre, con il
  motivo («riaperta il …, perché …»). Una correzione non chiude.
- **Il codice della nota.** Ogni nota si mostra con la lettera della sua natura davanti al numero:
  F fatto, I idea, D decisione, O aperta, T da fare, e ✓ se è chiusa (`✓T0049.3`). Il recap finisce
  con la legenda. Se il terminale non mostra ✓, si può scegliere un altro segno (`[codici]`,
  `chiusa = "x"`).
- **Le note di prima si leggono come versioni**, senza riscriverle: una vecchia correzione compare
  come `0049.1 (nota 0050)`, una vecchia chiusura come versione chiusa. Le note con i campi italiani
  si mostrano come le nuove.
- **Il comando `review` (`revisione`)**, solo lettura: segnala le questioni ferme da più di 30 giorni,
  i promemoria scaduti, le cose da fare nominate in una nota successiva, «ricordamelo» senza data e
  i rami delle note vecchie. Dice che cosa si può fare, non lo fa. Claude lo lancia a inizio chat,
  dopo il recap. Nel plugin c'è anche `/hypomnema:review`.
- **Tutte le regole scritte.** FORMATO.md ha una sezione «Le regole del quaderno»: 24 regole, ognuna
  con chi può usarla, che effetto ha e un esempio giusto e uno sbagliato.

Il quaderno e la configurazione che hai funzionano senza modifiche (le sezioni `[revisione]` e
`[codici]` sono facoltative).

**Aggiornare il plugin in Claude Code:**

```
claude plugin marketplace update hypomnema
claude plugin update hypomnema@hypomnema
```

La nuova versione vale dalla sessione successiva (o dopo `/reload-plugins`).

**Nella chat di claude.ai:** scarica il nuovo `hypomnema-skill.zip` e caricalo tra le skill nelle
impostazioni di Claude, sostituendo quello vecchio.

## 0.5.0 (prototipo) — lingua per ruolo e chiusure

*Da pubblicare: il testo qui sotto è la nota di rilascio proposta.*

- **Lingua per ruolo.** L'italiano resta per il contenuto (le tue parole nelle note, i messaggi che
  leggi, il README); la struttura passa all'inglese: comandi (`search`, `propose`, `recap`,
  `reminders`, `status`, `check`, `diary`…), campi delle note (`date`, `source`, `author`,
  `knowledge`, `kind`, `text`, `context`, `quote`, `confirms`, `corrects`, `remind`, `done`,
  `from_reply`), motivi di rifiuto dello sportello e istruzioni della skill per Claude. **I nomi
  italiani funzionano per sempre** (`cerca`, `autore: utente`, `/hypomnema:pausa`…). Le note che hai
  già non si convertono e non si toccano: il programma legge tutte e due le forme; le note nuove si
  scrivono in inglese, con diciture come «author not verified (witness off)».
- **Che cos'è una nota.** Il campo `kind` ha cinque valori: `fact`, `idea`, `decision`, `open`
  (prima «discorso aperto») e il nuovo `todo`.
- **Chiudere questioni aperte e cose da fare.** Una nota nuova con `done: <numero>` (anche più numeri:
  `done: 0012, 0015`) chiude un `open`, un `todo` o un promemoria; il testo è il motivo e il `kind`
  dice che cosa è diventata la questione. Gli `open` li chiudi solo tu; una nota si chiude una volta
  sola. Il recap e la ricerca non mostrano più le note chiuse (`search --all` sì); il recap ha un
  blocco nuovo, «Cose da fare».
- **Priorità.** Campo facoltativo `priority: high | normal | low`, solo tuo; si cambia con una nota
  che ha `corrects`. Il recap mostra prima le cose a priorità alta.
- **La nota-regola.** Quando cambiano le regole del quaderno, salvi una decisione che dice «Da
  questa nota in poi…»: il README e la skill spiegano come.
- Nuovi comandi del plugin `/hypomnema:pause` e `/hypomnema:resume` (restano `/hypomnema:pausa` e
  `/hypomnema:riprendi`).

Il quaderno e la configurazione che hai funzionano senza modifiche (la sezione `[recap]` accetta
in più `todo`, facoltativo).

**Aggiornare il plugin in Claude Code:**

```
claude plugin marketplace update hypomnema
claude plugin update hypomnema@hypomnema
```

La nuova versione vale dalla sessione successiva (o dopo `/reload-plugins`).

**Nella chat di claude.ai:** scarica il nuovo `hypomnema-skill.zip` e caricalo tra le skill nelle
impostazioni di Claude, sostituendo quello vecchio.

## 0.4.0 (prototipo) — rifiniture nate dall'uso

*Da pubblicare: il testo qui sotto è la nota di rilascio proposta.*

Le rifiniture vengono da una prova vera del 15 ottobre 2026: due chat nuove con le stesse
domande, una con il quaderno e una senza. Nessuna risposta inventata e il quaderno più preciso,
ma con alcuni difetti. Questa versione li corregge.

- **Le correzioni viaggiano insieme alla nota.** Nuovo campo facoltativo `corregge: <numero>`. Il
  cercatore mostra sempre, subito sotto una nota, le note che la correggono, la confermano o la
  segnano come fatta, anche se non contengono la parola cercata, e anche a catena. Così Claude non
  ripete un errore che una correzione aveva già sistemato.
- **Prima le note più recenti.** Il cercatore mostra le note dalla più recente alla più vecchia.
- **Parole composte.** Cercando `orto` si trova anche `orto_balcone.py`: le parole si spezzano anche
  su trattino basso, punto, trattino e barra. Vale anche per il diario.
- **Promemoria.** Nuovo campo facoltativo `riprendere_il: AAAA-MM-GG` e nuovo comando `promemoria`,
  che elenca i promemoria arrivati o scaduti, dal più vecchio. Un promemoria si chiude con una nota
  che ha `done: <numero>` («era giusto ed è fatto»); una correzione lo lascia aperto, e se ha una sua
  data vale quella.
- **«Dove eravamo rimasti» in un comando solo.** Nuovo comando `recap` (nel plugin anche
  `/hypomnema:recap`): promemoria scaduti, discorsi aperti, ultime decisioni e ultime righe del
  diario, scelti con regole fisse. Claude lo lancia a inizio chat invece di scegliere da solo le
  parole da cercare. Quante voci mostrare si regola nella sezione facoltativa `[recap]`.
- **Modalità chat.** Le note trovate sull'archivio della chat si chiamano sempre «riscontrate», mai
  «verificate». Le cartelle per riportare i file hanno un nome con data e ora
  (`riporto-20261015-1243-a`), che non si ripete nelle chat lunghe. Il programma `archivio` converte
  `&lt;`, `&gt;` e `&amp;` nei segni veri, e riconosce anche gli avvisi tecnici scritti così: Claude
  copia il testo così com'è, senza convertire niente.

Tutti i campi nuovi sono facoltativi: i quaderni e le configurazioni di prima funzionano senza
modifiche.

**Aggiornare il plugin in Claude Code:**

```
claude plugin marketplace update hypomnema
claude plugin update hypomnema@hypomnema
```

La nuova versione vale dalla sessione successiva (o dopo `/reload-plugins`).

**Nella chat di claude.ai:** scarica il nuovo `hypomnema-skill.zip` e caricalo tra le skill nelle
impostazioni di Claude, sostituendo quello vecchio.

## 0.3.0 (prototipo) — 11 ottobre 2026

Nella chat di claude.ai Claude rilegge la conversazione dall'archivio delle chat e la copia nel
quaderno: le note dell'utente il cui testo si trova lì sono «riscontrate sull'archivio della chat»,
con l'indirizzo della chat. All'inizio di una chat nuova Claude dice in tre righe dove eravate
rimasti.

Per la chat: scarica `hypomnema-skill.zip`, caricalo tra le skill nelle impostazioni di Claude
(sostituendo quello vecchio), attiva il permesso per cercare e consultare le chat passate, apri una
chat e scrivi «Usiamo Hypomnema».

## 0.2.0 (prototipo) — 11 ottobre 2026

Hypomnema diventa un plugin di Claude Code.

```
claude plugin marketplace add angelomaccarinelli8-sys/hypomnema
claude plugin install hypomnema@hypomnema
```

Ogni sessione ha la skill e i testimoni; configurazione e quaderno in `~/Hypomnema`. Pausa con
`/hypomnema:pausa`, ripresa con `/hypomnema:riprendi`.

Nella chat di claude.ai: scarica `hypomnema-skill.zip`, caricalo tra le skill nelle impostazioni di
Claude, apri una chat e scrivi «Usiamo Hypomnema».

## 0.1.0 (prototipo) — 11 ottobre 2026

Prima versione del prototipo. Per provarlo: scarica `hypomnema-skill.zip`, caricalo tra le skill
nelle impostazioni di Claude, apri una chat e scrivi «Usiamo Hypomnema». Con l'app desktop collegata
al computer il quaderno resta salvato; senza, è una prova che sparisce a fine chat.
