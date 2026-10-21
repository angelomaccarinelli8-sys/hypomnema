# Registro degli ingressi

Ogni riga è un passaggio dallo sportello. Questo file si allunga soltanto.

- 2026-01-15T10:00:00+01:00 | ACCETTATA | nota 0001 | da: 1-decisione.json
- 2026-01-15T10:01:00+01:00 | ACCETTATA | nota 0002 | da: 2-idea-di-claude.json
- 2026-01-15T10:02:00+01:00 | RIFIUTATA | da: 3-claude-annulla-la-decisione.json | motivi: note «0001» is the user's: only the user can cancel it. Claude can suggest it.
- 2026-01-15T10:03:00+01:00 | ACCETTATA | nota 0001.1 | da: 4-annullata-dall-utente.json
- 2026-01-15T10:04:00+01:00 | ACCETTATA | nota 0002.1 | da: 5-claude-annulla-la-sua-idea.json
- 2026-01-15T10:07:00+01:00 | RIFIUTATA | da: 6-chiudere-un-annullata.json | motivi: note «0001» is cancelled (CD0001.1): to make it count again use «reopens».
- 2026-01-15T10:08:00+01:00 | ACCETTATA | nota 0001.2 | da: 7-vale-di-nuovo.json
