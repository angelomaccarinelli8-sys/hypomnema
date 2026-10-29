# La porta 22 aperta solo per questo PC e solo per il tempo di un lavoro (0.11.0, seconda parte).
# La usano scarica-copie.ps1 ed esporta-taccuino.ps1.
function ConSsh([scriptblock]$Lavoro) {
    $mio = (Invoke-RestMethod -Uri "https://api.ipify.org" -TimeoutSec 20).Trim()
    if ($mio -notmatch '^\d{1,3}(\.\d{1,3}){3}$') {
        Write-Host "ERRORE: non trovo l'indirizzo IP di questo PC." -ForegroundColor Red
        exit 1
    }
    $nsg = Firewall
    Write-Host "Apro la porta 22 solo per $mio"
    az network nsg rule create --resource-group $Gruppo --nsg-name $nsg --name ssh-temporanea --priority 110 `
        --direction Inbound --access Allow --protocol Tcp --source-address-prefixes "$mio/32" `
        --destination-port-ranges 22 --output none
    Controlla "l'apertura temporanea della porta 22"
    try {
        Start-Sleep -Seconds 15
        & $Lavoro
    } finally {
        Write-Host "Richiudo la porta 22"
        az network nsg rule delete --resource-group $Gruppo --nsg-name $nsg --name ssh-temporanea --output none
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ATTENZIONE: la porta 22 NON si è richiusa. Rilancia questo script o scrivi a Claude." -ForegroundColor Red
        }
    }
}
