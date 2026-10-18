@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [*] Запускаем скрипт...
".venv\Scripts\python.exe" mine.py -t "yes" -n 255

echo.
pause