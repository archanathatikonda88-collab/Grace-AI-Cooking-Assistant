# 🚀 Cloud-Only Deployment Guide (No Local Docker Required)

If you prefer not to install Docker locally, you can deploy directly to Google Cloud Run using Cloud Build. This approach builds the container in the cloud.

## Option 1: Direct Cloud Build Deployment

### Prerequisites:
- Google Cloud account
- Google Cloud CLI installed
- Git repository (GitHub, GitLab, or Google Cloud Source)

### Step 1: Setup Google Cloud
```powershell
# Install Google Cloud CLI if not installed
# Download from: https://cloud.google.com/sdk/docs/install

# Login and setup project
gcloud auth login
gcloud projects create grace-chatbot-prod --name="Grace Cooking Chatbot"
gcloud config set project grace-chatbot-prod

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
```

### Step 2: Deploy Using Cloud Build
```powershell
# Navigate to your project directory
cd C:\Users\Archana\Documents\LatestUpdates_Chatbot

# Deploy directly from source (no local Docker needed!)
gcloud run deploy grace-chatbot \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars "FLASK_ENV=production,HOST=0.0.0.0,OPENAI_API_KEY=your_key,PEXELS_API_KEY=your_key" \
  --port 8080
```

### Step 3: Set Environment Variables
```powershell
# Update with your actual API keys
gcloud run services update grace-chatbot \
  --set-env-vars "OPENAI_API_KEY=your_openai_key_here" \
  --region us-central1

gcloud run services update grace-chatbot \
  --set-env-vars "PEXELS_API_KEY=your_pexels_key_here" \
  --region us-central1
```

## Option 2: GitHub Actions Deployment

### Step 1: Create GitHub Repository
1. Create a new repository on GitHub
2. Push your code:
```powershell
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/grace-chatbot.git
git push -u origin main
```

### Step 2: Setup GitHub Actions
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

env:
  PROJECT_ID: grace-chatbot-prod
  SERVICE: grace-chatbot
  REGION: us-central1

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout
      uses: actions/checkout@v3

    - name: Google Auth
      id: auth
      uses: 'google-github-actions/auth@v0'
      with:
        credentials_json: '${{ secrets.GCP_SA_KEY }}'

    - name: Deploy to Cloud Run
      id: deploy
      uses: google-github-actions/deploy-cloudrun@v0
      with:
        service: ${{ env.SERVICE }}
        region: ${{ env.REGION }}
        source: ./
        env_vars: |
          FLASK_ENV=production
          HOST=0.0.0.0
          OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}
          PEXELS_API_KEY=${{ secrets.PEXELS_API_KEY }}

    - name: Show Output
      run: echo ${{ steps.deploy.outputs.url }}
```

### Step 3: Setup Secrets
In your GitHub repository settings, add these secrets:
- `GCP_SA_KEY`: Google Cloud service account key (JSON)
- `OPENAI_API_KEY`: Your OpenAI API key
- `PEXELS_API_KEY`: Your Pexels API key

## Option 3: Railway Deployment (Simple Alternative)

Railway is a simpler alternative to Google Cloud Run:

### Step 1: Install Railway CLI
```powershell
# Install via npm (if Node.js installed)
npm install -g @railway/cli

# Or download from: https://railway.app/cli
```

### Step 2: Deploy
```powershell
# Login to Railway
railway login

# Deploy
railway deploy
```

Railway will automatically detect your Dockerfile and deploy.

## Option 4: Heroku Deployment

### Step 1: Install Heroku CLI
Download from: https://devcenter.heroku.com/articles/heroku-cli

### Step 2: Deploy
```powershell
# Login to Heroku
heroku login

# Create app
heroku create grace-chatbot-app

# Set environment variables
heroku config:set OPENAI_API_KEY=your_key
heroku config:set PEXELS_API_KEY=your_key
heroku config:set FLASK_ENV=production

# Deploy
git push heroku main
```

## Comparison of Options

| Platform | Free Tier | Ease of Setup | Docker Required |
|----------|-----------|---------------|-----------------|
| Google Cloud Run | 2M requests/month | Medium | No (Cloud Build) |
| Railway | $5/month after trial | Easy | No |
| Heroku | 550 hours/month | Easy | No |
| GitHub Actions + GCR | 2M requests/month | Medium | No |

## Recommended Approach

For your use case, I recommend **Google Cloud Run with Cloud Build** because:
- ✅ True free tier (not trial)
- ✅ Excellent scaling (scale to zero)
- ✅ No local Docker installation needed
- ✅ Professional-grade infrastructure
- ✅ Easy CI/CD integration

Simply run the cloud build deployment command and your app will be live without needing Docker locally!