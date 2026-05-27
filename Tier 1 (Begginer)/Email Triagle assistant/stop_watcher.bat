@echo off
set "PID_FILE=%~dp0watcher.pid"
if not exist "%PID_FILE%" (
    echo No watcher.pid found — watcher may not be running.
    pause
    exit /b 1
)
set /p PID=<"%PID_FILE%"
taskkill /F /PID %PID% >nul 2>&1
if %ERRORLEVEL%==0 (
    echo Watcher stopped (PID %PID%).
    del "%PID_FILE%" >nul 2>&1
) else (
    echo Could not find process %PID% — it may have already stopped.
    del "%PID_FILE%" >nul 2>&1
)
pause
