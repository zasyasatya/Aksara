@echo off
REM Aksara Platform - Full Auto Installer (Windows)
REM Usage: install.bat

echo.
echo    ___   _  __ _____   ___   ____   ___   INSTALLER
echo   / _ ^| / ^|/ // ___/  / _ ^| / __ \ / _ \
echo  / __ ^|/    / \__ \  / __ ^|/ /_/ // , _/
echo /_/ ^|_/_/^|_/ /____/ /_/ ^|_\____//_/^|_^|
echo.
echo Aksara Bali - Full Auto Installer (Windows)
echo.

echo [1] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Install from https://python.org
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo [OK] %%i
)

echo.
echo [2] Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found! Install from https://nodejs.org
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('node --version 2^>^&1') do echo [OK] Node %%i
)

echo.
echo [3] Checking npm...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm not found!
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('npm --version 2^>^&1') do echo [OK] npm %%i
)

echo.
echo [4] Backend Setup...
if exist "backend\requirements.txt" (
    echo Installing Python deps...
    python -m pip install -r backend\requirements.txt -q
    echo [OK] Backend ready
) else (
    echo [ERROR] backend\requirements.txt missing
)

echo.
echo [5] Frontend Setup...
if exist "frontend" (
    cd frontend
    if not exist "node_modules" (
        echo Installing Node deps (may take 1-2 minutes)...
        call npm install --silent
    ) else (
        echo node_modules exists, updating...
        call npm install --silent
    )
    echo Testing build...
    call npm run build
    echo [OK] Frontend ready
    cd ..
) else (
    echo [ERROR] frontend\ missing
)

echo.
echo [OK] Installation Complete!
echo.
echo To run:
echo   python run.py          - Run both
echo   run.bat                - Auto setup + run
echo.
echo URLs:
echo   Backend:  http://localhost:8000/docs
echo   Frontend: http://localhost:3000
echo.
echo Matur suksma!
pause
