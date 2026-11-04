@echo off
title Discord AI Bot
color 0A

set "OLLAMA_PID="

echo [1/3] Starting Ollama...

curl.exe -s http://localhost:11434/api/tags >nul 2>&1

if errorlevel 1 (
    for /f %%P in ('powershell.exe -NoProfile -Command "$p=Start-Process -FilePath (Get-Command ollama.exe).Source -ArgumentList serve -PassThru -WindowStyle Hidden; $p.Id"') do set "OLLAMA_PID=%%P"
)

echo [2/3] Waiting for Ollama API...

set /a attempts=0

:WAIT
curl.exe -s http://localhost:11434/api/tags >nul 2>&1
if not errorlevel 1 goto READY

set /a attempts+=1
if %attempts% GEQ 30 (
    echo ERROR: Ollama failed to start.
    goto CLEANUP
)

timeout /t 2 /nobreak >nul
goto WAIT

:READY
echo Ollama is running!
echo [3/3] Starting Discord Bot...

python Main.py

:CLEANUP
if defined OLLAMA_PID (
    taskkill /PID %OLLAMA_PID% /T /F >nul 2>&1
)

exit