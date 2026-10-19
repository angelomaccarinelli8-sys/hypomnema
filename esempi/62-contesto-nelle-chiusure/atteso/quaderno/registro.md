# Registro degli ingressi

Ogni riga è un passaggio dallo sportello. Questo file si allunga soltanto.

- 2026-01-15T10:00:00+01:00 | ACCETTATA | nota 0001 | da: 1-todo.json
- 2026-01-15T10:01:00+01:00 | ACCETTATA | nota 0002 | da: 2-open.json
- 2026-01-15T10:02:00+01:00 | ACCETTATA | nota 0003 | da: 3-todo-di-claude.json
- 2026-01-15T10:03:00+01:00 | ACCETTATA | nota 0001.1 | da: 4-fatto-con-contesto.json
- 2026-01-15T10:04:00+01:00 | RIFIUTATA | da: 5-claude-chiude-con-contesto.json | motivi: the field «context» is only for notes with author «user», to keep Claude's explanations apart from the user's words: in a note by Claude all the text is already Claude's.
- 2026-01-15T10:05:00+01:00 | RIFIUTATA | da: 6-chiusura-da-risposta.json | motivi: the field «from_reply» belongs to the text of a note: it can be used only in a new note or with «corrects», not with «done». / the field «from_reply» is only for Claude's notes: if the user makes one of Claude's replies their own, the note is the user's and where it comes from goes in «source».
- 2026-01-15T10:06:00+01:00 | ACCETTATA | nota 0002.1 | da: 7-priorita-con-contesto.json
