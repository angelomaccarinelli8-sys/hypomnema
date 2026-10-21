# Storia delle versioni

Le versioni pubblicate su GitHub, dalla più recente. Ogni versione dice cosa cambia per chi usa
Hypomnema e come aggiornarsi.

## 0.10.0 (prototipo) — l'albero delle etichette e la regola dell'integrazione

*Da pubblicare: il testo qui sotto è la nota di rilascio proposta.*

- **Rami e sotto-rami** (I0213). Nel file `etichette.toml` una COSA può avere dei sotto-rami, gli argomenti, ognuno con
  le sue parole: una tabella `[rami.orto]` con le righe `pomodori = ["pomodori", "pomodoro"]`. Conta solo la lista di
  parole, non il nome; una nota prende un sotto-ramo solo se ha già la COSA del ramo. I sotto-rami si calcolano quando
  si legge, anche per le note di prima. Un file senza `[rami…]` funziona come prima.
- **Il comando `tree`** (`albero`), in sola lettura: ramo → sotto-rami → note, con le catene di integrazione su una riga
  sola (`I0005.2 ← I0002 ← I0001`) e la voce «senza argomento» per le note del ramo che nessun sotto-ramo prende: lì
  mancano parole. `--cosa orto` per un ramo solo, `--all` anche per le note chiuse e annullate.

Le note già scritte non si toccano e il quaderno della 0.9.0 si legge come prima. Aggiorna tutte e due le copie del
programma (plugin di Claude Code e `programma-chat`).

```
claude plugin marketplace update hypomnema
claude plugin update hypomnema@hypomnema
```

e su Windows, nella cartella Hypomnema: `git -C programma-chat pull`.

**Nella chat di claude.ai:** scarica il nuovo `hypomnema-skill.zip` e caricalo tra le skill nelle impostazioni di
Claude, sostituendo quello vecchio.

## 0.9.0 (prototipo) — gli schemi del modo di parlare e il riordino del taccuino

*Da pubblicare: il testo qui sotto è la nota di rilascio proposta.*

- **Gli schemi del tuo modo di parlare** (D0210). Il comando nuovo `patterns` (`schemi`), in sola lettura, ricava dal
  quaderno le sequenze di 2 e 3 parole tipiche di ogni tipo di nota (decisione, idea, da fare, aperta, fatto), con
  regole fisse: solo le tue note, almeno 2 note di quel tipo, almeno il 60% delle volte in quel tipo, senza le coppie
  vuote come «di casa». Gli schemi si ricalcolano ogni volta: crescono con il taccuino. `patterns --misura` dice
  quante volte indovinano il tipo, sulle stesse note e «a turno» (il numero onesto).
- **Un suggerimento allo sportello.** Quando salvi una nota tua e il testo suona come un altro tipo («d'ora in poi» in
  un'idea), `propose` aggiunge una riga «SUGGERIMENTO (non cambia niente)». Non blocca e non cambia niente: il tipo lo
  scegli tu.
- **Etichette retroattive** (I0201). Le COSA trovate nel testo valgono per tutte le note, anche quelle scritte prima:
  si calcolano quando si leggono. Se aggiungi un'etichetta alla lista, tutte le note che la nominano la prendono
  subito, senza scrivere niente.
- **Integrare una nota** (I0202), con `integrates` (`integra`): aggiungere parole nuove in fondo a una nota, oppure
  mettere in fondo a una nota il testo di un'altra sulla stessa cosa (`from_note`, `da_nota`). Il testo di prima resta
  intatto; la nota integrata esce dal recap ma resta nel quaderno e nella ricerca con `--all`.
- **Annullare una nota** (I0168), con `cancels` (`annulla`): una nota che non vale più, anche un'idea o una decisione,
  diversa da «fatto». Il codice prende una C davanti: `CD0156.1`. Si fa valere di nuovo con `reopens`.
- **La revisione propone le sistemazioni** (I0167). `review` segnala anche le note integrabili (stesso autore, una COSA
  in comune, una nomina l'altra, anche di tipo diverso), e `review --proposte` stampa le proposte pronte: le completi
  con le tue parole e le passi allo sportello una alla volta, se le vuoi.
- **Il grafo del taccuino** (I0204). `graph grafo.html` scrive una pagina, fuori dal quaderno, con le note colorate per
  tipo, le etichette e i rimandi tra le note.

Le note già scritte non si toccano e il quaderno della 0.8.0 si legge come prima. Aggiorna tutte e due le copie del
programma (plugin di Claude Code e `programma-chat`).

```
claude plugin marketplace update hypomnema
claude plugin update hypomnema@hypomnema
```

e su Windows, nella cartella Hypomnema: `git -C programma-chat pull`.

**Nella chat di claude.ai:** scarica il nuovo `hypomnema-skill.zip` e caricalo tra le skill nelle impostazioni di
Claude, sostituendo quello vecchio.

## 0.8.0 (prototipo) — le etichette COSA le mette lo sportello

*Da pubblicare: il testo qui sotto è la nota di rilascio proposta.*

- **Le COSA le trova lo sportello.** Quando una nota passa dallo sportello, lo sportello cerca nel suo
  testo le etichette della lista `cosa` di `etichette.toml` e aggiunge quelle che trova, scritte come
  nella lista, una volta sola e senza limite di numero. Cerca la parola intera, come `search`, senza
  badare alle maiuscole: «l'Orto» dà `orto`, «ortografia» no. Le etichette non si dimenticano più.
- **Si vede chi le ha messe.** Nella nota `about` ha tutte le COSA; la riga
  `- labels from text: about orto` dice quali ha messo lo sportello. Le altre sono state proposte a mano.
- **Seguono il testo.** A ogni versione nuova (una correzione, una chiusura…) lo sportello le ricalcola
  dal testo; quelle proposte a mano non le tocca mai.
- **Le CHI restano a mano**, al massimo due per nota, come nella 0.7.0.
- **`labels`** dice, per ogni COSA, quante note la hanno dal testo e quante a mano; **`status`** dice se
  `etichette.toml` è letto bene; il comando nuovo **`matches`** (`riscontri`) mostra, in sola lettura,
  dove lo sportello ha trovato ogni COSA, e le COSA messe a mano che nel testo non ci sono.
- **La regola è fissa e non capisce il senso**: «è in gioco la scadenza» dà `gioco`, «i bilanci» non dà
  `bilancio`. `matches` serve proprio a vedere questi casi.
- **Attenzione:** lo sportello legge `etichette.toml` a ogni proposta. Se il file è scritto male, non
  salva niente finché non è corretto (`status` lo dice).
- Il file delle etichette **non cambia**: quello della 0.7.0 va bene così com'è. Le note già scritte non
  si toccano; prendono le COSA dal testo solo alla loro prossima versione.

**Aggiorna tutte e due le copie del programma.** Il plugin di Claude Code e `programma-chat` leggono lo
stesso quaderno: una copia rimasta alla 0.7.0 non si ferma, ma non aggiunge le COSA dal testo.

```
claude plugin marketplace update hypomnema
claude plugin update hypomnema@hypomnema
```

e su Windows, nella cartella Hypomnema: `git -C programma-chat pull`.

**Nella chat di claude.ai:** scarica il nuovo `hypomnema-skill.zip` e caricalo tra le skill nelle
impostazioni di Claude, sostituendo quello vecchio.

## 0.7.0 (prototipo) — etichette, recap per data, difetti trovati da Code

*Da pubblicare: il testo qui sotto è la nota di rilascio proposta.*

- **Etichette CHI e COSA.** Una nota può avere fino a due etichette CHI (le persone: `who`) e fino a
  due COSA (i progetti o gli argomenti: `about`). La lista la scrivi tu, nel file `etichette.toml`
  dentro la cartella del quaderno: la leggono Claude Code e la chat, quindi è una sola. Un modello
  commentato è `esempi/etichette.toml`. Senza il file nessuna nota può avere etichette; un'etichetta
  fuori dalla lista viene rifiutata, con l'elenco di quelle ammesse. Claude non scrive mai il file:
  in un quaderno dove scrive solo lui te la propone nel messaggio, e tu la salvi.
- **Filtri e conteggi.** `search --about orto` (anche senza parola), `search basilico --who Anna
  --about orto`, `recap --cosa orto` (senza il diario, che non ha etichette) e il comando nuovo
  `labels` (`etichette`): ogni etichetta con quante note ha, e quante sono ancora aperte.
- **Le note vecchie non si toccano:** le etichette si aggiungono con una versione nuova (`updates`).
  Claude può etichettare una tua nota solo se non ne ha ancora; poi le cambi solo tu.
- **Il recap per data.** In ogni blocco, dopo la priorità, prima le note con l'ultima versione più
  recente: una nota vecchia corretta oggi sale in cima. Le versioni che mettono solo le etichette non
  contano. I promemoria scaduti restano in ordine di scadenza.
- **Il contesto nelle chiusure.** Nei tuoi `done`, `updates` e `reopens` Claude può aggiungere la sua
  spiegazione (`context`) accanto al tuo motivo, tenuta a parte come sempre.
- **Il fuso orario viene dal sistema operativo.** Sul tuo computer vale sempre l'ora del sistema, anche
  su Windows senza la tabella dei fusi e anche se la configurazione ha una riga `fuso` (`status` segnala
  se è diversa). Hypomnema scrive il nome del fuso del sistema nel file `fuso-del-sistema.jsonl` del
  quaderno quando cambia (su Windows con la tabella ufficiale CLDR, per avere `Europe/Rome`); la chat e
  le sessioni in cloud, che hanno l'orologio in UTC, lo leggono da lì. Il modello della chat non ha più
  la riga `fuso`. `status` dice sempre quale fuso vale e perché.
- **`voci_diario = 0`** nella sezione `[recap]` toglie il blocco del diario dal recap.
- **Il file del blocco non sta più nel quaderno** ma nella cartella temporanea del computer: niente
  più `.sportello.lock` che finisce in git. Quello lasciato dalla 0.6.1 non serve più: puoi
  cancellarlo a mano o metterlo nel `.gitignore`.
- **Una skill più corta:** `SKILL.md` ha le regole di sempre (meno di 450 righe); la chat, le
  etichette, le risposte di Claude e il diario stanno in quattro file accanto, che Claude legge solo
  quando servono.

I quaderni della 0.6.1 si leggono come prima e `check` resta pulito: niente da convertire.

**Aggiornare il plugin in Claude Code:**

```
claude plugin marketplace update hypomnema
claude plugin update hypomnema@hypomnema
```

**Chat collegata al computer:** `git -C programma-chat pull` su Windows, nella cartella Hypomnema.

**Nella chat di claude.ai:** scarica il nuovo `hypomnema-skill.zip` (ora con cinque file) e caricalo
tra le skill nelle impostazioni di Claude, sostituendo quello vecchio.

## 0.6.1 (prototipo) — la chat scrive direttamente sul quaderno

*Da pubblicare: il testo qui sotto è la nota di rilascio proposta.*

- **La chat collegata al computer scrive direttamente sul quaderno vero.** Con l'app desktop, la
  chat ha una riga di comando su una macchina Linux che vede la tua cartella Hypomnema: se lì trova
  il programma aggiornato, propone allo sportello del quaderno vero. Per salvare una nota basta un
  comando (due con la copia dall'archivio della chat), invece di otto-dieci; niente copia, niente
  riporto, niente confronto. Se qualcosa non va, Claude usa la procedura di prima.
- **Python 3.10.** Hypomnema funziona dal 3.10 (sulla macchina della chat c'è il 3.10): quando manca
  `tomllib`, usa la sua copia di tomli (licenza MIT). Niente da installare.
- **Una configurazione per la chat accanto a quella di Claude Code**: `hypomnema-chat.toml`, stesso
  quaderno, testimone spento. Il tuo `hypomnema.toml` non si tocca.
- **Due che scrivono insieme.** Sulla stessa macchina lo sportello tiene un blocco per ogni passaggio
  (il file vuoto `quaderno/.sportello.lock`, che non va cancellato). Tra Windows e la chat il blocco
  non passa: lì valgono l'apertura esclusiva delle note, le righe del registro aggiunte con una sola
  scrittura, la rilettura delle note appena create e il `check` che Claude fa dopo ogni proposta in
  chat. Prima, con due scrittori insieme, il registro poteva sporcarsi; ora no.
- **Il fuso orario.** La configurazione della chat ha `fuso = "Europe/Rome"`: anche se la macchina
  della chat ha l'orologio in UTC, «oggi» e le ore del registro sono quelli italiani. Se il fuso non
  si trova, il programma si ferma con un errore e non scrive niente. Nella configurazione di Claude
  Code non c'è: vale l'ora del computer.
- **Stessi byte su Windows e su Linux**: sempre UTF-8 e a capo `\n`, provato da una prova apposta.

**Una volta sola, su Windows** (PowerShell), per la chat collegata:

```powershell
cd $env:USERPROFILE\Hypomnema
git clone --branch main https://github.com/angelomaccarinelli8-sys/hypomnema.git programma-chat
```

Per aggiornarla: `git -C programma-chat pull`.

**Aggiornare il plugin in Claude Code:**

```
claude plugin marketplace update hypomnema
claude plugin update hypomnema@hypomnema
```

**Nella chat di claude.ai:** scarica il nuovo `hypomnema-skill.zip` e caricalo tra le skill nelle
impostazioni di Claude, sostituendo quello vecchio.

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
  si mostrano come le nuove. Le regole di oggi valgono anche per loro: una vecchia nota di Claude che
  correggeva il tuo testo, o che faceva smettere una questione aperta di essere aperta, resta nella
  storia ma non vale (il testo resta il tuo, l'open resta open), e la revisione la segnala.
- **Il recap legge ogni nota per quello che è adesso.** Si nascondono le cose da fare o da decidere
  ormai chiuse; una questione chiusa come decisione compare in «Ultime decisioni» con il suo ✓
  (`✓D0049.3`). Sotto ogni nota la storia va dalla più recente alla più vecchia, e la chiusura dice il
  suo motivo come la riapertura.
- **Il comando `review` (`revisione`)**, solo lettura: segnala le questioni ferme da più di 30 giorni,
  i promemoria scaduti, le cose da fare nominate in una nota successiva, «ricordamelo» senza data, i
  rami delle note vecchie e le catene vecchie non permesse oggi. Dice che cosa si può fare, non lo
  fa. Claude lo lancia a inizio chat, dopo il recap. Nel plugin c'è anche `/hypomnema:review`.
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
