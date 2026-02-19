@echo off
echo ================================================================
echo Stopping CPG Analytics Services
echo ================================================================
echo.

echo Stopping Metabase...
docker-compose -f docker-compose.metabase.yml down

echo.
echo ================================================================
echo Services stopped successfully!
echo ================================================================
echo.
echo Note: Flask app needs to be stopped manually (Ctrl+C in its window)
echo.
pause
