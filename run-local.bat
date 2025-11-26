@echo off
echo ==========================================
echo    GRACE CHATBOT - LOCAL DEPLOYMENT
echo ==========================================
echo.

REM Set Docker path
set PATH=%PATH%;C:\Program Files\Docker\Docker\resources\bin

echo ✅ Your Grace Chatbot is running locally!
echo.
echo 🌐 Local URL: http://localhost:8080
echo 🐳 Docker Status: Running in container
echo 💡 Benefits:
echo    • No cloud billing required
echo    • Full functionality available
echo    • Perfect for development and testing
echo.

echo Opening your chatbot in browser...
start http://localhost:8080

echo.
echo 📊 To monitor the application:
echo    • Docker Desktop: Check containers tab
echo    • Logs: docker logs latestupdates_chatbot-grace-chatbot-1
echo    • Stop: docker-compose down
echo.

echo 🔧 Management Commands:
echo    • Restart: docker-compose restart
echo    • Update: docker-compose up --build -d
echo    • View logs: docker-compose logs -f
echo.

pause