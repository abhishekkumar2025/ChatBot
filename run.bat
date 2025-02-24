@echo off
if not exist venv (
    echo Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate
if not exist %CD%\venv\Scripts\chainlit.exe (
    echo Chainlit not installed. Running pip install...
    pip install chainlit
)
chainlit run app.py
pause
