@echo off
REM Lineup Builder - Launch Script
REM This batch file starts the Lineup Builder desktop application

cd /d "%~dp0"

REM Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Creating one...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Launch the application
python main.py