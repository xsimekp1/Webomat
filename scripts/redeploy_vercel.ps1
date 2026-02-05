# Vercel Frontend Redeploy Script
# This script triggers a new deployment from the git repository (master branch)
#
# NOTE: Vercel auto-deploys on git push. Only use this script if you need
# to manually trigger a redeploy without pushing new code.

$VERCEL_TOKEN = $env:VERCEL_TOKEN

Write-Host "Triggering Vercel deployment from git repository..."

# Change to frontend directory where vercel.json is located
Push-Location "$PSScriptRoot\..\frontend"

try {
    # Use Vercel CLI to deploy - this pulls fresh from the connected git repo
    # --prod deploys to production
    # --yes skips confirmation prompts
    $env:VERCEL_TOKEN = $VERCEL_TOKEN

    # Check if vercel CLI is installed
    $vercelPath = Get-Command vercel -ErrorAction SilentlyContinue
    if ($vercelPath) {
        Write-Host "Using Vercel CLI..."
        vercel --prod --yes --token $VERCEL_TOKEN
    } else {
        # Fallback: Use npx to run vercel
        Write-Host "Using npx vercel..."
        npx vercel --prod --yes --token $VERCEL_TOKEN
    }

    Write-Host ""
    Write-Host "Deployment triggered successfully!"
    Write-Host "Check https://vercel.com/dashboard for deployment status"
} catch {
    Write-Host "Error: $_"
    exit 1
} finally {
    Pop-Location
}
