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

Per saperne di più su Sophia: [articolo su LinkedIn](LINK_ARTICOLO_LINKEDIN) <!-- da aggiungere -->

## Cosa c'è dentro

| Parte | Cosa fa |
|---|---|
| **Sportello** (`proponi`) | Riceve una nota proposta, la controlla, la salva come file Markdown se è completa, altrimenti la rifiuta spiegando perché. |
| **Registro** (`registro.md`) | Annota ogni passaggio dallo sportello, accettato o rifiutato, con data e motivo. Solo aggiunta. |
| **Cercatore** (`cerca`) | Trova le note che contengono una parola. Solo lettura. |
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

### Con Claude

La skill in `skill/hypomnema/SKILL.md` spiega a Claude come usare il quaderno. Funziona dove
Claude può lanciare comandi sul tuo computer (per esempio Claude Code). Copia la cartella
`skill/hypomnema` tra le skill di Claude e digli dov'è la cartella di Hypomnema.

## Esempi

La cartella [esempi](esempi/README.md) contiene casi con dati inventati e il risultato
atteso di ciascuno. I test li rieseguono e controllano che il risultato sia identico.

## Licenza

[MIT](LICENSE) © Angelo Maccarinelli
