```bat
@echo off
setlocal EnableDelayedExpansion

title Discord AI Bot
title Made By @TooWoke
color 0A

set "OLLAMA_URL=http://localhost:11434"
set "OLLAMA_PID="
set "EXIT_CODE=0"

echo Starting Discord AI Bot...
echo.

where ollama.exe >nul 2>&1 || (
    echo [ERROR] Ollama not found.
    goto ERROR
)

where python.exe >nul 2>&1 || (
    echo [ERROR] Python not found.
    goto ERROR
)

if not exist "Main.py" (
    echo [ERROR] Main.py not found.
    goto ERROR
)

echo Checking Ollama...

curl.exe -fsS "%OLLAMA_URL%/api/tags" >nul 2>&1

if errorlevel 1 (
    echo Starting Ollama...

    for /f %%P in ('powershell -NoProfile -Command "(Start-Process ollama.exe -ArgumentList 'serve' -PassThru -WindowStyle Hidden).Id"') do (
        set "OLLAMA_PID=%%P"
    )

    if not defined OLLAMA_PID (
        echo [ERROR] Failed to start Ollama.
        goto ERROR
    )
)

echo Waiting for Ollama API...

set /a attempts=0

:WAIT
curl.exe -fsS "%OLLAMA_URL%/api/tags" >nul 2>&1

if not errorlevel 1 goto START_BOT

set /a attempts+=1

if !attempts! GEQ 45 (
    echo [ERROR] Ollama failed to respond.
    goto ERROR
)

timeout /t 2 /nobreak >nul
goto WAIT

:START_BOT
echo Ollama is ready.
echo.
echo Starting bot...
echo.

python -u Main.py
set "EXIT_CODE=!errorlevel!"

goto CLEANUP

:ERROR
set "EXIT_CODE=1"

:CLEANUP
if defined OLLAMA_PID (
    echo.
    echo Stopping Ollama...
    taskkill /PID !OLLAMA_PID! /T /F >nul 2>&1
)

echo.
echo Bot stopped with exit code !EXIT_CODE!.
pause

exit /b !EXIT_CODE!
```
