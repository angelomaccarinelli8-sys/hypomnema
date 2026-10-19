# Hypomnema: saving Claude's replies

Read this when the user asks to keep one of your replies. It completes section 2 of `SKILL.md`, whose
rules stay the same.

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
