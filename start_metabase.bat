@echo off
echo ================================================================
echo Starting CPG Analytics with Metabase Dashboards
echo ================================================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop first.
    echo.
    pause
    exit /b 1
)

echo [1/3] Starting Metabase...
docker-compose -f docker-compose.metabase.yml up -d

echo.
echo [2/3] Waiting for Metabase to start (this may take 1-2 minutes)...
timeout /t 5 /nobreak >nul

:wait_loop
curl -s http://localhost:3000/api/health >nul 2>&1
if errorlevel 1 (
    echo Still starting...
    timeout /t 5 /nobreak >nul
    goto wait_loop
)

echo.
echo [3/3] Starting Flask Application...
start cmd /k "python frontend/app.py"

echo.
echo ================================================================
echo SUCCESS! Services are running:
echo ================================================================
echo.
echo  Metabase Dashboard: http://localhost:3000
echo  Flask Chatbot:      http://localhost:5000
echo.
echo ================================================================
echo FIRST TIME SETUP:
echo ================================================================
echo 1. Open http://localhost:3000
echo 2. Create admin account (email + password)
echo 3. Skip "Add your data" - we'll do it manually
echo 4. Click "Settings" (gear icon) → "Admin" → "Databases"
echo 5. Click "Add database"
echo 6. Select "SQLite" from dropdown
echo 7. Enter:
echo    - Display name: CPG Analytics
echo    - Filename: /data/cpg_olap.duckdb
echo 8. Click "Save"
echo 9. Click "Exit admin" and start creating dashboards!
echo ================================================================
echo.
echo Press Ctrl+C in Flask window to stop chatbot
echo Run stop_metabase.bat to stop Metabase
echo.
pause
