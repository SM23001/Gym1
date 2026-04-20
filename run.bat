@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found.
    echo Run: python -m venv .venv  and  pip install -r requirements.txt
    pause
    exit /b 1
)

python cli.py
if errorlevel 1 (
    echo.
    echo [ERROR] The application exited with an error.
    pause
)
