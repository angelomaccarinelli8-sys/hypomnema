# CLAUDE.md: istruzioni per lavorare su Hypomnema

Leggi questo file all'inizio di ogni sessione.

## Cos'è

Hypomnema ("promemoria" in greco antico) dà a Claude una memoria permanente tra una chat e
l'altra, in file Markdown sul computer dell'utente. È fatto di una skill (`skill/hypomnema/SKILL.md`)
e di piccoli programmi Python (`hypomnema/`): lo **sportello** (`proponi`), il **registro degli
ingressi**, il **cercatore** (`cerca`) e il **testimone** (`testimone`), che registra le parole
esatte dell'utente perché lo sportello possa verificare le note con autore "utente".

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
  nella chat) e non esce mai con codice 2 (bloccherebbe il messaggio dell'utente).
- **Niente internet** nei programmi.
- **Impostazioni in `hypomnema.toml`**, mai valori fissi nel codice. I valori ammessi per
  autore/tipo/natura non sono impostazioni ma regole: stanno in `hypomnema/regole.py`.
- Python 3.12 o superiore (compatibile con 3.14), solo libreria standard, funzionante su
  Windows, macOS e Linux (percorsi con `pathlib`, file in UTF-8 con fine riga `\n`).

## Mappa del codice

| File | Ruolo |
|---|---|
| `hypomnema/cli.py` | Riga di comando (`proponi`, `cerca`), messaggi a schermo. |
| `hypomnema/sportello.py` | Legge la proposta, applica le regole, salva la nota, annota nel registro. |
| `hypomnema/regole.py` | Le regole fisse e i motivi di rifiuto in italiano semplice. |
| `hypomnema/nota.py` | La nota e il suo formato Markdown (scrittura e rilettura). |
| `hypomnema/quaderno.py` | Elenco delle note salvate e numero della prossima. |
| `hypomnema/registro.py` | Registro degli ingressi, solo aggiunta. |
| `hypomnema/cercatore.py` | Ricerca per parola esatta, solo lettura. |
| `hypomnema/testimone.py` | Registra i messaggi dell'utente (solo aggiunta, prefisso privato) e cerca le citazioni. |
| `aggancio_testimone.py` | Punto d'ingresso del testimone per l'aggancio: funziona da qualunque cartella e shell (Git Bash, PowerShell). |
| `.claude/settings.json` | Aggancia il testimone a ogni messaggio (UserPromptSubmit, con `py` se c'è, altrimenti `python3`) e vieta a Claude di modificare `quaderno/`. |
| `hypomnema/configurazione.py` | Lettura di `hypomnema.toml`. |
| `FORMATO.md` | Formato delle note e regole: tenerlo allineato al codice. |
| `esempi/` | Casi con dati inventati e risultati attesi (approvati da Angelo). |
| `tests/` | `test_esempi.py` confronta gli esempi con gli attesi; `test_regole.py` le singole regole; `test_testimone.py` il testimone e la regola della citazione. |

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
