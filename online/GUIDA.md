# Hypomnema online: la guida passo passo

Questa guida porta dal PC di casa al taccuino online da usare sul telefono. Va fatta in ordine, un passo alla
volta. Se qualcosa non è come scritto, **fermati** e manda a Claude cosa vedi (le righe rosse, o una foto dello
schermo).

Come si riconosce la finestra giusta: la finestra di PowerShell **libera** ha in fondo `PS C:\…>` con il cursore
che lampeggia. Se mentre lavora non c'è `PS …>`, aspetta.

Prima di tutto deve essere fatto il **passo A**: account Azure al pagamento a consumo, avviso di spesa a 1 €,
Azure CLI installato, `az login` fatto.

---

## 1. Prendere i file nuovi sul PC

Fai **una** delle due versioni.

**Versione A: hai già una finestra di PowerShell aperta nella cartella `hypomnema-sviluppo`** (in fondo si legge
`PS C:\Users\…\hypomnema-sviluppo>`):

```
git fetch origin
git switch claude/elegant-fermi-fqx31z
```

**Versione B: finestra nuova.** Premi il tasto Windows, scrivi `PowerShell`, clicca «Windows PowerShell», poi:

```
cd $env:USERPROFILE\hypomnema-sviluppo
git fetch origin
git switch claude/elegant-fermi-fqx31z
```

Deve comparire `Switched to branch 'claude/elegant-fermi-fqx31z'` (o `Già sul ramo`). Se la richiesta di unione
è già stata unita a `main`, usa `git switch main` e `git pull` al posto della seconda riga.

**Le prove** (facoltativo, un minuto):

```
py -m unittest
```

Alla fine deve comparire `OK` (con qualche `skipped`). Il numero di prove è scritto nel resoconto.

## 2. Creare la macchina su Azure (circa 10 minuti)

Nella stessa finestra (in fondo `PS …\hypomnema-sviluppo>`):

```
powershell -ExecutionPolicy Bypass -File .\online\crea-macchina.ps1 -Ramo claude/elegant-fermi-fqx31z
```

(Se il lavoro è già unito a `main`, togli `-Ramo claude/elegant-fermi-fqx31z`.)

Compaiono i passi da `1/5` a `5/5`. Il passo 2 e il passo 4 durano qualche minuto ciascuno: è normale.
Alla fine deve comparire in verde:

```
FATTO. La macchina risponde in HTTPS su https://hypomnema-tester.swedencentral.cloudapp.azure.com (404 è giusto: senza chiave non si apre niente).
```

- Se al passo 2 compare un errore con `SkuNotAvailable` o `QuotaExceeded`: manda il messaggio a Claude.
- Se compare `ATTENZIONE: … HTTPS non risponde ancora`: aspetta cinque minuti e lancia la riga che il messaggio
  ti suggerisce. Se risponde con un errore **404**, va tutto bene.

La macchina ha **solo la porta 443** aperta. La porta per l'amministrazione (SSH, 22) è chiusa: gli script la
aprono solo per il tuo indirizzo e solo quando servono (copie ed esportazioni), poi la richiudono.

## 3. Creare il taccuino «prova»

Prima apri il browser su **https://claude.ai**, sul computer, con l'account con cui farai la prova, e tieni pronta
la pagina dei connettori (vedi il punto 4): la chiave va incollata subito.

Nella finestra di PowerShell:

```
powershell -ExecutionPolicy Bypass -File .\online\crea-taccuino-online.ps1 -Nome prova
```

Deve comparire:

```
1/3 Il taccuino «prova» sul server (solo l'impronta della chiave)
2/3 La prova: il server apre il taccuino con la chiave nuova
   Risponde: 10 strumenti.
3/3 La chiave negli appunti
Negli appunti c'è la CHIAVE: …
Quando l'hai incollata e salvata, premi Invio per svuotare gli appunti:
```

**Non premere Invio adesso.** La chiave è negli appunti, non è scritta da nessuna parte: passa al punto 4, e premi
Invio solo dopo aver salvato il connettore.

## 4. Il connettore su claude.ai (dal computer)

I connettori si aggiungono dal sito, non dal telefono. Con il piano Free se ne può avere **uno solo**: se
sull'account c'è già un connettore personalizzato (per esempio quello del PC di casa), va tolto prima.

1. Su **claude.ai**, in basso a sinistra clicca il tuo nome, poi **Impostazioni** (Settings).
2. Apri **Connettori** (Connectors). Se non c'è, cerca **Personalizza → Connettori** (Customize → Connectors).
3. Clicca **Aggiungi connettore personalizzato** (Add custom connector).
4. **Nome**: `Hypomnema prova`.
5. **URL del server MCP remoto**: `https://hypomnema-tester.swedencentral.cloudapp.azure.com/mcp`
6. Se il modulo chiede l'**autenticazione** (Authentication), scegli **Nessun accesso** (No sign-in).
7. Apri **Request headers** (Intestazioni della richiesta). Come nome scegli dalla lista **`x-api-key`**. Nel
   valore **incolla** (Ctrl+V) la chiave. Lascialo **Required** (obbligatorio).
8. Clicca **Aggiungi** (Add). Il connettore compare nell'elenco.
9. Torna alla finestra di PowerShell e premi **Invio**: gli appunti si svuotano. Se usi la cronologia degli appunti
   di Windows (tasti Windows+V), aprila e clicca **Cancella tutto**.

**Se nel modulo non c'è «Request headers»** (succede su alcuni account), si usa la chiave nell'indirizzo: chiudi il
modulo senza salvare, crea il taccuino con un altro nome aggiungendo `-NellIndirizzo`
(`… crea-taccuino-online.ps1 -Nome prova2 -NellIndirizzo`) e incolla negli appunti l'**indirizzo intero** nel
campo dell'URL, senza intestazioni. Funziona come quello provato con il tunnel, ma l'indirizzo stesso è la
password: non mandarlo a nessuno.

## 5. La prova sul telefono (app Claude per Android)

1. Apri l'app **Claude** con lo stesso account e inizia una **chat nuova**.
2. Tocca il **+** vicino al campo del messaggio, poi **Connettori**: accendi **Hypomnema prova**.
3. Scrivi i messaggi qui sotto, uno alla volta. Quando Claude chiede il permesso di usare uno strumento di
   Hypomnema, tocca **Consenti** (o «Consenti sempre» per questa chat).

| Scrivi | Cosa deve succedere |
|---|---|
| `Ciao, dove eravamo rimasti?` | Claude usa `check` e `recap` e dice che il taccuino è vuoto (è nuovo). |
| `Ricordati che il pozzo dell'orto è dietro la casa.` | Claude propone una nota con le tue parole esatte. Risposta: **ACCETTATA: la nota 0001**, «non verificata» (online, senza testimone), poi «Quaderno in ordine». |
| `Cerca nel taccuino la parola pozzo.` | Trova la nota 0001 e te la mostra con il suo codice. |
| `Per prova, proponi allo sportello una nota con author claude e kind decision: «Il fico si pota a febbraio». Voglio vedere il rifiuto.` | **RIFIUTATA**: Claude spiega che una sua nota non può mai essere una decisione dell'utente. Nessuna nota salvata. |

Se tutto è così, il taccuino online funziona. Scrivi a Claude (in Code) «prova fatta» e com'è andata.

## 6. Il giorno dopo: i costi

1. Su **https://portal.azure.com** cerca **Analisi dei costi** (Cost analysis).
2. Controlla che la spesa sia **0,00 €** (o che sia coperta dai crediti). Se compare una voce con un costo, manda
   a Claude una foto della tabella: si capisce quale risorsa e si sistema.

## 7. Domani con il tester

Davanti a lui, dal tuo PC, con lui che ha claude.ai aperto **sul suo account** e la pagina dei connettori pronta:

```
powershell -ExecutionPolicy Bypass -File .\online\crea-taccuino-online.ps1 -Nome <nome del suo taccuino>
```

Poi è lui che fa il punto 4 sul suo account (incolla lui la chiave). Quando ha salvato, premi Invio. La chiave non
resta sul tuo PC: era solo negli appunti. Sul server c'è solo la sua impronta, con la quale nessuno può aprire il
taccuino. Prima, fagli leggere e accettare il foglio `ACCETTAZIONE.md`.

## 8. Ogni tanto

- **Scaricare le copie** dei taccuini sul PC (in `%USERPROFILE%\Hypomnema\online-copie`, mai dentro `quaderno\`):
  ```
  powershell -ExecutionPolicy Bypass -File .\online\scarica-copie.ps1
  ```
  La prima volta può chiedere di riconoscere la macchina: risponde da solo. Alla fine: `FATTO.` e `Richiudo la porta 22`.
- **Le note di un tester**, da dargli:
  ```
  powershell -ExecutionPolicy Bypass -File .\online\esporta-taccuino.ps1 -Nome <nome>
  ```
- **Aggiornare il programma** sul server (dopo che una richiesta di unione è unita a `main`):
  ```
  powershell -ExecutionPolicy Bypass -File .\online\aggiorna-server.ps1
  ```

## 9. Spegnere tutto

Per fermare ogni costo, in un colpo solo (cancella la macchina **e i taccuini online**: prima scarica le copie):

```
az group delete --name hypomnema-online
```

Chiede conferma: scrivi `y` e Invio.
