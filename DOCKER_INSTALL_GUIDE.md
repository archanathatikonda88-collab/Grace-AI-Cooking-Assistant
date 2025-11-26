# 🐳 Docker Installation Guide for Windows

## Step 1: Download Docker Desktop

1. **Visit the Docker Desktop website:**
   - Go to: https://docs.docker.com/desktop/install/windows-install/
   - Click "Download Docker Desktop for Windows"

2. **System Requirements:**
   - Windows 10 64-bit: Pro, Enterprise, or Education (Build 19041 or higher)
   - Or Windows 11 64-bit: Home or Pro version 21H2 or higher
   - WSL 2 feature enabled
   - 4GB RAM minimum

## Step 2: Install Docker Desktop

1. **Run the installer:**
   - Double-click `Docker Desktop Installer.exe`
   - Follow the installation wizard
   - **Important:** Keep "Use WSL 2 instead of Hyper-V" checked (recommended)

2. **Complete installation:**
   - The installer will download required components
   - Restart your computer when prompted

## Step 3: Enable WSL 2 (if not already enabled)

Open PowerShell as Administrator and run:
```powershell
# Enable WSL and Virtual Machine Platform
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Restart your computer
Restart-Computer
```

After restart, set WSL 2 as default:
```powershell
wsl --set-default-version 2
```

## Step 4: Start Docker Desktop

1. **Launch Docker Desktop:**
   - Search for "Docker Desktop" in Start menu
   - Start the application
   - Wait for Docker to initialize (this may take a few minutes)

2. **Verify installation:**
   ```powershell
   docker --version
   docker-compose --version
   ```

## Step 5: Test Docker Installation

Run a simple test container:
```powershell
docker run hello-world
```

You should see a message confirming Docker is working correctly.

## Alternative: Quick Installation Commands

If you have Windows Package Manager (winget):
```powershell
# Install Docker Desktop via winget
winget install Docker.DockerDesktop
```

Or via Chocolatey (if installed):
```powershell
# Install Docker Desktop via Chocolatey
choco install docker-desktop
```

## Troubleshooting

### Common Issues:

1. **WSL 2 not enabled:**
   - Follow Step 3 above to enable WSL 2

2. **Virtualization not enabled:**
   - Enable Hardware Virtualization in BIOS/UEFI settings
   - Look for "Intel VT-x" or "AMD-V" settings

3. **Docker Desktop won't start:**
   - Restart Windows
   - Run as Administrator
   - Check Windows Event Viewer for errors

4. **Permission errors:**
   - Add your user to "docker-users" group:
   ```powershell
   net localgroup docker-users "your-username" /add
   ```

## Next Steps After Installation

Once Docker is installed and running:

1. **Test our Grace Chatbot Docker setup:**
   ```powershell
   cd C:\Users\Archana\Documents\LatestUpdates_Chatbot
   .\quick-start.bat
   ```

2. **Or manually build and run:**
   ```powershell
   docker build -t grace-chatbot .
   docker run -p 8080:8080 --env-file .env grace-chatbot
   ```

## Resources

- **Docker Desktop Documentation:** https://docs.docker.com/desktop/
- **WSL 2 Setup:** https://docs.microsoft.com/en-us/windows/wsl/install
- **Docker Getting Started:** https://docs.docker.com/get-started/