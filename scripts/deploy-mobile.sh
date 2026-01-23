#!/bin/bash

# Webomat Mobile Deployment Script
# Builds and submits to EAS (Expo Application Services)

echo "🚀 Deploying Webomat Mobile to EAS..."

# Check if EAS CLI is installed
if ! command -v eas &> /dev/null; then
    echo "❌ EAS CLI not found. Install it first:"
    echo "npm install -g @expo/eas-cli"
    exit 1
fi

# Check if logged in
if ! eas whoami &> /dev/null; then
    echo "❌ Not logged in to EAS. Run 'eas login' first"
    exit 1
fi

cd mobile

# Build for production
echo "📦 Building mobile app for production..."
eas build --profile production --platform all

if [ $? -eq 0 ]; then
    echo "✅ Mobile app built successfully!"
    echo "📱 Download links will be available in Expo dashboard"
    echo "🌐 Check: https://expo.dev/accounts/[your-account]/projects/webomat-mobile"
else
    echo "❌ Mobile build failed!"
    exit 1
fi