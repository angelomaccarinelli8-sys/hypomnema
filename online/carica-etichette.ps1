# Carica la lista delle etichette di un taccuino online (0.11.0, seconda parte), per esempio quella nata dal
# questionario del tester. Il file etichette.toml lo scrive l'utente (o lo detta il tester), mai Claude da solo.
# Uso:  powershell -ExecutionPolicy Bypass -File .\online\carica-etichette.ps1 -Nome <taccuino> -File <etichette.toml> [-Sostituisci]
#
# 1. controlla la lista QUI, sul PC, con le stesse regole dello sportello: se è scritta male si ferma e non carica;
# 2. la manda al server con «az vm run-command» (nessuna porta aperta), che la ricontrolla e la scrive;
# 3. mai sopra una lista che ha già delle etichette senza -Sostituisci e la tua conferma; la lista di prima resta
#    accanto sul server, con la data nel nome.
param([Parameter(Mandatory = $true)][string]$Nome, [Parameter(Mandatory = $true)][string]$File, [switch]$Sostituisci)
. (Join-Path $PSScriptRoot "impostazioni.ps1")

if (-not (Test-Path -LiteralPath $File -PathType Leaf)) {
    Write-Host "ERRORE: non trovo il file $File" -ForegroundColor Red
    exit 1
}
if ((Get-Item -LiteralPath $File).Length -gt 32KB) {
    Write-Host "ERRORE: il file è troppo grande per una lista di etichette (più di 32 KB)." -ForegroundColor Red
    exit 1
}

Write-Host "1/2 Controllo la lista sul PC"
$programma = Join-Path (Split-Path $PSScriptRoot -Parent) "programma.py"
py $programma notebook-labels --labels $File
if ($LASTEXITCODE -ne 0) {
    Write-Host "La lista non è stata caricata: correggi il file e rilancia." -ForegroundColor Red
    exit 1
}

$conferma = "no"
if ($Sostituisci) {
    Write-Host "Hai chiesto di SOSTITUIRE la lista del taccuino «$Nome», se ne ha già una con dentro qualcosa." -ForegroundColor Yellow
    Write-Host "Quella di adesso non si cancella: resta sul server accanto alla nuova, con la data nel nome."
    if ((Read-Host "Per confermare scrivi SI e premi Invio") -cne "SI") {
        Write-Host "Non ho caricato niente."
        exit 1
    }
    $conferma = "sostituisci"
}

Write-Host "2/2 Carico la lista nel taccuino «$Nome»"
$base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $File)))
$risposta = SulServer "carica-etichette.sh" @($Nome, $base64, $conferma)
Write-Host $risposta
if ($risposta -notmatch "Etichette caricate") {
    Write-Host "ERRORE: la lista non è stata caricata (il motivo è qui sopra)." -ForegroundColor Red
    exit 1
}
Write-Host "FATTO. Lo sportello usa la lista nuova dalla prossima proposta: non serve riavviare niente." -ForegroundColor Green
