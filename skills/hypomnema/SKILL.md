---
name: hypomnema
description: Permanent memory between one chat and the next, in Markdown files on the user's computer. Use it at the start of every chat to reread the useful notes, and during the chat to propose to Hypomnema's desk the things worth remembering (facts, ideas, decisions, open questions, things to do). Claude proposes, the programs decide.
---

# Hypomnema: the memory notebook

Hypomnema is a notebook of notes on the user's computer. **You never write directly into the
notebook's files.** You propose notes to the desk (`propose`), a program that applies fixed rules
and decides whether they get in. To read, you use the search (`search`) and the recap (`recap`).

**Language by role.** The structure is in English: commands, field names, field values, the
desk's rejection reasons, these instructions. The content stays in its own language: the user's
words in a note are copied exactly as written (usually Italian), and **you always talk to the user
in Italian**. The sentences to say to the user are written below in Italian, between «».
The Italian names of commands and fields of earlier versions still work (`cerca` = `search`,
`autore: utente` = `author: user`), but write new proposals in English.

If the user switched it on, another program, the **witness**, records the exact words of each of
their messages before you read it. The desk uses it to check that notes with `author: user`
really contain words the user said. Never write into the witness's file, not even through
commands or scripts: its whole value lies in the fact that you do not touch it.

## Where you are

- **In Claude Code** (you can run commands on the user's computer): follow the sections from
  "How to run the programs" to 6.
- **In a Claude chat** (claude.ai, desktop or mobile app): **read `chat-mode.md`** (in this skill's
  folder) before doing anything else, and otherwise follow sections 1, 2, 4 and 5. Sections 0 and 6 do
  not apply: in chat there are neither witnesses nor diary. Start from **C0**: if the chat has a
  command line on the user's computer, it writes directly on the real notebook.

**The other files of this skill**, next to this one, read only when they are needed: `chat-mode.md`
(the chat, C0-C5), `labels.md` (the labels CHI and COSA, in full), `replies.md` (saving your
replies), `diary.md` (section 6, what was said).

## How to run the programs (Claude Code)

In Claude Code Hypomnema is a **plugin**: the programs live inside the plugin and run like this,
from any folder:

```
py "${CLAUDE_PLUGIN_ROOT}/programma.py" status
```

Below, `P` means exactly `py "${CLAUDE_PLUGIN_ROOT}/programma.py"` (on macOS and Linux `python3`
instead of `py`): for example `P search <word>`, `P propose <file.json>`.

- The configuration and the notebook are found automatically: `~/Hypomnema/hypomnema.toml` (on
  Windows `%USERPROFILE%\Hypomnema\hypomnema.toml`), or the file named by the `HYPOMNEMA_CONFIG`
  variable. Do not pass `--config`.
- If in the command above you still see the text `${CLAUDE_PLUGIN_ROOT}`, the plugin is not
  loaded: tell the user and do not save anything.
- Exit codes: `0` all good, `1` note rejected, `2` error (configuration, missing file).
- The programs' messages to the user are in Italian (`ACCETTATA`, `RIFIUTATA`, «Trovate 2 note…»).
- If at the start of the session there is a notice beginning with «Hypomnema» (the first time, a
  notebook in a synced folder, witnesses paused…), report it to the user in simple Italian.

## 0. Check the witness (Claude Code)

Run `P status` **at the start of the session** and **every time before proposing a note with
`author: user`**. It is a comparison, not an estimate: look at two lines.

1. `Testimone:` must say `ACCESO`, or `IN PAUSA` if the user asked for a pause.
2. If it is `ACCESO`, the user's message you have just received must be the last one recorded:
   the text under `Testo dell'ultimo messaggio:` must be the same, word for word (the spaces at the
   start of the lines are added by the command). If the message you received starts with
   `#privato`, the last one recorded must be `(messaggio privato, non registrato)`.

If something does not match, warn the user with a clear sentence **before** saving their notes:

- witness `SPENTO`: «Il testimone non è attivo: le note che salvi ora saranno marcate come non
  verificate. Per accenderlo serve attivo = true nella configurazione di Hypomnema.»
- witness `IN PAUSA`: it is not a fault, the user asked for it. Just remind them that the notes
  they save now will be marked as not verified and that `/hypomnema:resume` resumes.
- witness `ACCESO`, but the last recorded message is not the one you received: «Il testimone non
  ha registrato il tuo ultimo messaggio: le note con le tue parole di adesso verrebbero rifiutate,
  perché non si possono verificare. Controlla con /plugin che il plugin di Hypomnema sia
  installato e attivo.»
- the command exits with `ERRORE`: report the error message to the user as it is.

Do not try to repair the witness yourself: do not touch configuration, notebook or settings.

**La pausa la decide solo l'utente**: only the user decides the pause, by writing
`/hypomnema:pause` or `/hypomnema:resume` (also `/hypomnema:pausa` and `/hypomnema:riprendi`). You
never pause or resume the witnesses: do not write those commands, do not create scheduled tasks or
messages that contain them, do not touch the witnesses' files.

## 1. At the start of a chat: reread

First check that notes and register match: `P check` (in chat: `H check`, point C2). If it answers
«ATTENZIONE», tell the user which notes do not match the register and why. **Do not repair
anything**: the register only grows and the decision is theirs. Then carry on normally.

1. **Where we left off**: run `P recap` (in chat `H recap`). With fixed rules it shows the overdue
   reminders, the open questions, the things to do, the latest decisions and the last lines of
   the diary, high priority first in each block: you do not choose the words to search for.
   In each block, after the priority, the notes go from the most recently changed (the day of their
   last version; a version that only sets labels does not count). Reminders go by their date.
   Report to the user **in a few lines, in Italian**, what is there, keeping the notes (chosen by
   the user) apart from the diary (only the conversation).
   Then run `P review` (in chat `H review`): read only, it lists with fixed rules what is worth
   looking at (questions or todos stuck for a long time, overdue reminders, todos named in a later
   note, «ricordamelo» without a date, old branches, old chains not allowed today). If it finds something, **tell the user in
   one line**, for example «La revisione segnala 2 cose: la T0006 ha il promemoria scaduto e la
   O0004 è ferma da 46 giorni.» Do not change anything by yourself: each line says what *can* be
   done, the user decides. From 0.9.0 it also lists notes **integrable** into another; from 0.10.0 as **chains**:
   all the live notes of the same author and kind in one sub-branch go into the most recent one (without
   sub-branches: a COSA in common and one names the other **in its text**). Propose them in the printed order. And `P review --proposals` prints ready-made proposals with `source`
   (and `text`) left empty: if the user accepts one, fill them with **the user's words** (never invented)
   and propose it as usual, one at a time.
   `P graph <file.html>` writes, outside the notebook, a page with the graph of the notebook: offer it when
   the user wants to see the notebook as a whole.
2. When a specific topic is needed later, run `P search <word>`. The search is by exact word,
   case-insensitive: try singular/plural too if needed. It also finds words inside compound names
   (`orto` finds `orto_balcone.py`). Notes come **from the most recent to the oldest**. **Closed
   notes** are not shown: the output says how many were hidden, and `P search <word> --all` shows
   them too.
3. Every note is shown at its **last version**, in full, followed by its **history**: one line per
   version (what changed, who, when, why). **The last version is what counts**; the history tells
   you what was wrong before, so you do not repeat it. Under a note come, indented, the notes that
   **confirm** it.
4. Use the notes found respecting what they are:
   - a user's **decision** counts as a decision;
   - an **idea** is only a proposal, not a decision;
   - an **inferred** note is a hypothesis: do not present it as certain;
   - cite the note by its code when you use it («dalla nota T0004.2 …»). The code is the letter of
     its kind (F fact, I idea, D decision, O open, T todo), with `✓` in front if it is closed, then
     the number and the version: `✓T0049.3`. The recap ends with this legend.
5. Do not invent notes the search did not return.

## 2. During the chat: prepare the notes

Propose a note when something comes up that will be useful in a future chat: a fact, a
preference, an idea, a decision, an open question, something to do. One note = one thing.

Format (JSON, UTF-8), with **all** these fields:

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

- `date`: today, `YYYY-MM-DD` (optionally with the time: `YYYY-MM-DDThh:mm`).
- `source`: where it comes from, on one line (usually «chat del <data> su <argomento>»; it is
  content, so write it in Italian).
- `author`: `user` if the user said it; `claude` if it is your observation, inference or proposal.
  **Never attribute to the user things they did not say.**
- `knowledge`: how it is known.
  - `stated`: the author said it explicitly;
  - `observed`: you saw it directly (in a file, in a result, in the conversation);
  - `inferred`: you worked it out by reasoning. When in doubt, `inferred`.
- `kind`: what the note is (optional only in a change, see below). Five values:
  - `fact`: something that is so;
  - `idea`: a proposal (your proposals are always `idea`);
  - `decision`: only if the user decided explicitly: `author: user`, `knowledge: stated`;
  - `open`: a question still open (in earlier versions «discorso aperto»);
  - `todo`: something to do.
- `text`: **depends on the author** (see below). The user's words and yours never mix in the
  same field.
- `context` (optional, only in the user's notes): your explanations.
- `quote` (optional, only in your notes): the user's words you are relying on.
- `remind` (optional): a **reminder**, the date `YYYY-MM-DD` on which to pick the note up again (for
  example when the user says «ricordamelo lunedì» or «tra tre giorni»: you compute the day from the
  date of the chat). `P reminders` lists the overdue ones.
- `priority` (optional, **only in the user's notes**): `high`, `normal` or `low`. See "Priority".
- `who` and `about` (optional): the **labels** CHI (people) and COSA (projects, topics), at most two
  each, comma-separated, only from the user's list. See "Labels" below.
- `corrects`, `updates`, `done`, `reopens` (optional, one at a time): they **change a note that is
  already there**. See "Changing a note: versions" below.

### The user's notes: the text is their words

In a note with `author: user`, `text` is **the user's exact words**, copied from one of their
messages: a continuous piece of a single message, with the same capitals, accents and
punctuation. You may choose the most useful piece, but **do not summarise, correct, translate or
change a single word**. Everything you add (what was being discussed, what it refers to, an
explanation) goes in the field `context`, which will be shown as «contesto scritto da Claude».

```json
{
  "date": "2026-01-15",
  "source": "chat del 15 gennaio 2026 sul progetto dell'orto",
  "author": "user",
  "knowledge": "stated",
  "kind": "fact",
  "text": "il basilico sul balcone sta crescendo bene",
  "context": "Detto parlando delle piante aromatiche dell'orto."
}
```

- With the witness on, the desk looks for the `text` in the recorded messages. If it answers that
  it is not found, copy it again more carefully. If the user did not say that thing in their own
  words, **it is not a user's note**: at most it is a note of yours (`author: claude`, usually
  `knowledge: inferred`).
- With the witness off the rule is the same (exact words in `text`), but nobody checks it: the
  note will be marked "author not verified".
- Do not write the field `verification` yourself: the desk adds it.

### Pasted text and source

Hypomnema is a notebook of jottings: collecting passages read elsewhere is exactly its purpose.
A text the user pastes into a message counts as brought by them into the notebook: the note is
`author: user`. **Where it comes from is said by `source`**: for example «dal libro <titolo>»,
«dalla spiegazione di Claude del <data>», «mio pensiero». There is no need to tell written text
from pasted text.

### The `>` sign (optional)

If the user starts some lines of the message with `>` (the classic sign for reporting someone
else's words), they are marking those lines as a quotation. When you copy those lines into
`text`, **remove the `>`** at the start of each line and put in `source` where the passage comes
from, if the user says so. If the text comes entirely from marked lines, the desk adds by itself
the wording "quote reported by the user". Without the sign everything works as always.

### Your notes

In a note with `author: claude` the `text` is yours. If it relies on the user's words you can put
those exact words in `quote`: with the witness on it is checked the same way. Do not use `context`
in your notes: it is all yours already.

### Changing a note: versions

A note is never rewritten. **Every change is a new version** of the note: the desk writes a new
file (`0049.1.md`, `0049.2.md`) with the whole note, the change applied and, at the bottom, who
changed what, when and why. You always change the **last** version: write only the number
(`"0049"`), **without the letter of the code** (`"T0049"` is rejected). A change does not create a
new note number.

| The user (or you) want to… | Proposal | `text` is |
|---|---|---|
| correct the text («no, era a marzo») | `"corrects": "0049"` | the new text |
| change kind, priority, reminder date or labels | `"updates": "0049"` with `kind`, `priority`, `remind`, `who` and/or `about` | the reason |
| close an open question, a todo or a reminder | `"done": "0049"` or `"done": "0012, 0015"` | the reason |
| reopen a closed note | `"reopens": "0049"` | the reason |
| add new words at the end of a note (0.9.0) | `"integrates": "0049"` | the new words (same author as the note) |
| cancel a note: it no longer counts, it was not done (0.9.0) | `"cancels": "0049"` | the reason |
| put another note about the same thing at the end of this one (0.9.0) | `"integrates": "0049", "from_note": "0052"` | **no `text`**: the desk copies the text of 0052 |

- In a change `kind` is optional: without it the kind stays as it is (with `reopens`, it goes back to
  the kind before the closure). With `done` it can say what the question became: `decision`,
  `fact` or `idea`.
- `date`, `source`, `author`, `knowledge` and `text` are always needed. If the change is the user's,
  `text` is **their exact words** (the reason, or the new text), checked by the witness like any
  note of theirs; if it is yours, it is your words (with `quote` if you rely on theirs).
- In a change **by the user** (`updates`, `done`, `reopens`) you may add `context`: your
  explanation next to their reason (for example what «fatto» refers to). It is saved apart, as
  «contesto scritto da Claude». Never in your own changes; never `from_reply` in a change.
- **A correction does not close**: correcting a todo leaves it to do. To say it is done, use `done`.
- **`integrates`** (from 0.9.0) keeps the text of the note **intact** and adds a piece at the end: new words
  (verified like any note, and only by the note's author: never your words in a user's note), or with
  `from_note` the text of another note **as it is**, with that note's date, source and verification. Only
  notes with a COSA label in common, with the same author, and only the user integrates a user's note
  (it leaves the recap; with `search --all` it shows «integrata nella nota …»). No `kind`: use `updates`.
  Propose it when the user says that two notes are the same idea growing; never on your own initiative.
- **`cancels`** (from 0.9.0): the note **no longer counts** (any kind, decisions too), which is not «done». The code
  gets a C in front: `CD0156.1`. It leaves the recap and the basic search; `reopens` makes it count again. Only the
  user cancels (and makes count again) the user's notes; you only your own.
- `done: 0012, 0015` creates one closed version for each note, with the same reason.
- Who can do what:
  - **only the user** closes, reopens or changes the kind of an `open`, makes a note a
    `decision`, changes the kind of a decision or of one of the user's notes, sets `priority`, and
    corrects the text of one of the user's notes (they are their words);
  - you can close and reopen `todo`s and reminders, correct your own notes and change the kind of
    your own notes (never into `decision`);
  - an idea becomes a decision only with a **new** note with `confirms` (section 5);
  - a `fact`, a `decision` or an `idea` without `remind` is not closed: it is corrected or changed.
  When a rule blocks you, suggest it to the user: «La questione O0012 sembra risolta: vuoi che la
  chiuda con le tue parole?».
- The desk answers with the new version: `ACCETTATA: la versione 0049.1 della nota 0049 …` (one line
  per note with `done` on several notes).

A closure by the user:

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

A change of priority by the user:

```json
{
  "date": "2026-01-15",
  "source": "chat del 15 gennaio 2026 sull'orto",
  "author": "user",
  "knowledge": "stated",
  "updates": "0006",
  "priority": "high",
  "text": "il basilico è urgente"
}
```

`recap` and `search` read every note as it is **now** (its last version). They hide closed todos,
open questions and reminders, also when they became facts or ideas; `search <word> --all` shows them,
with their history. A question closed as a **decision is a decision**: it appears in «Ultime
decisioni» and in the search, with its code (`✓D0049.3`): the ✓ means it is settled, not hidden. In the
recap the history lines under a note go from the most recent to the oldest.
Notes written before versions existed (old corrections with `corrects`, old closing notes with
`done`) are shown as versions too, with their real number next to them: `T0001.1 (nota 0002)`; their
old number still works in a proposal if that version is the last one. Today's rules apply to them
too: an old note of yours that corrected the user's text, or made an `open` stop being open, stays in
the history but does not count («non applicato (catena vecchia non permessa oggi)»): the user's text
stays theirs, an open stays open. Never treat that old change as valid; if it is needed, propose it to
the user.

### Priority

`priority` (`high`, `normal`, `low`) is **only the user's**: the desk rejects it in your notes. If
you think something is urgent, say it to the user or write it in the text of one of your `idea`
notes («Proposta: priorità alta per la nota 0012»); the user decides. To change the priority of a
note, propose `updates: <number>` by the user with the new `priority`. A note without priority
counts as `normal`. The recap shows high-priority notes first in each block.

### The rules of the notebook, in short

The complete list, with right and wrong examples, is in `FORMATO.md` («Le regole del quaderno»).
The ones the programs cannot check are yours to follow:

- **one note = one thing**: two things are two notes;
- `open` is a question or something still to decide; `todo` is something to do;
- «ricordati questa cosa» (a program, an address, a number) is a `fact`, not an `open`;
- «ricordamelo», «tra tre giorni» → the `remind` field with the date;
- the user's words are **copied** (in chat, from the archive), never from memory; a message
  dictated by voice keeps its transcription mistakes;
- `source` says in which chat (or book) the note was born, not what it is about;
- `date` is when the thing was said, not the day you save it.

### Notebook rules that change: the rule note

When the user decides that from now on the notebook works differently (for example «da adesso le
spese le segno solo come todo»), propose a `decision` by the user whose text says it, with their
words, for example «Da questa nota in poi le spese le segno solo come todo». It is a normal
decision: no special field. From then on follow it, and when you find it in the recap or in a
search, respect it as a rule of the notebook.

### Labels: CHI and COSA (from version 0.7.0; COSA by the desk from 0.8.0)

**Before proposing labels for the first time in a chat, read `labels.md`.** In short:

- The list is the file `etichette.toml` **in the notebook folder** (`chi = [...]`, `cosa = [...]`),
  shared by Claude Code and the chat. **The user writes it; you never write it.** Without the file no
  note can have labels. In a notebook where only you write (for example Claude Code's «diario di
  cantiere» on a project), propose the list **in your message**, ready to paste, and the user saves it.
- **COSA labels are added by the desk** (from 0.8.0): it finds the COSA of the list in the note's
  `text` (whole word, any case) and adds them. You no longer need to remember them. Propose `about`
  only when the topic is not written in the text (at most two, exactly as in the list).
- **CHI labels are only proposed by hand**, as before: `who`, at most two, exactly as in the list. For
  the user's notes you propose them and say them to the user; the user can change them.
- Labels change with `updates`. You can add labels to one of the user's notes **only if it has none
  proposed by hand yet**; once set, only the user changes them.
- **Sub-branches** (from 0.10.0): a COSA can have sub-branches (topics) with their words, in `[rami.<cosa>]` of
  `etichette.toml` (only the user writes them). `P tree` (`albero`, `--cosa X` for one branch) shows branch →
  sub-branches → notes, integration chains on one line (`I0005.2 ← I0002 ← I0001`), and «senza argomento» for the
  notes of the branch that no sub-branch catches: tell the user when that list is long, words are missing.
- **One idea, one note per sub-branch** (I0213): the desk rejects a new `idea` when a live idea of the same author is in
  the same sub-branch («this idea already has its note (0002, sub-branch orto/pomodori)…»): propose it as `integrates`
  of that note instead. For a new `fact` it only prints a SUGGERIMENTO and the note passes: ask the user whether it is
  the same fact growing. Never get around the rule: if the ideas are really different, tell the user that the
  sub-branch needs more precise words in `etichette.toml`.
- `P search --about orto`, `P recap --about orto` (`--who`, `--chi`, `--cosa` too), `P labels` (counts),
  `P matches` (where the desk found each COSA, read only). If `P status` says `ERRORE` on the labels
  line, tell the user: until the file is fixed the desk saves nothing.

### Saving your replies

When the user asks to keep one of your replies («salva questa risposta», «questa la faccio mia»),
**read `replies.md`** first: the two cases have different authors.

### Private messages

A message starting with `#privato` (or with the prefix the user chose in `hypomnema.toml`) **does
not end up in the witness, but you read it anyway**: "private" means its words are not recorded.
**Do not propose notes about what the user says in a private message**, neither theirs nor yours,
unless they explicitly ask you in a normal message (and even then their words cannot be verified,
because the witness did not record them).

## 3. Pass the notes to the desk

1. Write the proposal in a temporary file **outside the notebook folder** (for example
   `proposta.json` in the program folder, where git ignores it), in UTF-8.
2. Run `P propose proposta.json`. Alternatively you can pass it through standard input:
   `P propose -`.
3. Read the answer:
   - `ACCETTATA`: the note has a number (a change: a new version, such as `0049.1`) and is saved;
   - `RIFIUTATA`: read the reasons (in English). If it is a format mistake of yours, fix it and
     propose again. **Never get around a rule** (for example by changing the author to get a
     decision through): if the rule blocks the note, the note does not get in.
   - `SUGGERIMENTO (non cambia niente): suona come una decisione (…)` (from 0.9.0, only for the user's new
     notes): the patterns of the user's way of speaking, counted from the notebook with fixed rules, say
     that the text sounds like another kind. It changes nothing. Tell the user in one line («Lo schema
     dice che suona come una decisione: la lascio idea?») and **never change the kind by yourself**: if
     the user says so, propose an `updates` by the user. `P patterns` shows the patterns.
4. You can delete the temporary proposal file: it is not part of the notebook.

Do not modify, rename or delete the notebook's files (`note/`, `registro.md`, `etichette.toml`). The
notebook only grows.

## 4. Tell the user what happened

After each pass through the desk, tell the user in a few Italian words:
- what was **saved** (note code and short text, for example «salvata la T0049.1: priorità alta»);
- what was **rejected** and why (with the desk's reason, in plain Italian).

Never say that something was saved if the desk did not answer `ACCETTATA`. When you use a note
marked "author not verified" (in older notes «autore non verificato»), remember that nobody
checked that the user really said it.

## 5. From idea to decision

An idea becomes a decision **only with the user's explicit confirmation**. For example: «sì,
facciamo così», «confermo l'idea 0001», «decidiamo questo». A silence, an «interessante» or a
«vedremo» are **not** confirmations: when in doubt, ask.

When the user confirms:

1. find the number of the idea (with `search`, if you do not know it already);
2. propose a **new** note:

```json
{
  "date": "2026-01-15",
  "source": "chat del 15 gennaio 2026 sul progetto dell'orto",
  "author": "user",
  "knowledge": "stated",
  "kind": "decision",
  "confirms": "0001",
  "text": "sì, da domani annaffio la mattina presto",
  "context": "Conferma dell'idea 0001: annaffiare la mattina presto invece che la sera."
}
```

   The `text` is the exact words with which the user confirmed.
3. the original idea stays as it is: the notebook keeps both the idea and the decision.

The user may also say «ricorda che ho deciso …»: in that case propose a decision directly
(`author: user`, `knowledge: stated`) without `confirms`.

## 6. What we said: notebook and diary (Claude Code)

When the user asks «cosa ci eravamo detti su…», «cosa ti avevo detto di…», **read `diary.md`**: the
notebook (chosen notes, `P search`) comes first, the diary (the raw conversation, `P diary`) only
after, and you always say where the answer comes from.
