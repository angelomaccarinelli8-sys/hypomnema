# Registro degli ingressi

Ogni riga è un passaggio dallo sportello. Questo file si allunga soltanto.

- 2025-11-27T18:00:00+01:00 | ACCETTATA | nota 0001 | da: 0001.json
- 2025-11-28T18:00:00+01:00 | ACCETTATA | nota 0002 | da: 0002.json
- 2025-11-29T18:00:00+01:00 | ACCETTATA | nota 0003 | da: 0003.json
- 2025-11-30T18:00:00+01:00 | ACCETTATA | nota 0004 | da: 0004.json
- 2025-11-30T18:00:00+01:00 | ACCETTATA | nota 0005 | da: 0005.json
- 2025-12-27T18:00:00+01:00 | ACCETTATA | nota 0006 | da: 0006.json
- 2025-11-30T18:00:00+01:00 | ACCETTATA | nota 0007 | da: 0007.json
- 2026-01-15T10:01:00+01:00 | RIFIUTATA | da: 1-lettera-nel-rimando.json | motivi: write only the number in «corrects»: «0006», not «T0006» (the letter of the code is only shown, it is not part of the number).
- 2026-01-15T10:02:00+01:00 | RIFIUTATA | da: 2-segno-nel-rimando.json | motivi: write only the number in «reopens»: «0001.2», not «✓F0001.2» (the letter of the code is only shown, it is not part of the number).
- 2026-01-15T10:03:00+01:00 | RIFIUTATA | da: 3-numero-vecchio.json | motivi: 0001.1 (note 0002) is not the last version of 0001: the last is xF0001.2. Changes are made only to the last version (write «0001»).
- 2026-01-15T10:04:00+01:00 | ACCETTATA | nota 0001.3 | da: 4-chiusura-di-una-chiusura-vecchia.json
