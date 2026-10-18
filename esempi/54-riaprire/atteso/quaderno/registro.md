# Registro degli ingressi

Ogni riga è un passaggio dallo sportello. Questo file si allunga soltanto.

- 2025-11-27T18:00:00+01:00 | ACCETTATA | nota 0001 | da: 0001.json
- 2025-11-28T18:00:00+01:00 | ACCETTATA | nota 0002 | da: 0002.json
- 2025-11-29T18:00:00+01:00 | ACCETTATA | nota 0003 | da: 0003.json
- 2025-11-30T18:00:00+01:00 | ACCETTATA | nota 0004 | da: 0004.json
- 2025-11-30T18:00:00+01:00 | ACCETTATA | nota 0005 | da: 0005.json
- 2025-12-27T18:00:00+01:00 | ACCETTATA | nota 0006 | da: 0006.json
- 2025-11-30T18:00:00+01:00 | ACCETTATA | nota 0007 | da: 0007.json
- 2026-01-15T10:00:00+01:00 | ACCETTATA | nota 0006.1 | da: 1-chiusura-del-basilico.json
- 2026-01-15T10:01:00+01:00 | ACCETTATA | nota 0004.1 | da: 2-chiusura-della-compostiera.json
- 2026-01-15T10:05:00+01:00 | ACCETTATA | nota 0006.2 | da: 3-riapre-il-basilico.json
- 2026-01-15T10:06:00+01:00 | RIFIUTATA | da: 4-riapre-una-nota-aperta.json | motivi: note «0006» is not closed (T0006.2): only a closed note can be reopened.
- 2026-01-15T10:07:00+01:00 | RIFIUTATA | da: 5-claude-riapre-la-compostiera.json | motivi: only the user can reopen an open note («0004»): Claude can suggest it.
- 2026-01-15T10:08:00+01:00 | ACCETTATA | nota 0004.2 | da: 6-riapre-la-compostiera.json
