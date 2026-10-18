# Registro degli ingressi

Ogni riga è un passaggio dallo sportello. Questo file si allunga soltanto.

- 2026-01-15T10:00:00+01:00 | ACCETTATA | nota 0001 | da: 1-open.json
- 2026-01-15T10:02:00+01:00 | RIFIUTATA | da: 2-chiusura-di-claude.json | motivi: only the user can close an open note («0001»): Claude can suggest it, but the proposal must have author «user».
- 2026-01-15T10:03:00+01:00 | ACCETTATA | nota 0001.1 | da: 3-chiusura-dell-utente.json
- 2026-01-15T10:04:00+01:00 | RIFIUTATA | da: 4-seconda-chiusura.json | motivi: note «0001» is already closed (✓D0001.1): to reopen it use «reopens».
- 2026-01-15T10:05:00+01:00 | RIFIUTATA | da: 5-chiusura-open.json | motivi: note «0001» is already closed (✓D0001.1): to reopen it use «reopens».
- 2026-01-15T10:06:00+01:00 | RIFIUTATA | da: 6-chiudere-un-fatto.json | motivi: note «0002» named in «done» does not exist in the notebook.
