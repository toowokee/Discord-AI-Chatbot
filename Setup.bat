@echo off
setlocal
title Discord-AI-Chatbot Setup

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

echo.
echo Downloading Qwen 2.5 1.5B...
"%OLLAMA%" pull qwen2.5:1.5b
if errorlevel 1 (
    echo Model download failed.
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
echo     Run Start.Bat to start the bot!
Echo         Have A Good Day
echo ==========================================
pause
endlocal
