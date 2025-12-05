@echo off
REM MSI AI Assistant - Stop All Services
REM Saves collected data and stops all Python and Node.js processes

echo.
echo ========================================
echo   MSI AI Assistant - Stopping Services
echo ========================================
echo.

REM Save collected Ragas data before shutdown
echo Saving collected Ragas data...
curl -X POST http://localhost:8080/api/admin/save-data -H "Content-Type: application/json" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Data saved successfully
) else (
    echo Warning: Could not reach API endpoint ^(server may already be stopped^)
)

echo.
echo Stopping all Python and Node.js processes...
echo.

powershell -Command "Get-Process python,node -ErrorAction SilentlyContinue | Stop-Process -Force"

echo.
echo Done! All services stopped.
echo.
echo You can now run: start.bat
echo.