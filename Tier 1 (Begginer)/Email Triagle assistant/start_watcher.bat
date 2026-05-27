@echo off
cd /d "%~dp0"
start "EmailTriangleWatcher" /B pythonw.exe watcher.py
echo Watcher started. Check watcher.log for activity.
timeout /t 2 /nobreak >nul
