# Crea la macchina online di Hypomnema su Azure e la prepara (0.11.0, seconda parte). Una volta sola.
# Uso:  powershell -ExecutionPolicy Bypass -File .\online\crea-macchina.ps1 [-Ramo main]
# Crea solo risorse dei servizi gratuiti dei 12 mesi: macchina B2ats v2, disco Premium SSD da 64 GB (P6),
# indirizzo IP pubblico con il nome DNS gratuito di Azure, rete e firewall. Nel firewall è aperta SOLO la 443.
param([string]$Ramo = "main")
. (Join-Path $PSScriptRoot "impostazioni.ps1")

Write-Host "1/5 Il gruppo di risorse $Gruppo in $Regione"
az group create --name $Gruppo --location $Regione --output none
Controlla "la creazione del gruppo"

Write-Host "2/5 La macchina $Macchina (ci vogliono alcuni minuti)"
az vm create --resource-group $Gruppo --name $Macchina --location $Regione `
    --image "Canonical:ubuntu-24_04-lts:server:latest" --size Standard_B2ats_v2 `
    --storage-sku Premium_LRS --os-disk-size-gb 64 `
    --public-ip-sku Standard --public-ip-address-allocation static --public-ip-address-dns-name $NomeDns `
    --nsg-rule NONE --admin-username $Amministratore --generate-ssh-keys --output none
Controlla "la creazione della macchina"

Write-Host "3/5 Il firewall: aperta solo la porta 443 (HTTPS)"
az network nsg rule create --resource-group $Gruppo --nsg-name (Firewall) --name https --priority 100 `
    --direction Inbound --access Allow --protocol Tcp --destination-port-ranges 443 --output none
Controlla "l'apertura della porta 443"

Write-Host "4/5 La preparazione della macchina: programmi, Caddy, Hypomnema (ci vogliono alcuni minuti)"
$risposta = SulServer "installa.sh" @($Dominio, $Ramo, $Amministratore, $Autore)
if ($risposta -notmatch "PRONTO") {
    Write-Host $risposta
    Write-Host "ERRORE: la preparazione non è finita. Manda a Claude le righe qui sopra." -ForegroundColor Red
    exit 1
}

Write-Host "5/5 La prova di HTTPS (il primo certificato può chiedere un minuto)"
for ($giro = 1; $giro -le 12; $giro++) {
    try {
        Invoke-WebRequest -Uri "https://$Dominio/" -UseBasicParsing -TimeoutSec 20 | Out-Null
    } catch {
        if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 404) {
            Write-Host ""
            Write-Host "FATTO. La macchina risponde in HTTPS su https://$Dominio (404 è giusto: senza chiave non si apre niente)." -ForegroundColor Green
            Write-Host "Prossimo passo: crea il taccuino «prova» con crea-taccuino-online.ps1."
            exit 0
        }
    }
    Start-Sleep -Seconds 10
}
Write-Host "ATTENZIONE: la macchina c'è ma HTTPS non risponde ancora. Riprova tra cinque minuti con:" -ForegroundColor Yellow
Write-Host "  Invoke-WebRequest -Uri https://$Dominio/ -UseBasicParsing"
Write-Host "Se dà «404 Non trovato», va bene. Altrimenti manda a Claude il messaggio."
