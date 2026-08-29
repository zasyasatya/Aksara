@echo off
REM Aksara Platform - Auto Setup & Run (Windows)
REM Menyiapkan instalasi dan menjalankan backend + frontend sekaligus
REM Usage: run.bat  atau  run.bat --install

setlocal enabledelayedexpansion

echo.
echo    ___   _  __ _____   ___   ____   ___
echo   / _ ^| / ^|/ // ___/  / _ ^| / __ \ / _ \
echo  / __ ^|/    / \__ \  / __ ^|/ /_/ // , _/
echo /_/ ^|_/_/^|_/ /____/ /_/ ^|_\____//_/^|_^|
echo.
echo Platform Belajar Aksara Bali - Auto Setup
echo Aksara - Melestarikan Warisan, Menulis Masa Depan
echo.

REM Check if we're in correct dir
if not exist "run.py" (
    echo [ERROR] run.py not found! Run this script from repository root
    pause
    exit /b 1
)

echo [CHECK] Checking requirements...

REM Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Install from https://python.org
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo [OK] %%i
)

REM Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found! Install from https://nodejs.org
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('node --version 2^>^&1') do echo [OK] Node %%i
)

REM npm
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm not found!
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('npm --version 2^>^&1') do echo [OK] npm %%i
)

echo.
echo [SETUP] Installing dependencies...

REM Backend
echo [BACKEND] pip install -r backend\requirements.txt
if exist "backend\requirements.txt" (
    python -m pip install -r backend\requirements.txt -q
    if %errorlevel% equ 0 (
        echo [OK] Backend installed
    ) else (
        echo [WARN] Backend install failed, trying with --break-system-packages
        python -m pip install -r backend\requirements.txt -q --break-system-packages
    )
) else (
    echo [ERROR] backend\requirements.txt not found!
)

REM Frontend
echo [FRONTEND] npm install
if exist "frontend" (
    cd frontend
    if not exist "node_modules" (
        call npm install --silent
        echo [OK] Frontend installed
    ) else (
        echo [SKIP] node_modules exists, skipping (use --force-install to reinstall)
        echo %* | findstr /C:"--force-install" >nul
        if %errorlevel% equ 0 (
            echo [FORCE] Reinstalling...
            rmdir /s /q node_modules 2>nul
            call npm install --silent
        )
    )
    cd ..
) else (
    echo [ERROR] frontend\ not found!
)

echo.
echo [OK] Setup complete! Starting servers...
echo Backend: http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo.
echo Press Ctrl+C to stop both servers
echo.

REM Run the Python unified runner
python run.py --no-install %*

pause
