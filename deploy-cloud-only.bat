@echo off
echo ===========================================
echo Grace Chatbot - Cloud Deploy (No Docker)
echo ===========================================
echo.

REM Check if gcloud is installed
gcloud version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Google Cloud CLI is not installed.
    echo.
    echo Please install Google Cloud CLI:
    echo 1. Visit: https://cloud.google.com/sdk/docs/install
    echo 2. Download and install the CLI
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo ✅ Google Cloud CLI is available
echo.

REM Get project ID
set /p PROJECT_ID="Enter your Google Cloud Project ID (or press Enter to create new): "
if "%PROJECT_ID%"=="" (
    echo.
    echo Creating new project...
    set PROJECT_ID=grace-chatbot-%RANDOM%
    echo Project ID will be: %PROJECT_ID%
    gcloud projects create %PROJECT_ID% --name="Grace Cooking Chatbot"
    if %errorlevel% neq 0 (
        echo ❌ Failed to create project
        pause
        exit /b 1
    )
)

echo.
echo Setting project: %PROJECT_ID%
gcloud config set project %PROJECT_ID%

echo.
echo Enabling required APIs...
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com

echo.
echo ====================================
echo IMPORTANT: API Keys Setup
echo ====================================
echo.
echo You'll need your API keys for deployment.
echo.
set /p OPENAI_KEY="Enter your OpenAI API Key: "
set /p PEXELS_KEY="Enter your Pexels API Key: "

if "%OPENAI_KEY%"=="" (
    echo ❌ OpenAI API key is required
    pause
    exit /b 1
)

if "%PEXELS_KEY%"=="" (
    echo ❌ Pexels API key is required
    pause
    exit /b 1
)

echo.
echo ====================================
echo Deploying to Cloud Run...
echo ====================================
echo.
echo This will build your app in the cloud (no local Docker needed)
echo.

gcloud run deploy grace-chatbot ^
  --source . ^
  --platform managed ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --memory 1Gi ^
  --cpu 1 ^
  --timeout 300 ^
  --concurrency 80 ^
  --min-instances 0 ^
  --max-instances 10 ^
  --set-env-vars "FLASK_ENV=production,HOST=0.0.0.0,PORT=8080,OPENAI_API_KEY=%OPENAI_KEY%,PEXELS_API_KEY=%PEXELS_KEY%" ^
  --port 8080

if %errorlevel% neq 0 (
    echo.
    echo ❌ Deployment failed!
    echo.
    echo Common issues:
    echo 1. Make sure you're authenticated: gcloud auth login
    echo 2. Check that billing is enabled for your project
    echo 3. Verify API keys are correct
    echo.
    pause
    exit /b 1
)

echo.
echo ====================================
echo 🎉 Deployment Successful!
echo ====================================
echo.
echo Getting your app URL...
for /f "delims=" %%i in ('gcloud run services describe grace-chatbot --region us-central1 --format="value(status.url)"') do set APP_URL=%%i

echo.
echo ✅ Your Grace Chatbot is now live at:
echo %APP_URL%
echo.
echo 📊 Management Commands:
echo.
echo View logs:
echo   gcloud logs read --service grace-chatbot --region us-central1 --limit 50
echo.
echo Update environment variables:
echo   gcloud run services update grace-chatbot --set-env-vars "NEW_VAR=value" --region us-central1
echo.
echo View in Cloud Console:
echo   https://console.cloud.google.com/run/detail/us-central1/grace-chatbot/metrics?project=%PROJECT_ID%
echo.
echo 💰 Cost Info:
echo - Free tier: 2 million requests per month
echo - Your app scales to zero when not in use (no idle costs)
echo - Monitor usage in Google Cloud Console
echo.

pause