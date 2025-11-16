@echo off
REM Docker Start Script for Supply Chain Forecasting Agent (Windows)
REM This script starts the Docker containers

echo 🚀 Starting Supply Chain Forecasting Agent...
echo.

REM Check if .env file exists
if not exist .env (
    echo ⚠️  Warning: .env file not found!
    echo    Please create a .env file with your GOOGLE_API_KEY
    echo    Example: echo GOOGLE_API_KEY=your_key_here > .env
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /i not "%continue%"=="y" exit /b 1
)

REM Start the services
docker-compose up -d

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ⏳ Waiting for services to start...
    timeout /t 5 /nobreak >nul
    
    echo.
    echo 📊 Checking service health...
    docker-compose ps
    
    echo.
    echo ✅ Services started!
    echo.
    echo 📋 Access points:
    echo    Frontend (Streamlit): http://localhost:8501
    echo    Backend API:         http://localhost:8000
    echo    API Documentation:   http://localhost:8000/docs
    echo    Health Check:        http://localhost:8000/health
    echo.
    echo 📝 Useful commands:
    echo    View logs:      docker-compose logs -f
    echo    Stop services:  docker-compose down
    echo    Restart:        docker-compose restart
) else (
    echo.
    echo ❌ Failed to start services! Check the error messages above.
    exit /b %ERRORLEVEL%
)

