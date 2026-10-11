# Hypomnema

**Una memoria permanente per Claude, scritta in file Markdown sul tuo computer.**

Ogni chat con Claude riparte da zero. Hypomnema gli dà un quaderno: a inizio chat Claude
rilegge le note utili, durante la chat propone cosa ricordare. Ma **non è Claude a decidere
cosa entra**: lo decide un piccolo programma con regole fisse, che dà sempre lo stesso risultato.

> Claude propone le note, i programmi decidono se entrano.

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
| **Sportello** (`proponi`) | Riceve una nota proposta, la controlla, la salva come file Markdown se è completa, altrimenti la rifiuta spiegando perché. |
| **Registro** (`registro.md`) | Annota ogni passaggio dallo sportello, accettato o rifiutato, con data e motivo. Solo aggiunta. |
| **Cercatore** (`cerca`) | Trova le note che contengono una parola. Solo lettura. |
| **Testimone** (`testimone`) | Se lo accendi, registra le parole esatte dei tuoi messaggi, così lo sportello può controllare che una nota "dell'utente" riporti parole che hai detto davvero. |
| **Skill** (`skill/hypomnema/SKILL.md`) | Le istruzioni per Claude: quando leggere, come preparare le note, come confermare una decisione. |

Il formato delle note e le regole dello sportello sono descritti in [FORMATO.md](FORMATO.md).

## Installazione

Serve **Python 3.12 o più recente** (da [python.org](https://www.python.org/downloads/)).
Non servono altre librerie.

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
python -m hypomnema proponi esempi/01-nota-accettata/nota.json
python -m hypomnema cerca orto
python -m hypomnema testimone messaggio.json   # di solito lo lancia Claude Code da solo
```

Su Windows scrivi `py` al posto di `python`:

```
py -m hypomnema cerca orto
```

Una nota proposta è un piccolo file JSON:

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

Lo sportello risponde `ACCETTATA` (e dice il numero della nota) oppure `RIFIUTATA` con i motivi.
Il formato completo è in [FORMATO.md](FORMATO.md).

### Le tue parole e quelle di Claude restano separate

In una nota con `autore: utente`, il `testo` sono **le tue parole esatte**. Se Claude vuole
aggiungere una spiegazione (di cosa si parlava, a cosa ti riferivi), la mette in un campo a parte,
`contesto`, che nel quaderno compare sotto il titolo "Contesto scritto da Claude":

```json
{
  "data": "2026-01-15",
  "fonte": "chat del 15 gennaio 2026 sul progetto dell'orto",
  "autore": "utente",
  "tipo": "dichiarata",
  "natura": "fatto",
  "testo": "Il fico va potato solo quando ha perso tutte le foglie.",
  "contesto": "Detto parlando del fico in vaso sul terrazzo."
}
```

Le note scritte da Claude (`autore: claude`) sono tutte parole sue: lì il `contesto` non serve.
Se si basano su qualcosa che hai detto, Claude può riportare le tue parole nel campo `citazione`.

### Testo incollato: va bene così

Hypomnema è un quaderno di appunti, come gli hypomnemata antichi: raccogliere passi letti
altrove è proprio lo scopo. Se incolli in un messaggio un testo che non hai scritto tu (un passo
di un libro, una spiegazione di Claude, un appunto), conta come portato da te nel quaderno: la
nota è tua (`autore: utente`). **Da dove viene lo dice il campo `fonte`**, per esempio:

- `"fonte": "dal libro «Il quaderno dell'ortolano»"`
- `"fonte": "dalla spiegazione di Claude del 15 gennaio 2026"`
- `"fonte": "mio pensiero"`

Non c'è nessuna regola che distingua il testo scritto da quello incollato.

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

La skill in `skill/hypomnema/SKILL.md` spiega a Claude come usare il quaderno. Funziona dove
Claude può lanciare comandi sul tuo computer (per esempio Claude Code). Copia la cartella
`skill/hypomnema` tra le skill di Claude e digli dov'è la cartella di Hypomnema.

## Il testimone

**Il problema.** Una nota può dire `autore: utente`, ma chi la scrive è Claude. Senza un
controllo, il programma dovrebbe fidarsi.

**La soluzione.** Il testimone è un piccolo programma che Claude Code lancia ogni volta che invii
un messaggio, *prima* che Claude lo legga. Il programma aggiunge il testo esatto del messaggio, con
data e ora, in fondo a un file. Lo sportello cerca il `testo` di ogni nota con `autore: utente` in
quel file, parola per parola: se non lo trova, rifiuta la nota.

**Cosa registra.** Il testo di ogni messaggio che scrivi a Claude in questo progetto, con data e
ora. Non registra le risposte di Claude. Se incolli un testo nel messaggio, il testimone registra
anche quello.

**Dove.** Nel file `testimone.jsonl` dentro la cartella del quaderno (di base `quaderno/`).
È un file di testo: puoi aprirlo e leggerlo quando vuoi. Il quaderno e il testimone sono esclusi
da git (`.gitignore`) e i programmi non si collegano a internet: **non lasciano mai il tuo computer**.

**Come si accende e si spegne.** In `hypomnema.toml`, sezione `[testimone]`:
`attivo = true` per accenderlo, `attivo = false` per spegnerlo. **Di base è spento.**
Da spento non registra niente, e le note con `autore: utente` vengono salvate con la scritta
ben visibile "autore non verificato (testimone spento)".

**Messaggi privati.** Se un messaggio inizia con `#privato`, il testimone non ne registra il
testo: annota solo data e ora con "messaggio privato, non registrato". Il prefisso si cambia in
`hypomnema.toml` (`prefisso_privato`).
**Attenzione: un messaggio privato non finisce nel testimone, ma Claude lo legge comunque**, come
ogni altro messaggio. "Privato" vuol dire solo che le sue parole non vengono registrate; la skill
chiede a Claude di non farne note.

**Come è collegato.** Il file `.claude/settings.json` del progetto contiene l'aggancio
(`UserPromptSubmit`): a ogni messaggio lancia il programma `aggancio_testimone.py` con `py` se
esiste (Windows), altrimenti con `python3` (macOS e Linux). Lo stesso file vieta a Claude di
modificare con i suoi strumenti i file della cartella `quaderno/`. Se usi Hypomnema da un'altra
cartella o hai spostato il quaderno, copia l'aggancio nelle impostazioni di quel progetto e
aggiorna il divieto con il nuovo percorso.

### Il testimone su Windows

Su Windows Claude Code lancia gli agganci con **Git Bash**, se è installato (arriva insieme a
Git per Windows), altrimenti con **PowerShell**. L'aggancio di Hypomnema funziona così com'è con
Git Bash e il comando `py`. Per controllare, in PowerShell, dalla cartella di Hypomnema:

1. `py --version`: deve rispondere Python 3.12 o più recente.
2. `Test-Path "C:\Program Files\Git\bin\bash.exe"`: `True` vuol dire che Git Bash c'è.
3. In `hypomnema.toml` metti `attivo = true`.
4. Prova il programma da solo:
   `'{"prompt": "prova del testimone"}' | py .\aggancio_testimone.py`
   poi `Get-Content -Encoding UTF8 quaderno\testimone.jsonl`: l'ultima riga deve contenere
   `"testo": "prova del testimone"`. (Nella prova usa solo lettere senza accenti: PowerShell
   può alterarle quando le passa a un programma. Con Claude Code gli accenti arrivano giusti.)
5. Apri Claude Code nella cartella di Hypomnema, scrivi un messaggio (per esempio
   "prova dal vero") e ricontrolla il file come al punto 4.

**Se Git Bash non c'è** (il punto 2 risponde `False`), hai due strade:
- installare Git per Windows (consigliato: serve anche per scaricare gli aggiornamenti), oppure
- in `.claude/settings.json`, sostituire la riga `"command": ...` dell'aggancio con queste due:

  ```json
  "command": "py",
  "args": ["${CLAUDE_PROJECT_DIR}/aggancio_testimone.py"]
  ```

  Così Claude Code lancia `py` direttamente, senza passare da nessuna shell. Ricorda che hai
  modificato un file del repository: `git status` lo mostrerà come cambiato.

Se il messaggio non viene registrato, in Claude Code il comando `/hooks` mostra gli agganci
attivi; un errore del testimone compare come avviso nella chat, ma non blocca mai il messaggio.

**I limiti, detti onestamente.**
- Il divieto vale per gli strumenti di Claude, non per il computer: tu, o chiunque abbia accesso al
  tuo computer, può aprire e modificare il file del testimone. Anche un programma lanciato da
  Claude (per esempio uno script Python) non è fermato dal divieto: lo impedisce solo la skill, che
  lo vieta a Claude. Per un blocco completo serve il sandbox di Claude Code.
- Il testimone dimostra che quelle parole erano in un tuo messaggio, non che le abbia scritte tu:
  un testo incollato conta come portato da te, e da dove viene lo dice la `fonte`.
- Il `contesto` scritto da Claude non viene controllato: per questo è sempre separato dalle tue
  parole e porta la scritta "Contesto scritto da Claude".

**Cancellare.** I programmi non cancellano e non riscrivono mai niente. Tu resti sempre libero di
cancellare i tuoi file, compreso il testimone: le note già salvate restano, ma le loro parole
non si potranno più controllare.

## Esempi

La cartella [esempi](esempi/README.md) contiene casi con dati inventati e il risultato
atteso di ciascuno. I test li rieseguono e controllano che il risultato sia identico.

## Licenza

[MIT](LICENSE) © Angelo Maccarinelli
