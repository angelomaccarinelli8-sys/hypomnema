# Registro degli ingressi

Ogni riga è un passaggio dallo sportello. Questo file si allunga soltanto.

- 2026-01-15T10:00:00+01:00 | ACCETTATA | nota 0001 | da: 1-promemoria.json
- 2026-01-15T10:02:00+01:00 | ACCETTATA | nota 0002 | da: 2-fatto.json
- 2026-01-15T10:04:00+01:00 | RIFIUTATA | da: 3-fatto-di-una-nota-qualsiasi.json | motivi: la nota «0002» indicata in «done» non è un promemoria (non ha «riprendere_il»): «done» segna come fatto solo un promemoria.
- 2026-01-15T10:05:00+01:00 | RIFIUTATA | da: 4-fatto-di-una-nota-che-non-c-e.json | motivi: la nota «0099» indicata in «done» non esiste nel quaderno.
