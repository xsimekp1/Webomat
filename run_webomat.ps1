# Webomat Launcher - PowerShell Version

Write-Host "=================================" -ForegroundColor Cyan
Write-Host "   WEBOMAT LAUNCHER" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "* Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python -c "import sys; print(sys.version.split()[0])"
    Write-Host "* Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "* ERROR: Python not found!" -ForegroundColor Red
    Write-Host "* Please install Python from: https://python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "* Checking streamlit installation..." -ForegroundColor Yellow
try {
    python -c "import streamlit; print('OK')" | Out-Null
    Write-Host "* Streamlit found" -ForegroundColor Green
} catch {
    Write-Host "* Streamlit not found, attempting to install..." -ForegroundColor Yellow
    try {
        python -m pip install --user streamlit pandas plotly
        Write-Host "* Streamlit and dependencies installed" -ForegroundColor Green
    } catch {
        Write-Host "* ERROR: Failed to install streamlit!" -ForegroundColor Red
        Write-Host "* Please run: pip install streamlit pandas plotly" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "* Checking port availability..." -ForegroundColor Yellow

# Check if port 8501 is busy
$port = 8501
try {
    $connection = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue
    if ($connection.TcpTestSucceeded) {
        Write-Host "* Port 8501 is busy (your other project)" -ForegroundColor Yellow
        Write-Host "* Finding free port..." -ForegroundColor Yellow

        # Find next free port
        while ($true) {
            $port++
            try {
                $connection = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue
                if (-not $connection.TcpTestSucceeded) {
                    Write-Host "* Found free port: $port" -ForegroundColor Green
                    break
                }
            } catch {
                Write-Host "* Found free port: $port" -ForegroundColor Green
                break
            }
        }
    } else {
        Write-Host "* Port 8501 is free, using it" -ForegroundColor Green
    }
} catch {
    Write-Host "* Port check failed, using 8501" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "* Starting Webomat on port $port..." -ForegroundColor Cyan
Write-Host ""

# Change to app directory
Set-Location "C:\Users\psimek\Projects\Webomat\webomat\streamlit_app"

# Check for plotly
Write-Host "* Checking plotly installation..." -ForegroundColor Yellow
try {
    python -c "import plotly; print('OK')" | Out-Null
    Write-Host "* Plotly found" -ForegroundColor Green
} catch {
    Write-Host "* Plotly not found, installing..." -ForegroundColor Yellow
    try {
        python -m pip install --user plotly
        Write-Host "* Plotly installed" -ForegroundColor Green
    } catch {
        Write-Host "* WARNING: Failed to install plotly, continuing anyway..." -ForegroundColor Yellow
        Write-Host "* Some features may not work without plotly" -ForegroundColor Yellow
    }
}

# Start streamlit
try {
    Write-Host "* Starting streamlit..." -ForegroundColor Cyan
    python -m streamlit run app.py --server.port $port --server.address localhost

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=================================" -ForegroundColor Green
        Write-Host "   WEBOMAT IS RUNNING!" -ForegroundColor Green
        Write-Host "   Open: http://localhost:$port" -ForegroundColor Green
        Write-Host "=================================" -ForegroundColor Green
        Write-Host ""

        Write-Host "* Opening browser..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
        Start-Process "http://localhost:$port"

        Write-Host ""
        Write-Host "* Web application is running!" -ForegroundColor Green
        Write-Host "* Press Ctrl+C to stop" -ForegroundColor Yellow
        Write-Host ""

        # Keep running
        while ($true) {
            Start-Sleep -Seconds 10
        }
    } else {
        Write-Host ""
        Write-Host "=================================" -ForegroundColor Red
        Write-Host "   ERROR: Failed to start Streamlit!" -ForegroundColor Red
        Write-Host "   Code: $LASTEXITCODE" -ForegroundColor Red
        Write-Host "=================================" -ForegroundColor Red
        Write-Host ""
        Write-Host "* Possible solutions:" -ForegroundColor Yellow
        Write-Host "* 1. Install streamlit: pip install streamlit pandas" -ForegroundColor Yellow
        Write-Host "* 2. Try different port: streamlit run app.py --server.port 8502" -ForegroundColor Yellow
        Write-Host "* 3. Check app.py file exists" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to exit"
    }
} catch {
    Write-Host ""
    Write-Host "ERROR: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}

Write-Host ""
Write-Host "Thank you for using Webomat!" -ForegroundColor Cyan