# 🚀 Grace Cooking Chatbot - Docker & Google Cloud Run Deployment Guide

This guide will walk you through containerizing your application with Docker and deploying it to Google Cloud Run for free tier hosting.

## 📋 Prerequisites

1. **Google Cloud Account** (Free tier includes 2 million requests/month)
2. **Docker Desktop** installed on your machine
3. **Google Cloud CLI (gcloud)** installed
4. **Git** (optional, for version control)

## 🏗️ Part 1: Local Docker Setup

### Step 1: Verify Docker Installation
```bash
docker --version
docker-compose --version
```

### Step 2: Create Environment File for Local Testing
Create a `.env.production` file in your project root:
```bash
# Production environment variables
FLASK_ENV=production
PORT=8080
HOST=0.0.0.0
OPENAI_API_KEY=your_openai_api_key_here
PEXELS_API_KEY=your_pexels_api_key_here
```

### Step 3: Build Docker Image Locally
```bash
# Navigate to your project directory
cd C:\Users\Archana\Documents\LatestUpdates_Chatbot

# Build the Docker image
docker build -t grace-chatbot .

# Verify the image was created
docker images | findstr grace-chatbot
```

### Step 4: Test Docker Container Locally
```bash
# Run the container with environment variables
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=your_key_here \
  -e PEXELS_API_KEY=your_key_here \
  -e PORT=8080 \
  -e HOST=0.0.0.0 \
  grace-chatbot

# Or use docker-compose (recommended)
docker-compose up --build
```

### Step 5: Verify Local Container
- Open browser to `http://localhost:8080`
- Test recipe search functionality
- Verify images load correctly

## ☁️ Part 2: Google Cloud Setup

### Step 1: Create Google Cloud Project
```bash
# Install gcloud CLI if not installed
# Download from: https://cloud.google.com/sdk/docs/install

# Login to Google Cloud
gcloud auth login

# Create a new project (replace PROJECT_ID with your choice)
gcloud projects create grace-chatbot-prod --name="Grace Cooking Chatbot"

# Set the project as default
gcloud config set project grace-chatbot-prod

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### Step 2: Configure Container Registry
```bash
# Configure Docker to use gcloud as credential helper
gcloud auth configure-docker

# Tag your image for Google Container Registry
docker tag grace-chatbot gcr.io/grace-chatbot-prod/grace-chatbot:latest
```

### Step 3: Push Image to Container Registry
```bash
# Push the image to Google Container Registry
docker push gcr.io/grace-chatbot-prod/grace-chatbot:latest
```

## 🚀 Part 3: Deploy to Cloud Run

### Step 1: Deploy to Cloud Run
```bash
# Deploy to Cloud Run
gcloud run deploy grace-chatbot \
  --image gcr.io/grace-chatbot-prod/grace-chatbot:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "FLASK_ENV=production,HOST=0.0.0.0" \
  --port 8080
```

### Step 2: Set Environment Variables (Secure Method)
```bash
# Set OpenAI API Key
gcloud run services update grace-chatbot \
  --set-env-vars "OPENAI_API_KEY=your_openai_api_key_here" \
  --region us-central1

# Set Pexels API Key
gcloud run services update grace-chatbot \
  --set-env-vars "PEXELS_API_KEY=your_pexels_api_key_here" \
  --region us-central1
```

### Step 3: Get Your Deployment URL
```bash
# Get the service URL
gcloud run services describe grace-chatbot \
  --region us-central1 \
  --format "value(status.url)"
```

## 🔒 Part 4: Security & Secrets Management

### Option A: Using Google Secret Manager (Recommended)
```bash
# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Create secrets
echo "your_openai_api_key" | gcloud secrets create openai-api-key --data-file=-
echo "your_pexels_api_key" | gcloud secrets create pexels-api-key --data-file=-

# Update Cloud Run to use secrets
gcloud run services update grace-chatbot \
  --set-secrets "OPENAI_API_KEY=openai-api-key:latest,PEXELS_API_KEY=pexels-api-key:latest" \
  --region us-central1
```

### Option B: Environment Variables (Simpler)
Use the method in Step 3.2 above for direct environment variables.

## 📊 Part 5: Monitoring & Maintenance

### View Logs
```bash
# View recent logs
gcloud logs read --limit 50 --format "table(timestamp,severity,textPayload)" \
  --filter "resource.type=cloud_run_revision AND resource.labels.service_name=grace-chatbot"
```

### Update Deployment
```bash
# Build new image with changes
docker build -t grace-chatbot .
docker tag grace-chatbot gcr.io/grace-chatbot-prod/grace-chatbot:latest
docker push gcr.io/grace-chatbot-prod/grace-chatbot:latest

# Deploy update
gcloud run deploy grace-chatbot \
  --image gcr.io/grace-chatbot-prod/grace-chatbot:latest \
  --region us-central1
```

### Scale and Configure
```bash
# Update CPU/Memory
gcloud run services update grace-chatbot \
  --memory 2Gi \
  --cpu 2 \
  --region us-central1

# Update concurrency
gcloud run services update grace-chatbot \
  --concurrency 100 \
  --region us-central1
```

## 💰 Cost Optimization

**Free Tier Limits:**
- 2 million requests per month
- 360,000 GB-seconds of memory
- 180,000 vCPU-seconds
- Always free tier includes these limits

**Cost-Saving Tips:**
1. Set `--min-instances 0` (scale to zero when not used)
2. Use appropriate memory/CPU settings
3. Enable request timeout to prevent hanging requests
4. Monitor usage in Google Cloud Console

## 🔧 Troubleshooting

### Common Issues:

1. **Build fails**: Check Dockerfile syntax and requirements.txt
2. **Container won't start**: Verify PORT environment variable
3. **API keys not working**: Check secret configuration
4. **Images not loading**: Verify static file serving in production

### Debug Commands:
```bash
# Test container locally
docker run -it --rm grace-chatbot /bin/bash

# Check Cloud Run logs
gcloud logs read --service grace-chatbot --region us-central1 --limit 100

# Check service status
gcloud run services describe grace-chatbot --region us-central1
```

## 🎉 Success!

Your Grace Cooking Chatbot is now deployed to Google Cloud Run with:
- ✅ Automatic scaling (including scale-to-zero)
- ✅ HTTPS by default
- ✅ Global CDN
- ✅ 99.95% SLA
- ✅ Free tier benefits

Your app is now accessible worldwide at your Cloud Run URL!