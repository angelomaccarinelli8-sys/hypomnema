# Registro degli ingressi

Ogni riga è un passaggio dallo sportello. Questo file si allunga soltanto.

- 2026-01-15T10:00:00+01:00 | ACCETTATA | nota 0001 | da: 1-open.json
- 2026-01-15T10:02:00+01:00 | RIFIUTATA | da: 2-chiusura-di-claude.json | motivi: only the user can close an open note («0001»): Claude can suggest it, but the closing note must have author «user».
- 2026-01-15T10:03:00+01:00 | ACCETTATA | nota 0002 | da: 3-chiusura-dell-utente.json
- 2026-01-15T10:04:00+01:00 | RIFIUTATA | da: 4-seconda-chiusura.json | motivi: note «0001» is already closed by note «0002».
- 2026-01-15T10:05:00+01:00 | RIFIUTATA | da: 5-chiusura-open.json | motivi: a note that closes something cannot be «open»: its kind says what the question became (decision, todo, fact or idea). / note «0001» is already closed by note «0002».
- 2026-01-15T10:06:00+01:00 | RIFIUTATA | da: 6-chiudere-un-fatto.json | motivi: note «0002» is a «decision»: «done» closes only open, todo and reminder notes (with «remind»). A fact, a decision or an idea is not closed: write a new note with «corrects».
