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
- **In a Claude chat** (claude.ai, desktop or mobile app): follow the "Chat mode" section at the
  end, and otherwise sections 1, 2, 4 and 5. Sections 0 and 6 do not apply: in chat there are
  neither witnesses nor diary. Start from **C0**: if the chat has a command line on the user's
  computer, it writes directly on the real notebook.

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
   Report to the user **in a few lines, in Italian**, what is there, keeping the notes (chosen by
   the user) apart from the diary (only the conversation).
   Then run `P review` (in chat `H review`): read only, it lists with fixed rules what is worth
   looking at (questions or todos stuck for a long time, overdue reminders, todos named in a later
   note, «ricordamelo» without a date, old branches, old chains not allowed today). If it finds something, **tell the user in
   one line**, for example «La revisione segnala 2 cose: la T0006 ha il promemoria scaduto e la
   O0004 è ferma da 46 giorni.» Do not change anything by yourself: each line says what *can* be
   done, the user decides.
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
| change kind, priority or reminder date | `"updates": "0049"` with `kind`, `priority` and/or `remind` | the reason |
| close an open question, a todo or a reminder | `"done": "0049"` or `"done": "0012, 0015"` | the reason |
| reopen a closed note | `"reopens": "0049"` | the reason |

- In a change `kind` is optional: without it the kind stays as it is (with `reopens`, it goes back to
  the kind before the closure). With `done` it can say what the question became: `decision`,
  `fact` or `idea`.
- `date`, `source`, `author`, `knowledge` and `text` are always needed. If the change is the user's,
  `text` is **their exact words** (the reason, or the new text), checked by the witness like any
  note of theirs; if it is yours, it is your words (with `quote` if you rely on theirs).
- **A correction does not close**: correcting a todo leaves it to do. To say it is done, use `done`.
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

### Saving Claude's replies

The user may ask you to keep one of your replies. These are two different cases, not to be
confused.

**«Salva questa risposta di Claude»** (or similar: «salvami questa spiegazione», «tieni nota di
quello che hai detto»): the note is **yours**.
- `author: claude`; `text`: the piece of your reply the user points to, copied as it is (if it is
  not clear which piece, ask);
- `knowledge`: `inferred` if it was your reasoning or a proposal, `observed` if it reported what
  you saw (a file, a result);
- `kind`: `idea` or `fact`, **never** `decision` (the desk would reject it);
- `source`: «risposta di Claude del <data> su <argomento>»;
- `from_reply: "yes"`: tells the desk that the text comes from one of your replies. If the replies
  witness is on, the desk looks for the text, word for word, in your recorded replies and rejects
  the note if it does not find it. If it is off (or in chat), the note is saved as "reply not
  verified". In the replies file code blocks may be replaced by their fingerprint: if the piece
  contains code, save it without the code.
- A note with `from_reply` **cannot also have `quote`**: the desk rejects it, because it comes
  either from one of your replies or from the user's words, not from both.

**«Questa risposta la faccio mia»** (or similar: «sono d'accordo, salvala come mia», «adotto
questa parte»), with the piece **pasted in the message**: the note is **the user's**, because the
adoption is theirs.
- `author: user`, `knowledge: stated`; `text`: the pasted piece, word for word as it appears in
  the user's message;
- `source`: which reply of yours it comes from, for example «risposta di Claude dell'11 ottobre
  2026 su <argomento>»;
- `kind`: whatever the user says; it can also be `decision`, because the adoption is theirs;
- with the witness on the text is verified as always, on the message where the user pasted it;
- if the user says «la faccio mia» without pasting anything, ask them to paste the piece: the
  words of a user's note must be in one of their messages.

In both cases advise the user to point to or paste **only the piece that matters**, not the whole
reply: short notes are found more easily.

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
4. You can delete the temporary proposal file: it is not part of the notebook.

Do not modify, rename or delete the notebook's files (`note/`, `registro.md`). The notebook only
grows.

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

There are two places to search, and they are not the same thing:

- the **notebook** is the **chosen notes**: `P search <word>`;
- the **diary** is **the whole recorded conversation**, raw: the user's messages and, if the
  replies witness is on, your replies. `P diary <word>`; with `--around` you also see the message
  just before and just after each one found; `P diary --last 10` shows the last ten.

When the user asks «cosa ci eravamo detti su…», «cosa ti avevo detto di…», «cosa mi avevi
consigliato…»:

1. search **the notebook first**;
2. **then, if needed**, the diary;
3. always say **where** the answer comes from: «Dalle note del quaderno (scelte da te): …» or
   «Dal diario, cioè dalla conversazione registrata, non da una nota: …». A note is the user's
   choice; the diary is only what was said. Something found only in the diary is **not** a
   decision, even if it sounded like one: if the user wants to keep it, propose a note.

You can also use the diary to reread what you advised and notice if you are now saying the
opposite: in that case tell the user openly.


## Chat mode

Follow this section when you are in a **Claude chat** (claude.ai, desktop or mobile app) and not
in Claude Code. In chat you cannot run commands on the user's computer, but you have a temporary
**work computer**, which disappears at the end of the conversation, where you can download the
programs and run Python. In chat **there are no witnesses**. In their place there is the **chat
archive**: with the tool that rereads chats (the «cerca e consulta le chat passate» permission in
Claude's settings) you can reread this conversation as Anthropic stored it, with the user's exact
words, the date and time of each message and the chat address. With the `archive` command you
copy it into the notebook (C5), and the user's notes whose text is found there are **matched
against the chat archive** (in Italian, to the user: «riscontrate sull'archivio della chat»; never
«verificate»), with the address anyone can open to check. Without the archive they stay "author
not verified (chat, no witness)".

Three levels, from the strongest: **verified by the witness** (Claude Code only), **matched against
the chat archive** (in chat, with the archive), **not verified**. The archive text passes through
you before reaching the programs: copy it **exactly as it is**, without retouching it.

All the other rules of this skill stay the same, and **you never save a note by hand**: you always
go through the desk. You do the dirty work; from the user you only ask permission for their
folder.

There are two ways, try them in this order:
- **C0, chat connected to the computer**: you have a command line on a machine that sees the
  user's `Hypomnema` folder, and the program works there. You use the desk of the **real notebook**
  directly: one command to save, nothing to copy back.
- **C1-C5, the work computer**: otherwise. You copy the notebook to your work computer, propose
  there and bring back the changed files.

### C0. Chat connected to the computer (from version 0.6.1)

With the desktop app the chat may have a command line on a Linux machine that sees the folders the
user connected, for example the `Hypomnema` folder as `$HOME/mnt/Hypomnema`. Below, `<HY>` is that
folder as you see it. On that machine **you must never delete or overwrite files in the connected
folders**, and GitHub cannot be reached.

**D1. Recognise the case** (at the start of the chat, once):

```
ls <HY>                                    # quaderno/ and programma-chat/ must be there
python3 --version                          # 3.10 or newer
python3 -B <HY>/programma-chat/programma.py --version   # hypomnema 0.6.1 or newer
```

- `programma-chat` is a copy of the program **updated by the user on Windows** with git (README,
  «Chat collegata al computer»). Never use the old `programma` folder, and never copy, change or
  update the program yourself from here.
- If `programma-chat` is missing or older than 0.6.1, tell the user once: «Per scrivere direttamente
  sul quaderno serve la cartella programma-chat aggiornata: su Windows, nella cartella Hypomnema,
  lancia `git clone --branch main https://github.com/angelomaccarinelli8-sys/hypomnema.git
  programma-chat` la prima volta, oppure `git -C programma-chat pull` per aggiornarla.» Then go on
  with C1-C5.
- **Always `python3 -B`**: so Python writes no `__pycache__` folders into the connected folder.

**D2. The chat configuration.** The chat uses its own file, `<HY>/hypomnema-chat.toml`, next to
`hypomnema.toml` (Claude Code's, with the witnesses on), **which you never use and never touch**.
If `hypomnema-chat.toml` is missing, create it from the model, without overwriting anything, and
tell the user («Ho creato hypomnema-chat.toml, la configurazione della chat, accanto a quella di
Claude Code: stesso quaderno.»):

```
[ -e <HY>/hypomnema-chat.toml ] || cp <HY>/programma-chat/chat/hypomnema-chat.toml <HY>/hypomnema-chat.toml
```

From here on `H` means exactly:

```
python3 -B <HY>/programma-chat/programma.py --config <HY>/hypomnema-chat.toml
```

**D3. At the start: check, recap, review on the real notebook.**
- `H status` must say `Testimone: NON C'È (configurazione per la chat di Claude)`. If it says
  anything else you are using the wrong configuration: **save nothing**, and go back to D2.
- Then `H check`, `H recap` and `H review`, with the rules of section 1 and of C2 point 4 (three
  lines to the user about where you left off, one line for the review).

**D4. Saving a note.**
1. If you have the chat archive, copy the new messages first (as in C5, step 2), writing the copy
   in `~/hypomnema-temp/archivio.json` in the **personal folder of the machine** (create it with
   `mkdir -p ~/hypomnema-temp`), **never** in the notebook or in a connected folder; then
   `H archive ~/hypomnema-temp/archivio.json`.
2. Write the proposal in `~/hypomnema-temp/proposta.json` (same folder), with the rules of
   section 2; the user's words from the archive copy, never from memory.
3. `H propose ~/hypomnema-temp/proposta.json`.
4. **Always, right after every `propose` (and every `archive`): `H check`.** It must answer «Quaderno
   in ordine». If it answers «ATTENZIONE», tell the user exactly what it lists (for example a note
   without its line in the register, or a damaged line): **do not repair anything and do not propose
   the same note again** until the user has looked.
5. Tell the user `ACCETTATA` or `RIFIUTATA` (section 4), and at which level («riscontrata
   sull'archivio della chat» or «non verificata»).

That is all: **no snapshot, no copy, no bringing back, no compare**. The temporary files stay
where they are: they are outside the connected folders.

**Two writers: the limit.** Claude Code (with the plugin, on Windows) may write on the same notebook
at the same moment. The desk's lock (the empty file `quaderno/.sportello.lock`, never to be deleted)
works only between programs **on the same machine**: it does **not** pass between Windows and the
chat's machine (tried on 18/10/2026). Between the two machines only these defences remain: a note is
created with an exclusive open (two writers never get the same number and never overwrite a note),
each register line is added with one single append, a note just being written is reread for a
moment, and **your `H check` after every `propose`**. If `propose` answers «ERRORE: il quaderno è
occupato da un altro passaggio», nothing was written: wait a few seconds and propose again. If the
user is working in Claude Code at the same time, prefer saving when they are not.

**D5. If something does not work** (the machine does not answer, Python older than 3.10,
`programma-chat` missing or old, `status` not saying «NON C'È», an `ERRORE` of the program), tell
the user in one line («Non riesco a scrivere direttamente sul quaderno: uso la procedura con la
copia.») and go on with C1-C5. If a proposal may have been half done, first run `H check` (or,
in C1-C5, check the copied register): a note already saved must not be proposed again.

### C1. Prepare the work computer (once per chat)

```
git clone --depth 1 --branch main https://github.com/angelomaccarinelli8-sys/hypomnema.git ~/hypomnema-programma
mkdir -p ~/hypomnema-lavoro/quaderno
cp ~/hypomnema-programma/chat/hypomnema-chat.toml ~/hypomnema-lavoro/hypomnema.toml
python3 --version
```

- You need Python 3.10 or newer (with 3.10 the program uses its own copy of the TOML reader).
  If `git` is not there, download and unpack
  `https://github.com/angelomaccarinelli8-sys/hypomnema/archive/refs/heads/main.zip`.
- From here on run every command from the folder `~/hypomnema-programma`, always with the chat
  configuration:

  ```
  python3 -m hypomnema --config ~/hypomnema-lavoro/hypomnema.toml <command>
  ```

  Below, `H <command>` means exactly this line.
- Check with `H status`: it must say `Testimone: NON C'È (configurazione per la chat di Claude)`,
  and the line `Archivio della chat:` says every how many exchanges to copy (`copia_ogni`, by
  default 5).
- Check whether you have the tool that rereads past chats. **If it is not there**, tell the user
  once: «Non posso rileggere questa chat dall'archivio: le note che salvo saranno "non
  verificate". Per averle riscontrate, attiva nelle impostazioni di Claude il permesso per cercare
  e consultare le chat passate.» Then carry on without the archive.
- If you cannot download the programs, tell the user and stop: without the desk you save nothing.

### C2. The user's notebook

**If you have the tools for the user's computer** (usually: desktop app open and connected):

1. Ask permission for the `Hypomnema` folder in their user folder (`C:\Users\<nome>\Hypomnema` on
   Windows, `~/Hypomnema` on macOS and Linux), with a sentence: «Mi serve il permesso per la
   cartella Hypomnema: leggo il tuo quaderno e ci salvo le note nuove, senza toccare
   nient'altro.» If the folder does not exist and the tools do not allow asking permission for a
   folder that is not there, ask the user to create it empty.
2. List the contents of `Hypomnema/quaderno`.
   - **It is not there, or it is empty**: it is the first time. Tell the user («È la prima volta:
     il quaderno è vuoto, nascerà con la prima nota.»). The notebook is born on the work computer
     with the first proposal and you bring it back to the user's computer as in point C4.
   - **It is there**: copy to the work computer, under `~/hypomnema-lavoro/quaderno/`, with **the
     same paths**, the file `registro.md` and all the files of the `note/` folder (also the versions,
     such as `0049.1.md`), in groups of at
     most 50 files at a time, and the chat archive files `archivio-chat.jsonl` and
     `diario-chat.jsonl` if they are there. Then check that the number of copied files equals the
     number listed. **Do not copy `testimone.jsonl` or `risposte.jsonl`**: in chat they are not
     needed, and they contain private words.
3. Check the copied notebook: `H check` (see section 1). It catches a save left halfway in a
   previous chat, or a file touched by hand.
4. **Where we left off.** Before answering the first message run `H recap` (section 1): overdue
   reminders, open questions, things to do, latest decisions and last lines of the diary, chosen
   with fixed rules. Then tell the user, **in three lines at most**, in Italian, where we left
   off: what was in progress, what had been decided (only from the notes), what was still open.
   Keep the notes (chosen by the user) apart from the diary (only the conversation). Then run
   `H review` and, if it finds something, say it in one line (section 1).

**If you do not have the tools for the user's computer** (chat on the web, mobile app): it is
**trial mode**. Before starting say it clearly: «Qui non posso accedere al tuo computer: il
quaderno vivrà solo in questa chat e sparirà quando la chiudi. È una prova.» Then use the notebook
in `~/hypomnema-lavoro/quaderno` and bring nothing back.

### C3. The questions

When the user asks what they said or decided («cosa avevo deciso su…»), use the search on the
copied notebook: `H search <word>`, with the rules of section 1 (a decision is a decision, an idea
is only an idea, an inferred note is a hypothesis, cite the note number).

### C4. Saving a note

For each note, in this order:

1. Take a snapshot of the notebook: `H snapshot > ~/hypomnema-lavoro/prima.json`
2. If you have the chat archive, **first** reread the conversation from the archive and copy the
   new messages as in point C5 (steps 2 and 3, without a new snapshot). The `text` of a user's note
   you take **from the archive copy**, word for word. **Never copy the user's words from memory**
   (non copiare mai le parole dell'utente a memoria) if the archive is available.
3. Write the proposal in `~/hypomnema-lavoro/proposta.json` (outside the notebook folder), with the
   rules of section 2, and pass it to the desk: `H propose ~/hypomnema-lavoro/proposta.json`
4. Ask which files changed: `H changed ~/hypomnema-lavoro/prima.json`
   - It answers with a list: **bring back to the user's computer exactly those files**, to the
     same path under `Hypomnema/quaderno/` (for example `note/0007.md` goes to
     `Hypomnema/quaderno/note/0007.md`, and a version `note/0049.1.md` goes to
     `Hypomnema/quaderno/note/0049.1.md`: keep the dot in the name), using the check on changed
     files. A change can create several files at once (`done: 0012, 0015` creates `0012.1.md` and
     `0015.1.md`): bring back every one listed. **First `registro.md`, then the chat archive files,
     then the created notes and versions.** Every proposal lengthens the register:
     if writing it succeeds, no other chat has written into the notebook after your copy, and you
     can write the rest. A rejected note also lengthens the register: it must be brought back.
     For **each** file to bring back:
     1. copy it into a **new folder** of the work computer, never used before in this chat, and
        bring it back from there. The folder name is `riporto-<AAAAMMGG>-<hhmm>-<lettera>`, with the
        date and time of the work computer (`date +%Y%m%d-%H%M`) and the letter `a`; for example
        `/mnt/user-data/outputs/riporto-20261015-1243-a/registro.md`. Create the folder with
        `mkdir` **without** `-p`: if it answers that it already exists, use the next letter (`b`,
        `c`…). No progressive numbers: in long chats they repeat. Starting again from a path
        already used, the tool may send back an old copy even if it answers that it wrote;
     2. right after, copy the file just written back from the user's computer into another new
        folder, with the same naming rule (for example
        `~/hypomnema-lavoro/verifica-20261015-1243-a/`), and compare it with the one on the work
        computer:
        `H compare ~/hypomnema-lavoro/quaderno/registro.md ~/hypomnema-lavoro/verifica-20261015-1243-a/registro.md`
        It must answer `UGUALI`;
     3. if it answers `DIVERSI`, or if you cannot copy it back: **stop, do not write other files**
        and tell the user: on their computer that file is not the right one.
   - It answers «Nessun file del quaderno è cambiato»: there is nothing to bring back.
   - It answers `ERRORE`: **bring nothing back**. Tell the user with the message received, copy the
     notebook again from their computer (C2) and start again from point 1.
   If the desk itself answers `ERRORE: il registro è stato toccato a mano`, it wrote nothing: tell
   the user with its words and do not try again until the user has fixed the register (`H check`
   shows the line to look at).
5. If the check **refuses to write the register** (the register on the user's computer changed in
   the meantime, for example because of another chat): **do not force and do not write the
   notes**. Nothing changed on the user's computer. Tell the user, copy the notebook again (C2) and
   repeat the proposal from point 1.
   If instead the register was written but the check **refuses a note** (it happens only if
   someone touched the notebook by hand): stop and tell the user. After copying the notebook
   again, `H check` will show the register line without its note.
6. Tell the user what was saved and what was rejected (section 4), and at which level:
   «riscontrata sull'archivio della chat» or «non verificata». In trial mode remind them that the
   notebook will disappear at the end of the chat.

In trial mode points 1, 4 and 5 are not needed: points 2 and 3 are enough.

### C5. Copying the conversation from the archive

This way the conversation ends up in the notebook by itself. Do it **every `copia_ogni`
exchanges** (`H status` says it, by default 5), **before saving a note** (C4) and **when the user
says they are closing**:

1. Take a snapshot of the notebook: `H snapshot > ~/hypomnema-lavoro/prima.json` (not needed if
   you do it inside C4).
2. Reread this conversation with the archive tool. The tool returns **at most 50 turns at a time**
   (al massimo 50 turni per volta), with a **marker** (segnalino) to ask for the next ones: read in
   pieces, following the marker, until you have all the turns you need (at the first copy of the
   chat all of them; afterwards, those after the last one copied, which `H status` shows). For
   **each piece** write in `~/hypomnema-lavoro/archivio.json` the chat address, the time zone and
   the messages, the user's and your replies, **exactly as the archive returns them**: the turn
   number, the date and time as they are (to the minute) and the whole text. The keys of this
   file stay as they are (`turno`, `quando`, `chi`, `testo`; `chi` is `utente` or `claude`):

   ```json
   {"chat": "https://claude.ai/chat/<codice della chat>", "fuso": "UTC+02:00",
    "messaggi": [{"turno": 12, "quando": "Fri 2026-10-09 17:46", "chi": "utente", "testo": "…"},
                 {"turno": 13, "quando": "Fri 2026-10-09 17:46", "chi": "claude", "testo": "…"}]}
   ```

   Remove nothing from the text: the technical notices the app inserts between
   `<system-reminder>` and `</system-reminder>` are removed by the program, with a fixed rule.
   **Convert nothing**: the tool writes `<`, `>` and `&` as `&lt;`, `&gt;` and `&amp;`. Copy the
   text as it is, with `&lt;` and `&gt;`: the `archive` program converts them (and so it also
   recognises technical notices written that way). The real signs end up in the notebook: when you
   then take the `text` of a note from the copy, write `<` and `>`, not `&lt;` and `&gt;`. Include
   the messages already copied too: the program recognises duplicates from the chat address and
   the turn number, and does not duplicate them. Include the messages starting with `#privato` too:
   the program keeps only their date and time, and the same for your reply.
3. For each piece: `H archive ~/hypomnema-lavoro/archivio.json`. If it warns that a message already
   present has a different text, tell the user: touch nothing. If it refuses the copy (for example
   because of a technical notice without its closing), tell the user with the message received.
4. `H changed ~/hypomnema-lavoro/prima.json` and bring back the listed files as in C4 (a new
   folder for each bring-back, then `H compare`).
5. Tell the user in one line: «Ho copiato nel quaderno gli ultimi messaggi di questa chat.»
