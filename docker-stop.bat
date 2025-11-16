@echo off
REM Docker Stop Script for Supply Chain Forecasting Agent (Windows)
REM This script stops the Docker containers

echo 🛑 Stopping Supply Chain Forecasting Agent...
echo.

docker-compose down

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Services stopped!
) else (
    echo.
    echo ❌ Failed to stop services!
    exit /b %ERRORLEVEL%
)

