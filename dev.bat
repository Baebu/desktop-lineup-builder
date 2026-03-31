@echo off
REM Development batch script that activates venv and runs the auto-restart dev script

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install/update dependencies if needed
pip install -r requirements.txt

REM Run the development script
python dev.py

REM Deactivate venv when done
call deactivate