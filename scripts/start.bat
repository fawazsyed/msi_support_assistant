@echo off
REM MSI AI Assistant - Start All Services
REM This wrapper ensures proper UTF-8 encoding on Windows

chcp 65001 >nul
set PYTHONIOENCODING=utf-8

echo.
echo ========================================
echo   MSI AI Assistant - Starting Services
echo ========================================
echo.
echo Starting all services with Honcho...
echo Press Ctrl+C to stop all services
echo.

REM Change to project root (parent directory of scripts/)
cd /d "%~dp0.."

uv run honcho start