# Hypomnema: chat mode

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
If `hypomnema-chat.toml` is missing, create it from the model, without overwriting anything:

```
[ -e <HY>/hypomnema-chat.toml ] || cp <HY>/programma-chat/chat/hypomnema-chat.toml <HY>/hypomnema-chat.toml
```

Then tell the user («Ho creato hypomnema-chat.toml, la configurazione della chat, accanto a quella di
Claude Code: stesso quaderno.»). If the file already exists, never change it. **Do not add a `fuso`
line**: from 0.7.0 the time zone comes from the user's operating system (see «The time zone» below).

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
at the same moment. The desk's lock (from 0.7.0 an empty file in the temporary folder of each
machine; the old `quaderno/.sportello.lock` of 0.6.1 is no longer used and must not be deleted by you)
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

**The time zone** (from 0.7.0). The time zone of the notebook comes from **the user's operating
system**: on the user's computer Hypomnema reads it (on Windows with the official CLDR table) and writes
it in the file `fuso-del-sistema.jsonl` of the notebook, adding a line when it changes. The chat's
machine keeps its clock in UTC: there the programs use, in this order, a `fuso` line of the
configuration if the user wrote one, then the last line of that file, then UTC. `H status` says which,
on the line `Fuso orario:`. If it says «UTC, quello di questa macchina» with «il quaderno non ha ancora
il file», tell the user once: «Il quaderno non sa ancora il tuo fuso orario: lo scrive Hypomnema la
prima volta che lo usi in Claude Code sul tuo computer. Fino ad allora date e ore della chat sono in
UTC.» **Never write that file and never add a `fuso` line yourself**; nothing is blocked either way.

**Labels** (`who`, `about`, `H labels`) need `programma-chat` 0.7.0 or newer: with an older one,
propose notes without labels. The list is `<HY>/quaderno/etichette.toml`, the same for Claude Code
and the chat: read `labels.md`.

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
     most 50 files at a time, the chat archive files `archivio-chat.jsonl` and
     `diario-chat.jsonl` if they are there, the list of labels `etichette.toml` and the time zone
     file `fuso-del-sistema.jsonl` if they are there (never bring them back: the user and their
     computer write them). Then check that the number of copied files equals the
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
