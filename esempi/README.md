# Esempi (risultati attesi da approvare)

Tutti i dati qui sono **inventati**.

Ogni cartella è un esempio:

- `comandi.txt`: i comandi da lanciare, uno per riga, nell'ordine;
- i file `.json`: le note proposte;
- `atteso/uscita.txt`: ciò che il programma deve scrivere a schermo, con il codice di uscita;
- `atteso/quaderno/`: come deve essere il quaderno alla fine (note, registro, testimone);
- i percorsi della cartella temporanea in cui gira l'esempio compaiono come
  `<cartella di prova>/...` (per esempio nell'uscita di `stato`);
- `hypomnema-chat.toml` (solo negli esempi 59 e 60): una seconda configurazione sullo stesso quaderno;
  le righe di `comandi.txt` che cominciano con `chat:` usano quella;
- `quaderno-iniziale/` (solo in alcuni esempi): il quaderno da cui parte l'esempio, invece di
  un quaderno vuoto;
- `hypomnema.toml` (solo in alcuni esempi): la configurazione usata, per esempio con il
  testimone acceso. Se manca, l'esempio usa una configurazione con il testimone **spento**;
- `messaggio*.json` / `1-privato.json` ecc.: un messaggio inventato dell'utente, come Claude Code
  lo passa al testimone. Il comando `testimone FILE` simula l'arrivo di quel messaggio.

Un file `sistema-operativo.txt` (solo nell'esempio 63) contiene il nome di un fuso: l'esempio gira come
sul computer dell'utente con quel fuso del sistema operativo; senza, ogni esempio gira come una macchina
in UTC.

Il file `etichette.toml` di questa cartella non è un esempio da eseguire: è il **modello commentato**
della lista delle etichette (dalla 0.7.0), da copiare nella cartella del quaderno.

Ogni esempio parte da un quaderno vuoto. Per avere risultati sempre uguali, nei test l'ora del
primo comando è fissata al 15 gennaio 2026 alle 10:00 (ora italiana) e ogni comando successivo
avviene un minuto dopo. Quando si usa il programma davvero, l'ora è quella del computer.

| Esempio | Cosa mostra | Esito atteso |
|---|---|---|
| `01-nota-accettata` | Una nota completa. | Accettata, salvata come `note/0001.md`, una riga ACCETTATA nel registro. |
| `02-nota-senza-fonte` | Una nota senza il campo `fonte`. | Rifiutata con il motivo «manca il campo fonte»; nessuna nota salvata; una riga RIFIUTATA nel registro. |
| `03-claude-decisione` | Una nota di Claude marcata come decisione. | Rifiutata: le decisioni le prende solo l'utente. |
| `04-idea-confermata` | Un'idea di Claude, poi la conferma dell'utente. | Due note: l'idea (0001) resta com'è, la decisione (0002) la cita con `conferma_di`. La ricerca di «orto» le trova entrambe. |
| `05-ricerca` | Tre note, poi la ricerca di «caffè». | Trova le note 0001 e 0002 (anche «Caffè» con la maiuscola); non trova la 0003, che contiene «caffèlatte» e non la parola esatta «caffè». |

| `06-citazione-trovata` | Testimone acceso. L'utente scrive un messaggio; Claude propone una decisione con le sue parole esatte nel `testo` (il messaggio aveva due spazi e un a capo, il testo uno spazio solo) e una spiegazione nel `contesto`. | Accettata; la nota dice «testo trovato nel messaggio del ...» e mostra a parte il «Contesto scritto da Claude». |
| `07-citazione-assente` | Testimone acceso. Una nota dell'utente con un riassunto di Claude al posto delle sue parole, poi una con parole mai dette. | Entrambe rifiutate: il testo non si trova nei messaggi (il motivo ricorda che i riassunti vanno nel `contesto`). |
| `08-citazione-modificata` | Testimone acceso. L'utente dice «zucchine», il testo della nota dice «melanzane». | Rifiutata: il testo non si trova parola per parola. |
| `09-messaggio-privato` | Testimone acceso. Un messaggio che inizia con `#privato`, poi uno normale; poi una nota che cita il messaggio privato. | Il testimone annota solo data e ora del messaggio privato; la nota è rifiutata perché quelle parole non sono registrate. |
| `10-testimone-spento` | Testimone spento. Arriva un messaggio, poi una nota dell'utente senza citazione. | Il testimone non registra niente (nessun file); la nota è accettata e marcata «autore non verificato (testimone spento)». |
| `11-citazione-di-claude-non-verificata` | Testimone spento. Un'idea di Claude con una citazione delle parole dell'utente. | Accettata e marcata «citazione non verificata (testimone spento)». |
| `12-contesto-di-claude` | Testimone acceso. Nota dell'utente con le sue parole nel `testo` e una spiegazione di Claude su due righe nel `contesto`; poi la ricerca di una parola che c'è solo nel contesto. | Accettata; testo e «Contesto scritto da Claude» separati nel file e nella ricerca. |
| `13-citazione-riportata` | Testimone acceso. L'utente incolla un passo di un libro (inventato) marcandolo con `>`, più un suo commento; la nota prende solo il passo, con la fonte del libro. | Il testimone annota `righe_citate: [2, 3]`; nota accettata con «citazione riportata dall'utente». |
| `14-citazione-mista` | Stesso messaggio; la nota prende l'ultima riga del passo e il commento non marcato. | Accettata con «testo trovato nel messaggio del ...», senza la dicitura «riportata». |
| `15-a-capo-nel-registro` | Una proposta con un nome di campo inventato che contiene degli «a capo» e, in mezzo, una finta riga «ACCETTATA \| nota 0099». | Rifiutata per il campo non previsto. Nel registro e a schermo il motivo resta su una riga, con il segno ⏎ al posto degli a capo: nessuna riga falsa. |
| `16-stato-testimone-acceso` | Testimone acceso. `stato` con il quaderno vuoto, poi dopo un messaggio su due righe, poi dopo un messaggio `#privato`. | Prima «nessuno»; poi data, ora e testo esatto dell'ultimo messaggio; poi «(messaggio privato, non registrato)». `stato` non crea niente: il quaderno nasce con il primo messaggio. |
| `17-stato-testimone-spento` | Testimone spento. Arriva un messaggio, poi `stato`. | «Testimone: SPENTO», con la spiegazione; nessun messaggio registrato. |
| `18-chat-nota-utente` | Configurazione per la chat (`chat/hypomnema-chat.toml`). `stato`, poi una nota dell'utente con un contesto di Claude, poi la ricerca. | `stato` dice «Testimone: NON C'È»; la nota è accettata e marcata «autore non verificato (chat, senza testimone)». |
| `19-chat-file-da-riportare` | Configurazione per la chat. `istantanea`, una nota accettata, `cambiati`; poi `istantanea`, una nota rifiutata, `cambiati` due volte. | Dopo la nota accettata: da riportare `note/0001.md` e `registro.md` (creati). Dopo quella rifiutata: solo `registro.md` (allungato), uguale anche la seconda volta perché `cambiati` non cambia niente. |
| `20-controlla-in-ordine` | `controlla` sul quaderno vuoto, poi una nota accettata e una rifiutata, poi di nuovo `controlla`. | Prima «nessuna nota», poi «1 nota, con la sua riga ACCETTATA nel registro»: la riga RIFIUTATA non conta. |
| `21-controlla-non-corrisponde` | Parte da un quaderno già pronto con le note 0001 e 0002 e un registro con ACCETTATA 0001, una riga RIFIUTATA e ACCETTATA 0003. | «ATTENZIONE»: la nota 0002 non ha la sua riga nel registro, e il registro dice ACCETTATA per la 0003 che non c'è. Codice di uscita 1; il quaderno resta identico. |
| `22-registro-senza-a-capo` | Parte da un registro la cui ultima riga, scritta a mano, non finisce con un «a capo». Arriva una proposta, poi `controlla`. | Lo sportello non scrive niente: errore «il registro è stato toccato a mano» (codice 2), nessuna nota e nessuna riga. `controlla` segnala la riga 6 estranea e il registro senza a capo finale. Il quaderno resta identico. |
| `23-controlla-riga-estranea` | Il caso trovato nella prova in chat: la riga dello sportello attaccata a una scritta a mano («riga scritta a mano- … ACCETTATA \| nota 0002 …»). | `controlla` segnala la riga 6 estranea, con il suo testo, e la nota 0002 senza la sua riga. |
| `24-salva-risposta-di-claude` | «Salva questa risposta di Claude»: la stessa frase di Claude proposta come idea e come decisione. | L'idea è accettata (`autore: claude`, fonte «risposta di Claude…»); come decisione è rifiutata: le decisioni sono dell'utente. |
| `25-risposta-fatta-propria` | «Questa risposta la faccio mia», con il pezzo incollato nel messaggio; testimone acceso. | Accettata come decisione dell'utente, fonte «risposta di Claude…», testo trovato nel messaggio dal testimone. |
| `27-risposta-con-codice` | Testimone delle risposte acceso. Un messaggio, una risposta di Claude con un blocco di codice di 3 righe, poi `impronta` del file con quelle 3 righe e `stato`. | Nel file delle risposte il blocco diventa «[blocco di codice di 3 righe omesso, impronta …]»; `impronta` del file dà la stessa impronta; `stato` mostra anche il testimone delle risposte. |
| `28-risposta-a-messaggio-privato` | Un messaggio `#privato` con la sua risposta, poi un messaggio normale con la sua risposta. | La prima risposta non è registrata («risposta a un messaggio privato, non registrata»); la seconda sì. |
| `29-diario-cerca` | Due messaggi e due risposte; poi `diario fragole`, `diario basilico --intorno` e una parola che non c'è. | «fragole»: il messaggio dell'utente e la risposta di Claude, in ordine di tempo; «basilico» con i vicini (il messaggio prima e la risposta dopo); «pomodori»: nessun messaggio. |
| `30-nota-da-risposta` | Una risposta di Claude registrata; poi due note di Claude con `da_risposta`: una con un pezzo della risposta, una con parole mai dette. | La prima è accettata con «testo trovato nella risposta di Claude del …»; la seconda è rifiutata. |
| `31-pausa-e-ripresa` | Testimoni dei messaggi e delle risposte accesi. Un messaggio con la risposta; poi `/hypomnema:pausa`, un messaggio e una risposta durante la pausa, `stato` e una nota dell'utente; poi `/hypomnema:riprendi`, un messaggio con la risposta, `stato` e il diario. | La pausa e la ripresa restano nel testimone come righe senza testo; il messaggio e la risposta in pausa non sono registrati («durante la pausa»); `stato` dice «IN PAUSA dal …»; la nota presa in pausa è marcata «autore non verificato (testimoni in pausa)»; dopo la ripresa si registra di nuovo. |
| `32-archivio-nota-riscontrata` | Configurazione per la chat con la sezione `[archivio]`. Claude copia dall'archivio della chat (ora al minuto e fuso a parte, come le dà lo strumento) un messaggio dell'utente, che contiene un avviso tecnico `<system-reminder>`, e una sua risposta; poi una nota dell'utente con un pezzo di quel messaggio, la ricerca e `stato`. | L'avviso tecnico è tolto; la nota è «testo riscontrato sull'archivio della chat <indirizzo>, messaggio del turno 0 (…, copiato da Claude)»; `stato` mostra l'archivio. |
| `33-archivio-testo-assente` | Come il 32, ma la nota ha parole che nell'archivio non ci sono. | Accettata e marcata «autore non verificato (chat, senza testimone)»: in chat non si rifiuta. |
| `34-archivio-messaggio-privato` | La copia comprende un messaggio `#privato` con la sua risposta, poi un messaggio normale con la sua risposta; poi gli ultimi 4 del diario. | Del messaggio privato e della sua risposta restano solo data e ora («non copiato»); gli altri due sono copiati. Le righe del diario dicono da quale chat vengono. |
| `35-archivio-senza-doppioni` | La stessa copia fatta due volte: la seconda ha anche un messaggio nuovo nello stesso minuto e una risposta con lo stesso turno ma un testo diverso. | I doppioni si riconoscono dal turno, non dall'ora: la seconda volta copia solo il messaggio nuovo (stesso minuto, turno diverso); i 2 già presenti non sono duplicati e il programma avvisa che uno ha un testo diverso, senza toccarlo. `controlla` dice che è tutto in ordine. |
| `36-diario-tre-livelli` | Parte da un quaderno con una nota verificata dal testimone di Claude Code; in chat copia dall'archivio e salva una nota riscontrata e una non verificata; poi la ricerca e il diario. | La ricerca mostra i tre livelli: «testo trovato nel messaggio…» (testimone), «testo riscontrato sull'archivio della chat…» e «autore non verificato». Nel diario la riga del testimone non ha indicazioni, quelle copiate dicono «archivio della chat …, copiato da Claude». |
| `37-correzioni-insieme` | La nota 0001, la sua correzione e la correzione della correzione (dalla 0.6.0 le versioni 0001.1 e 0001.2); un'altra nota 0002; una correzione di una nota che non c'è. Poi due ricerche. | La correzione di una nota che non c'è è rifiutata. «pomodoro» trova 0002 e 0001, dalla più recente; la 0001 è mostrata all'ultima versione, con la sua storia. |
| `38-parole-composte` | Una nota con «orto_balcone.py» e «semi-orto/vasi»; una con «caffèlatte». | «orto», «balcone», «vasi» e «orto_balcone» trovano la prima nota; «caffè» non trova «caffèlatte». |
| `39-promemoria-scaduti` | Oggi è il 15/01/2026. Promemoria per il 20/01, l'01/01 e il 15/01; uno con la data 30/02. | La data che non esiste è rifiutata. `promemoria` mostra l'01/01 e poi il 15/01, e dice che 1 promemoria ha una data non ancora arrivata. |
| `40-promemoria-fatto` | Un promemoria scaduto, poi `done`; poi un secondo `done` sulla stessa nota e uno su una nota che non c'è. | Dopo il `done` (la versione chiusa 0001.1) il promemoria non è più tra gli scaduti. I due `done` sbagliati sono rifiutati («already closed (✓F0001.1)», «does not exist»). |
| `41-promemoria-corretto` | Un promemoria scaduto e una sua correzione del testo, senza data. | Il promemoria resta tra gli scaduti, alla versione 0001.1, con la storia. |
| `42-promemoria-corretto-con-data` | Un promemoria scaduto; una correzione che lo sposta a marzo; una seconda correzione che lo riporta al 12/01. | Dopo la prima correzione non è scaduto («1 promemoria ha una data non ancora arrivata»); dopo la seconda (versione 0001.2) torna scaduto il 2026-01-12, con la storia. |
| `43-recap` | Testimone acceso, `[recap]` con 2 decisioni e 3 righe del diario. Quattro messaggi (l'ultimo privato), tre decisioni, due discorsi aperti (uno corretto da Claude, che resta aperto), un promemoria scaduto. | Il recap mostra il promemoria, i 2 discorsi aperti (con la versione sotto, `↳`), 2 decisioni su 3 con «1 decisione più vecchia non mostrata», le ultime 3 righe del diario con la privata come «(messaggio privato, non registrato)». |
| `44-recap-quaderno-vuoto` | Quaderno vuoto. | Il recap dice «nessuno»/«nessuna» per ogni blocco; nessun promemoria scaduto. |
| `45-archivio-segni-html` | In chat, una copia dell'archivio con «&lt;», «&gt;» e «&amp;», e un avviso tecnico scritto in quella forma; poi una nota con «<» e «&». | Nell'archivio finiscono i segni veri e l'avviso è tolto; la nota è riscontrata sull'archivio. |
| `46-quaderno-vecchio` | Un quaderno di prima della 0.4.0 (le note dell'esempio 05) con la configurazione di prima. | `controlla`, `cerca`, `promemoria` e `recap` funzionano senza modifiche; una correzione nuova entra come versione 0001.1. |
| `47-nota-in-inglese` | La stessa nota proposta con i nomi inglesi (`propose`) e con quelli italiani (`proponi`); una proposta con `data` e `date` insieme; poi `search` e `cerca`. | Le due note sono scritte uguali, in inglese; la terza è rifiutata («the field «date» appears twice»); `search` e `cerca` danno la stessa uscita. |
| `48-kind-todo` | Un `todo` di Claude, una `decision` di Claude, un `kind: choice`; poi il recap. | Il todo entra e compare in «Cose da fare»; la decisione di Claude e «choice» sono rifiutati. |
| `49-chiudere-open` | Un `open` di Claude; chiusure con `done`: di Claude, dell'utente, una seconda chiusura, una nota `open` che chiude, `done` su una decisione; poi `search`, `search --all` e il recap. | Accettata solo la chiusura dell'utente (`decision`, versione ✓D0001.1); le altre sono rifiutate con il loro motivo («already closed (✓D0001.1)», «only the user can close an open note», «0002 does not exist»: la chiusura non ha preso un numero nuovo). Il discorso aperto, chiuso come decisione, è una decisione: `search` lo mostra come `✓D0001.1`, con la storia («chiusa il …, perché «Nell'angolo nord.»»), e il recap lo mette in «Ultime decisioni» invece che tra i discorsi aperti. |
| `50-chiudere-todo` | Tre `todo` di Claude; una nota che ne chiude due insieme (`done: "0001, 0002"`); un `done` con un numero ripetuto. | «Cose da fare» passa da 3 a 1 (due versioni chiuse, 0001.1 e 0002.1, con due righe nel registro); il numero ripetuto è rifiutato; `search --all` mostra i todo chiusi con la loro storia. |
| `51-priorita` | Tre `todo` dell'utente (normale, bassa, alta); un `updates` che porta la bassa ad alta; una priorità in una nota di Claude; `priority: urgent`. | Il recap mostra prima l'alta, poi la normale, poi la bassa; dopo il cambiamento le due alte vengono prima (con `↳` la versione 0002.1). Le due proposte sbagliate sono rifiutate. |
| `52-quaderno-vecchio-italiano` | Il quaderno dell'esempio 43 della 0.4.0 (note in italiano, «discorso aperto», `riprendere_il`, `corregge`, configurazione senza `todo` nel `[recap]`), con comandi italiani e inglesi; poi una proposta dell'utente, con i nomi italiani, che chiude il promemoria 0006. | Tutti i comandi funzionano; le note vecchie restano identiche byte per byte. Dalla 0.6.0 la vecchia correzione 0007 è letta come versione `O0004.1 (nota 0007)`: il testo nuovo vale (Claude correggeva una sua nota), ma la natura «fatto» no, perché oggi solo l'utente fa smettere un open di essere open; il discorso aperto resta tra quelli aperti, e la storia dice «non applicato (catena vecchia non permessa oggi): natura open → fact». La chiusura è la versione 0006.1, scritta in inglese; il promemoria sparisce dal recap. |
| `53-versioni` | Il quaderno di prova della 0.6.0 (sette note vecchie, inventate). Revisione e recap; poi un cambio di priorità, un cambio di natura, una correzione del testo; e proposte sbagliate: Claude corregge una nota dell'utente, un rimando a una versione vecchia, una chiusura di una nota già chiusa, una decisione di Claude, un cambiamento che non cambia niente, due cambiamenti insieme. | Le versioni 0006.1, 0004.1, 0004.2 e 0006.2 sono file veri con il blocco «Change» e la loro riga nel registro; la nota nuova prende il numero 0008. Il recap mostra i codici (`T0006.1`, `T0004.2`) con `↳` per ogni versione; ogni rifiuto ha il suo motivo. |
| `54-riaprire` | Lo stesso quaderno: Claude chiude il basilico (todo) come fatto, l'utente chiude la compostiera (open) come decisione; poi le riaperture: dell'utente, di una nota non chiusa, di Claude su un open, dell'utente sull'open. | Il basilico chiuso sparisce dal recap e dalla ricerca di base; la compostiera chiusa come decisione compare in «Ultime decisioni» come `✓D0004.1`, con il motivo della chiusura; `--all` le mostra con la storia. Le riaperture valide creano `T0006.2` e `O0004.2` («riaperta il …, perché «…»»); le altre due sono rifiutate. |
| `55-codici` | Lo stesso quaderno con `[codici] chiusa = "x"`; rimandi con la lettera (`T0006`, `✓F0001.2`), un numero vecchio che non è l'ultima versione, la riapertura di una vecchia chiusura. | Il codice delle chiuse usa «x» (`xF0001.2 (nota 0003)`), anche nella legenda; i rimandi con la lettera sono rifiutati con il modo giusto di scriverli; `0003` (la vecchia chiusura) vale come `0001.2` e la riapertura crea `0001.3`. |
| `56-note-vecchie` | Lo stesso quaderno più quattro note vecchie: una correzione di un'idea, una decisione che conferma la correzione, un open chiuso da un todo. Poi una correzione nuova dell'idea. | Nota, correzione e chiusura sono una storia sola (`✓F0001.2 (nota 0003)`), assente dal recap. Il todo che chiudeva resta visibile da solo. Dopo la correzione nuova la decisione dice «conferma di: nota I0005.1 (nota 0008), versione vecchia: l'ultima è I0005.2». |
| `57-revisione` | Lo stesso quaderno più: una nota che nomina la 0006, due correzioni vecchie della stessa nota (un ramo), un todo con «ricordamelo tra una settimana» senza data, una nota con una data e un numero di un fatto. Poi la data del promemoria al todo. | `review` segnala 5 cose (ramo, open fermo da 46 giorni, promemoria scaduto, T0006 nominata nella F0008, «ricordamelo» senza data), con il codice 1; dopo l'`updates` con `remind` le cose sono 4. Le date e i numeri dei fatti non si segnalano. |
| `58-chat-versioni` | In chat: `snapshot`, una chiusura di due note, `changed`, `check`; poi una riapertura, `changed`, `compare` della versione riportata, `check`. | `changed` elenca le versioni create (`note/0004.1.md`, `note/0006.1.md`, poi `note/0006.2.md`) e il registro allungato; `check` conta note e versioni; `compare` dice `UGUALI`. |
| `59-chat-collegata` | La cartella Hypomnema con due configurazioni sullo stesso quaderno: `hypomnema.toml` (Claude Code, testimone acceso) e `hypomnema-chat.toml` (la chat collegata al computer). Le righe con `chat:` usano la seconda. Una nota dalla chat, un messaggio e una decisione da Claude Code, una chiusura dalla chat, poi recap e check. | `status` dice «ACCESO» con la prima e «NON C'È (configurazione per la chat di Claude)» con la seconda. La nota della chat è «author not verified (chat, no witness)», la decisione di Claude Code «text found in the message of …». Il quaderno resta in ordine per tutte e due. |
| `60-etichette` | Un quaderno con `etichette.toml` (CHI: Anna, Marco, Code; COSA: orto, bilancio, gioco) e due configurazioni, come nel 59. Un todo con `who` e `about`; un fatto senza etichette; tre proposte sbagliate (etichetta fuori lista, tre CHI, etichetta ripetuta); Claude etichetta il fatto dell'utente e poi prova a cambiare le etichette; dalla chat una nota con i nomi italiani `chi` e `cosa` e una con «Bilancio» maiuscolo. Poi `search` con i filtri, `recap --about orto`, `labels`, un filtro con un'etichetta che non c'è, `check`. | Accettate le note con etichette giuste (`- who: Anna`, `- about: orto` nell'intestazione) e la versione `F0002.1` («cosa → orto»); rifiutate le altre, ognuna con il suo motivo («not in the list… the allowed ones are orto, bilancio, gioco», «at most 2», «repeated», «only the user can change the labels…»); la chat legge la stessa lista. I filtri valgono tutti insieme; il recap filtrato non mostra il diario; `labels` conta le note (e le aperte); l'etichetta che non c'è dà errore (codice 2). |
| `61-recap-per-data` | Configurazione con `voci_diario = 0`. Tre todo con date non in ordine di numero (2, 10 e 5 gennaio), un open, una decisione; recap. Poi una correzione di oggi del todo più vecchio, una versione di Claude che mette solo un'etichetta, la chiusura dell'open come decisione il 14; recap. | Il primo recap mette i todo per data dell'ultima versione (T0002, T0003, T0001). Nel secondo il todo corretto oggi sale in cima (`T0001.1 2026-01-15`), quello con la sola etichetta resta al suo posto con la sua data (`T0003.1 2026-01-05 … · cosa: orto`), e la questione chiusa come decisione il 14 viene prima della decisione del 12. Il blocco del diario non c'è. |
| `62-contesto-nelle-chiusure` | Un todo, un open, un todo di Claude. L'utente chiude il todo con un motivo e un contesto di Claude; Claude chiude il suo todo con un contesto; una chiusura con `from_reply`; l'utente alza la priorità dell'open con un contesto. Poi `search` (anche di una parola che è solo nel contesto) e recap. | La versione `✓T0001.1` ha `### Reason` e poi `### Context written by Claude`; la ricerca mostra «chiusa il …, perché «Fatto ieri sera.» (contesto: «…»)». Il contesto nella chiusura di Claude e `from_reply` sono rifiutati come prima. «ferie», solo nel contesto della priorità, trova l'open. |
| `63-fuso-del-sistema` | Il computer dell'utente (il file `sistema-operativo.txt` fa girare l'esempio con il sistema operativo su `Europe/Rome`), con `fuso = "Europe/Zurich"` nella configurazione. `status`, due proposte, `status`, `check`. | `status` dice «Fuso orario: Europe/Rome, dal sistema operativo» e segnala che la riga della configurazione è diversa, senza bloccare. Il file `fuso-del-sistema.jsonl` nasce con una riga sola (la seconda proposta non la ripete); `check` è in ordine. |
| `64-etichette-dello-sportello` | Lista con CHI Anna, Marco, Luca e COSA orto, bilancio, gioco, Famiglia, orto botanico. Note con «orto» nel testo (con e senza COSA a mano), senza parole della lista, con tre COSA nel testo, con «è in gioco», con tre COSA a mano, con «orto» solo nel contesto, con «orto\nbotanico», e una nota di Claude. Poi `search --about orto`, `labels`, `matches`, `riscontri --cosa gioco`, `status`, `check`. | Lo sportello aggiunge le COSA trovate (`- labels from text: about orto`), mai le CHI; tre COSA nel testo vanno bene, tre a mano sono rifiutate; il contesto non conta; «orto botanico» dà anche «orto»; «è in gioco» dà `gioco` (un limite, visibile in `matches`). `labels` conta dal testo e a mano. |
| `65-etichette-e-versioni` | Correzioni, cambiamenti di Claude e una chiusura su note con COSA dal testo e a mano. | La correzione cambia le COSA dello sportello (orto → bilancio) e non quelle a mano; Claude aggiunge una COSA a mano a una nota con sole COSA dallo sportello, ma non la cambia di nuovo; può aggiungere una CHI; la chiusura tiene le COSA del testo. `matches` mostra anche le COSA a mano che nel testo non ci sono. |
| `66-schemi` | Otto note dell'utente (tre decisioni con «d'ora in poi», tre idee con «magari un giorno», due da fare con «devo ricordarmi») e un'idea di Claude; `patterns` e `schemi --misura`; poi un'idea dell'utente con «d'ora in poi», una decisione con «d'ora in poi», e di nuovo `patterns`. | Gli schemi di ogni tipo (l'idea di Claude non conta); la misura: 8 giuste su 8 sulle stesse note, 6 su 8 a turno. L'idea con «d'ora in poi» è salvata come idea con la riga SUGGERIMENTO; la decisione no. Gli schemi crescono con le note nuove. |
| `67-etichette-retroattive` | Il quaderno dell'esempio 61 (note scritte senza la lista), a cui si aggiunge `etichette.toml` (COSA serra, limone, terriccio). `search --about limone`, `labels`, `matches`, `recap --cosa serra`, `check`. | Le note vecchie prendono subito le COSA del loro testo, calcolate alla lettura; i file del quaderno restano identici byte per byte. |
| `68-integrare` | Due cose da fare sull'orto e un'idea sul gioco. L'utente integra la pompa nel pozzo (`integrates` + `from_note`), aggiunge parole nuove all'idea (`integrates`); poi tre proposte sbagliate (senza COSA in comune, Claude che aggiunge parole a una nota dell'utente, con `kind`); recap e ricerche. | T0001.1 ha il testo del pozzo e sotto quello della pompa, con `### From note 0002`; T0002 esce dal recap e dalla ricerca di base, con `--all` è «integrata nella nota T0001.1». I0003.1 ha `change: text added`. Le tre proposte sbagliate sono rifiutate. |
| `69-annullare` | Una decisione dell'utente e un'idea di Claude. Claude prova ad annullare la decisione; l'utente la annulla (con il nome italiano `annulla`); Claude annulla la sua idea; recap e `search --all`; poi un `done` sulla decisione annullata e la riapertura. | Claude non annulla la nota dell'utente; `CD0001.1` e `CI0002.1` escono dal recap («Ultime decisioni: nessuna»), la legenda dice «C annullata», `--all` le mostra con il motivo. Il `done` è rifiutato; la riapertura riporta D0001.2 tra le decisioni. |
| `26-confronta` | `confronta` tra due file uguali, due diversi e un file che manca. | `UGUALI` (codice 0); `DIVERSI` con il primo byte diverso (codice 1); errore (codice 2). |

Dal compito 2, negli esempi 01, 04 e 05 (testimone spento) le note con autore «utente» hanno
in più la riga «verifica: autore non verificato (testimone spento)».

I test (`tests/test_esempi.py`) rifanno ogni esempio e confrontano il risultato, carattere per
carattere, con la cartella `atteso/`.

Dal compito 3, negli esempi 06, 07, 08 e 09 le note dell'utente hanno le parole dell'utente nel
`testo` (non più nel campo `citazione`, che ora è solo per le note di Claude): cambiano le note
proposte, i motivi di rifiuto e la riga «verifica» («testo trovato» invece di «citazione trovata»).

Dalla versione 0.4.0 il cercatore mostra le note **dalla più recente alla più vecchia** e, sotto
ogni nota, le note collegate: cambia l'ordine delle ricerche con più risultati negli esempi 04, 05 e
36 (e nel 04 la nota 0001 ha in più «confermata da: nota 0002»). Nell'esempio 15 l'elenco dei campi
ammessi comprende i tre campi nuovi (`corregge`, `done`, `riprendere_il`).

Dalla versione 0.5.0 (lingua per ruolo) le note nuove si scrivono in inglese (`# Note`, `- date:`,
`## Text`, valori come `user`, `stated`, `fact`), i motivi di rifiuto sono in inglese e le diciture
`verification` anche. Per questo cambiano i risultati attesi di quasi tutti gli esempi da 01 a 46
che salvano o rifiutano una nota (l'elenco è nel resoconto della richiesta di unione); le proposte
e i comandi di quegli esempi restano in italiano, così provano che i nomi italiani funzionano
ancora. Nell'esempio 40 la ricerca non mostra più il promemoria chiuso.

Dalla versione 0.6.0 ogni cambiamento è una versione (`0001.1.md`) invece di una nota nuova, e la
ricerca e il recap mostrano i codici con la lettera, la storia e la legenda. Per questo cambiano i
risultati attesi degli esempi che cercano o fanno il recap (04, 05, 06, 10, 12, 13, 18, 25, 30, 32,
36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52) e, nell'esempio 15, l'elenco dei
campi ammessi (con `updates` e `reopens`). Cambiano anche alcune **proposte**, che rimandavano a
numeri di note che con le versioni non nascono più: 37 (la seconda correzione corregge `0001`), 40
(il secondo `done` è sulla stessa nota, file `3-fatto-di-nuovo.json`), 41 e 42 (il testo della
correzione è il testo nuovo), 43 (Claude corregge il testo del suo discorso aperto, che resta aperto),
51 (`updates` invece di `corrects`), 52 (la chiusura riguarda solo il promemoria 0006).

Dopo la prima prova sul quaderno vero (richiesta di unione #15) il recap legge ogni nota per quello che
è adesso: una questione chiusa come decisione compare in «Ultime decisioni» (esempi 49 e 54); sotto
ogni nota le righe della storia vanno dalla più recente alla più vecchia e la chiusura dice il suo
motivo («chiusa il …, perché «…»», esempi 50, 53-56); le catene vecchie che oggi non sarebbero
permesse restano nella storia ma non valgono (esempio 52: il discorso aperto 0004 resta aperto).

Dalla versione 0.7.0 cambiano i risultati attesi di questi esempi già approvati:
- 16, 17, 18, 27, 31, 32 e 59: `status` ha una riga nuova, «Fuso orario: …». Gli esempi girano come
  una macchina in UTC senza il file del fuso, quindi la riga dice «UTC, quello di questa macchina: il
  quaderno non ha ancora il file fuso-del-sistema.jsonl…» (le ore degli esempi restano quelle fisse);
- 18, 19, 58, 59 e 60: la configurazione della chat (copia del modello) non ha più la riga `fuso`;
- 15 e 53: i motivi di rifiuto elencano anche i campi nuovi (`who`, `about`) e i valori che `updates`
  può cambiare («write in «kind», «priority», «remind», «who» or «about» the new value»);
- 55 e 56: nel recap le cose da fare vanno per giorno dell'ultima versione (55: `T0001.3`, cambiata il
  15 gennaio, prima di `T0006`; 56: `T0006` del 27 dicembre prima di `T0011` del 4 dicembre);
- 59: nel quaderno atteso non c'è più il file vuoto `.sportello.lock` (il blocco sta nella cartella
  temporanea).

Dalla versione 0.8.0 cambiano i risultati attesi di questi esempi già approvati:
- 16, 17, 18, 27, 31, 32, 59 e 63: `status` ha la riga «Etichette: …»;
- 60: `labels` dice, per ogni COSA, quante dal testo e quante proposte, e la riga finale lo spiega.
- 15 (dalla 0.9.0): l'elenco dei campi ammessi comprende `integrates`, `from_note` e `cancels`.
- 54 (dalla 0.9.0): il motivo «only a closed or cancelled note can be reopened» (prima «only a closed note»).
