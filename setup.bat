@echo off
setlocal enabledelayedexpansion

:: Check if Python is in PATH
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python not found in PATH
    goto install_python
) else (
    :: Check Python version
    for /f "tokens=2 delims=." %%I in ('python -V 2^>^&1') do set pyver=%%I
    if !pyver! lss 10 (
        echo Python version too old
        goto install_python
    ) else (
        echo Found compatible Python installation
        goto setup_env
    )
)

:install_python
echo Installing Python 3.10...
powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.10.0/python-3.10.0-amd64.exe', 'python_installer.exe')"
python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
del python_installer.exe

:: Update PATH without requiring restart
set PATH=%PATH%;C:\Program Files\Python310;C:\Program Files\Python310\Scripts
echo Python installation complete

:setup_env
echo Setting up virtual environment...
python -m venv venv
call venv\Scripts\activate

echo Installing requirements...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo Setup complete! Run the chatbot using: run.bat
pause
