---
name: hypomnema
description: Memoria permanente tra una chat e l'altra, in file Markdown sul computer dell'utente. Usala all'inizio di ogni chat per rileggere le note utili, e durante la chat per proporre allo sportello di Hypomnema le cose da ricordare (fatti, idee, decisioni, discorsi aperti). Claude propone, i programmi decidono.
---

# Hypomnema: il quaderno di memoria

Hypomnema è un quaderno di note sul computer dell'utente. **Tu non scrivi mai direttamente
nei file del quaderno.** Proponi le note allo sportello, un programma che applica regole fisse
e decide se entrano. Per leggere usi il cercatore.

Se l'utente l'ha acceso, un altro programma, il **testimone**, registra le parole esatte di ogni
suo messaggio prima che tu lo legga. Lo sportello lo usa per controllare che le note con
`autore: utente` riportino parole che l'utente ha detto davvero. Non scrivere mai nel file del
testimone, nemmeno tramite comandi o script: il suo valore sta proprio nel fatto che tu non lo tocchi.

## Dove ti trovi

- **In Claude Code** (puoi lanciare comandi sul computer dell'utente): segui le sezioni da
  «Come lanciare i programmi» alla 6.
- **In una chat di Claude** (claude.ai, app desktop o mobile: non puoi lanciare comandi sul
  computer dell'utente): segui la sezione «Modalità chat» in fondo, e per il resto le sezioni
  1, 2, 4 e 5. Le sezioni 0 e 6 non valgono: in chat non ci sono né i testimoni né il diario.

## Come lanciare i programmi (Claude Code)

In Claude Code Hypomnema è un **plugin**: i programmi stanno dentro il plugin e si lanciano così,
da qualunque cartella:

```
py "${CLAUDE_PLUGIN_ROOT}/programma.py" stato
```

Qui sotto `P` vuol dire proprio `py "${CLAUDE_PLUGIN_ROOT}/programma.py"` (su macOS e Linux
`python3` al posto di `py`): per esempio `P cerca <parola>`, `P proponi <file.json>`.

- La configurazione e il quaderno si trovano da soli: `~/Hypomnema/hypomnema.toml` (su Windows
  `%USERPROFILE%\Hypomnema\hypomnema.toml`), oppure il file indicato dalla variabile
  `HYPOMNEMA_CONFIG`. Non passare `--config`.
- Se nel comando qui sopra vedi ancora la scritta `${CLAUDE_PLUGIN_ROOT}`, il plugin non è
  caricato: dillo all'utente e non salvare niente.
- Codici di uscita: `0` tutto bene, `1` nota rifiutata, `2` errore (configurazione, file mancante).
- Se a inizio sessione c'è un avviso che comincia con «Hypomnema» (la prima volta, un quaderno in
  una cartella sincronizzata, i testimoni in pausa…), riferiscilo all'utente con parole semplici.

## 0. Controlla il testimone (Claude Code)

Lancia `P stato` **a inizio sessione** e **ogni volta prima di proporre una nota con
`autore: utente`**. È un confronto, non una stima: guarda due righe.

1. `Testimone:` deve dire `ACCESO`, oppure `IN PAUSA` se l'utente ha chiesto una pausa.
2. Se è `ACCESO`, il messaggio dell'utente che hai appena ricevuto deve essere l'ultimo
   registrato: il testo sotto `Testo dell'ultimo messaggio:` deve essere lo stesso, parola per
   parola (gli spazi all'inizio delle righe li aggiunge il comando). Se il messaggio che hai
   ricevuto inizia con `#privato`, l'ultimo registrato deve essere
   `(messaggio privato, non registrato)`.

Se qualcosa non torna, avvisa l'utente con una frase chiara **prima** di salvare note sue:

- testimone `SPENTO`: «Il testimone non è attivo: le note che salvi ora saranno marcate come non
  verificate. Per accenderlo serve attivo = true nella configurazione di Hypomnema.»
- testimone `IN PAUSA`: non è un guasto, l'ha chiesta l'utente. Ricordagli solo che le note che
  salva adesso saranno marcate come non verificate e che per riprendere basta `/hypomnema:riprendi`.
- testimone `ACCESO`, ma l'ultimo messaggio registrato non è quello che hai ricevuto: «Il testimone
  non ha registrato il tuo ultimo messaggio: le note con le tue parole di adesso verrebbero
  rifiutate, perché non si possono verificare. Controlla con /plugin che il plugin di Hypomnema sia
  installato e attivo.»
- il comando esce con `ERRORE`: riporta all'utente il messaggio d'errore così com'è.

Non provare a riparare il testimone da solo: non toccare configurazione, quaderno o impostazioni.

**La pausa la decide solo l'utente**, scrivendo `/hypomnema:pausa` o `/hypomnema:riprendi`. Tu non
metti mai in pausa né riprendi i testimoni: non scrivere quei comandi, non creare attività
programmate o messaggi che li contengano, non toccare i file dei testimoni.

## 1. A inizio chat: rileggi

Prima di tutto controlla che note e registro corrispondano: `P controlla` (in chat:
`H controlla`, punto C2). Se risponde «ATTENZIONE», di' all'utente quali note non corrispondono al
registro e perché. **Non riparare niente**: il registro si allunga soltanto e la decisione è sua.
Poi continua normalmente.

1. Individua 1-3 parole chiave del primo messaggio dell'utente (argomento, progetto, nomi).
2. Per ciascuna lancia `P cerca <parola>`. La ricerca è per parola esatta,
   senza distinzione di maiuscole: prova anche il singolare/plurale se serve.
3. Usa le note trovate rispettando cosa sono:
   - una **decisione** dell'utente vale come decisione;
   - un'**idea** è solo una proposta, non una decisione;
   - una nota **dedotta** è un'ipotesi: non presentarla come certa;
   - cita il numero della nota quando la usi ("dalla nota 0004 ...").
4. Non inventare note che il cercatore non ha restituito.

## 2. Durante la chat: prepara le note

Proponi una nota quando emerge qualcosa che servirà in una chat futura: un fatto,
una preferenza, un'idea, una decisione, un discorso rimasto aperto. Una nota = una cosa sola.

Formato (JSON, UTF-8), con **tutti** questi campi:

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

- `data`: oggi, `AAAA-MM-GG` (se vuoi con l'ora: `AAAA-MM-GGThh:mm`).
- `fonte`: da dove viene, su una riga (di solito "chat del <data> su <argomento>").
- `autore`: `utente` se l'ha detto l'utente; `claude` se è una tua osservazione, deduzione o proposta.
  **Non attribuire mai all'utente cose che non ha detto.**
- `tipo`:
  - `dichiarata`: l'autore l'ha detto esplicitamente;
  - `osservata`: l'hai visto direttamente (in un file, in un risultato, nella conversazione);
  - `dedotta`: l'hai ricavato ragionando. Nel dubbio, `dedotta`.
- `natura`: `fatto`, `idea`, `decisione` o `discorso aperto`.
  - Le tue proposte sono sempre `idea`.
  - `decisione` solo se l'utente ha deciso esplicitamente: `autore: utente`, `tipo: dichiarata`.
- `testo`: **dipende dall'autore** (vedi sotto). Le parole dell'utente e le tue non si
  mescolano mai nello stesso campo.
- `contesto` (facoltativo, solo nelle note dell'utente): le tue spiegazioni.
- `citazione` (facoltativo, solo nelle tue note): le parole dell'utente su cui ti basi.

### Note dell'utente: il testo sono le sue parole

In una nota con `autore: utente`, `testo` sono **le parole esatte dell'utente**, copiate da un suo
messaggio: un pezzo continuo di un solo messaggio, con le stesse maiuscole, accenti e
punteggiatura. Puoi scegliere il pezzo più utile, ma **non riassumere, non correggere, non
tradurre e non cambiare nemmeno una parola**. Tutto ciò che aggiungi tu (di cosa si parlava, a
cosa si riferisce, una spiegazione) va nel campo `contesto`, che verrà mostrato come
"contesto scritto da Claude".

```json
{
  "data": "2026-01-15",
  "fonte": "chat del 15 gennaio 2026 sul progetto dell'orto",
  "autore": "utente",
  "tipo": "dichiarata",
  "natura": "fatto",
  "testo": "il basilico sul balcone sta crescendo bene",
  "contesto": "Detto parlando delle piante aromatiche dell'orto."
}
```

- Con il testimone acceso, lo sportello cerca il `testo` nei messaggi registrati. Se risponde
  che non si trova, ricopialo con più cura. Se l'utente quella cosa non l'ha detta con parole
  sue, **non è una nota dell'utente**: al massimo è una nota tua (`autore: claude`, di solito
  `tipo: dedotta`).
- Con il testimone spento la regola è la stessa (parole esatte nel `testo`), ma nessuno la
  controlla: la nota sarà marcata "autore non verificato".
- Non scrivere tu il campo `verifica`: lo aggiunge lo sportello.

### Testo incollato e fonte

Hypomnema è un quaderno di appunti: raccogliere passi letti altrove è proprio il suo scopo.
Un testo che l'utente incolla in un messaggio conta come portato da lui nel quaderno: la nota è
`autore: utente`. **Da dove viene lo dice la `fonte`**: per esempio "dal libro <titolo>",
"dalla spiegazione di Claude del <data>", "mio pensiero". Non c'è bisogno di distinguere tra
testo scritto e testo incollato.

### Il segno `>` (facoltativo)

Se l'utente inizia alcune righe del messaggio con `>` (il segno classico per riportare parole
altrui), sta segnalando che quelle righe sono una citazione. Quando copi quelle righe nel `testo`,
**togli il `>`** all'inizio di ogni riga e metti nella `fonte` da dove viene il passo, se l'utente
lo dice. Se il testo viene tutto da righe marcate, lo sportello aggiunge da solo la dicitura
"citazione riportata dall'utente". Senza il segno tutto funziona come sempre.

### Le tue note

In una nota con `autore: claude` il `testo` è tuo. Se si basa su parole dell'utente puoi mettere
quelle parole esatte in `citazione`: con il testimone acceso viene controllata allo stesso modo.
Non usare `contesto` nelle tue note: è già tutto tuo.

### Salvare le risposte di Claude

L'utente può chiederti di conservare una tua risposta. Sono due casi diversi, da non confondere.

**«Salva questa risposta di Claude»** (o simili: «salvami questa spiegazione», «tieni nota di quello
che hai detto»): la nota è **tua**.
- `autore: claude`; `testo`: il pezzo della tua risposta che l'utente indica, copiato così com'è
  (se non è chiaro quale pezzo, chiediglielo);
- `tipo`: `dedotta` se era un tuo ragionamento o una proposta, `osservata` se riportava ciò che hai
  visto (un file, un risultato);
- `natura`: `idea` o `fatto`, **mai** `decisione` (lo sportello la rifiuterebbe);
- `fonte`: «risposta di Claude del <data> su <argomento>»;
- `da_risposta: "sì"`: dice allo sportello che il testo viene da una tua risposta. Se il
  testimone delle risposte è acceso, lo sportello cerca il testo, parola per parola, nelle tue
  risposte registrate e rifiuta la nota se non lo trova. Se è spento (o in chat), la nota viene
  salvata come «risposta non verificata». Nel file delle risposte i blocchi di codice possono
  essere sostituiti dalla loro impronta: se il pezzo contiene codice, salvalo senza il codice.

**«Questa risposta la faccio mia»** (o simili: «sono d'accordo, salvala come mia», «adotto questa
parte»), con il pezzo **incollato nel messaggio**: la nota è **dell'utente**, perché l'adozione è sua.
- `autore: utente`, `tipo: dichiarata`; `testo`: il pezzo incollato, parola per parola come compare
  nel messaggio dell'utente;
- `fonte`: da quale tua risposta viene, per esempio «risposta di Claude dell'11 ottobre 2026 su
  <argomento>»;
- `natura`: quella che dice l'utente; può essere anche `decisione`, perché l'adozione è sua;
- con il testimone acceso il testo viene verificato come sempre, sul messaggio in cui l'utente l'ha
  incollato;
- se l'utente dice «la faccio mia» senza incollare niente, chiedigli di incollare il pezzo: le
  parole di una nota dell'utente devono stare in un suo messaggio.

In tutti e due i casi consiglia all'utente di indicare o incollare **solo il pezzo che conta**, non
tutta la risposta: le note brevi si ritrovano meglio.

### Messaggi privati

Un messaggio che inizia con `#privato` (o con il prefisso scelto dall'utente in `hypomnema.toml`)
**non finisce nel testimone, ma tu lo leggi comunque**: "privato" vuol dire che le sue parole non
vengono registrate. **Non proporre note su ciò che l'utente dice in un messaggio privato**, né
sue né tue, a meno che non te lo chieda esplicitamente in un messaggio normale (e anche allora le
sue parole non si possono verificare, perché il testimone non le ha registrate).

## 3. Passa le note allo sportello

1. Scrivi la proposta in un file temporaneo **fuori dalla cartella del quaderno**
   (per esempio `proposta.json` nella cartella del programma, dove git lo ignora), in UTF-8.
2. Lancia `P proponi proposta.json`.
   In alternativa puoi passarla dall'ingresso standard: `P proponi -`.
3. Leggi la risposta:
   - `ACCETTATA`: la nota ha un numero ed è salvata;
   - `RIFIUTATA`: leggi i motivi. Se è un errore tuo di formato, correggi e riproponi.
     **Non aggirare mai una regola** (per esempio cambiando l'autore per far passare una decisione):
     se la regola blocca la nota, la nota non entra.
4. Puoi cancellare il file temporaneo della proposta: non fa parte del quaderno.

Non modificare, rinominare o cancellare i file del quaderno (`note/`, `registro.md`).
Il quaderno si allunga soltanto.

## 4. Di' all'utente cosa è successo

Dopo ogni passaggio dallo sportello, dì all'utente in poche parole:
- cosa è stato **salvato** (numero della nota e testo breve);
- cosa è stato **rifiutato** e perché (con il motivo dato dallo sportello).

Non dire mai che una cosa è stata salvata se lo sportello non ha risposto `ACCETTATA`.
Quando usi una nota marcata "autore non verificato", ricorda che nessuno ha controllato
che l'utente l'abbia detta davvero.

## 5. Da idea a decisione

Un'idea diventa decisione **solo con la conferma esplicita dell'utente**. Per esempio:
"sì, facciamo così", "confermo l'idea 0001", "decidiamo questo".
Un silenzio, un "interessante" o un "vedremo" **non** sono conferme: nel dubbio, chiedi.

Quando l'utente conferma:

1. trova il numero dell'idea (con `cerca`, se non lo sai già);
2. proponi una **nuova** nota:

```json
{
  "data": "2026-01-15",
  "fonte": "chat del 15 gennaio 2026 sul progetto dell'orto",
  "autore": "utente",
  "tipo": "dichiarata",
  "natura": "decisione",
  "conferma_di": "0001",
  "testo": "sì, da domani annaffio la mattina presto",
  "contesto": "Conferma dell'idea 0001: annaffiare la mattina presto invece che la sera."
}
```

   Il `testo` sono le parole esatte con cui l'utente ha confermato.
3. l'idea originale resta com'è: il quaderno conserva sia l'idea sia la decisione.

L'utente può anche dire "ricorda che ho deciso ...": in quel caso proponi direttamente una
decisione (`autore: utente`, `tipo: dichiarata`) senza `conferma_di`.

## 6. Cosa ci eravamo detti: quaderno e diario (Claude Code)

Ci sono due posti dove cercare, e non sono la stessa cosa:

- il **quaderno** sono le **note scelte**: `P cerca <parola>`;
- il **diario** è **tutta la conversazione registrata** dai testimoni, grezza: i messaggi
  dell'utente e, se il testimone delle risposte è acceso, le tue risposte.
  `P diario <parola>`; con `--intorno` vedi anche il messaggio subito prima e
  subito dopo ognuno di quelli trovati.

Quando l'utente chiede «cosa ci eravamo detti su…», «cosa ti avevo detto di…», «cosa mi avevi
consigliato…»:

1. cerca **prima nel quaderno**;
2. **poi, se serve**, nel diario;
3. di' sempre **da dove** viene la risposta: «Dalle note del quaderno (scelte da te): …» oppure
   «Dal diario, cioè dalla conversazione registrata, non da una nota: …». Una nota è una scelta
   dell'utente; il diario è solo ciò che è stato detto. Una cosa trovata solo nel diario **non**
   è una decisione, anche se suonava come tale: se l'utente vuole conservarla, proponi una nota.

Puoi usare il diario anche per rileggere cosa avevi consigliato tu e accorgerti se ora stai
dicendo il contrario: in quel caso dillo all'utente apertamente.


## Modalità chat

Segui questa sezione quando sei in una **chat di Claude** (claude.ai, app desktop o mobile) e non
in Claude Code. In chat non puoi lanciare comandi sul computer dell'utente, ma hai un **computer di
lavoro** temporaneo, che sparisce a fine conversazione, dove puoi scaricare i programmi e lanciare
Python. In chat **i testimoni non ci sono**, né quello dei messaggi dell'utente né quello delle
tue risposte, e quindi non c'è nemmeno il diario: le note dell'utente vengono salvate come «autore
non verificato (chat, senza testimone)», e le tue note con `da_risposta` come «risposta non
verificata (chat, senza testimone)». Tutte le altre regole di questa skill restano uguali, e
**non salvi mai una nota a mano**: passi sempre dallo sportello. Il lavoro sporco lo fai tu;
all'utente chiedi solo il permesso per la sua cartella.

### C1. Prepara il computer di lavoro (una volta per chat)

```
git clone --depth 1 --branch main https://github.com/angelomaccarinelli8-sys/hypomnema.git ~/hypomnema-programma
mkdir -p ~/hypomnema-lavoro/quaderno
cp ~/hypomnema-programma/chat/hypomnema-chat.toml ~/hypomnema-lavoro/hypomnema.toml
python3 --version
```

- Serve Python 3.11 o più recente (Hypomnema è garantito dal 3.12; con il 3.11 i test passano).
  Se `git` non c'è, scarica e scompatta
  `https://github.com/angelomaccarinelli8-sys/hypomnema/archive/refs/heads/main.zip`.
- Da qui in poi lancia ogni comando dalla cartella `~/hypomnema-programma`, sempre con la
  configurazione per la chat:

  ```
  python3 -m hypomnema --config ~/hypomnema-lavoro/hypomnema.toml <comando>
  ```

  Qui sotto, `H <comando>` vuol dire proprio questa riga.
- Controlla con `H stato`: deve dire `Testimone: NON C'È (configurazione per la chat di Claude)`.
- Se non riesci a scaricare i programmi, dillo all'utente e fermati: senza sportello non salvi niente.

### C2. Il quaderno dell'utente

**Se hai gli strumenti per il computer dell'utente** (di solito: app desktop aperta e collegata):

1. Chiedi il permesso per la cartella `Hypomnema` nella sua cartella utente
   (`C:\Users\<nome>\Hypomnema` su Windows, `~/Hypomnema` su macOS e Linux), con una frase:
   «Mi serve il permesso per la cartella Hypomnema: leggo il tuo quaderno e ci salvo le note
   nuove, senza toccare nient'altro.» Se la cartella non esiste e gli strumenti non permettono di
   chiedere il permesso per una cartella che non c'è, chiedi all'utente di crearla vuota.
2. Elenca il contenuto di `Hypomnema/quaderno`.
   - **Non c'è, o è vuota**: è la prima volta. Dillo all'utente («È la prima volta: il quaderno è
     vuoto, nascerà con la prima nota.»). Il quaderno nasce nel computer di lavoro con la prima
     proposta e lo riporti sul computer dell'utente come al punto C4.
   - **C'è**: copia nel computer di lavoro, sotto `~/hypomnema-lavoro/quaderno/`, con **gli
     stessi percorsi**, il file `registro.md` e tutti i file della cartella `note/`, a gruppi di
     massimo 50 file per volta. Poi controlla che il numero dei file copiati sia uguale a quello
     elencato. **Non copiare `testimone.jsonl`**: in chat non serve, e contiene parole private
     dell'utente.
3. Controlla il quaderno copiato: `H controlla` (vedi la sezione 1). Serve ad accorgersi di un
   salvataggio rimasto a metà in una chat precedente, o di un file toccato a mano.

**Se non hai gli strumenti per il computer dell'utente** (chat sul web, app mobile): è la
**modalità prova**. Prima di cominciare dillo chiaramente: «Qui non posso accedere al tuo
computer: il quaderno vivrà solo in questa chat e sparirà quando la chiudi. È una prova.» Poi
usa il quaderno di `~/hypomnema-lavoro/quaderno` e non riportare niente.

### C3. Le domande

Quando l'utente chiede cosa aveva detto o deciso («cosa avevo deciso su…»), usa il cercatore sul
quaderno copiato: `H cerca <parola>`, con le regole della sezione 1 (una decisione è una decisione,
un'idea è solo un'idea, una nota dedotta è un'ipotesi, cita il numero della nota).

### C4. Salvare una nota

Per ogni nota, in quest'ordine:

1. Fotografa il quaderno: `H istantanea > ~/hypomnema-lavoro/prima.json`
2. Scrivi la proposta in `~/hypomnema-lavoro/proposta.json` (fuori dalla cartella del quaderno),
   con le regole della sezione 2, e passala allo sportello:
   `H proponi ~/hypomnema-lavoro/proposta.json`
3. Chiedi quali file sono cambiati: `H cambiati ~/hypomnema-lavoro/prima.json`
   - Risponde con un elenco: **riporta sul computer dell'utente esattamente quei file**, allo stesso
     percorso sotto `Hypomnema/quaderno/` (per esempio `note/0007.md` va in
     `Hypomnema/quaderno/note/0007.md`), usando il controllo sui file cambiati.
     **Prima `registro.md`, poi le note create.** Ogni proposta allunga il registro: se la sua
     scrittura riesce, vuol dire che nessun'altra chat ha scritto nel quaderno dopo la tua copia,
     e puoi scrivere le note. Anche una nota rifiutata allunga il registro: va riportato.
     Per **ogni** file da riportare:
     1. copialo in una **cartella nuova** del computer di lavoro, mai usata prima in questa chat, e
        riportalo da lì: per esempio `/mnt/user-data/outputs/riporto-<numero progressivo>/registro.md`.
        Ripartendo da un percorso già usato, lo strumento può rimandare una copia vecchia anche se
        risponde che ha scritto;
     2. subito dopo, ricopia dal computer dell'utente il file appena scritto in un'altra cartella
        nuova (per esempio `~/hypomnema-lavoro/verifica-<numero>/`) e confrontalo con quello del
        computer di lavoro:
        `H confronta ~/hypomnema-lavoro/quaderno/registro.md ~/hypomnema-lavoro/verifica-<numero>/registro.md`
        Deve rispondere `UGUALI`;
     3. se risponde `DIVERSI`, o se non riesci a ricopiarlo: **fermati, non scrivere altri file** e
        dillo all'utente: sul suo computer quel file non è quello giusto.
   - Risponde «Nessun file del quaderno è cambiato»: non c'è niente da riportare.
   - Risponde `ERRORE`: **non riportare niente**. Dillo all'utente con il messaggio ricevuto,
     ricopia il quaderno dal suo computer (C2) e riparti dal punto 1.
   Se già lo sportello risponde `ERRORE: il registro è stato toccato a mano`, non ha scritto
   niente: dillo all'utente con le sue parole e non riprovare finché l'utente non ha sistemato il
   registro (`H controlla` mostra la riga da guardare).
4. Se il controllo **rifiuta la scrittura del registro** (il registro sul computer dell'utente è
   cambiato nel frattempo, per esempio per un'altra chat): **non forzare e non scrivere le note**.
   Sul computer dell'utente non è cambiato niente. Dillo all'utente, ricopia il quaderno (C2) e
   ripeti la proposta dal punto 1.
   Se invece il registro è stato scritto ma il controllo **rifiuta una nota** (succede solo se
   qualcuno ha toccato il quaderno a mano): fermati e dillo all'utente. Dopo aver ricopiato il
   quaderno, `H controlla` mostrerà la riga del registro senza la sua nota.
5. Di' all'utente cosa è stato salvato e cosa è stato rifiutato (sezione 4). In modalità prova
   ricorda che il quaderno sparirà a fine chat.

In modalità prova i punti 1, 3 e 4 non servono: basta il punto 2.
