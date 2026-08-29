@echo off
REM Aksara launcher for Windows.
REM Python may be installed through the Python Launcher (py) without a
REM usable `python` PATH alias. Probe real interpreters before reporting an
REM error so a preinstalled Python is never mistaken for a missing one.

setlocal EnableExtensions
cd /d "%~dp0"

call :try_python py -3
if not errorlevel 1 goto :python_found
call :try_python python3
if not errorlevel 1 goto :python_found
call :try_python python
if not errorlevel 1 goto :python_found
call :try_python "%~dp0.venv\Scripts\python.exe"
if not errorlevel 1 goto :python_found

echo.
echo [ERROR] Aksara needs a runnable Python 3.10+ interpreter.
echo         Python may already be installed but not exposed as `python` in PATH.
echo         Try: py -3 --version
echo         Or install/repair Python from https://python.org/downloads
echo.
exit /b 1

:python_found
"%PYTHON_EXE%" %PYTHON_ARGS% "%~dp0run.py" %*
exit /b %errorlevel%

:try_python
set "CANDIDATE=%~1"
set "CANDIDATE_ARGS=%~2"
"%CANDIDATE%" %CANDIDATE_ARGS% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 exit /b 1
set "PYTHON_EXE=%CANDIDATE%"
set "PYTHON_ARGS=%CANDIDATE_ARGS%"
exit /b 0
