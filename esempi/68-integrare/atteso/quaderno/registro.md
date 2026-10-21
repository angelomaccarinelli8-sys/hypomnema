# Registro degli ingressi

Ogni riga è un passaggio dallo sportello. Questo file si allunga soltanto.

- 2026-01-15T10:00:00+01:00 | ACCETTATA | nota 0001 | da: 1-todo-pozzo.json
- 2026-01-15T10:01:00+01:00 | ACCETTATA | nota 0002 | da: 2-todo-pompa.json
- 2026-01-15T10:02:00+01:00 | ACCETTATA | nota 0003 | da: 3-idea-gioco.json
- 2026-01-15T10:03:00+01:00 | ACCETTATA | nota 0001.1 | da: 4-integra-la-pompa-nel-pozzo.json
- 2026-01-15T10:04:00+01:00 | ACCETTATA | nota 0003.1 | da: 5-parole-nuove.json
- 2026-01-15T10:05:00+01:00 | RIFIUTATA | da: 6-senza-cosa-in-comune.json | motivi: notes «0001» and «0003» have no COSA label in common: only notes about the same thing can be integrated.
- 2026-01-15T10:06:00+01:00 | RIFIUTATA | da: 7-claude-aggiunge-alla-nota-dell-utente.json | motivi: note «0003» is written by «user»: only «user» can add words to it, so that the user's words and Claude's never mix.
- 2026-01-15T10:07:00+01:00 | RIFIUTATA | da: 8-con-il-tipo.json | motivi: «integrates» only adds text at the end of the note: «kind» is not allowed (to change kind, priority or reminder use «updates»).
