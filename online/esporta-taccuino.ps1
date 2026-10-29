# Scarica le note di UN taccuino online, per darle al suo tester (0.11.0, seconda parte).
# Uso:  powershell -ExecutionPolicy Bypass -File .\online\esporta-taccuino.ps1 -Nome <nome del taccuino>
# Il file arriva in %USERPROFILE%\Hypomnema\online-copie\esportazioni (un archivio .tar.gz: Windows lo apre con
# tasto destro, «Estrai tutto», oppure con  tar -xzf <file>).
param([Parameter(Mandatory = $true)][string]$Nome)
. (Join-Path $PSScriptRoot "impostazioni.ps1")
. (Join-Path $PSScriptRoot "porta-ssh.ps1")

$risposta = SulServer "esporta.sh" @($Nome)
if ($risposta -match "ESPORTATO: (\S+)") {
    $remoto = $Matches[1]
} else {
    Write-Host $risposta
    Write-Host "ERRORE: l'esportazione non è riuscita." -ForegroundColor Red
    exit 1
}
$cartella = Join-Path $Copie "esportazioni"
New-Item -ItemType Directory -Force -Path $cartella | Out-Null
ConSsh {
    scp -o StrictHostKeyChecking=accept-new "${Amministratore}@${Dominio}:$remoto" "$cartella"
    Controlla "lo scaricamento dell'esportazione"
}
Write-Host "FATTO. Il file è in $cartella" -ForegroundColor Green
