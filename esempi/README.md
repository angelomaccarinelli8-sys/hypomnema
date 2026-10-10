# Esempi (risultati attesi da approvare)

Tutti i dati qui sono **inventati**.

Ogni cartella è un esempio:

- `comandi.txt`: i comandi da lanciare, uno per riga, nell'ordine;
- i file `.json`: le note proposte;
- `atteso/uscita.txt`: ciò che il programma deve scrivere a schermo, con il codice di uscita;
- `atteso/quaderno/`: come deve essere il quaderno alla fine (note, registro, testimone);
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

| `06-citazione-trovata` | Testimone acceso. L'utente scrive un messaggio; Claude propone una decisione con la citazione esatta (il messaggio aveva due spazi e un a capo, la citazione uno spazio solo). | Accettata; la nota riporta la citazione e «citazione trovata nel messaggio del ...». |
| `07-citazione-assente` | Testimone acceso. Una nota dell'utente senza citazione, poi una con parole mai dette. | Entrambe rifiutate, con motivi diversi. |
| `08-citazione-modificata` | Testimone acceso. L'utente dice «zucchine», la citazione dice «melanzane». | Rifiutata: la citazione non si trova parola per parola. |
| `09-messaggio-privato` | Testimone acceso. Un messaggio che inizia con `#privato`, poi uno normale; poi una nota che cita il messaggio privato. | Il testimone annota solo data e ora del messaggio privato; la nota è rifiutata perché quelle parole non sono registrate. |
| `10-testimone-spento` | Testimone spento. Arriva un messaggio, poi una nota dell'utente senza citazione. | Il testimone non registra niente (nessun file); la nota è accettata e marcata «autore non verificato (testimone spento)». |
| `11-citazione-di-claude-non-verificata` | Testimone spento. Un'idea di Claude con una citazione delle parole dell'utente. | Accettata e marcata «citazione non verificata (testimone spento)». |

Dal compito 2, negli esempi 01, 04 e 05 (testimone spento) le note con autore «utente» hanno
in più la riga «verifica: autore non verificato (testimone spento)».

I test (`tests/test_esempi.py`) rifanno ogni esempio e confrontano il risultato, carattere per
carattere, con la cartella `atteso/`.
