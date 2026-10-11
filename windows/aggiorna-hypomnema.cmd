@echo off
rem Aggiorna la copia in uso di Hypomnema alla versione principale (main) gia' unita su GitHub.
rem Tocca solo i file del programma: il quaderno e la configurazione in uso stanno fuori
rem da questa cartella (in %USERPROFILE%\Hypomnema) e non vengono mai toccati.
title Aggiorna Hypomnema
cd /d "%~dp0.."
set RAMO=
for /f "delims=" %%r in ('git rev-parse --abbrev-ref HEAD') do set RAMO=%%r
if not "%RAMO%"=="main" (
    echo Questa copia non e' sulla versione principale ^(main^) ma su "%RAMO%".
    echo La copia in uso deve stare su main: non aggiorno niente.
    goto fine
)
git pull --ff-only origin main
if errorlevel 1 (
    echo.
    echo Aggiornamento NON riuscito: leggi il messaggio qui sopra. Non ho cambiato niente.
    goto fine
)
echo.
echo Controllo che la nuova versione funzioni sul tuo computer...
py -m unittest -q
:fine
echo.
pause
