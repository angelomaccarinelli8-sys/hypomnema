# Aggiorna il programma sul server online e lo riavvia (0.11.0, seconda parte). I taccuini non si toccano.
# Uso:  powershell -ExecutionPolicy Bypass -File .\online\aggiorna-server.ps1 [-Ramo main]
param([string]$Ramo = "main")
. (Join-Path $PSScriptRoot "impostazioni.ps1")

$risposta = SulServer "aggiorna.sh" @($Ramo)
Write-Host $risposta
if ($risposta -notmatch "Programma aggiornato") {
    Write-Host "ERRORE: l'aggiornamento non è riuscito." -ForegroundColor Red
    exit 1
}
Write-Host "FATTO." -ForegroundColor Green
