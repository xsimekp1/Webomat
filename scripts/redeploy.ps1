# Webomat Redeploy Script
# Restartuje backend (Railway) i frontend (Vercel)

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

# Konfigurace - tokeny jsou v env variables
$RAILWAY_TOKEN = $env:RAILWAY_TOKEN
$VERCEL_TOKEN = $env:VERCEL_TOKEN

# Railway IDs
$RAILWAY_PROJECT_ID = "d6a191b5-bc63-4836-b905-1cdee9fe51e5"
$RAILWAY_SERVICE_ID = "54b194dd-644f-4c26-a806-faabaaeacc7b"
$RAILWAY_ENV_ID = "9afdeb2c-17e7-44d5-bfe9-1258121a59aa"

if (-not $RAILWAY_TOKEN -or -not $VERCEL_TOKEN) {
    Write-Host "ERROR: RAILWAY_TOKEN a VERCEL_TOKEN musi byt nastaveny v environment variables" -ForegroundColor Red
    Write-Host "Nastav je pomoci:" -ForegroundColor Yellow
    Write-Host '  $env:RAILWAY_TOKEN = "tvuj-railway-token"'
    Write-Host '  $env:VERCEL_TOKEN = "tvuj-vercel-token"'
    exit 1
}

function Redeploy-Backend {
    Write-Host "`n[Railway] Restartuji backend..." -ForegroundColor Cyan

    $body = @{
        query = "mutation { serviceInstanceRedeploy(environmentId: `"$RAILWAY_ENV_ID`", serviceId: `"$RAILWAY_SERVICE_ID`") }"
    } | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" `
            -Method Post `
            -Headers @{
                "Content-Type" = "application/json"
                "Authorization" = "Bearer $RAILWAY_TOKEN"
            } `
            -Body $body

        if ($response.data.serviceInstanceRedeploy) {
            Write-Host "[Railway] Backend redeploy spusten!" -ForegroundColor Green
            Write-Host "         URL: https://webomat-backend-production.up.railway.app" -ForegroundColor Gray
        } else {
            Write-Host "[Railway] Chyba pri redeployi" -ForegroundColor Red
            Write-Host $response | ConvertTo-Json
        }
    } catch {
        Write-Host "[Railway] Chyba: $_" -ForegroundColor Red
    }
}

function Redeploy-Frontend {
    Write-Host "`n[Vercel] Restartuji frontend..." -ForegroundColor Cyan

    # Najdi posledni uspesny deployment
    try {
        $deployments = Invoke-RestMethod -Uri "https://api.vercel.com/v6/deployments?app=webomat&limit=10" `
            -Method Get `
            -Headers @{ "Authorization" = "Bearer $VERCEL_TOKEN" }

        $lastReady = $deployments.deployments | Where-Object { $_.readyState -eq "READY" } | Select-Object -First 1

        if (-not $lastReady) {
            Write-Host "[Vercel] Nenalezen zadny uspesny deployment" -ForegroundColor Red
            return
        }

        # Redeploy z posledniho uspesneho
        $body = @{
            name = "webomat"
            deploymentId = $lastReady.uid
            target = "production"
        } | ConvertTo-Json

        $response = Invoke-RestMethod -Uri "https://api.vercel.com/v13/deployments?forceNew=1&withCache=1" `
            -Method Post `
            -Headers @{
                "Content-Type" = "application/json"
                "Authorization" = "Bearer $VERCEL_TOKEN"
            } `
            -Body $body

        Write-Host "[Vercel] Frontend redeploy spusten!" -ForegroundColor Green
        Write-Host "         URL: https://webomat.vercel.app" -ForegroundColor Gray
        Write-Host "         Deployment ID: $($response.id)" -ForegroundColor Gray
    } catch {
        Write-Host "[Vercel] Chyba: $_" -ForegroundColor Red
    }
}

Write-Host "========================================" -ForegroundColor White
Write-Host "  WEBOMAT REDEPLOY" -ForegroundColor White
Write-Host "========================================" -ForegroundColor White

if (-not $FrontendOnly) {
    Redeploy-Backend
}

if (-not $BackendOnly) {
    Redeploy-Frontend
}

Write-Host "`n[Done] Redeploy prikazy odeslany." -ForegroundColor Green
Write-Host "       Deploymenty bezi na pozadi, muze to trvat 1-2 minuty." -ForegroundColor Gray
