# Crea un taccuino sul server online (0.11.0, seconda parte), per esempio «prova» o quello di un tester.
# Uso:  powershell -ExecutionPolicy Bypass -File .\online\crea-taccuino-online.ps1 -Nome prova [-NellIndirizzo] [-Etichette <file>]
#
# La chiave nasce QUI, sul PC, solo in memoria. Al server arriva soltanto la sua impronta (SHA-256): sul server la
# chiave non c'è, e nemmeno l'amministratore può leggerla. La chiave non compare mai a schermo: alla fine va negli
# appunti, una volta sola, per incollarla nel connettore di claude.ai. Poi gli appunti si svuotano.
# -NellIndirizzo: negli appunti va l'indirizzo con la chiave dentro (https://.../<chiave>/mcp), per gli account
# che nel modulo del connettore non hanno «Request headers».
# -Etichette: la lista delle etichette (etichette.toml scritto dall'utente), controllata PRIMA di creare il taccuino e
# caricata subito dopo con carica-etichette.ps1.
param([Parameter(Mandatory = $true)][string]$Nome, [switch]$NellIndirizzo, [string]$Etichette)
. (Join-Path $PSScriptRoot "impostazioni.ps1")

if ($Etichette) {
    Write-Host "0/3 Controllo la lista delle etichette sul PC"
    py (Join-Path (Split-Path $PSScriptRoot -Parent) "programma.py") notebook-labels --labels $Etichette
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRORE: la lista delle etichette non va: correggila prima. Non ho creato niente." -ForegroundColor Red
        exit 1
    }
}

if ($Nome -cnotmatch '^[a-z0-9][a-z0-9-]{0,39}$') {
    Write-Host "ERRORE: il nome può avere solo lettere minuscole, cifre e - (per esempio prova)." -ForegroundColor Red
    exit 1
}

# 32 byte casuali dal generatore crittografico di Windows: 43 caratteri (lettere, cifre, - e _).
$byte = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($byte)
$chiave = [Convert]::ToBase64String($byte).TrimEnd('=').Replace('+', '-').Replace('/', '_')
$sha = [Security.Cryptography.SHA256]::Create()
$impronta = -join ($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($chiave)) | ForEach-Object { $_.ToString("x2") })

Write-Host "1/3 Il taccuino «$Nome» sul server (solo l'impronta della chiave)"
$risposta = SulServer "nuovo-taccuino.sh" @($Nome, $impronta)
if ($risposta -notmatch "creato in" -or $risposta -notmatch "(?m)^active") {
    Write-Host $risposta
    Write-Host "ERRORE: il taccuino non è stato creato. Manda a Claude le righe qui sopra." -ForegroundColor Red
    exit 1
}

Write-Host "2/3 La prova: il server apre il taccuino con la chiave nuova"
Start-Sleep -Seconds 3
$corpo = '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
try {
    $prova = Invoke-RestMethod -Method Post -Uri "https://$Dominio/mcp" -ContentType "application/json" `
        -Headers @{ "x-api-key" = $chiave } -Body $corpo -TimeoutSec 30
    $strumenti = $prova.result.tools.Count
} catch {
    $strumenti = 0
}
if ($strumenti -lt 1) {
    Write-Host "ERRORE: il taccuino è creato ma la prova non risponde. Manda a Claude questo messaggio." -ForegroundColor Red
    exit 1
}
Write-Host "   Risponde: $strumenti strumenti." -ForegroundColor Green
if ($Etichette) {
    & (Join-Path $PSScriptRoot "carica-etichette.ps1") -Nome $Nome -File $Etichette
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ATTENZIONE: il taccuino è creato ma le etichette no. La chiave arriva lo stesso negli appunti;" -ForegroundColor Yellow
        Write-Host "dopo, rilancia solo carica-etichette.ps1 -Nome $Nome -File <file>."
    }
}

Write-Host "3/3 La chiave negli appunti"
if ($NellIndirizzo) {
    Set-Clipboard -Value "https://$Dominio/$chiave/mcp"
    $cosa = "l'INDIRIZZO con la chiave dentro: incollalo in «URL del server MCP remoto». Non serve nient'altro."
} else {
    Set-Clipboard -Value $chiave
    $cosa = "la CHIAVE: indirizzo  https://$Dominio/mcp , poi in «Request headers» il nome  x-api-key  e come valore incolla la chiave."
}
Remove-Variable chiave, byte
Write-Host ""
Write-Host "Negli appunti c'è $cosa" -ForegroundColor Green
Write-Host "Incollala ADESSO nel modulo del connettore di claude.ai. Non viene mostrata e non è salvata da nessuna parte:"
Write-Host "se va persa, si rifà il taccuino con un altro nome."
Read-Host "Quando l'hai incollata e salvata, premi Invio per svuotare gli appunti"
Set-Clipboard -Value " "
Write-Host "Appunti svuotati. Se la cronologia degli appunti di Windows è accesa (tasti Windows+V), aprila e scegli «Cancella tutto»."
