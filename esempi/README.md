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

Dal compito 2, negli esempi 01, 04 e 05 (testimone spento) le note con autore «utente» hanno
in più la riga «verifica: autore non verificato (testimone spento)».

I test (`tests/test_esempi.py`) rifanno ogni esempio e confrontano il risultato, carattere per
carattere, con la cartella `atteso/`.

Dal compito 3, negli esempi 06, 07, 08 e 09 le note dell'utente hanno le parole dell'utente nel
`testo` (non più nel campo `citazione`, che ora è solo per le note di Claude): cambiano le note
proposte, i motivi di rifiuto e la riga «verifica» («testo trovato» invece di «citazione trovata»).
