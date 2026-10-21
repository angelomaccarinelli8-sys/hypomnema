# Hypomnema

Stato: prototipo in evoluzione, usato ogni giorno dall'autore.

**Una memoria permanente per Claude, scritta in file Markdown sul tuo computer.**

Ogni chat con Claude riparte da zero. Hypomnema gli dà un quaderno: a inizio chat Claude
rilegge le note utili, durante la chat propone cosa ricordare. Ma **non è Claude a decidere
cosa entra**: lo decide un piccolo programma con regole fisse, che dà sempre lo stesso risultato.

> Claude propone le note, i programmi decidono se entrano.

Hypomnema è un **plugin per Claude Code** (nel terminale o nell'app desktop), con i testimoni che
registrano la conversazione; nella **chat di claude.ai** funziona con la sola skill.

> **Provalo in 2 minuti, nella chat**
>
> 1. Scarica [`hypomnema-skill.zip`](https://github.com/angelomaccarinelli8-sys/hypomnema/releases/latest/download/hypomnema-skill.zip).
> 2. Caricalo tra le skill nelle impostazioni di Claude.
> 3. Apri una chat e scrivi «Usiamo Hypomnema».
>
> Con l'app desktop di Claude collegata al computer il quaderno resta salvato; senza, è una prova
> che sparisce a fine chat. Per usarlo ogni giorno, con i testimoni, installa il plugin in Claude Code
> (vedi «Installa il plugin in Claude Code»).

## Da dove viene il nome

*Hypomnema* (ὑπόμνημα) in greco antico vuol dire "promemoria". Gli *hypomnemata* erano i
quaderni personali dove si annotava ciò che si era letto, sentito o pensato, per rileggerlo e
ragionarci sopra.

## Perché: le regole di Sophia

Hypomnema è estratto dall'idea di **Sophia**, la memoria deterministica a cui lavora
Angelo Maccarinelli e che resta in sviluppo. Hypomnema è un mattoncino a sé: non dipende da
Sophia e non ne contiene il codice, ma ne segue le regole:

- **Provenienza sempre**: ogni nota dice quando, da dove e chi l'ha detta (l'utente o Claude).
- **L'incerto resta incerto**: ogni nota è *osservata*, *dichiarata* o *dedotta*.
- **Idee separate dalle decisioni**: un'idea diventa decisione solo se l'utente la conferma.
  Una nota di Claude non può mai essere una decisione.
- **Niente si cancella e niente si riscrive**: il quaderno si allunga soltanto.
- **Una sola porta d'ingresso**: tutto passa dallo sportello, che annota ogni passaggio in un registro.
- **Solo regole fisse**: niente intelligenza artificiale nei programmi, niente statistica.
  Stessi ingressi, stesso risultato.
- **I dati restano tuoi**: i programmi non si collegano a internet.

<!-- Da rendere visibile quando c'è il link all'articolo di Angelo:
Per saperne di più su Sophia: [articolo su LinkedIn](LINK_ARTICOLO_LINKEDIN)
-->

## Cosa c'è dentro

| Parte | Cosa fa |
|---|---|
| **Sportello** (`propose`, o `proponi`) | Riceve una nota proposta, la controlla, la salva come file Markdown se è completa, altrimenti la rifiuta spiegando perché. |
| **Registro** (`registro.md`) | Annota ogni passaggio dallo sportello, accettato o rifiutato, con data e motivo. Solo aggiunta. |
| **Cercatore** (`search`, o `cerca`) | Trova le note che contengono una parola, dalla più recente, senza quelle chiuse (con `--all` anche quelle); di ogni nota mostra l'ultima versione e la sua storia, e sotto le note che la confermano. Solo lettura. |
| **Promemoria** (`reminders`, o `promemoria`) | Elenca le note con la data `remind` arrivata o già passata, dalla più vecchia. Solo lettura. |
| **Recap** (`recap`) | «Dove eravamo rimasti»: promemoria scaduti, discorsi aperti, cose da fare, ultime decisioni e ultime righe del diario, scelti con regole fisse, prima le priorità alte. Solo lettura. |
| **Revisione** (`review`, o `revisione`) | Che cosa conviene guardare: questioni ferme da tanto, promemoria scaduti, cose da fare nominate in una nota successiva, «ricordamelo» senza data, rami e catene vecchie non permesse oggi. Dice cosa si può fare, non lo fa. Solo lettura. |
| **Testimone** (`testimone`) | Se lo accendi, registra le parole esatte dei tuoi messaggi, così lo sportello può controllare che una nota "dell'utente" riporti parole che hai detto davvero. |
| **Stato** (`status`, o `stato`) | Dice se il testimone è acceso, dov'è il quaderno e quale messaggio ha registrato per ultimo. Solo lettura. |
| **Skill** (`skills/hypomnema/`) | Le istruzioni per Claude: quando leggere, come controllare il testimone, come preparare le note, come confermare una decisione. Dalla 0.7.0 `SKILL.md` ha le regole di sempre, e quattro file accanto, letti solo quando servono: `chat-mode.md` (la chat), `labels.md` (le etichette), `replies.md` (salvare le risposte di Claude), `diary.md` (quaderno e diario). |
| **Etichette** (`labels`, o `etichette`; dalla 0.7.0) | Le etichette CHI e COSA della lista che scrivi tu in `etichette.toml`, con quante note ha ognuna. `search` e `recap` filtrano per etichette. Vedi «Le etichette CHI e COSA». |
| **Plugin** (`.claude-plugin/`, `hooks/`, `commands/`, `programma.py`) | Il repository stesso è un plugin di Claude Code: la skill, i programmi, gli agganci dei testimoni e i comandi `/hypomnema:pause`, `/hypomnema:resume` e `/hypomnema:recap` (valgono anche `/hypomnema:pausa` e `/hypomnema:riprendi`). Vedi «Installa il plugin in Claude Code». |
| **Modalità chat** (`chat/`, `istantanea`, `cambiati`) | La configurazione per la chat di Claude e i due comandi, in sola lettura, che dicono quali file del quaderno riportare sul tuo computer dopo una proposta. Vedi «Usarlo nella chat di Claude». |
| **Avviabile** (`windows/Hypomnema.cmd`) | Alternativa al plugin installato, solo Windows: un doppio clic per aprire Claude Code con Hypomnema acceso. Vedi «Alternativa: l'avviabile di Windows». |

Il formato delle note, le regole dello sportello e tutte le regole del quaderno (con esempi giusti e
sbagliati) sono descritti in [FORMATO.md](FORMATO.md).

## Installa il plugin in Claude Code (consigliato)

Si installa una volta; da quel momento **ogni sessione di Claude Code** ha la skill e i testimoni,
in ogni progetto.

**Prima di tutto servono:** Claude Code; Python 3.10 o più recente (su Windows il comando `py`, da
[python.org](https://www.python.org/downloads/)); su Windows anche **Git per Windows**
([git-scm.com](https://git-scm.com/download/win)), perché Claude Code lancia gli agganci con Git Bash.

**Installazione**, in un terminale (PowerShell va bene):

```
claude plugin marketplace add angelomaccarinelli8-sys/hypomnema
claude plugin install hypomnema@hypomnema
```

La prima riga aggiunge il catalogo di questo repository, la seconda installa il plugin. Dentro una
sessione di Claude Code puoi fare lo stesso con `/plugin marketplace add angelomaccarinelli8-sys/hypomnema`
e `/plugin install hypomnema@hypomnema`; da Claude Code 2.1.275 basta
`/plugin install hypomnema --marketplace angelomaccarinelli8-sys/hypomnema`. Nell'app desktop,
scheda Code: pulsante **+** accanto al riquadro del messaggio → **Plugins** → **Add plugin**.

**La prima sessione.** All'avvio Hypomnema crea la configurazione `~/Hypomnema/hypomnema.toml` (su
Windows `%USERPROFILE%\Hypomnema\hypomnema.toml`) con il testimone dei messaggi e quello delle
risposte **accesi**, e te lo dice con un avviso. Il quaderno nasce accanto, in `~/Hypomnema/quaderno`.
Configurazione e quaderno stanno **fuori dal plugin**: un aggiornamento non li tocca mai. Se il
quaderno finisse dentro il plugin, i testimoni non registrano; se finisse in OneDrive, l'avviso te
lo dice a ogni sessione.

**Pausa.** Con il plugin installato i testimoni registrano tutto quello che scrivi in Claude Code,
anche negli altri progetti. Quando non vuoi:

- `/hypomnema:pause` (o `/hypomnema:pausa`) mette in pausa i testimoni: da lì in poi annotano solo
  data e ora, senza testo, finché non scrivi `/hypomnema:resume` (o `/hypomnema:riprendi`);
- le note che salvi in pausa sono marcate «author not verified (witnesses paused)»;
- `status` dice «IN PAUSA dal …», e a ogni nuova sessione un avviso te lo ricorda;
- per un solo messaggio basta cominciarlo con `#privato`;
- per spegnerli del tutto: `attivo = false` nella configurazione.

**Aggiornare**, quando su GitHub viene unita una nuova versione:

```
claude plugin marketplace update hypomnema
claude plugin update hypomnema@hypomnema
```

La nuova versione vale dalla sessione successiva (o dopo `/reload-plugins`).

**Disinstallare:** `claude plugin uninstall hypomnema@hypomnema`. La cartella `~/Hypomnema` resta
dov'è: decidi tu se tenerla.

**Il quaderno protetto.** Un plugin non può portare con sé regole di permesso, quindi la protezione
la fa un aggancio (`PreToolUse`): quando Claude prova a modificare con i suoi strumenti (Edit, Write,
NotebookEdit) un file del quaderno o la configurazione, l'aggancio lo ferma. Non ferma un comando o
uno script lanciato da Claude: per un divieto in più sui comandi più comuni puoi aggiungere a mano,
in `~/.claude/settings.json`, le regole che stampa `py "<cartella del plugin>/programma.py" impostazioni-claude`.

**Claude può mettere in pausa i testimoni da solo?** Non con gli strumenti normali: i comandi di
pausa e ripresa li riconosce il testimone solo nei messaggi che arrivano come tuoi, i due comandi
con la barra non possono essere lanciati da Claude (`disable-model-invocation`), e i file del
testimone sono protetti dall'aggancio. Restano due vie, e la skill le vieta a Claude: scrivere nei
file con uno script, oppure creare un'attività programmata che manda «/hypomnema:pausa» come
messaggio (Claude Code tratta anche quelle come messaggi). In ogni caso **la pausa si vede**: resta
nel testimone con data e ora, `status` la mostra, e l'avviso d'inizio sessione la ricorda.

**Non usare insieme** il plugin installato e l'avviabile di Windows: gli agganci partirebbero due volte.

## Usarlo nella chat di Claude

Da ottobre 2026 Hypomnema si sviluppa come **skill per la chat di Claude** (claude.ai, app desktop
e mobile). Il lavoro sporco lo fa Claude: a te chiede solo il permesso per la cartella dove sta il
quaderno, sul tuo computer.

> La modalità chat è nuova e **non è ancora stata provata dal vero**: le parti che dipendono dai
> programmi sono provate dai test, quelle che dipendono dall'app di Claude no.

**Cosa succede.**

1. Claude scarica i programmi di Hypomnema (la versione principale, `main`, da questo repository)
   nel suo **computer di lavoro**: un piccolo computer temporaneo della chat, che sparisce a fine
   conversazione.
2. Ti chiede il permesso per la cartella **Hypomnema** nella tua cartella utente
   (`C:\Users\<nome>\Hypomnema` su Windows, `~/Hypomnema` su macOS e Linux) e copia nel computer
   di lavoro le note e il registro. La prima volta il quaderno non c'è: Claude te lo dice, e il
   quaderno nasce con la prima nota.
3. Quando c'è qualcosa da ricordare, Claude propone la nota allo sportello, come sempre: le regole
   sono le stesse e Claude non salva mai una nota a mano. Poi riporta sul tuo computer **solo i
   file che lo sportello ha creato o allungato**: prima il registro, poi la nota nuova. Lo scrive
   con un controllo che rifiuta la scrittura se nel frattempo il file sul tuo computer è cambiato.
   Il registro si allunga a ogni proposta, quindi se la sua scrittura riesce nessun'altra chat ha
   scritto nel frattempo; se viene rifiutata, Claude non forza e non scrive la nota, ricopia il
   quaderno, riprova e te lo dice. Anche le proposte rifiutate finiscono nel registro, che quindi
   viene riportato anche dopo un rifiuto. Ogni file riportato parte da una cartella nuova del
   computer di lavoro e, appena scritto, Claude lo ricopia e lo confronta byte per byte con
   `confronta`: se non è identico si ferma e te lo dice.
4. Quando chiedi «cosa avevo deciso su…», Claude cerca nel quaderno con il cercatore.
5. A inizio chat Claude controlla che ogni nota abbia la sua riga ACCETTATA nel registro, e
   viceversa, e che nel registro non ci siano righe estranee (`check`). Se qualcosa non corrisponde, per esempio per un salvataggio rimasto a
   metà, te lo dice; non ripara niente da solo.
6. **L'archivio della chat.** Se nelle impostazioni di Claude è attivo il permesso per cercare e
   consultare le chat passate, Claude rilegge la conversazione dall'archivio di Anthropic e la copia
   nel quaderno con il comando `archivio`: i tuoi messaggi in `archivio-chat.jsonl`, le sue risposte
   in `diario-chat.jsonl`, con la data, l'ora, il numero del turno e l'indirizzo della chat. Lo
   strumento dà al massimo 50 turni per volta: Claude legge a pezzi. I doppioni si riconoscono dal
   numero del turno (l'ora arriva solo al minuto), e dai tuoi messaggi si tolgono gli avvisi tecnici
   che l'app inserisce tra `<system-reminder>` e `</system-reminder>`. Lo strumento dell'archivio
   scrive «<», «>» e «&» come «&lt;», «&gt;» e «&amp;»: Claude copia il testo così com'è, e il
   programma `archivio` lo riporta ai segni veri con una regola fissa (così riconosce anche gli
   avvisi scritti in quella forma). Unico limite: se tu scrivessi davvero «&lt;» a mano, nel
   quaderno diventerebbe «<». Lo fa ogni 5 scambi (si
   regola con `copia_ogni`), prima di salvare una nota e quando dici che chiudi. Così la
   conversazione finisce nel quaderno da sola, e all'inizio di una chat nuova Claude lancia `recap`
   e ti dice in tre righe dove eravate rimasti.

**Tre livelli di fiducia.** Ogni nota tua dice quanto è sicuro che quelle parole siano tue:

| Livello | Dove | Cosa c'è scritto nella nota |
|---|---|---|
| **Verificato** | Claude Code, con il testimone | `text found in the message of <data e ora>` |
| **Riscontrato sull'archivio della chat** | Chat, con l'archivio | `text matched in the chat archive <indirizzo>, message of turn <numero> (<data e ora>, copied by Claude)` |
| **Non verificato** | Chat senza archivio, o testo che non si trova | `author not verified (chat, no witness)` |

Dalla versione 0.5.0 queste diciture si scrivono in inglese (vedi «Lingua per ruolo»); le note
salvate prima conservano la loro dicitura italiana («testo trovato…», «testo riscontrato…»,
«autore non verificato…»).

In chat una nota con parole che nell'archivio non ci sono **non viene rifiutata**: resta «non
verificata», perché l'archivio può non essere disponibile o non ancora copiato. Nel diario
(`diary`) le righe copiate dall'archivio dicono «archivio della chat …, copiato da Claude»; quelle
senza indicazione vengono dai testimoni di Claude Code.

**Il permesso richiesto.** Solo la cartella `Hypomnema`. In chat Claude non lancia comandi sul tuo
computer: legge e scrive solo lì, e non copia il file del testimone (`testimone.jsonl`), se c'è.

**I limiti.**

- **Niente testimoni.** In chat i tuoi messaggi e le risposte di Claude arrivano solo a Claude:
  nessun programma li registra mentre scrivi. Al loro posto c'è la copia dall'archivio della chat
  (punto 6), che però **passa da Claude**: Claude potrebbe alterarla. Per questo le note
  riscontrate così portano l'indirizzo della chat, e chiunque può aprirla per controllare. Senza
  archivio, le tue note sono salvate come «author not verified (chat, no witness)», così si
  distinguono da quelle dell'avviabile con il testimone spento («testimone spento»).
- **Dal telefono o da un altro computer** Hypomnema funziona solo se la chat è collegata al tuo PC,
  con il PC acceso e l'app desktop di Claude aperta; altrimenti è la modalità prova.
- **Serve l'app desktop di Claude aperta e collegata al computer**: è lei che dà a Claude gli
  strumenti per la tua cartella.
- **Senza computer collegato è solo una prova** (sito, app mobile): il quaderno vive nella chat e
  sparisce quando la chiudi. Claude te lo dice prima di cominciare.
- Il computer di lavoro deve poter scaricare da GitHub e avere Python 3.10 o più recente.
- Meglio una chat alla volta sullo stesso quaderno: se due chat scrivono insieme, il controllo sui
  file cambiati ferma la seconda, che deve ricominciare.

### Chat collegata al computer: scrive direttamente sul quaderno (dalla 0.6.1)

Quando la chat è collegata al tuo computer con l'app desktop, Claude ha anche una riga di comando
su una macchina Linux che vede le cartelle che hai collegato (per esempio la cartella Hypomnema
come `$HOME/mnt/Hypomnema`). Se lì trova il programma aggiornato, Claude **propone direttamente
allo sportello del quaderno vero**: niente copia del quaderno, niente file da riportare e
ricontrollare. Per salvare una nota basta **un comando** (due, se prima copia la conversazione
dall'archivio della chat), invece di otto-dieci. Lo sportello resta il guardiano, come con Claude
Code.

**Una volta sola, su Windows** (PowerShell), nella cartella Hypomnema:

```powershell
cd $env:USERPROFILE\Hypomnema
git clone --branch main https://github.com/angelomaccarinelli8-sys/hypomnema.git programma-chat
```

Per aggiornarla, quando esce una versione nuova: `git -C programma-chat pull`. Serve a te, perché
dalla macchina della chat GitHub non si raggiunge. La cartella `programma` che hai già (quella
dell'avviabile) non si tocca.

**La configurazione della chat** è un file a parte, `hypomnema-chat.toml`, accanto al tuo
`hypomnema.toml`: stesso quaderno, testimone spento (`modalita = "chat"`), archivio della chat. La
prima volta lo crea Claude dal modello (`programma-chat/chat/hypomnema-chat.toml`), senza
sovrascrivere niente; puoi anche copiarlo tu:

```powershell
Copy-Item programma-chat\chat\hypomnema-chat.toml hypomnema-chat.toml
```

**Il fuso orario (dalla 0.7.0) viene dal sistema operativo del tuo computer.**
- **Sul tuo computer** vale sempre l'ora del sistema: non serve la tabella dei fusi, e nemmeno una
  riga `fuso` nella configurazione. Se la configurazione ha una riga `fuso` diversa dal sistema,
  `status` lo dice, ma non blocca niente.
- Hypomnema legge anche il **nome** del fuso del sistema (su Windows con la tabella ufficiale di
  Unicode CLDR che collega i nomi di Windows, come «W. Europe Standard Time», a quelli come
  `Europe/Rome`, con la tua regione) e lo scrive nel file `fuso-del-sistema.jsonl` del quaderno, a
  inizio sessione e a ogni proposta, **solo quando cambia**: una riga in più, vale l'ultima. Se usi due
  computer con fusi diversi, vale quello che ha scritto per ultimo.
- **Le macchine in UTC** (la chat collegata al computer, le sessioni in cloud) usano, in quest'ordine:
  la riga `fuso` della loro configurazione, se c'è; poi l'ultima riga del file del quaderno; poi UTC,
  e `status` lo dice chiaramente («Fuso orario: UTC, quello di questa macchina: …»). Un fuso che lì
  non si trova si salta: niente si blocca.
- Una macchina è «in UTC» se il nome del suo fuso è UTC (UTC, Etc/UTC, Zulu…), oppure se il nome non
  si legge e l'ora è quella universale.

Il tuo `hypomnema.toml` (quello di Claude Code, con i testimoni accesi) resta com'è: la chat non lo
usa. Le note salvate dalla chat sono marcate come sempre: «chat, no witness», oppure riscontrate
sull'archivio della chat.

**Python 3.10.** La macchina della chat ha Python 3.10. Hypomnema funziona dal 3.10: per leggere
la configurazione usa `tomllib` di Python (dal 3.11) oppure, se manca, la sua copia di
[tomli](https://github.com/hukkin/tomli) (licenza MIT, di Taneli Hukkinen) in
[`hypomnema/_tomli`](hypomnema/_tomli/LEGGIMI.md). Niente da installare.

**Se qualcosa non va** (la macchina non risponde, il programma manca o è vecchio, un errore),
Claude te lo dice in una riga e usa la procedura con la copia descritta sopra.

**Claude Code e la chat insieme.** Possono scrivere sullo stesso quaderno nello stesso momento.
Per ogni passaggio lo sportello prende un **blocco** su un file vuoto. Dalla 0.7.0 il file sta nella
**cartella temporanea del computer** (`hypomnema-blocchi`, con un nome calcolato dal percorso del
quaderno), non più nel quaderno: così nel quaderno non nasce niente che possa finire, per esempio, in
git. Il file `quaderno/.sportello.lock` lasciato dalla 0.6.1 non serve più e il programma non lo tocca:
puoi cancellarlo a mano, oppure, se il quaderno sta in git, aggiungere `.sportello.lock` al
`.gitignore`. Se il quaderno è occupato per più di 10 secondi lo sportello si ferma con un errore,
senza scrivere, e basta riproporre.

**Limite, provato il 18/10/2026:** il blocco funziona solo tra programmi sulla **stessa macchina**
(due sessioni di Claude Code su Windows, due chat). **Tra Windows e la macchina della chat non passa:**
con il blocco tenuto da Windows, una proposta dalla chat è entrata subito. Tra le due macchine restano
queste difese, che non hanno bisogno di cancellare niente:
- ogni nota si crea con apertura esclusiva: due proposte insieme non prendono mai lo stesso numero e
  una nota non viene mai sovrascritta;
- ogni riga del registro (e dei file dei testimoni e dell'archivio) si aggiunge con **una sola
  scrittura in aggiunta**, decisa dal sistema (su Windows con il solo permesso di aggiungere): due
  righe non si sovrappongono;
- chi trova una nota appena creata e non ancora scritta la rilegge per un attimo invece di fermarsi;
- in chat Claude lancia **`check` subito dopo ogni proposta** e ti dice se trova qualcosa che non va
  (per esempio una nota senza la sua riga nel registro).

Quello che resta scoperto: due passaggi insieme possono controllare le regole sullo stesso quaderno
nello stesso istante. Per una nota nuova non succede niente di male; per due cambiamenti della stessa
nota (per esempio due chiusure) il secondo trova il file della versione già scritto e viene rifiutato.
Se lavori in Claude Code e in chat nello stesso momento, è meglio non salvare dalle due parti insieme.

**Stessi byte da Windows e da Linux.** Tutti i file del quaderno si scrivono sempre in UTF-8 con
l'a capo `\n`, scelti in modo esplicito, su ogni sistema: una nota scritta da Claude Code su
Windows e una scritta dalla chat su Linux hanno la stessa forma, byte per byte.

**Come aggiungere la skill.** La skill è la cartella
[`skills/hypomnema`](skills/hypomnema/SKILL.md) (dalla 0.7.0 con cinque file: `SKILL.md` e i quattro
che Claude legge solo quando servono), già pronta nella release come
[`hypomnema-skill.zip`](https://github.com/angelomaccarinelli8-sys/hypomnema/releases/latest/download/hypomnema-skill.zip).
Nella chat di Claude le skill
personali si aggiungono dalle impostazioni, caricando la cartella compressa in un file `.zip`: il
percorso esatto nelle impostazioni lo verificheremo nella prima prova.

**Come funziona dentro.** Claude usa la configurazione [`chat/hypomnema-chat.toml`](chat/hypomnema-chat.toml)
(testimone spento e `modalita = "chat"`). Prima di ogni proposta fotografa il quaderno con
`istantanea`; dopo, `cambiati` elenca i file da riportare e controlla che sia successo solo ciò che
lo sportello sa fare: creare note annotate come ACCETTATA nel registro, e allungare il registro
con righe nella forma dello sportello. Se trova altro, per esempio una nota cambiata a mano o del
testo libero nel registro, risponde con un errore e Claude non riporta niente. Una riga scritta a
mano ma con la forma giusta non si può distinguere da una vera: è un limite dichiarato.
`check` confronta note e registro, in sola lettura.

## Dove funziona davvero

Hypomnema ha bisogno di due cose: che Claude possa lanciare i programmi sul tuo computer, e che
Claude Code lanci i testimoni. Dove provato, l'ho provato su Windows 11 con Claude Code 2.1.274.

| Dove | Funziona? | Come lo so |
|---|---|---|
| Claude Code nel terminale, con il plugin installato | **Sì** | **Provato** il 11/10/2026 su Windows 11 con Claude Code 2.1.274: installazione dal catalogo su GitHub (con una configurazione di Claude temporanea) e sessioni non interattive (`claude -p`) con la copia installata e una cartella dei dati temporanea: prima volta, testimoni, skill, scrittura nel quaderno bloccata, pausa e ripresa con i comandi. |
| App desktop di Claude, scheda Code, con il plugin installato | **Sì**, come nel terminale | **Dalla documentazione** di Claude Code: nella scheda Code i plugin si installano dal pulsante **+**, e impostazioni, agganci e skill valgono come nel terminale. Non provato. |
| Claude Code nel terminale (PowerShell), aperto con l'avviabile | **Sì** | **Provato** con dati inventati e una sessione non interattiva (`claude -p`): il testimone ha registrato il messaggio, la skill era disponibile, la scrittura nel quaderno è stata bloccata. Il doppio clic con una sessione normale lo prova Angelo. |
| Claude Code senza il plugin installato e senza l'avviabile | **No, resta spento** | **Provato**: nessuna skill, niente registrato. |
| Claude Code in VS Code (pannello dell'estensione) | Probabilmente sì, con il plugin installato | **Non provato.** Il pannello usa le stesse impostazioni di Claude Code; i plugin installati dovrebbero valere anche lì. |
| Chat di Claude nell'app desktop, collegata al computer | **Sì, in modalità chat**, senza testimone; dalla 0.6.1 direttamente sul quaderno, se c'è `programma-chat` | **Provato in parte** il 18/10/2026: la macchina Linux della chat vede la cartella Hypomnema e ha Python 3.10 (da qui nasce la 0.6.1). Il giro completo è provato dai test con Python 3.10; sulla macchina vera lo prova Angelo. Vedi «Usarlo nella chat di Claude». |
| Chat di Claude sul sito o nell'app mobile | **Solo come prova**: il quaderno sparisce a fine chat | **Non ancora provato**, come sopra. |

## Installazione per provarlo o svilupparlo

Serve **Python 3.10 o più recente** (da [python.org](https://www.python.org/downloads/)).
Non servono altre librerie (con Python 3.10 si usa la copia di tomli che è nel repository).

1. Scarica il repository (pulsante *Code* → *Download ZIP*, oppure `git clone`).
2. Apri un terminale nella cartella scaricata.
3. Controlla che funzioni:

   ```
   python -m unittest
   ```

   (su Windows, se `python` non c'è, usa `py -m unittest`). Deve finire con `OK`.

4. Apri `hypomnema.toml` e scegli dove tenere il quaderno (di base: la cartella `quaderno`
   accanto al file, esclusa da git).

Facoltativo: `python -m pip install -e .` installa il comando `hypomnema`, utilizzabile da
qualunque cartella. In quel caso indica dov'è il file di configurazione con la variabile
d'ambiente `HYPOMNEMA_CONFIG` oppure con `--config`.

## Uso

Dalla cartella di Hypomnema:

```
python -m hypomnema propose esempi/01-nota-accettata/nota.json
python -m hypomnema search orto                # aggiungi --all per vedere anche le note chiuse
python -m hypomnema reminders                  # i promemoria con la data arrivata o passata
python -m hypomnema recap                      # dove eravamo rimasti
python -m hypomnema review                     # che cosa conviene guardare (solo lettura)
python -m hypomnema witness messaggio.json     # di solito lo lancia Claude Code da solo
python -m hypomnema status                     # testimone acceso? ultimo messaggio registrato?
python -m hypomnema snapshot > prima.json      # chat: fotografa il quaderno prima di una proposta
python -m hypomnema changed prima.json         # chat: quali file riportare sul computer
python -m hypomnema check                      # note e registro corrispondono? righe estranee?
python -m hypomnema compare a.md b.md          # due file identici byte per byte?
python -m hypomnema fingerprint giorni.py      # l'impronta di un file, come per i blocchi di codice omessi
python -m hypomnema diary fragole --around     # cerca nel diario, con i messaggi vicini
```

Su Windows scrivi `py` al posto di `python`:

```
py -m hypomnema search orto
```

I nomi italiani dei comandi delle versioni precedenti funzionano per sempre: `cerca` è `search`,
`proponi` è `propose`, `promemoria` è `reminders`, `stato` è `status`, `controlla` è `check`,
`diario` è `diary` (con `--ultimi` e `--intorno` al posto di `--last` e `--around`), e così via.

Una nota proposta è un piccolo file JSON:

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

Lo sportello risponde `ACCETTATA` (e dice il numero della nota) oppure `RIFIUTATA` con i motivi.
Il formato completo è in [FORMATO.md](FORMATO.md).

### Lingua per ruolo

Dalla versione 0.5.0 Hypomnema usa **l'italiano per il contenuto e l'inglese per la struttura**:

- **in italiano** restano le tue parole nelle note, tutto quello che leggi tu (i messaggi dei
  comandi come «ACCETTATA» o «Trovate 2 note», il recap, questo README) e le frasi che Claude ti dice;
- **in inglese** vanno i nomi dei comandi e dei campi, i loro valori, i motivi di rifiuto dello
  sportello (sono regole rivolte a Claude) e le istruzioni della skill per Claude.

Le note che hai già **non si convertono e non si toccano**: il programma legge tutte e due le forme.
Le note nuove si scrivono con i campi in inglese. Anche nelle proposte valgono tutti e due i nomi
(`autore: utente` è `author: user`), ma lo stesso campo non può comparire due volte (per esempio
`data` e `date` insieme).

| Prima (italiano) | Ora (inglese) | Valori |
|---|---|---|
| `data` | `date` | |
| `fonte` | `source` | |
| `autore` | `author` | `utente` → `user`, `claude` |
| `tipo` | `knowledge` | `dichiarata` → `stated`, `osservata` → `observed`, `dedotta` → `inferred` |
| `natura` | `kind` | `fatto` → `fact`, `idea`, `decisione` → `decision`, `discorso aperto` → `open`, `todo` |
| `testo` | `text` | |
| `contesto` | `context` | |
| `citazione` | `quote` | |
| `conferma_di` | `confirms` | |
| `corregge` | `corrects` | |
| `aggiorna` (dalla 0.6.0) | `updates` | |
| `riapre` (dalla 0.6.0) | `reopens` | |
| `riprendere_il` | `remind` | |
| `done` | `done` | |
| `da_risposta` | `from_reply` | `sì` → `yes` |
| `verifica` | `verification` | scritta dallo sportello |
| | `priority` (nuovo) | `high`, `normal`, `low` |

Non cambiano, perché sono formati interni che i file di oggi devono continuare a usare: le righe
del registro (`ACCETTATA`/`RIFIUTATA`), i file dei testimoni e le chiavi di `hypomnema.toml`.

### Che cos'è una nota: fact, idea, decision, open, todo

Il campo `kind` dice che cosa è una nota:

- `fact`: una cosa che è così;
- `idea`: una proposta (quelle di Claude sono sempre idee);
- `decision`: una decisione, **solo tua** (`author: user`);
- `open`: una questione aperta (prima si chiamava «discorso aperto»);
- `todo`: una cosa da fare.

### Ogni cambiamento è una versione nuova

Dalla 0.6.0 una nota non si cambia scrivendo una nota nuova che rimanda alla vecchia: **ogni
cambiamento è una versione nuova della stessa nota**. La nota 0049 diventa `0049.1`, poi `0049.2`:
ogni versione è un file vero (`note/0049.1.md`) con tutta la nota, il cambiamento applicato e in
fondo un blocco «Change» che dice quando, chi, che cosa e perché (con le tue parole, se il cambiamento
è tuo). I file di prima non si toccano e ogni versione ha la sua riga nel registro. Si cambia sempre
l'ultima versione.

| Vuoi… | Proposta | Il testo è |
|---|---|---|
| correggere il testo («no, era a marzo») | `"corrects": "0049"` | il testo nuovo |
| cambiare natura, priorità o data del promemoria | `"updates": "0049"` (o `aggiorna`) con `kind`, `priority` o `remind` | il motivo |
| chiudere una questione aperta, una cosa da fare o un promemoria | `"done": "0049"` oppure `"done": "0012, 0015"` | il motivo |
| riaprire una nota chiusa | `"reopens": "0049"` (o `riapre`) | il motivo |

```json
{
  "date": "2026-01-15",
  "source": "chat del 15 gennaio 2026 sull'orto",
  "author": "user",
  "knowledge": "stated",
  "kind": "decision",
  "done": "0012",
  "text": "la compostiera va nell'angolo nord"
}
```

- **Una correzione non chiude**: una cosa da fare corretta resta da fare.
- Chiusa e aperta sono **stati**: una nota chiusa si può riaprire, con il motivo («riaperta il …,
  perché …»). Con `done` il `kind` facoltativo dice che cosa è diventata la questione (`decision`,
  `fact` o `idea`).
- `done: 0012, 0015` crea una versione chiusa per ciascuna, con lo stesso motivo.
- **Gli `open` li chiudi e li riapri solo tu**, e solo tu fai diventare una nota una decisione,
  cambi la natura delle tue note e ne correggi il testo (sono le tue parole). Claude può chiudere e
  riaprire le cose da fare e i promemoria, e correggere le sue note.
- `fact`, `decision` e `idea` senza promemoria non si chiudono: si correggono o si cambiano.

Il `recap` e la ricerca leggono ogni nota per quello che è **adesso**. Non mostrano le cose da fare
o da decidere ormai chiuse: la ricerca dice quante ne ha nascoste, e `search <parola> --all` le
mostra, con la loro storia. Una questione chiusa come decisione invece è una decisione: compare in
«Ultime decisioni», con il suo codice (per esempio `✓D0049.3`). Il ✓ dice che è risolta, non che va
nascosta.

### Il codice della nota

Ogni nota si mostra con un codice: la lettera della sua natura davanti al numero, e `✓` se è chiusa.

```
F fatto · I idea · D decisione · O aperta · T da fare · ✓ chiusa
```

Per esempio `T0049.2` è una cosa da fare alla versione 2, `✓T0049.3` la stessa chiusa. La lettera si
mostra soltanto: quando Claude rimanda a una nota scrive solo il numero (`"0049"`). Se il tuo
terminale non mostra `✓`, puoi scegliere un altro segno in `hypomnema.toml`:

```toml
[codici]
chiusa = "x"
```

Un pezzo di recap dopo tre cambiamenti (dati inventati): la priorità del basilico alzata, la
compostiera passata da questione aperta a cosa da fare, poi il suo testo corretto.

```
Cose da fare: 2 di 2 (prima la priorità alta, poi dal più recente)
- [T0006.1] [alta] 2026-01-15: Seminare il basilico.
    ↳ T0006.1 2026-01-15 · user: priorità normal → high
- [T0004.2] 2026-01-15: Montare la compostiera nell'angolo nord.
    ↳ T0004.1 2026-01-15 · user: natura open → todo
    ↳ T0004.2 2026-01-15 · user: testo corretto

Legenda: F fatto · I idea · D decisione · O aperta · T da fare · ✓ chiusa
```

### Le note di prima

Le note salvate prima della 0.6.0 non si toccano: si leggono come versioni. Una vecchia correzione
(la 0050 con `corrects: 0049`) si mostra come `0049.1 (nota 0050)`; una vecchia nota con `done` come la
versione chiusa di ciò che chiude. Una nota, la sua correzione e una terza nota che le chiude entrambe
sono una storia sola: il recap non la mostra, `search --all` la mostra una volta. Se la nota che
chiudeva è a sua volta una cosa da fare o conferma un'idea, resta visibile anche da sola, così non si
perde niente. Le note con i campi italiani si mostrano esattamente come le nuove.

Le regole di oggi valgono anche per le note vecchie. Se una nota vecchia di Claude correggeva il testo
di una tua nota, o faceva smettere una questione aperta di essere aperta, resta nella storia ma non
vale: il testo resta il tuo, la questione resta aperta. La storia lo scrive («non applicato (catena
vecchia non permessa oggi)») e la revisione lo segnala: se quel cambiamento va fatto, lo decidi tu.

### La revisione

Il comando `review` (o `revisione`) guarda il quaderno con regole fisse e dice che cosa conviene
controllare, senza cambiare niente: le questioni aperte e le cose da fare ferme da più di 30 giorni
(si regola con `[revisione]` e `giorni`), i promemoria scaduti, le cose da fare nominate nel testo di
una nota successiva («la 0006 è fatta»), quelle con «ricordamelo» o «tra tre giorni» ma senza data, i
rami delle note vecchie (due correzioni della stessa nota) e le catene vecchie che oggi non sarebbero
permesse. Ogni riga dice che cosa si può fare; decidi tu. Claude la lancia a inizio chat, dopo il recap, e se trova qualcosa te lo dice in una riga.

### La priorità

Il campo facoltativo `priority` vale `high`, `normal` o `low` (senza priorità vale `normal`). È
**solo tua**: in una nota di Claude lo sportello la rifiuta, e Claude può al massimo proporla nel
testo di una sua idea. Per cambiarla: `"updates": "<numero>"` con la priorità nuova. Nel recap,
dentro ogni blocco, vengono prima le cose a priorità alta (segnate `[alta]`), poi le normali, poi le
basse (`[bassa]`).

### Quando cambiano le regole del quaderno: la nota-regola

Se decidi che da un certo momento il quaderno funziona in modo diverso (per esempio «le spese le
segno solo come cose da fare»), non serve cambiare niente nei programmi: chiedi a Claude di salvare
una **decisione** con le tue parole, che cominci con «Da questa nota in poi…». Per esempio:
«Da questa nota in poi le spese le segno solo come todo.» È una decisione come le altre: compare nel
recap e nelle ricerche, e Claude la rispetta come regola del quaderno.

### Ricerca, promemoria e «dove eravamo rimasti»

Niente si cancella. Quando il cercatore trova una nota, mostra la sua **ultima versione** e sotto la
sua storia (che cosa è cambiato, quando, chi e perché), anche se la parola cercata era solo in una
versione vecchia. Così Claude non può ripetere un errore che una correzione aveva già sistemato.

Il cercatore elenca le note **dalla più recente alla più vecchia** (cioè dal numero più alto), e
trova anche le parole dentro i nomi composti: `orto` trova `orto_balcone.py`, `semi-orto` e
`orto/vasi`. Le note restano scritte in fondo al quaderno come sempre: cambia solo l'ordine in cui
si mostrano.

**Promemoria.** Una nota con `"remind": "2026-10-20"` è un promemoria. Il comando `reminders`
elenca quelli con la data arrivata o già passata, dal più vecchio. Per chiuderlo: `"done": "0007"`
(«era giusto ed è fatto»), e il promemoria esce dagli scaduti. Per spostarlo: `"updates": "0007"` con
il `remind` nuovo. Una correzione del testo lo lascia tra gli scaduti.

**Dove eravamo rimasti.** Il comando `recap` (nel plugin anche `/hypomnema:recap`) mostra in poche
righe, con regole fisse: i promemoria scaduti, gli ultimi 5 discorsi aperti, le ultime 5 cose da
fare, le ultime 5 decisioni e le ultime 10 righe del diario, senza le note chiuse e con le priorità
alte per prime. Dalla 0.7.0, dopo la priorità, ogni blocco va **dal giorno dell'ultima versione più
recente** (una nota vecchia corretta oggi sale in cima; una versione che mette solo le etichette non
conta), e a parità di giorno dal numero più alto; i promemoria scaduti restano in ordine di scadenza.
Claude lo lancia a inizio chat, così non deve scegliere da solo le parole da
cercare. I numeri si regolano nella sezione facoltativa `[recap]` di `hypomnema.toml` (con
`voci_diario = 0`, dalla 0.7.0, il blocco del diario non compare):

```toml
[recap]
discorsi_aperti = 5
todo = 5
decisioni = 5
voci_diario = 10
```

### Le etichette CHI e COSA (dalla 0.7.0; le COSA dallo sportello dalla 0.8.0)

Una nota può avere delle **etichette**: CHI (le persone, `who`) e COSA (i progetti o gli argomenti,
`about`). Servono a leggere il quaderno per persona o per progetto.

**Dalla 0.8.0 le COSA le mette lo sportello.** Cerca nel testo della nota (il campo `text`) le
etichette della lista `cosa` e aggiunge quelle che trova, scritte come nella lista, una volta sola e
senza limite di numero. Cerca la parola intera, come `search`, senza badare alle maiuscole: «l'Orto»
dà `orto`, «ortografia» no. Nella nota le trovi in `about`, e la riga `- labels from text: about orto`
dice quali ha messo lo sportello; le altre sono state proposte a mano. A ogni versione nuova (una
correzione, una chiusura…) lo sportello le ricalcola dal testo; quelle proposte a mano non le tocca
mai. Le **CHI** restano solo a mano, al massimo due per nota, come nella 0.7.0. La regola è fissa e
non capisce il senso: «è in gioco la scadenza» dà `gioco`, «i bilanci» non dà `bilancio`. Il comando
`matches` (`riscontri`) mostra, in sola lettura, dove lo sportello ha trovato ogni COSA.

**La lista la scrivi tu**, nel file `etichette.toml` dentro la cartella del quaderno (accanto a
`registro.md`): così la leggono tutte e due le configurazioni dello stesso quaderno (Claude Code e la
chat) e la lista è una sola. Un modello commentato, con etichette inventate, è
[`esempi/etichette.toml`](esempi/etichette.toml): copialo nel quaderno e scrivi le tue.

```toml
chi = ["Anna", "Marco"]
cosa = ["orto", "bilancio", "gioco"]
```

- Se il file manca, nessuna nota può avere etichette. Se è scritto male, il comando si ferma con un
  errore chiaro e non scrive niente: dalla 0.8.0 vale per **ogni** proposta, perché lo sportello legge
  la lista ogni volta. `status` dice se il file è letto bene.
- Nelle proposte a mano il confronto è esatto: «Orto» non è «orto». Un'etichetta fuori dalla lista viene
  rifiutata, con l'elenco di quelle ammesse.
- Claude non scrive mai il file. In un quaderno dove scrive solo Claude (per esempio il diario di
  cantiere di Claude Code su un progetto) Claude ti propone la lista nel suo messaggio, e tu la salvi
  nel file.
- Le CHI (e le COSA che non sono scritte nel testo) le propone chi propone la nota: nelle note di
  Claude, Claude; nelle tue, Claude te le propone e tu puoi cambiarle.
- Le note vecchie non si toccano: le etichette si aggiungono con una versione nuova (`updates`), e
  ogni versione nuova prende anche le COSA del suo testo. Claude può etichettare una tua nota solo se
  non ha ancora etichette proposte a mano (quelle dello sportello non contano); poi le cambi solo tu. Una versione
  che cambia solo le etichette non sposta la nota nel recap e non riazzera i giorni della revisione.
- `source` resta la chat da cui viene la nota: non è un'etichetta.

```
search --about orto                     # tutte le note su orto (la parola si può omettere)
search basilico --who Anna --about orto # con la parola e tutte e due le etichette
recap --cosa orto                       # il recap delle sole note su orto (senza il diario)
labels                                  # le etichette, con quante note ha ognuna (COSA: dal testo e a mano)
matches                                 # dove lo sportello ha trovato ogni COSA (--cosa orto per una sola)
```

Si possono ripetere i filtri, e devono valere tutti. I nomi italiani sono `--chi`, `--cosa`,
`etichette` e `riscontri`.

**Due copie del programma** (il plugin di Claude Code e `programma-chat`) leggono lo stesso
`etichette.toml`. Il file non cambia rispetto alla 0.7.0, quindi una copia rimasta alla 0.7.0 non si
ferma: semplicemente non aggiunge le COSA dal testo. Aggiornale tutte e due.

### Gli schemi del tuo modo di parlare e il riordino (dalla 0.9.0)

- `patterns` (`schemi`) mostra, in sola lettura, le sequenze di parole tipiche di ogni tipo delle tue note, ricavate
  dal quaderno con regole fisse (vedi FORMATO, «Gli schemi del modo di parlare»); `patterns --misura` dice quante volte
  indovinano il tipo. Quando salvi una nota tua che suona come un altro tipo, `propose` aggiunge una riga
  «SUGGERIMENTO (non cambia niente)»: il tipo lo scegli sempre tu.
- Le COSA trovate nel testo valgono anche per le note scritte prima: un'etichetta aggiunta alla lista vale subito.
- `integrates` (`integra`) aggiunge parole nuove in fondo a una nota, oppure (con `from_note`) il testo di un'altra nota
  sulla stessa cosa, che esce dal recap.
- `cancels` (`annulla`) annulla una nota che non vale più (codice con la C: `CD0156.1`); `reopens` la fa valere di nuovo.

### Le tue parole e quelle di Claude restano separate

In una nota con `author: user`, il `text` sono **le tue parole esatte**. Se Claude vuole
aggiungere una spiegazione (di cosa si parlava, a cosa ti riferivi), la mette in un campo a parte,
`context`, che nel quaderno compare sotto il titolo "Context written by Claude" (nelle note di
prima della 0.5.0: "Contesto scritto da Claude"):

```json
{
  "date": "2026-01-15",
  "source": "chat del 15 gennaio 2026 sul progetto dell'orto",
  "author": "user",
  "knowledge": "stated",
  "kind": "fact",
  "text": "Il fico va potato solo quando ha perso tutte le foglie.",
  "context": "Detto parlando del fico in vaso sul terrazzo."
}
```

Le note scritte da Claude (`author: claude`) sono tutte parole sue: lì il `context` non serve.
Se si basano su qualcosa che hai detto, Claude può riportare le tue parole nel campo `quote`.

Dalla 0.7.0 il `context` si può mettere anche nei **tuoi cambiamenti** (`done`, `updates`,
`reopens`): il motivo resta con le tue parole («Fatto ieri sera.»), e la spiegazione di Claude («Riferito
al rinvaso del limone.») va a parte, nel blocco del cambiamento, sotto «Context written by Claude». La
ricerca la mostra nella storia: «chiusa il …, perché «Fatto ieri sera.» (contesto: «…»)».

### Testo incollato: va bene così

Hypomnema è un quaderno di appunti, come gli hypomnemata antichi: raccogliere passi letti
altrove è proprio lo scopo. Se incolli in un messaggio un testo che non hai scritto tu (un passo
di un libro, una spiegazione di Claude, un appunto), conta come portato da te nel quaderno: la
nota è tua (`author: user`). **Da dove viene lo dice il campo `source`**, per esempio:

- `"source": "dal libro «Il quaderno dell'ortolano»"`
- `"source": "dalla spiegazione di Claude del 15 gennaio 2026"`
- `"source": "mio pensiero"`

Non c'è nessuna regola che distingua il testo scritto da quello incollato.

### Salvare le risposte di Claude

Puoi chiedere a Claude di conservare una sua risposta, in due modi:

- **«Salva questa risposta di Claude»**: la nota è **di Claude** (`author: claude`). Il testo è il
  pezzo di risposta che indichi; è un'idea o un fatto, mai una decisione.
- **«Questa risposta la faccio mia»**, incollando il pezzo nel messaggio: la nota è **tua**
  (`author: user`), con la fonte che dice da quale risposta di Claude viene (per esempio
  «risposta di Claude dell'11 ottobre 2026»). Può essere anche una decisione, perché l'adozione è
  tua. Con il testimone acceso il testo incollato viene verificato come sempre.

Nel primo caso la nota ha il campo `from_reply: "yes"`: con il testimone delle risposte acceso
(vedi «Il testimone delle risposte e il diario») lo sportello controlla che il testo sia davvero
in una risposta di Claude registrata; altrimenti la nota è salvata come «reply not verified».

Indica o incolla **solo il pezzo che conta**, non tutta la risposta: le note brevi si ritrovano
meglio.

### Il segno `>` per le citazioni (facoltativo)

Per chi vuole essere più preciso: se in un messaggio inizi alcune righe con `>` (il segno
classico per riportare parole altrui), il testimone registra il messaggio identico e in più annota
quali righe erano marcate. Una nota il cui testo viene tutto da righe marcate viene salvata con la
dicitura "citazione riportata dall'utente". Per esempio:

```
Ho trovato questo passo e lo voglio conservare:
> Un orto non si finisce mai:
> si continua, una stagione dopo l'altra.
Mi sembra il modo giusto di pensarci.
```

Una nota con il testo "Un orto non si finisce mai: si continua, una stagione dopo l'altra." porta
la dicitura; una nota che prende anche la riga del tuo commento no. Senza il segno tutto funziona
come sempre. Il segno si può cambiare in `hypomnema.toml` (`segno_citazione`).

### Con Claude

La skill (`skills/hypomnema/SKILL.md`) spiega a Claude come usare il quaderno. In Claude Code la
porta il plugin installato (vedi «Installa il plugin in Claude Code»); per una sola sessione, senza
installarlo, dalla cartella del programma: `claude --plugin-dir .`

## Il testimone

**Il problema.** Una nota può dire `author: user`, ma chi la scrive è Claude. Senza un
controllo, il programma dovrebbe fidarsi.

**La soluzione.** Il testimone è un piccolo programma che Claude Code lancia ogni volta che invii
un messaggio, *prima* che Claude lo legga. Il programma aggiunge il testo esatto del messaggio, con
data e ora, in fondo a un file. Lo sportello cerca il `text` di ogni nota con `author: user` in
quel file, parola per parola: se non lo trova, rifiuta la nota.

**Cosa registra.** Il testo di ogni messaggio che scrivi a Claude in questo progetto, con data e
ora. Non registra le risposte di Claude. Se incolli un testo nel messaggio, il testimone registra
anche quello.

**Dove.** Nel file `testimone.jsonl` dentro la cartella del quaderno (di base `quaderno/`).
È un file di testo: puoi aprirlo e leggerlo quando vuoi. Il quaderno e il testimone sono esclusi
da git (`.gitignore`) e i programmi non si collegano a internet: **non lasciano mai il tuo computer**.

**Come si accende e si spegne.** In `hypomnema.toml`, sezione `[testimone]`:
`attivo = true` per accenderlo, `attivo = false` per spegnerlo. Nel file del repository (copia di
sviluppo) **è spento**; nella configurazione in uso (`~/Hypomnema/hypomnema.toml`, creata la prima
volta dal plugin o dall'avviabile) è acceso. Per fermarlo per un po': `/hypomnema:pause`.
Da spento non registra niente, e le note con `author: user` vengono salvate con la scritta
ben visibile "author not verified (witness off)".

**Messaggi privati.** Se un messaggio inizia con `#privato`, il testimone non ne registra il
testo: annota solo data e ora con "messaggio privato, non registrato". Il prefisso si cambia in
`hypomnema.toml` (`prefisso_privato`).
**Attenzione: un messaggio privato non finisce nel testimone, ma Claude lo legge comunque**, come
ogni altro messaggio. "Privato" vuol dire solo che le sue parole non vengono registrate; la skill
chiede a Claude di non farne note.

**Come è collegato.** Gli agganci stanno nel plugin, in `hooks/hooks.json`: all'avvio della sessione
(`SessionStart`), a ogni messaggio (`UserPromptSubmit`), alla fine di ogni risposta (`Stop`) e prima
che Claude modifichi un file (`PreToolUse`). Lanciano `programma.py` dalla cartella del plugin
(`${CLAUDE_PLUGIN_ROOT}`) con `py` se esiste (Windows), altrimenti con `python3` (macOS e Linux).
La configurazione è `~/Hypomnema/hypomnema.toml`, oppure quella indicata dalla variabile
`HYPOMNEMA_CONFIG` (la imposta l'avviabile).

Con l'avviabile, le regole che vietano a Claude di modificare il quaderno e la configurazione le
calcola `impostazioni-claude` e l'avviabile le passa a Claude Code con `--settings`; con il plugin
installato lo fa l'aggancio `PreToolUse`. Nella copia di sviluppo il file `.claude/settings.json` vieta in più di modificare la
cartella `quaderno/` di prova.

### Il testimone su Windows

Su Windows Claude Code lancia gli agganci con **Git Bash**, se è installato (arriva insieme a
Git per Windows), altrimenti con **PowerShell**. L'aggancio di Hypomnema funziona così com'è con
Git Bash e il comando `py`. Per controllare:

1. In PowerShell: `py --version` deve rispondere Python 3.12 o più recente.
2. `Test-Path "C:\Program Files\Git\bin\bash.exe"`: `True` vuol dire che Git Bash c'è.
3. Con il plugin installato, apri Claude Code e scrivi un messaggio, per esempio "prova del testimone".
4. Chiedi a Claude di lanciare `status`: l'ultimo messaggio registrato deve essere "prova del testimone".

**Se Git Bash non c'è** (il punto 2 risponde `False`), hai due strade:
- installare Git per Windows (consigliato: serve anche per gli aggiornamenti), oppure
- nel file `hooks/hooks.json` del plugin, sostituire ogni riga `"command": ...` con due righe come
  queste (al posto di `testimone` il comando di quell'aggancio: `avvio`, `risposte`, `protezione`):

  ```json
  "command": "py",
  "args": ["${CLAUDE_PLUGIN_ROOT}/programma.py", "testimone"]
  ```

  Così Claude Code lancia `py` direttamente, senza passare da nessuna shell. Un aggiornamento del
  plugin rimette il file com'era: va rifatto dopo ogni aggiornamento.

Se il messaggio non viene registrato, in Claude Code il comando `/hooks` mostra gli agganci
attivi; un errore del testimone compare come avviso nella chat, ma non blocca mai il messaggio.

**I limiti, detti onestamente.**
- Il divieto di modificare il quaderno vale nelle sessioni con il plugin installato (aggancio
  `PreToolUse`) o aperte con l'avviabile (regole di permesso): in una sessione senza nessuno dei
  due Hypomnema è spento, e il divieto sul quaderno in uso non c'è.
- Il divieto vale per gli strumenti di Claude, non per il computer: tu, o chiunque abbia accesso al
  tuo computer, può aprire e modificare il file del testimone. Anche un programma lanciato da
  Claude (per esempio uno script Python) non è fermato dal divieto: lo impedisce solo la skill, che
  lo vieta a Claude. Per un blocco completo serve il sandbox di Claude Code.
- Il testimone dimostra che quelle parole erano in un tuo messaggio, non che le abbia scritte tu:
  un testo incollato conta come portato da te, e da dove viene lo dice la `source`.
- Il `context` scritto da Claude non viene controllato: per questo è sempre separato dalle tue
  parole e porta la scritta "Contesto scritto da Claude".
- Note, registro e testimone devono stare dentro la cartella del quaderno: il programma rifiuta
  percorsi completi e `..` nelle impostazioni. Ma se dentro il quaderno crei un collegamento
  (link simbolico) a un'altra cartella, i file vanno dove punta il collegamento: è una tua scelta,
  e il programma la rispetta.

**Cancellare.** I programmi non cancellano e non riscrivono mai niente. Tu resti sempre libero di
cancellare i tuoi file, compreso il testimone: le note già salvate restano, ma le loro parole
non si potranno più controllare.

## Il testimone delle risposte e il diario

Il testimone registra solo metà della conversazione: le tue parole. Il **testimone delle risposte**
registra l'altra metà: il testo di ogni risposta di Claude, con data e ora. Così, in una sessione
nuova, Claude può rileggere cosa ti aveva consigliato e accorgersi se si contraddice.

- **Diario** = tutto quello che tu e Claude vi siete detti, grezzo e completo, che si allunga
  soltanto (i due file dei testimoni).
- **Quaderno** = le note scelte.

**Come funziona.** Quando Claude ha finito di rispondere, Claude Code lancia l'aggancio `Stop` del
plugin (`hooks/hooks.json`), che passa al programma il testo dell'ultima risposta. Il
programma lo aggiunge in fondo al file `risposte.jsonl` del quaderno. Non scrive niente a schermo e
non blocca mai la sessione. Funziona solo in Claude Code, con il plugin installato (o
dall'avviabile); **in chat non esiste**, come il primo testimone. In pausa non registra.

**Come si accende.** Nella configurazione, sezione `[risposte]`: `attivo = true` per accenderlo,
`false` per spegnerlo, separatamente dal testimone dei tuoi messaggi. Se la sezione manca, è
spento. Funziona solo insieme al testimone dei tuoi messaggi: gli serve sapere a quale messaggio
Claude risponde, per rispettare i messaggi privati. **La tua configurazione in uso creata prima di
questa versione non ha la sezione**: per accenderlo copia la sezione `[risposte]` da
`windows/hypomnema-uso.toml` in fondo a `%USERPROFILE%\Hypomnema\hypomnema.toml`.

**Messaggi privati.** Se il tuo messaggio comincia con `#privato`, anche la risposta di Claude a
quel messaggio non viene registrata: resta solo data e ora con "risposta a un messaggio privato, non
registrata". Se il programma non riesce a capire a quale messaggio risponde Claude, per prudenza fa
lo stesso.

**Il filtro sul codice.** Con `ometti_codice = true` (di base) ogni blocco di codice della risposta
(tra tre apici inversi) viene registrato come una riga:
`[blocco di codice di N righe omesso, impronta XXXXXXXXXXXX]`. Serve a non riempire la ricerca di
codice. L'impronta (le prime 12 cifre dello SHA-256 del contenuto del blocco) è sempre la stessa
per lo stesso blocco: per sapere se un blocco omesso corrisponde a un file, `py -m hypomnema
impronta <file>`. Il file deve avere gli "a capo" di Linux e macOS (come tutti i file di questo
repository). Con `ometti_codice = false` il blocco viene registrato intero.

**Leggere il diario.** `py -m hypomnema diario <parola>` trova la parola (esatta, maiuscole
indifferenti) nei tuoi messaggi e nelle risposte di Claude, e li mostra in ordine di tempo con
data, ora e chi parla. Con `--intorno` mostra anche il messaggio subito prima e subito dopo.

**I limiti, detti onestamente.**
- Il divieto di modifica vale anche per questo file, perché sta nel quaderno: Claude non può
  toccarlo con i suoi strumenti, ma chi ha accesso al computer sì, come per il primo testimone.
- Se interrompi una risposta di Claude, Claude Code non lancia l'aggancio: quella risposta non viene
  registrata. Lo stesso succede se la risposta finisce per un errore del servizio.
- Il programma lega la risposta al tuo messaggio con il codice del turno che Claude Code gli passa
  (`prompt_id`); se manca, usa l'ultimo messaggio registrato. Provato con Claude Code 2.1.274: il
  codice è lo stesso per il messaggio e per la sua risposta.

## Alternativa: l'avviabile di Windows (funzionante, non più consigliato)

**L'avviabile per Windows funziona ancora, ma non è più la via consigliata**: con il plugin
installato (vedi «Installa il plugin in Claude Code») ogni sessione di Claude Code ha già la skill e
i testimoni. L'avviabile resta per chi vuole Hypomnema acceso solo in una finestra. Non usarlo
insieme al plugin installato.

Questa parte è per chi vuole usare Hypomnema davvero, sul proprio computer, mentre il
programma continua a essere sviluppato su GitHub.

### Due copie: una in uso, una per lo sviluppo

- La **copia in uso** è quella con cui lavori ogni giorno. Si aggiorna solo con la versione
  principale (`main`), cioè con le modifiche già controllate e unite su GitHub.
- La **copia di sviluppo** (se ne hai una) serve a provare le modifiche nuove. Ha il suo
  `hypomnema.toml`, con il testimone spento e un quaderno di prova.

Le note vere non stanno in nessuna delle due: stanno in una cartella tua, fuori dal programma.

| Cartella | Cosa contiene | Chi la cambia |
|---|---|---|
| `%USERPROFILE%\Hypomnema\programma` | La copia in uso del programma | Solo l'aggiornamento (`aggiorna-hypomnema.cmd`) |
| `%USERPROFILE%\Hypomnema\hypomnema.toml` | La configurazione in uso, con il testimone acceso | Tu; l'avviabile la crea la prima volta e poi non la tocca più |
| `%USERPROFILE%\Hypomnema\quaderno` | Note, registro e testimone | Solo i programmi di Hypomnema, che aggiungono e non cancellano mai |

`%USERPROFILE%` è la tua cartella utente, per esempio `C:\Users\nome`.

**Perché non in Documenti.** Su molti computer Windows la cartella Documenti è sincronizzata con
OneDrive: il quaderno e il testimone verrebbero copiati su internet. Per questo la cartella dei dati
è `%USERPROFILE%\Hypomnema`, che OneDrive di base non sincronizza. Se vuoi il quaderno altrove,
cambia `cartella` nella configurazione in uso; evita le cartelle sincronizzate.

### Installazione, passo per passo

Una volta sola. Servono tre programmi:

1. **Python 3.12 o più recente**, da [python.org](https://www.python.org/downloads/). Durante
   l'installazione lascia attivo il "Python Launcher" (il comando `py`).
2. **Git per Windows**, da [git-scm.com](https://git-scm.com/download/win): serve per scaricare e
   aggiornare il programma, e porta con sé Git Bash, che Claude Code usa per il testimone.
3. **Claude Code** (il comando `claude`), seguendo le istruzioni sul sito di Claude.

Poi, in PowerShell:

```
mkdir $env:USERPROFILE\Hypomnema
git clone --branch main https://github.com/angelomaccarinelli8-sys/hypomnema.git $env:USERPROFILE\Hypomnema\programma
cd $env:USERPROFILE\Hypomnema\programma
py -m unittest
```

L'ultimo comando deve finire con `OK`.

`--branch main` è importante: la copia in uso deve stare sulla versione principale, l'unica che
l'aggiornamento accetta.

**Il collegamento sul desktop.** Apri la cartella `%USERPROFILE%\Hypomnema\programma\windows`
con Esplora file, fai clic con il tasto destro su **`Hypomnema.cmd`**, poi *Mostra altre opzioni* →
*Invia a* → *Desktop (crea collegamento)*. Se vuoi, rinomina il collegamento in "Hypomnema".

### Ogni giorno

1. **Doppio clic** sul collegamento "Hypomnema". Si apre una finestra che:
   - la prima volta crea `%USERPROFILE%\Hypomnema\hypomnema.toml` (copiandolo da
     `windows\hypomnema-uso.toml`);
   - mostra lo stato del testimone (`stato`);
   - avvia Claude Code nella cartella del programma, con la skill di Hypomnema e il testimone
     acceso, collegati al quaderno in uso.
2. Scrivi a Claude come sempre. All'inizio Claude controlla il testimone e rilegge le note utili.
3. Per chiudere, esci da Claude Code (`/exit`) o chiudi la finestra.

**Fuori dall'avviabile Hypomnema è spento**: se apri Claude Code in un altro modo, anche nella
stessa cartella, non c'è né la skill né il testimone, e non viene registrato niente.

**Per controllare a mano il testimone**, in PowerShell:

```
cd $env:USERPROFILE\Hypomnema\programma
$env:HYPOMNEMA_CONFIG = "$env:USERPROFILE\Hypomnema\hypomnema.toml"
py -m hypomnema stato
```

Dice se il testimone è acceso, dov'è il quaderno, quanti messaggi ha registrato e data, ora e testo
dell'ultimo. Non cambia niente.

### Aggiornare la copia in uso

Quando su GitHub viene unita una nuova pull request, fai **doppio clic su
`windows\aggiorna-hypomnema.cmd`** nella cartella del programma (o crea anche per lui un
collegamento sul desktop). Il comando:

- controlla che la copia sia sulla versione principale (`main`), altrimenti non fa niente;
- scarica le novità con `git pull --ff-only`: se qualcosa non torna si ferma senza cambiare niente;
- lancia i test per controllare che la nuova versione funzioni sul tuo computer.

Tocca solo i file del programma: il quaderno e la configurazione in uso stanno fuori dalla sua
cartella e non vengono mai toccati.

### Cosa fa l'avviabile, e perché è fatto così

`Hypomnema.cmd` lancia lo script PowerShell `avvia-hypomnema.ps1`. Windows di solito blocca gli
script PowerShell aperti con un doppio clic; il file `.cmd` li avvia con `-ExecutionPolicy Bypass`,
che vale **solo per quella esecuzione** e non cambia le impostazioni di sicurezza del computer.
L'avviabile:

- non cancella niente e non tocca altre cartelle: crea solo la cartella dei dati e la
  configurazione in uso, e solo se mancano;
- si ferma con un messaggio chiaro se mancano `py` o `claude`, se la configurazione non va bene, o
  se il quaderno è dentro la cartella del programma;
- avvia Claude Code con il plugin di Hypomnema (la cartella del programma: skill e agganci) e
  con le regole che vietano a Claude di modificare il quaderno e la configurazione in uso. Plugin e
  regole valgono solo per quella sessione.

Per smettere di usarlo: cancella il collegamento sul desktop e, se vuoi, la cartella `programma`.
Il quaderno resta dov'è: decidi tu se tenerlo.

## Versioni

La storia delle versioni è in [STORIA.md](STORIA.md).

## Esempi

La cartella [esempi](esempi/README.md) contiene casi con dati inventati e il risultato
atteso di ciascuno. I test li rieseguono e controllano che il risultato sia identico.

## Licenza

[MIT](LICENSE) © Angelo Maccarinelli
