# Scarica sul PC le copie notturne dei taccuini online (0.11.0, seconda parte), in %USERPROFILE%\Hypomnema\online-copie.
# Uso:  powershell -ExecutionPolicy Bypass -File .\online\scarica-copie.ps1
# Apre la porta 22 (SSH) SOLO per l'indirizzo IP di questo PC, scarica, e la richiude subito, anche se qualcosa va storto.
. (Join-Path $PSScriptRoot "impostazioni.ps1")
. (Join-Path $PSScriptRoot "porta-ssh.ps1")

New-Item -ItemType Directory -Force -Path $Copie | Out-Null
ConSsh {
    scp -r -o StrictHostKeyChecking=accept-new "${Amministratore}@${Dominio}:/var/backups/hypomnema/*" "$Copie"
    Controlla "lo scaricamento delle copie"
}
Write-Host "FATTO. Le copie sono in $Copie" -ForegroundColor Green
