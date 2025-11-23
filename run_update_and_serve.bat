@echo off
REM Launcher wrapper for MegaSmart AI
REM This batch file runs the project launcher using the venv python if present.

SETLOCAL ENABLEDELAYEDEXPANSION
REM Resolve script directory
SET ROOT=%~dp0

REM Trim trailing backslash if present
IF "%ROOT:~-1%"=="\" SET ROOT=%ROOT:~0,-1%

SET VENV_PY="%ROOT%\venv\Scripts\python.exe"
SET LAUNCHER="%ROOT%\scripts\run_update_and_serve.py"

IF EXIST %VENV_PY% (
    echo Using virtualenv Python: %VENV_PY%
    %VENV_PY% %LAUNCHER% %*
) ELSE (
    echo Virtual environment Python not found at %VENV_PY%
    echo You can activate your venv and run the launcher manually:
    echo.
    echo    PowerShell:  .\venv\Scripts\Activate.ps1 ; python .\scripts\run_update_and_serve.py
    echo    CMD:         venv\Scripts\activate.bat && python scripts\run_update_and_serve.py
    echo.
    pause
    exit /b 1
)
