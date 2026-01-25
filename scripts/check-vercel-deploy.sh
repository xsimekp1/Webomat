#!/bin/bash

# Check Vercel deployment status after push
echo "🔍 Checking Vercel deployment status..."

# Wait a bit for deployment to start
sleep 30

# Try to check the site
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://webomat.vercel.app)

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Vercel deployment successful - Site is up (HTTP $HTTP_STATUS)"
    echo "🌐 Check: https://webomat.vercel.app"
elif [ "$HTTP_STATUS" = "404" ] || [ "$HTTP_STATUS" = "500" ]; then
    echo "❌ Vercel deployment failed - HTTP $HTTP_STATUS"
    echo "🔧 Check Vercel dashboard: https://vercel.com/xsimekp1/webomat"
elif [ "$HTTP_STATUS" = "403" ]; then
    echo "⚠️ Vercel deploying - HTTP $HTTP_STATUS (try again in 2 minutes)"
    sleep 60
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://webomat.vercel.app)
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "✅ Vercel deployment successful after waiting"
    else
        echo "❌ Vercel deployment still failing - HTTP $HTTP_STATUS"
    fi
else
    echo "⚠️ Unknown status - HTTP $HTTP_STATUS"
fi