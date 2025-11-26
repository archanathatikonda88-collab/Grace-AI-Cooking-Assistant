@echo off
echo ============================================
echo    GRACE CHATBOT - GOOGLE CLOUD DEPLOYMENT
echo ============================================
echo.

REM Set environment variables
set PATH=%PATH%;C:\Users\%USERNAME%\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin
set PATH=%PATH%;C:\Program Files\Docker\Docker\resources\bin

echo Step 1: Verifying project setup...
gcloud config get-value project
if errorlevel 1 (
    echo ERROR: No project configured. Please run setup first.
    pause
    exit /b 1
)

echo.
echo Step 2: Building and deploying to Cloud Run...
echo Building Docker image for Cloud Run...

gcloud run deploy grace-chatbot ^
    --source . ^
    --platform managed ^
    --region us-central1 ^
    --allow-unauthenticated ^
    --set-env-vars OPENAI_API_KEY=your_openai_api_key_here,PEXELS_API_KEY=your_pexels_api_key_here ^
    --memory 512Mi ^
    --cpu 1 ^
    --timeout 300 ^
    --max-instances 10

if errorlevel 1 (
    echo.
    echo ❌ Deployment failed. Please check the error above.
    echo Common issues:
    echo - Billing not enabled
    echo - APIs not enabled
    echo - Authentication issues
    pause
    exit /b 1
)

echo.
echo ✅ SUCCESS! Your Grace Chatbot is now deployed to Google Cloud!
echo.
echo 🌐 Your app should be available at the URL shown above.
echo 💰 Free tier: 2M requests/month included
echo 📊 Monitor usage: https://console.cloud.google.com/run
echo.
pause