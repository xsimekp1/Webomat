#!/bin/bash

# Webomat Backend Deployment Script
# Deploys to Railway

echo "🚀 Deploying Webomat Backend to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Install it first:"
    echo "npm install -g @railway/cli"
    exit 1
fi

# Check if logged in
if ! railway status &> /dev/null; then
    echo "❌ Not logged in to Railway. Run 'railway login' first"
    exit 1
fi

# Deploy to Railway
echo "📦 Deploying to Railway..."
railway deploy

if [ $? -eq 0 ]; then
    echo "✅ Backend deployed successfully!"
    echo "🌐 Backend URL: https://webomat-backend-production.up.railway.app"
else
    echo "❌ Backend deployment failed!"
    exit 1
fi