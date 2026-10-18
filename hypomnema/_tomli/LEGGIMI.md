# Copia di tomli 2.0.1

Questa cartella è una copia **non modificata** di [tomli](https://github.com/hukkin/tomli) 2.0.1,
di Taneli Hukkinen, con licenza MIT (vedi `LICENSE`). È il codice da cui è nato `tomllib`, il
lettore di file TOML della libreria standard di Python dal 3.11.

Hypomnema la usa **solo quando `tomllib` manca**, cioè con Python 3.10 (per esempio sulla macchina
Linux della chat di Claude collegata al computer): così non c'è niente da installare. Dal 3.11 in
su si usa sempre `tomllib`.

Da dove viene: il pacchetto sorgente `tomli-2.0.1.tar.gz` di PyPI
(SHA-256 `de526c12914f0c550d15924c62d72abc48d6fe7364aa87328337a31007fe8a4f`), cartella `src/tomli`.
