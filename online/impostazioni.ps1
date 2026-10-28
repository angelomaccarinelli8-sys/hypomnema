# Le impostazioni comuni degli script del server online di Hypomnema (0.11.0, seconda parte).
# Gli altri script le leggono da qui: se cambi un nome, cambialo solo qui.
$Gruppo = "hypomnema-online"          # il gruppo di risorse di Azure che contiene tutto
$Macchina = "hypomnema-tester"        # il nome della macchina
$Regione = "swedencentral"            # Sweden Central (Svezia): l'unica regione europea con la B2ats v2 per questa sottoscrizione
$NomeDns = "hypomnema-tester"         # il nome su internet: hypomnema-tester.swedencentral.cloudapp.azure.com
$Dominio = "$NomeDns.$Regione.cloudapp.azure.com"
$Autore = "Angelo"                   # chi gestisce il servizio: la scheda per Claude dice di chiedere a lui i dettagli interni
$Amministratore = "amministratore"    # l'utente di amministrazione della macchina (accesso solo con la chiave SSH)
$Copie = Join-Path $env:USERPROFILE "Hypomnema\online-copie"   # mai dentro quaderno\

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Controlla([string]$Cosa) {
    # Gli errori di az non fermano PowerShell da soli: si controlla il codice di uscita.
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERRORE durante: $Cosa. Fermati e manda a Claude le righe rosse qui sopra." -ForegroundColor Red
        exit 1
    }
}

function SulServer([string]$Script, [string[]]$Parametri) {
    # Lancia uno script sulla macchina con «az vm run-command»: passa da Azure, nessuna porta aperta.
    $file = Join-Path $PSScriptRoot $Script
    $risposta = az vm run-command invoke --resource-group $Gruppo --name $Macchina --command-id RunShellScript `
        --scripts "@$file" --parameters @Parametri --query "value[0].message" --output tsv
    Controlla "lo script $Script sul server"
    return ($risposta -join "`n")
}

function Firewall {
    return (az network nsg list --resource-group $Gruppo --query "[0].name" --output tsv)
}
