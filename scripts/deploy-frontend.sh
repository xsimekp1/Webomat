#!/bin/bash

# Webomat Frontend Deployment Script
# Deploys to Vercel

echo "🚀 Deploying Webomat Frontend to Vercel..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Install it first:"
    echo "npm install -g vercel"
    exit 1
fi

# Check if logged in
if ! vercel whoami &> /dev/null; then
    echo "❌ Not logged in to Vercel. Run 'vercel login' first"
    exit 1
fi

cd frontend

# Deploy to Vercel
echo "📦 Deploying to Vercel..."
vercel --prod

if [ $? -eq 0 ]; then
    echo "✅ Frontend deployed successfully!"
    echo "🌐 Frontend URL will be shown above"
else
    echo "❌ Frontend deployment failed!"
    exit 1
fi