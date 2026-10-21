# Hypomnema: the models of the moves (from 0.10.0)

Read this file before writing a proposal if you are not sure of its fields. Every move has **only these
fields**; anything else is rejected or changes something you did not mean. `P template <move>` (in chat
`H template <move>`) prints the same models empty, with today's date. In all of them:

- `author` is `user` (their words in `text`, your additions in `context`) or `claude` (your words in
  `text`, theirs in `quote`; never `context`, never `priority`);
- `knowledge` is `stated`, `observed` or `inferred` (a decision is always `stated`);
- references to a note are **only the number** (`"0012"`, never `"I0012"`);
- the user's words are copied exactly, never from memory; nothing is ever invented to fill a field.

## 1. New note (`new`)

```json
{"date": "2026-01-15", "source": "chat del 15 gennaio 2026 sull'orto", "author": "user", "knowledge": "stated",
 "kind": "idea", "text": "per i pomodori dell'orto userei i tutori di bambù"}
```

Optional: `context` (user's notes), `quote` (yours), `remind`, `priority` (only the user), `who`, `about`
(only labels from the list, and `about` only when the COSA is **not** written in the text), `confirms` (only
a decision that confirms an idea). Before an `idea` or a `fact`, look at its sub-branch (SKILL.md, section 2):
if a live note of the same author and kind is there, the move is an integration, not a new note.

## 2. Integration (`integrates`)

New words at the end of a note of the **same author**:

```json
{"date": "2026-01-15", "source": "chat del 15 gennaio 2026 sull'orto", "author": "user", "knowledge": "stated",
 "integrates": "0002", "text": "i pomodori dell'orto li coprirei con la rete antigrandine"}
```

Or the text of another note about the same thing at the end of this one (**no `text`**: the desk copies it):

```json
{"date": "2026-01-15", "source": "chat del 15 gennaio 2026 sull'orto", "author": "user", "knowledge": "stated",
 "integrates": "0002", "from_note": "0001"}
```

**Never `kind`, `about`, `who`, `priority`, `remind` or `context`** in an integration: the desk rejects them
(the note keeps its own kind and labels; to change them use `updates`).

## 3. Update (`updates`)

```json
{"date": "2026-01-15", "source": "chat del 15 gennaio 2026 sull'orto", "author": "user", "knowledge": "stated",
 "updates": "0006", "priority": "high", "text": "il basilico è urgente"}
```

Only the fields that change, among `kind`, `priority`, `remind`, `who`, `about`; `text` is the reason.
Optional: `context`, only if the change is the user's.

## 4. Closure (`done`)

```json
{"date": "2026-01-15", "source": "chat del 15 gennaio 2026 sull'orto", "author": "user", "knowledge": "stated",
 "done": "0012", "kind": "decision", "text": "la compostiera va nell'angolo nord"}
```

Only for `open`, `todo` and reminders (`"done": "0012, 0015"` closes several). `kind` is optional: what the
note became (`decision`, `fact` or `idea`; `decision` and every `open` only by the user). Optional: `context`
(user's closures).

## 5. Cancellation (`cancels`)

```json
{"date": "2026-01-15", "source": "chat del 15 gennaio 2026 sull'orto", "author": "user", "knowledge": "stated",
 "cancels": "0004", "text": "la panchina non serve più"}
```

The note **no longer counts** (any kind), which is not «done». Only the user cancels the user's notes.
Optional: `context` (user's cancellations). `reopens` makes it count again.

The other moves (`corrects`, `reopens`, `confirms`) are in SKILL.md, «Changing a note: versions».
