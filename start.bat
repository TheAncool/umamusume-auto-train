@echo off
cd /d "%~dp0"
mode con: cols=80 lines=25

:loop
python main.py
echo.
echo Script ended or terminated.
set /p choice="Press [Enter] to restart or close this window manually... "
goto loop
