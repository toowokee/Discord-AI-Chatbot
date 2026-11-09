@echo off
setlocal
title Discord-AI-Chatbot Setup

rem ---- Settings ----
set "DEFAULT_MODEL=qwen2.5:1.5b"
set "ENV_KEY=OLLAMA_MODEL"
rem ------------------

echo ==========================================
echo       Discord-AI-Chatbot Setup
echo          Made By @Toowoke
echo ==========================================
echo.

where winget >nul 2>&1
if errorlevel 1 (
    echo winget is missing. Install App Installer from the Microsoft Store.
    pause
    exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
    echo Python is not installed.
    echo Install Python 3 from https://www.python.org/
    pause
    exit /b 1
)

where ollama >nul 2>&1
if errorlevel 1 (
    echo Installing Ollama...
    winget install --id Ollama.Ollama -e --accept-package-agreements --accept-source-agreements
)

set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"

if exist "%OLLAMA_EXE%" (
    set "OLLAMA=%OLLAMA_EXE%"
) else (
    set "OLLAMA=ollama"
)

echo.
echo Checking Ollama...

"%OLLAMA%" --version >nul 2>&1
if errorlevel 1 (
    echo Ollama isn't available. Restart your terminal and try again.
    pause
    exit /b 1
)

rem ---- Make sure the Ollama server is running ----
"%OLLAMA%" list >nul 2>&1
if errorlevel 1 (
    echo Starting Ollama server...
    start "" /min "%OLLAMA%" serve
    timeout /t 5 /nobreak >nul
)

"%OLLAMA%" list >nul 2>&1
if errorlevel 1 (
    echo Could not connect to the Ollama server. Open Ollama and try again.
    pause
    exit /b 1
)

rem ---- Check which models are already installed ----
echo.
echo Checking installed models...

set "MODEL="
for /f "skip=1 tokens=1" %%M in ('"%OLLAMA%" list') do (
    if not defined MODEL set "MODEL=%%M"
)

if defined MODEL (
    echo Found installed model: %MODEL%
) else (
    echo No models installed.
    echo Downloading %DEFAULT_MODEL%...
    "%OLLAMA%" pull %DEFAULT_MODEL%
    if errorlevel 1 (
        echo Model download failed.
        pause
        exit /b 1
    )
    set "MODEL=%DEFAULT_MODEL%"
)

rem ---- Write the model into .env ----
echo.
echo Setting %ENV_KEY%=%MODEL% in .env...

powershell -NoProfile -Command "$k=$env:ENV_KEY; $v=$env:MODEL; $f='.env'; if (Test-Path $f) { $l=@(Get-Content $f) } else { $l=@() }; $found=$false; $l=@($l | ForEach-Object { if ($_ -match ('^\s*' + $k + '\s*=')) { $found=$true; $k + '=' + $v } else { $_ } }); if (-not $found) { $l += ($k + '=' + $v) }; Set-Content -Path $f -Value $l -Encoding ascii"
if errorlevel 1 (
    echo Failed to update .env
    pause
    exit /b 1
)

echo.
echo Installing Python requirements...

if not exist requirements.txt (
    echo requirements.txt was not found.
    pause
    exit /b 1
)

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Failed to install Python requirements.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo         Setup complete!
echo     Model in use: %MODEL%
echo     Run Start.Bat to start the bot!
echo         Have A Good Day
echo ==========================================
pause
endlocal
