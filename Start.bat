@echo off
setlocal EnableDelayedExpansion

title AI Companion
chcp 65001 >nul

echo ========================================
echo    AI Companion - Starting...
echo ========================================
echo.

:: Check if venv exists and activate it
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    set PYTHON=python
) else (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Please ensure Python is installed correctly
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    set PYTHON=python
)

:: Install/update dependencies
echo.
echo Installing dependencies...
%PYTHON% -m pip install --upgrade pip
%PYTHON% -m pip install -r requirements.txt

:: Start the application
echo.
echo ========================================
echo    Starting AI Companion...
echo ========================================
echo.
%PYTHON% main.py

pause