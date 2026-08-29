@echo off
REM Install Aksara without Docker, then exit.
REM Delegate to run.bat so the Windows Python Launcher (py -3) is detected.

setlocal EnableExtensions
cd /d "%~dp0"
call "%~dp0run.bat" --install-only %*
exit /b %errorlevel%
