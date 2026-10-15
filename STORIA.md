# Storia delle versioni

Le versioni pubblicate su GitHub, dalla più recente. Ogni versione dice cosa cambia per chi usa
Hypomnema e come aggiornarsi.

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
