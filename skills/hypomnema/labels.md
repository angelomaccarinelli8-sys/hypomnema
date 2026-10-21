# Hypomnema: labels CHI and COSA (from version 0.7.0; COSA by the desk from 0.8.0)

Read this before proposing labels for the first time in a chat. It completes the "Labels" part of
`SKILL.md`, whose rules stay the same.

A note can have **labels**: CHI (`who`: people) and COSA (`about`: projects or topics). They make the
notebook easier to read by person or by project: `search` and `recap` can show only the notes with
some labels.

## The list: `etichette.toml`, written by the user

The labels allowed are a short, fixed list that **the user writes** in the file `etichette.toml`, in
the notebook folder (next to `registro.md` and `note/`):

```toml
chi = ["Anna", "Marco"]
cosa = ["orto", "bilancio"]
```

- The same file is read by Claude Code and by the chat (both configurations of the same notebook):
  there is only one list.
- **You never write, change or delete this file**: not with your tools, not with commands or scripts.
  In Claude Code the plugin stops you anyway. A commented model is `esempi/etichette.toml` in the
  repository: the user copies it into the notebook folder and writes their own labels.
- **If the file is not there, no note can have labels**: the desk rejects `who` and `about` («there
  are no labels in this notebook»). Propose the notes without labels, and tell the user once, if it
  helps: «Se vuoi le etichette, scrivi la lista nel file etichette.toml della cartella del quaderno
  (c'è un modello negli esempi di Hypomnema).»
- **A notebook where only you write** (for example Claude Code's «diario di cantiere» on a project,
  where the notes are yours): you know the people and the topics better than anyone, so **propose the
  list in your message**, ready to paste, for example:

  «Per questo diario di cantiere ti propongo queste etichette. Se ti vanno bene, salvale tu nel file
  `etichette.toml` della cartella del quaderno:

  ```toml
  chi = ["Angelo", "Code"]
  cosa = ["interfaccia", "dati", "prove"]
  ```
  »

  Then wait: the labels work only after the user has saved the file. Never create it yourself.
- If the file is written wrong, the commands that need it stop with «ERRORE: … Non ho scritto
  niente.»: from 0.8.0 that means **every** `propose`, because the desk reads the list each time. Tell
  the user the error as it is; do not fix the file.
- `P labels` (`H labels` in chat) shows the list with how many notes have each label (and how many are
  still open), and the labels used in some note but no longer in the list.

## COSA labels: the desk adds them (from 0.8.0)

When a note passes through the desk, the desk looks in its `text` for the COSA labels of the list and
adds every one it finds, **written as in the list**, once, with no limit on their number:

- whole word, as `search` does, any case: «Orto», «ORTO», «l'orto», «orto-giardino» give `orto`;
  «ortografia» does not; accents count («caffe» is not «caffè»); a label of several words is found
  with any space or line break between the words;
- only in `text`: not in `context`, not in `quote`;
- the note then has the final list in `about` and, on its own line, the ones the desk added:
  `- labels from text: about orto`. The others were proposed by hand;
- at every new version (`corrects`, `updates`, `done`, `reopens`) the desk recomputes them from the
  text of the version, with the list as it is now: they follow the text. Labels proposed by hand are
  never touched by the desk;
- it never touches CHI labels and never changes the kind of the note.

So **you no longer need to remember the COSA labels**. Propose `about` only when the topic is not
written in the text (for example «Fatto!» about the garden): at most two, exactly as in the list.

The desk follows a fixed rule and does not understand meaning: «è in gioco la scadenza» gets `gioco`,
«la famiglia del vicino» gets `Famiglia`, «i bilanci» does not get `bilancio`. Do not try to fix this
by changing the user's words or by avoiding words: report it to the user if it matters. `P matches`
(`riscontri`) shows, read only, where the desk found each COSA, and the COSA proposed by hand that are
not in the text; `--about orto` for one label.

## CHI labels: only by hand

- **At most two** CHI per note, comma-separated: `"who": "Anna, Marco"`, **exactly as in the list**
  («anna» is not «Anna»). If no label fits, leave the field out: do not invent one (the desk rejects
  labels not in the list).
- The desk never looks for CHI in the text: nicknames and words like «papà» or «mia sorella» are yours
  to recognise.
- Labels are about **what the note is about**, not about where it comes from: `source` stays the chat
  (or book) the note was born in.
- **Your notes**: you choose the CHI labels.
- **The user's notes**: you propose them and **say them to the user** when you report the saved note
  («Salvata la T0012 con chi: Anna; cosa orto l'ha messa lo sportello. Se le vuoi diverse dimmelo.»). If
  the user wants other labels, propose an `updates` by the user with the labels they say.

```json
{
  "date": "2026-01-15",
  "source": "chat del 15 gennaio 2026 sull'orto",
  "author": "user",
  "knowledge": "stated",
  "kind": "todo",
  "who": "Anna",
  "text": "sabato semino il basilico nell'orto con Anna"
}
```

The desk adds `about: orto` by itself (it is in the text).

## Labels on notes already in the notebook

Old notes are never touched. Labels are added or changed with **`updates`**: a new version of the
note, with `who` and/or `about` and, as always, `text` = the reason.

- **The user** can always change the labels of any note.
- **You** can change the labels of your own notes, and **add** labels to one of the user's notes
  **only if it has none proposed by hand yet** (the ones added by the desk do not count). Once a
  user's note has labels proposed by hand, only the user changes them: if you think they are wrong,
  suggest it.
- From 0.9.0 the COSA from the text are also computed **when reading** (search, recap, labels, matches) for every
  note, old ones too, with the list as it is now: when the user adds a label to the list, every note that names it
  gets it at once, and no file is written. So **never propose versions just to add COSA that are in the text**.
- A version that only changes labels does not move the note in the recap and does not reset the days
  of the review: the note keeps the date of its last real change.
- Labelling many old notes: ask the user first («Vuoi che metta le etichette alle note vecchie? Sono
  N: una versione nuova per ciascuna.»), then propose one `updates` per note, with a short reason of
  yours («Etichetta messa dopo: la nota parla dell'orto.»).

```json
{
  "date": "2026-01-15",
  "source": "chat del 15 gennaio 2026",
  "author": "claude",
  "knowledge": "inferred",
  "updates": "0002",
  "about": "orto",
  "text": "Etichetta messa dopo: la nota parla dell'orto."
}
```

## Reading by label

- `P search --about orto`: all the notes with that label, **also without a word**; with a word,
  `P search basilico --who Anna --about orto`. The Italian names are `--chi` and `--cosa`.
- `P recap --about orto`: the recap with only those notes. The diary has no labels, so it is not shown.
- Several filters must **all** hold: `--who Anna --about orto` = the notes about Anna **and** the
  garden.
- A label that is neither in the list nor in any note is an error: check the spelling.
- `P labels` shows, for every COSA, how many notes have it from the text and how many by hand.
- `P status` has a line about the labels file. If it says `ERRORE`, tell the user the message as it is:
  until the file is fixed, **the desk saves nothing**. Never fix the file yourself.
