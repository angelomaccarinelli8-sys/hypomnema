---
name: hypomnema
description: Memoria permanente tra una chat e l'altra, in file Markdown sul computer dell'utente. Usala all'inizio di ogni chat per rileggere le note utili, e durante la chat per proporre allo sportello di Hypomnema le cose da ricordare (fatti, idee, decisioni, discorsi aperti). Claude propone, i programmi decidono.
---

# Hypomnema: il quaderno di memoria

Hypomnema è un quaderno di note sul computer dell'utente. **Tu non scrivi mai direttamente
nei file del quaderno.** Proponi le note allo sportello, un programma che applica regole fisse
e decide se entrano. Per leggere usi il cercatore.

## Come lanciare i programmi

I comandi si lanciano dalla cartella di Hypomnema (quella che contiene `hypomnema.toml`):

```
python -m hypomnema cerca <parola>
python -m hypomnema proponi <file.json>
```

- Su Windows, se `python` non esiste, usa `py`.
- Se Hypomnema è installato, puoi scrivere `hypomnema` al posto di `python -m hypomnema`;
  in quel caso la variabile `HYPOMNEMA_CONFIG` indica dove sta `hypomnema.toml`.
- Se non sai dov'è la cartella di Hypomnema, chiedilo all'utente una volta.
- Codici di uscita: `0` tutto bene, `1` nota rifiutata, `2` errore (configurazione, file mancante).

## 1. A inizio chat: rileggi

1. Individua 1-3 parole chiave del primo messaggio dell'utente (argomento, progetto, nomi).
2. Per ciascuna lancia `python -m hypomnema cerca <parola>`. La ricerca è per parola esatta,
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
- `testo`: frase chiara e autosufficiente, comprensibile anche fra mesi senza la chat.

## 3. Passa le note allo sportello

1. Scrivi la proposta in un file temporaneo **fuori dalla cartella del quaderno**
   (per esempio `proposta.json` nella cartella di lavoro), in UTF-8.
2. Lancia `python -m hypomnema proponi proposta.json`.
   In alternativa puoi passarla dall'ingresso standard: `python -m hypomnema proponi -`.
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
  "testo": "D'ora in poi annaffio l'orto la mattina presto invece che la sera."
}
```

3. l'idea originale resta com'è: il quaderno conserva sia l'idea sia la decisione.

L'utente può anche dire "ricorda che ho deciso ...": in quel caso proponi direttamente una
decisione (`autore: utente`, `tipo: dichiarata`) senza `conferma_di`.
