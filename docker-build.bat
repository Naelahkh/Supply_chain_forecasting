@echo off
REM Docker Build Script for Supply Chain Forecasting Agent (Windows)
REM This script builds the Docker image(s) for the application

echo 🐳 Building Supply Chain Forecasting Agent Docker Image...
echo.

REM Build the image
docker-compose build

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Build completed successfully!
    echo.
    echo 📋 Next steps:
    echo    1. Create a .env file with your GOOGLE_API_KEY
    echo    2. Run: docker-compose up -d
    echo    3. Access frontend at: http://localhost:8501
    echo    4. Access backend API at: http://localhost:8000/docs
) else (
    echo.
    echo ❌ Build failed! Check the error messages above.
    exit /b %ERRORLEVEL%
)

