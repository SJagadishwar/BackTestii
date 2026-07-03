@echo off
setlocal

:: Navigate to the project directory
cd /d "%~dp0"

:: Set up logging
set LOG_FILE=logs\daily_update.log
if not exist "logs" mkdir logs

echo ======================================================== >> %LOG_FILE%
echo Starting Daily Database Update at %date% %time% >> %LOG_FILE%
echo ======================================================== >> %LOG_FILE%

:: Ensure the virtual environment exists before calling it
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found at .venv >> %LOG_FILE%
    exit /b 1
)

:: Activate the virtual environment
call .venv\Scripts\activate.bat

:: Execute the corporate actions loader first
echo [%time%] Running Corporate Actions Loader... >> %LOG_FILE%
python -m engine.data.ingestion.corporate_actions_loader >> %LOG_FILE% 2>&1

:: Execute the daily bhavcopy update sequentially
echo [%time%] Running Daily Bhavcopy Update... >> %LOG_FILE%
python -m engine.data.ingestion.daily_update >> %LOG_FILE% 2>&1

:: Execute the daily index update
echo [%time%] Running Daily Index Update... >> %LOG_FILE%
python -m engine.data.ingestion.daily_index_update >> %LOG_FILE% 2>&1

:: Execute the daily F&O update
echo [%time%] Running Daily F&O Update... >> %LOG_FILE%
python -m engine.data.ingestion.fo_daily_update >> %LOG_FILE% 2>&1

echo [%time%] Update Complete! >> %LOG_FILE%
echo ======================================================== >> %LOG_FILE%

:: Deactivate env
call deactivate
endlocal
exit /b 0
