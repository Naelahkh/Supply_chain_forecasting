@echo off
REM Docker Test Script for Supply Chain Forecasting Agent (Windows)
REM This script tests if the Docker setup is working correctly

echo 🧪 Testing Docker Setup...
echo.

REM Check Docker installation
echo 1️⃣ Checking Docker installation...
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker is not installed!
    exit /b 1
)
docker-compose --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker Compose is not installed!
    exit /b 1
)
echo ✅ Docker and Docker Compose are installed

REM Check if .env file exists
echo.
echo 2️⃣ Checking environment file...
if not exist .env (
    echo ⚠️  Warning: .env file not found!
    echo    Create one with: echo GOOGLE_API_KEY=your_key > .env
) else (
    echo ✅ .env file found
)

REM Check if models directory exists
echo.
echo 3️⃣ Checking models directory...
if not exist models (
    echo ⚠️  Warning: models directory not found!
) else (
    echo ✅ models directory found
)

REM Check if knowledge_base directory exists
echo.
echo 4️⃣ Checking knowledge_base directory...
if not exist knowledge_base (
    echo ⚠️  Warning: knowledge_base directory not found!
) else (
    echo ✅ knowledge_base directory found
)

REM Test Docker build (dry-run)
echo.
echo 5️⃣ Testing Docker build...
docker-compose config >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ docker-compose.yml is valid
) else (
    echo ❌ docker-compose.yml has errors!
    docker-compose config
    exit /b 1
)

REM Check if containers are running
echo.
echo 6️⃣ Checking running containers...
docker-compose ps | findstr "Up" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Containers are running
    
    REM Test health check
    echo.
    echo 7️⃣ Testing health check...
    timeout /t 2 /nobreak >nul
    curl -f http://localhost:8000/health >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo ✅ Backend health check passed
    ) else (
        echo ⚠️  Backend health check failed (might still be starting)
    )
) else (
    echo ℹ️  Containers are not running
    echo    Start them with: docker-compose up -d
)

echo.
echo ✅ Docker setup test completed!
echo.
echo 📋 Next steps:
echo    If containers are not running:
echo    - Build: docker-compose build
echo    - Start: docker-compose up -d
echo    - Logs:  docker-compose logs -f

