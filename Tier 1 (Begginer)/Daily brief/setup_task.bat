@echo off
REM Registers the Daily Brief agent as a Windows Task Scheduler job.
REM Run this script ONCE as Administrator.
REM Adjust BRIEF_TIME to your preferred delivery time (24-hour format).

set BRIEF_TIME=07:00
set SCRIPT_DIR=%~dp0
set PYTHON=python

echo Registering Daily Brief task to run at %BRIEF_TIME% daily...

schtasks /create ^
  /tn "DailyBrief" ^
  /tr "\"%PYTHON%\" \"%SCRIPT_DIR%brief.py\"" ^
  /sc daily ^
  /st %BRIEF_TIME% ^
  /f ^
  /rl HIGHEST

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS: Task registered. Brief will run every day at %BRIEF_TIME%.
    echo To test immediately: schtasks /run /tn "DailyBrief"
    echo To remove the task:  schtasks /delete /tn "DailyBrief" /f
) else (
    echo.
    echo ERROR: Failed to register task. Make sure you ran this as Administrator.
)

pause
