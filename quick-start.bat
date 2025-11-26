@echo off
echo ====================================
echo Grace Chatbot - Docker Quick Start
echo ====================================
echo.

REM Check if Docker is running
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running or not installed.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo ✅ Docker is running

REM Check if .env file exists
if not exist .env (
    echo.
    echo ⚠️  WARNING: .env file not found
    echo Creating .env template...
    echo OPENAI_API_KEY=your_openai_api_key_here > .env
    echo PEXELS_API_KEY=your_pexels_api_key_here >> .env
    echo.
    echo Please edit .env file with your actual API keys before proceeding.
    pause
)

echo.
echo Building Docker image...
docker build -t grace-chatbot .

if %errorlevel% neq 0 (
    echo.
    echo ❌ Docker build failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ✅ Docker image built successfully!
echo.
echo Starting container on http://localhost:8080...
echo Press Ctrl+C to stop the container
echo.

docker run -p 8080:8080 --env-file .env -e PORT=8080 -e HOST=0.0.0.0 grace-chatbot