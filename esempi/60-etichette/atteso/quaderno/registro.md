# Registro degli ingressi

Ogni riga è un passaggio dallo sportello. Questo file si allunga soltanto.

- 2026-01-15T10:00:00+01:00 | ACCETTATA | nota 0001 | da: 1-todo-con-etichette.json
- 2026-01-15T10:01:00+01:00 | ACCETTATA | nota 0002 | da: 2-fatto-senza-etichette.json
- 2026-01-15T10:02:00+01:00 | RIFIUTATA | da: 3-etichetta-non-in-lista.json | motivi: the label «giardino» is not in the list of «about» labels: the allowed ones are orto, bilancio, gioco. Only the user adds labels, in the file etichette.toml.
- 2026-01-15T10:03:00+01:00 | RIFIUTATA | da: 4-tre-etichette-chi.json | motivi: a note can have at most 2 «who» labels: «Anna, Marco, Code» has 3.
- 2026-01-15T10:04:00+01:00 | RIFIUTATA | da: 5-etichetta-ripetuta.json | motivi: the label «orto» is repeated in «about»: write it once.
- 2026-01-15T10:05:00+01:00 | ACCETTATA | nota 0002.1 | da: 6-claude-etichetta-nota-vecchia.json
- 2026-01-15T10:06:00+01:00 | RIFIUTATA | da: 7-claude-cambia-di-nuovo.json | motivi: only the user can change the labels of one of the user's notes once they are set (note «0002» has them already): Claude can suggest the change to the user.
- 2026-01-15T10:07:00+01:00 | ACCETTATA | nota 0003 | da: 8-nomi-italiani-dalla-chat.json
- 2026-01-15T10:08:00+01:00 | RIFIUTATA | da: 9-maiuscola-dalla-chat.json | motivi: the label «Bilancio» is not in the list of «about» labels: the allowed ones are orto, bilancio, gioco. Only the user adds labels, in the file etichette.toml.
