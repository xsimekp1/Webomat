$VERCEL_TOKEN = "uanxoOOLz8mCzrjFupSNoznD"

$deployments = Invoke-RestMethod -Uri "https://api.vercel.com/v6/deployments?app=webomat&limit=10" -Method Get -Headers @{"Authorization" = "Bearer $VERCEL_TOKEN"}

$lastReady = $deployments.deployments | Where-Object { $_.readyState -eq "READY" } | Select-Object -First 1

if ($lastReady) {
    Write-Host "Redeploying from: $($lastReady.uid)"
    $body = @{
        name = "webomat"
        deploymentId = $lastReady.uid
        target = "production"
    } | ConvertTo-Json

    $result = Invoke-RestMethod -Uri "https://api.vercel.com/v13/deployments?forceNew=1&withCache=1" -Method Post -Headers @{
        "Authorization" = "Bearer $VERCEL_TOKEN"
        "Content-Type" = "application/json"
    } -Body $body

    Write-Host "Deployment started: $($result.id)"
    Write-Host "URL: $($result.url)"
} else {
    Write-Host "No ready deployment found"
}
