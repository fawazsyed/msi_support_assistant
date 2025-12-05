@echo off
REM MSI AI Assistant - Stop All Services
REM Stops all Python and Node.js processes

echo.
echo ========================================
echo   MSI AI Assistant - Stopping Services
echo ========================================
echo.
echo Stopping all Python and Node.js processes...
echo.

powershell -Command "Get-Process python,node -ErrorAction SilentlyContinue | Stop-Process -Force"

echo.
echo Done! All services stopped.
echo.
echo You can now run: start.bat
echo.