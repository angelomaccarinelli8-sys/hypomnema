# CLAUDE.md: istruzioni per lavorare su Hypomnema

Leggi questo file all'inizio di ogni sessione.

## Cos'è

Hypomnema ("promemoria" in greco antico) dà a Claude una memoria permanente tra una chat e
l'altra, in file Markdown sul computer dell'utente. È fatto di una skill (`skills/hypomnema/SKILL.md`)
e di piccoli programmi Python (`hypomnema/`): lo **sportello** (`proponi`), il **registro degli
ingressi**, il **cercatore** (`cerca`), il **testimone** (`testimone`), che registra le parole
esatte dell'utente perché lo sportello possa verificare le note con autore "utente", e lo
**stato** (`stato`), che dice se il testimone è acceso e qual è l'ultimo messaggio registrato.

Per l'uso quotidiano su Windows c'è l'**avviabile** (`windows/Hypomnema.cmd`): apre Claude Code
con il plugin (skill e testimone) e con il quaderno in uso fuori dal repository
(`%USERPROFILE%\Hypomnema`). Fuori dall'avviabile Hypomnema è spento.

**Direzione (decisioni di Angelo, 11/10/2026 sera)**: Hypomnema si presenta come un **plugin di
Claude Code** con una skill. La via consigliata è il plugin installato dal catalogo di questo
repository (`claude plugin marketplace add angelomaccarinelli8-sys/hypomnema`, poi
`claude plugin install hypomnema@hypomnema`): ogni sessione ha skill e testimoni, con la
configurazione e il quaderno in `~/Hypomnema`, fuori dal plugin. L'avviabile resta funzionante ma
non è più la via consigliata. Nella chat di claude.ai Hypomnema funziona con la sola skill.

**Direzione precedente (11/10/2026)**: l'avviabile resta funzionante ma il suo sviluppo
è in pausa. Hypomnema si sviluppa come skill piena nella **chat di Claude** (claude.ai, app
desktop e mobile): Claude scarica i programmi nel computer di lavoro della chat, copia il quaderno
dalla cartella `Hypomnema` dell'utente (con il suo permesso), passa dallo sportello con
`chat/hypomnema-chat.toml` e riporta solo i file che `cambiati` elenca. In chat non c'è testimone.

Divisione dei compiti, il cuore del progetto: **Claude propone le note, i programmi decidono
se entrano.** Claude non scrive mai direttamente nei file del quaderno.

Segue le regole di Sophia (la memoria deterministica di Angelo Maccarinelli, in sviluppo), ma è
un mattoncino a sé: non dipende da Sophia e non ne contiene il codice.

**Il repository è pubblico**: nessun dato personale, nessun riferimento a file privati di Angelo,
nessun pezzo del codice di Sophia. Negli esempi e nei test solo dati inventati.

## Principi vincolanti

- **Solo logica deterministica e verificata**: niente modelli linguistici, statistica o soglie
  indovinate. Stessi ingressi, stesso risultato. "Verificata" = dimostrata da esempi e test.
- **Una sola porta d'ingresso**: tutto ciò che entra nel quaderno passa dallo sportello.
- **Niente si cancella e niente si riscrive**: note create con apertura esclusiva (`"x"`),
  registro aperto solo in aggiunta (`"a"`).
- **Provenienza sempre**: data, fonte, autore (utente o claude) in ogni nota.
- **Parole dell'utente e di Claude mai mescolate**: in una nota dell'utente `testo` = sue parole
  esatte, `contesto` = aggiunte di Claude; in una nota di Claude `citazione` = parole dell'utente.
- **L'incerto resta incerto**: tipo `osservata`, `dichiarata` o `dedotta`. Una nota di Claude
  non può mai essere una decisione dell'utente.
- **Idee separate dalle decisioni**: un'idea diventa decisione solo con conferma esplicita
  dell'utente (nuova nota con `conferma_di`).
- **Il testimone non si fida di Claude**: il comando `testimone` non scrive mai a schermo (finirebbe
  nella chat) e non esce mai con codice 2 (bloccherebbe il messaggio dell'utente). Lo stesso vale per
  `risposte`: con l'aggancio Stop il codice 2 costringerebbe Claude a continuare.
- **Diario e quaderno sono cose diverse**: il diario è la conversazione grezza registrata dai due
  testimoni; il quaderno sono le note scelte. Una cosa trovata solo nel diario non è una decisione.
- **Niente internet** nei programmi.
- **Le note vere stanno fuori dal repository**: l'aggiornamento della copia in uso non deve mai
  toccarle. Il quaderno di prova `quaderno/` del repository è escluso da git.
- **Impostazioni in `hypomnema.toml`**, mai valori fissi nel codice. I valori ammessi per
  autore/tipo/natura non sono impostazioni ma regole: stanno in `hypomnema/regole.py`.
- Python 3.12 o superiore (compatibile con 3.14), solo libreria standard, funzionante su
  Windows, macOS e Linux (percorsi con `pathlib`, file in UTF-8 con fine riga `\n`).

## Mappa del codice

| File | Ruolo |
|---|---|
| `hypomnema/cli.py` | Riga di comando (`proponi`, `cerca`, `promemoria`, `recap`, `testimone`, `stato`, `istantanea`, `cambiati`, `controlla`, `confronta`, `risposte`, `impronta`, `diario`, `archivio`, `avvio`, `protezione`, `impostazioni-claude`), messaggi a schermo. `confronta` (due file identici byte per byte?) non usa la configurazione. |
| `hypomnema/cambiamenti.py` | `istantanea` e `cambiati` (solo lettura): i file del quaderno da riportare dopo una proposta, con il controllo che sia successo solo ciò che fa lo sportello. |
| `chat/hypomnema-chat.toml` | Modello della configurazione per la chat: testimone spento e `modalita = "chat"` (note dell'utente marcate «chat, senza testimone»). |
| `hypomnema/controllo.py` | `controlla` (solo lettura): ogni nota ha la sua riga ACCETTATA nel registro, e viceversa; righe del registro estranee (con il numero) e registro senza a capo finale. Segnala, non ripara. |
| `hypomnema/risposte.py` | Il testimone delle risposte di Claude (aggancio Stop): solo aggiunta, rispetta i messaggi privati, sostituisce i blocchi di codice con la loro impronta; `impronta`. |
| `hypomnema/diario.py` | Il diario: messaggi dell'utente e risposte di Claude insieme, in ordine di tempo; ricerca per parola esatta. Solo lettura. |
| `hypomnema/archivio.py` | Il testimone dell'archivio (modalità chat): il comando `archivio` aggiunge a `archivio-chat.jsonl` e `diario-chat.jsonl` la copia della conversazione presa da Claude dall'archivio delle chat, senza doppioni e con i privati ridotti a data e ora. Le note dell'utente il cui testo si trova lì sono «riscontrate sull'archivio della chat». |
| `hypomnema/avvio.py` | Configurazione di base `~/Hypomnema`, prima volta (creata dal modello `windows/hypomnema-uso.toml`), avvisi (quaderno nel plugin, OneDrive, pausa), protezione del quaderno; le regole per l'avviabile. |
| `hypomnema/sportello.py` | Legge la proposta, applica le regole, salva la nota, annota nel registro. |
| `hypomnema/regole.py` | Le regole fisse e i motivi di rifiuto in italiano semplice. |
| `hypomnema/nota.py` | La nota e il suo formato Markdown (scrittura e rilettura). |
| `hypomnema/quaderno.py` | Elenco delle note salvate e numero della prossima. |
| `hypomnema/registro.py` | Registro degli ingressi, solo aggiunta; le due forme di riga (ACCETTATA, RIFIUTATA) che riconoscono `cambiati` e `controlla`; lo sportello si ferma se il registro non finisce con un a capo. |
| `hypomnema/cercatore.py` | Ricerca per parola esatta (parole composte spezzate su `_ . - /`), dalla nota più recente, solo lettura; le note collegate (`corregge`, `conferma_di`, `done`, anche a catena). |
| `hypomnema/promemoria.py` | I promemoria (`riprendere_il`): gruppi con le correzioni, data in vigore, `done`, scaduti dal più vecchio. Solo lettura. |
| `hypomnema/testimone.py` | Registra i messaggi dell'utente (solo aggiunta, prefisso privato) e cerca le citazioni. |
| `programma.py` | Punto d'ingresso del plugin: lo lanciano gli agganci e Claude (`py "${CLAUDE_PLUGIN_ROOT}/programma.py" …`); i programmi stanno nel plugin, la configurazione di base è `~/Hypomnema/hypomnema.toml`. |
| `.claude-plugin/` | `plugin.json` (il manifesto, senza versione: ogni aggiornamento di `main` arriva con l'update) e `marketplace.json` (il catalogo; il plugin è la radice del repository, `source: "./"`). |
| `hooks/hooks.json` | Gli agganci: SessionStart (`avvio`: prima volta e avvisi), UserPromptSubmit (`testimone`), Stop (`risposte`), PreToolUse (`protezione`: blocca Edit/Write sul quaderno). |
| `commands/` | `/hypomnema:pausa` e `/hypomnema:riprendi`, che Claude non può lanciare (`disable-model-invocation`). La pausa la riconosce il testimone nel messaggio dell'utente. `/hypomnema:recap` lancia il recap. |
| `STORIA.md` | La storia delle versioni e le note di rilascio. |
| `skills/hypomnema/SKILL.md` | La skill. |
| `windows/` | L'avviabile (`Hypomnema.cmd` → `avvia-hypomnema.ps1`), il modello della configurazione in uso (`hypomnema-uso.toml`) e l'aggiornamento della copia in uso (`aggiorna-hypomnema.cmd`). I `.cmd` sono ASCII con fine riga CRLF; il `.ps1` è UTF-8 con BOM. |
| `.claude/settings.json` | Nella copia di sviluppo vieta a Claude di modificare `quaderno/`. Nessun aggancio. |
| `hypomnema/configurazione.py` | Lettura di `hypomnema.toml`. |
| `FORMATO.md` | Formato delle note e regole: tenerlo allineato al codice. |
| `esempi/` | Casi con dati inventati e risultati attesi (approvati da Angelo). |
| `tests/` | `test_esempi.py` confronta gli esempi con gli attesi; `test_regole.py` le singole regole; `test_testimone.py` il testimone e la regola della citazione; `test_avvio.py` `stato`, le regole per l'avviabile, il plugin e l'avviabile vero (solo su Windows); `test_chat.py` la modalità chat (configurazione, marcatura, `istantanea`, `cambiati` e `controlla`); `test_risposte.py` il testimone delle risposte, il filtro sul codice, `impronta`, il diario e `da_risposta`; `test_plugin.py` il plugin installabile (catalogo, agganci da una copia del plugin, prima volta, protezione, pausa); `test_archivio.py` l'archivio della chat e i tre livelli; `test_rifiniture.py` le rifiniture della 0.4.0 (correzioni, ordine, parole composte, promemoria, recap, segni dell'archivio, quaderno vecchio). |

## Metodo di lavoro

1. **Analisi**: leggi il compito, il codice coinvolto e `FORMATO.md`.
2. **Piano breve**: pochi punti, prima di scrivere codice.
3. **Implementazione minima**: solo ciò che serve al compito, niente fuori perimetro.
4. **Test verdi**: `python -m unittest` dalla radice del repository. Si salva solo con test verdi.
   Ogni nuova regola ha un test; ogni nuovo comportamento visibile ha un esempio con il
   risultato atteso **proposto** in un file separato (lo approva Angelo).
   Non modificare un risultato atteso già approvato senza dirlo esplicitamente nel report.
5. **Salvataggi** (commit) con messaggi chiari in italiano.
6. **Branch dedicato e pull request verso `main`**: non unire mai a `main`, lo fa Angelo.
7. Se un passo richiede una scelta non scritta, scegli la soluzione più semplice e reversibile
   e segnalala nel report.

## Report finale (italiano semplice)

```
REPORT OPERATIVO
Branch e pull request:
Obiettivo:
Fatto:
Test (quanti, esito):
Come provarlo sul computer di Angelo (comandi esatti per Windows/PowerShell):
Bozze da approvare (formato delle note, risultati attesi degli esempi):
Scelte fatte da confermare:
Errori / dubbi:
Prossimo passo proposto:
```

## Da ricordare per i compiti futuri

- **Lingua per ruolo** (decisione di Angelo, 15/10/2026): in un compito successivo comandi e campi
  passeranno all'inglese. Per ora solo `recap` e `done` sono in inglese; il resto resta in italiano.

- **Versioni delle note** (segnalato dalla revisione della PR #3): il formato della nota non ha
  un numero di versione. Una nota salvata prima del compito 3 che contenesse nel testo la riga
  esatta `## Contesto scritto da Claude` verrebbe riletta come se da lì in poi ci fosse il
  contesto. Caso improbabile; da risolvere quando si affrontano le versioni, con un formato
  versionato o una migrazione.
- **Fuori perimetro del compito 9** (11/10/2026): la verifica a posteriori sull'esportazione
  ufficiale delle chat di Claude (potrà promuovere le note «riscontrate sull'archivio della chat» a
  «verificate»); il vocabolario (compito 10); un'interfaccia propria.
- **Il quaderno in valigia** (idea parcheggiata l'11/10/2026 sera): portare il quaderno con sé
  tra computer diversi. Non si fa per ora; da riprendere più avanti.
