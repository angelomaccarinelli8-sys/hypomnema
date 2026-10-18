# Registro degli ingressi

Ogni riga è un passaggio dallo sportello. Questo file si allunga soltanto.

- 2025-11-27T18:00:00+01:00 | ACCETTATA | nota 0001 | da: 0001.json
- 2025-11-28T18:00:00+01:00 | ACCETTATA | nota 0002 | da: 0002.json
- 2025-11-29T18:00:00+01:00 | ACCETTATA | nota 0003 | da: 0003.json
- 2025-11-30T18:00:00+01:00 | ACCETTATA | nota 0004 | da: 0004.json
- 2025-11-30T18:00:00+01:00 | ACCETTATA | nota 0005 | da: 0005.json
- 2025-12-27T18:00:00+01:00 | ACCETTATA | nota 0006 | da: 0006.json
- 2025-11-30T18:00:00+01:00 | ACCETTATA | nota 0007 | da: 0007.json
- 2026-01-15T10:02:00+01:00 | ACCETTATA | nota 0006.1 | da: 1a-priorita.json
- 2026-01-15T10:03:00+01:00 | ACCETTATA | nota 0004.1 | da: 1b-natura.json
- 2026-01-15T10:04:00+01:00 | ACCETTATA | nota 0004.2 | da: 1c-correzione.json
- 2026-01-15T10:06:00+01:00 | RIFIUTATA | da: 1d-claude-corregge-l-utente.json | motivi: the text of note «0007» is the user's words: only the user can correct it. Claude can suggest the correction to the user, or save its own idea note.
- 2026-01-15T10:07:00+01:00 | RIFIUTATA | da: 1e-versione-vecchia.json | motivi: 0004.1 is not the last version of 0004: the last is T0004.2. Changes are made only to the last version (write «0004»).
- 2026-01-15T10:08:00+01:00 | ACCETTATA | nota 0006.2 | da: 1f-chiusura-di-claude.json
- 2026-01-15T10:09:00+01:00 | RIFIUTATA | da: 1g-chiusura-doppia.json | motivi: note «0006» is already closed (✓F0006.2): to reopen it use «reopens».
- 2026-01-15T10:10:00+01:00 | RIFIUTATA | da: 1h-decisione-di-claude.json | motivi: a decision must be stated by the user: it cannot be «inferred». / only the user can make a note a decision: Claude can suggest it to the user.
- 2026-01-15T10:11:00+01:00 | ACCETTATA | nota 0008 | da: 1i-nota-nuova.json
- 2026-01-15T10:12:00+01:00 | RIFIUTATA | da: 1l-niente-cambia.json | motivi: «updates» on note «0004» changes nothing: write in «kind», «priority» or «remind» the new value.
- 2026-01-15T10:13:00+01:00 | RIFIUTATA | da: 1m-due-cambiamenti.json | motivi: a proposal can make only one change: use only one of «corrects», «updates», «done» and «reopens».
