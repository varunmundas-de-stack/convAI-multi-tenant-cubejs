@echo off
echo ============================================================
echo CPG Conversational AI Chatbot
echo ============================================================
echo.
echo Starting the web server...
echo.
echo Open your browser and go to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.
echo ============================================================
echo.

cd %~dp0
python frontend\app.py

pause
