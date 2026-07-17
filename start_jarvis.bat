@echo off
title JARVIS - AI Desktop Assistant
echo.
echo  ================================
echo   JARVIS - AI Desktop Assistant
echo  ================================
echo.

REM Check if conda is available
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Anaconda/Miniconda not found!
    echo Please install from: https://docs.anaconda.com/miniconda/
    echo.
    pause
    exit /b 1
)

REM Activate the jarvis environment
echo Activating jarvis-env environment...
call conda activate jarvis-env
if %errorlevel% neq 0 (
    echo [ERROR] Could not activate jarvis-env
    echo Run this first: conda create -n jarvis-env python=3.14 -y
    echo Then: conda activate jarvis-env
    echo Then: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Copy .env.example to .env and fill in your API keys.
    echo.
    copy .env.example .env
    echo Created .env from template. Please edit it with your API keys.
    echo.
)

REM Check if Chrome is installed
if not exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    if not exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
        echo [WARNING] Google Chrome not found!
        echo Jarvis uses Chrome for web browsing. Install from: https://www.google.com/chrome/
        echo.
    )
)

echo Starting JARVIS...
echo Press Alt+Space to activate the HUD
echo Press Alt+Q to force quit
echo.
python jarvis_ui.py
pause
