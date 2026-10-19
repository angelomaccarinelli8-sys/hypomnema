# Copia della tabella dei fusi di Windows (Unicode CLDR)

`windowsZones.xml` è una copia **non modificata** del file `common/supplemental/windowsZones.xml` di
[Unicode CLDR](https://github.com/unicode-org/cldr), versione `release-46`, con la licenza Unicode
(vedi `LICENSE`, Unicode License v3).

È la tabella ufficiale che collega i nomi dei fusi di Windows (per esempio «W. Europe Standard Time»)
ai nomi della tabella dei fusi orari (per esempio `Europe/Rome`), anche per regione (`IT` → `Europe/Rome`,
mentre senza regione «W. Europe Standard Time» vale `Europe/Berlin`).

Hypomnema la usa dalla 0.7.0 su Windows, per scrivere nel file `fuso-del-sistema.jsonl` del quaderno il
nome del fuso del sistema operativo dell'utente (vedi `hypomnema/fuso_del_sistema.py`). Si legge con
`xml.etree.ElementTree` della libreria standard: niente da installare, niente internet.

Da dove viene: https://raw.githubusercontent.com/unicode-org/cldr/release-46/common/supplemental/windowsZones.xml
(SHA-256 `39714d7a5a276508aeca2289a490dddb8424dea0063f3f5fbc8bd8520dcbfcba`).
Per aggiornarla: scaricare lo stesso file da una versione più recente di CLDR, senza modificarlo, e
cambiare qui la versione e l'impronta.
