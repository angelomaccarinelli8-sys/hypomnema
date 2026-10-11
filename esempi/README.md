# Esempi (risultati attesi da approvare)

Tutti i dati qui sono **inventati**.

Ogni cartella è un esempio:

- `comandi.txt`: i comandi da lanciare, uno per riga, nell'ordine;
- i file `.json`: le note proposte;
- `atteso/uscita.txt`: ciò che il programma deve scrivere a schermo, con il codice di uscita;
- `atteso/quaderno/`: come deve essere il quaderno alla fine (note, registro, testimone);
- i percorsi della cartella temporanea in cui gira l'esempio compaiono come
  `<cartella di prova>/...` (per esempio nell'uscita di `stato`);
- `quaderno-iniziale/` (solo in alcuni esempi): il quaderno da cui parte l'esempio, invece di
  un quaderno vuoto;
- `hypomnema.toml` (solo in alcuni esempi): la configurazione usata, per esempio con il
  testimone acceso. Se manca, l'esempio usa una configurazione con il testimone **spento**;
- `messaggio*.json` / `1-privato.json` ecc.: un messaggio inventato dell'utente, come Claude Code
  lo passa al testimone. Il comando `testimone FILE` simula l'arrivo di quel messaggio.

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
| `32-archivio-nota-riscontrata` | Configurazione per la chat con la sezione `[archivio]`. Claude copia dall'archivio della chat un messaggio dell'utente e una sua risposta; poi una nota dell'utente con un pezzo di quel messaggio, la ricerca e `stato`. | La nota è «testo riscontrato sull'archivio della chat <indirizzo>, messaggio del … (copiato da Claude)»; `stato` mostra l'archivio. |
| `33-archivio-testo-assente` | Come il 32, ma la nota ha parole che nell'archivio non ci sono. | Accettata e marcata «autore non verificato (chat, senza testimone)»: in chat non si rifiuta. |
| `34-archivio-messaggio-privato` | La copia comprende un messaggio `#privato` con la sua risposta, poi un messaggio normale con la sua risposta; poi gli ultimi 4 del diario. | Del messaggio privato e della sua risposta restano solo data e ora («non copiato»); gli altri due sono copiati. Le righe del diario dicono da quale chat vengono. |
| `35-archivio-senza-doppioni` | La stessa copia fatta due volte: la seconda ha anche un messaggio nuovo e una risposta con lo stesso orario ma un testo diverso. | La seconda volta copia solo il messaggio nuovo; i 2 già presenti non sono duplicati e il programma avvisa che uno ha un testo diverso, senza toccarlo. `controlla` dice che è tutto in ordine. |
| `36-diario-tre-livelli` | Parte da un quaderno con una nota verificata dal testimone di Claude Code; in chat copia dall'archivio e salva una nota riscontrata e una non verificata; poi la ricerca e il diario. | La ricerca mostra i tre livelli: «testo trovato nel messaggio…» (testimone), «testo riscontrato sull'archivio della chat…» e «autore non verificato». Nel diario la riga del testimone non ha indicazioni, quelle copiate dicono «archivio della chat …, copiato da Claude». |
| `26-confronta` | `confronta` tra due file uguali, due diversi e un file che manca. | `UGUALI` (codice 0); `DIVERSI` con il primo byte diverso (codice 1); errore (codice 2). |

Dal compito 2, negli esempi 01, 04 e 05 (testimone spento) le note con autore «utente» hanno
in più la riga «verifica: autore non verificato (testimone spento)».

I test (`tests/test_esempi.py`) rifanno ogni esempio e confrontano il risultato, carattere per
carattere, con la cartella `atteso/`.

Dal compito 3, negli esempi 06, 07, 08 e 09 le note dell'utente hanno le parole dell'utente nel
`testo` (non più nel campo `citazione`, che ora è solo per le note di Claude): cambiano le note
proposte, i motivi di rifiuto e la riga «verifica» («testo trovato» invece di «citazione trovata»).
