# Avvia Hypomnema: apre Claude Code con il testimone acceso e la skill disponibile,
# collegati al quaderno in uso. Si lancia con un doppio clic su Hypomnema.cmd.
#
# Cosa fa, nell'ordine:
#  1. controlla che ci siano Python (comando py) e Claude Code (comando claude);
#  2. la prima volta crea la cartella dei dati e ci copia la configurazione in uso
#     (hypomnema-uso.toml); se c'e' gia', non la tocca;
#  3. mostra lo stato del testimone (py -m hypomnema stato);
#  4. avvia Claude Code nella cartella del programma, con il plugin di Hypomnema (skill e
#     testimone) e le regole che vietano a Claude di modificare quaderno e configurazione.
# Tutto vale solo per questa finestra: fuori dall'avviabile Hypomnema resta spento.
# Non cancella niente e non tocca altre cartelle.

param(
    # Cartella dei dati: configurazione in uso e quaderno. Di base fuori da OneDrive,
    # perche' i dati restino sul computer.
    [string]$CartellaDati = (Join-Path $env:USERPROFILE 'Hypomnema'),
    # Solo per le prove: il comando da lanciare al posto di claude, con i suoi primi argomenti.
    [string[]]$Claude = @('claude'),
    # Solo per le prove: argomenti in più per Claude Code.
    [string[]]$ArgomentiClaude = @()
)

$ErrorActionPreference = 'Stop'

function Ferma([string]$Messaggio) {
    Write-Host ''
    Write-Host "ERRORE: $Messaggio" -ForegroundColor Red
    if (-not ([Environment]::GetCommandLineArgs() -contains '-NonInteractive')) {
        Read-Host 'Premi Invio per chiudere' | Out-Null
    }
    exit 1
}

$Programma = Split-Path -Parent $PSScriptRoot
$Modello = Join-Path $PSScriptRoot 'hypomnema-uso.toml'
$Configurazione = Join-Path $CartellaDati 'hypomnema.toml'

if (-not (Get-Command 'py' -ErrorAction SilentlyContinue)) {
    Ferma 'non trovo il comando py: installa Python 3.12 o più recente da python.org.'
}
if (-not (Get-Command $Claude[0] -ErrorAction SilentlyContinue)) {
    Ferma 'non trovo Claude Code (comando claude): installalo seguendo le istruzioni sul sito di Claude.'
}

if (-not (Test-Path -LiteralPath $Configurazione)) {
    New-Item -ItemType Directory -Path $CartellaDati -Force | Out-Null
    Copy-Item -LiteralPath $Modello -Destination $Configurazione
    Write-Host "Prima volta: ho creato la configurazione in uso $Configurazione"
}

$env:HYPOMNEMA_CONFIG = $Configurazione
Set-Location -LiteralPath $Programma

& py -m hypomnema stato
if ($LASTEXITCODE -ne 0) {
    Ferma "la configurazione in uso non va bene (vedi sopra). Il file è $Configurazione"
}

$Impostazioni = (& py -m hypomnema impostazioni-claude) -join ''
if ($LASTEXITCODE -ne 0) {
    Ferma $Impostazioni
}
# Windows PowerShell 5.1 toglie le virgolette dentro gli argomenti passati ai programmi:
# vanno protette con \ perché Claude Code riceva il testo JSON intatto.
if ($PSVersionTable.PSVersion -lt [version]'7.3' -or $PSNativeCommandArgumentPassing -eq 'Legacy') {
    $Impostazioni = $Impostazioni -replace '"', '\"'
}

Write-Host ''
Write-Host 'Avvio Claude Code con Hypomnema: testimone e skill sono attivi solo in questa finestra.'
$Comando = $Claude[0]
$PrimiArgomenti = @($Claude | Select-Object -Skip 1)
& $Comando @PrimiArgomenti --plugin-dir $Programma --settings $Impostazioni @ArgomentiClaude
exit $LASTEXITCODE
