@echo off
echo ================================================
echo Docker Installation Checker for Grace Chatbot
echo ================================================
echo.

echo Checking Docker installation...
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Docker is already installed!
    docker --version
    docker-compose --version
    echo.
    echo You can now run: .\quick-start.bat
    goto end
)

echo ❌ Docker is not installed.
echo.
echo Your system information:
for /f "tokens=*" %%i in ('powershell -command "(Get-CimInstance Win32_OperatingSystem).Caption"') do echo Windows: %%i
for /f "tokens=*" %%i in ('powershell -command "(Get-CimInstance Win32_OperatingSystem).BuildNumber"') do echo Build: %%i
echo.

echo ============================================
echo Installation Options:
echo ============================================
echo.
echo Option 1 - Manual Download (Recommended):
echo   1. Visit: https://docs.docker.com/desktop/install/windows-install/
echo   2. Download "Docker Desktop for Windows"
echo   3. Run the installer
echo   4. Restart your computer
echo   5. Come back and run this script again
echo.

echo Option 2 - Using winget (if available):
winget --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✅ winget is available - you can run:
    echo   winget install Docker.DockerDesktop
) else (
    echo   ❌ winget not available
)
echo.

echo Option 3 - Using Chocolatey (if available):
choco --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✅ Chocolatey is available - you can run:
    echo   choco install docker-desktop
) else (
    echo   ❌ Chocolatey not available
)
echo.

echo ============================================
echo Alternative: Deploy without Docker
echo ============================================
echo.
echo If you prefer not to install Docker, you can:
echo 1. Deploy directly to Google Cloud Run using Cloud Build
echo 2. Use GitHub Actions for automated deployment
echo 3. Deploy to other platforms like Heroku, Railway, or Fly.io
echo.
echo See DEPLOYMENT_GUIDE.md for cloud-based deployment options.
echo.

:end
pause