@echo off
echo ==========================================
echo Grace Chatbot - Google Cloud Run Deploy
echo ==========================================
echo.

REM Check if gcloud is installed
gcloud version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Google Cloud CLI is not installed.
    echo Please install gcloud CLI and try again.
    echo Download: https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

echo ✅ Google Cloud CLI is available

REM Get project ID
set /p PROJECT_ID="Enter your Google Cloud Project ID: "
if "%PROJECT_ID%"=="" (
    echo ERROR: Project ID is required
    pause
    exit /b 1
)

echo.
echo Setting project: %PROJECT_ID%
gcloud config set project %PROJECT_ID%

echo.
echo Building and pushing to Container Registry...
docker build -t grace-chatbot .
docker tag grace-chatbot gcr.io/%PROJECT_ID%/grace-chatbot:latest
docker push gcr.io/%PROJECT_ID%/grace-chatbot:latest

if %errorlevel% neq 0 (
    echo.
    echo ❌ Failed to push to Container Registry
    echo Make sure you're authenticated: gcloud auth configure-docker
    pause
    exit /b 1
)

echo.
echo Deploying to Cloud Run...
gcloud run deploy grace-chatbot ^
  --image gcr.io/%PROJECT_ID%/grace-chatbot:latest ^
  --platform managed ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --memory 1Gi ^
  --cpu 1 ^
  --timeout 300 ^
  --concurrency 80 ^
  --min-instances 0 ^
  --max-instances 10 ^
  --set-env-vars "FLASK_ENV=production,HOST=0.0.0.0" ^
  --port 8080

if %errorlevel% neq 0 (
    echo.
    echo ❌ Deployment failed!
    pause
    exit /b 1
)

echo.
echo ✅ Deployment successful!
echo.
echo Getting service URL...
gcloud run services describe grace-chatbot --region us-central1 --format "value(status.url)"

echo.
echo 🎉 Your app is now live on Google Cloud Run!
echo.
echo Next steps:
echo 1. Set your API keys using:
echo    gcloud run services update grace-chatbot --set-env-vars "OPENAI_API_KEY=your_key" --region us-central1
echo 2. Visit your app URL above
echo 3. Monitor logs: gcloud logs read --service grace-chatbot --region us-central1
echo.
pause