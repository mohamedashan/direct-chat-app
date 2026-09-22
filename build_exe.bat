@echo off
echo ============================================
echo   Building Direct PC Chat as a Windows app
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python is not installed or not on PATH.
    echo Download it from https://www.python.org/downloads/
    echo IMPORTANT: during install, check "Add python.exe to PATH"
    pause
    exit /b 1
)

echo Installing PyInstaller (one-time)...
pip install --quiet pyinstaller

echo.
echo Building DirectChat.exe ...
pyinstaller --onefile --windowed --name "DirectChat" direct_chat.py

echo.
if exist dist\DirectChat.exe (
    echo SUCCESS! Your app is at: dist\DirectChat.exe
    echo Copy that single .exe file to the other PC and double-click it there too.
    echo No Python installation is needed on the other PC.
) else (
    echo Something went wrong - check the messages above for errors.
)

pause
