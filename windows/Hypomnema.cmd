@echo off
rem Avviabile di Hypomnema: doppio clic per aprire Claude Code con il testimone acceso
rem e la skill, collegati al quaderno in uso. Fuori da qui Hypomnema resta spento.
rem Lancia avvia-hypomnema.ps1 con PowerShell. "-ExecutionPolicy Bypass" vale solo per
rem questa esecuzione: non cambia le impostazioni di sicurezza del computer.
title Hypomnema
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0avvia-hypomnema.ps1"
