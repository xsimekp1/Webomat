@echo off
setlocal EnableDelayedExpansion

chcp 65001 >nul

echo.
echo 🌐 WEBOMAT - Automatický Spouštěč
echo =====================================
echo.

if not exist "streamlit_app\app.py" (
    echo ❌ CHYBA: Aplikace nenalezena!
    echo.
    echo Očekávaná struktura:
    echo   webomat\streamlit_app\
    echo       app.py
    echo.
    echo Spouštějte tento skript z adresáře: %~dp0
    echo.
    pause
    exit /b 1
)

echo ✅ Aplikační soubory nalezeny
echo.

echo 🔍 Kontrola Python instalace...
for /f "tokens=*" %%i in ('python -c "import sys; print(sys.version.split()[0])" 2^>nul') do set PYTHON_VERSION=%%i
if "!PYTHON_VERSION!"=="" (
    echo ❌ CHYBA: Python není správně nainstalován!
    echo.
    echo Prosím nainstalujte Python 3.8+ z: https://python.org
    echo.
    pause
    exit /b 1
)

echo ✅ Python nalezen: !PYTHON_VERSION!
echo.

echo 🔍 Kontrola Streamlit instalace...
python -c "import streamlit" 2>nul
if !errorlevel! neq 0 (
    echo ⚠️ Streamlit není nainstalován, instaluji...
    echo.
    pip install streamlit pandas plotly
    if !errorlevel! neq 0 (
        echo ❌ CHYBA: Instalace Streamlit selhala!
        echo.
        echo Zkuste ručně: pip install streamlit pandas plotly
        echo.
        pause
        exit /b 1
    )
    echo ✅ Streamlit a závislosti nainstalovány
    echo.
) else (
    echo ✅ Streamlit je připraven
    echo.
)

cd /d "streamlit_app"

echo 🚀 Spouštím Webomat...
echo.
echo 📋 Dostupné stránky:
echo    • Dashboard - přehled a statistiky
echo    • Businesses - správa firem
echo    • Map - interaktivní mapa
echo    • Search - vyhledávání
echo    • Quick Generate - rychlá tvorba webů
echo    • Settings - nastavení API klíčů
echo.

echo 🌐 Aplikace se spustí na: http://localhost:8501
echo 💡 První návštěva: Settings → nastavit API klíče pro plnou funkcionalitu
echo.

REM Zkontrolujeme, zda port 8501 je volný
netstat -an | findstr ":8501" >nul 2>&1
if !errorlevel! equ 0 (
    echo ⚠️ Port 8501 je obsazený, hledám volný port...
    for /l %%i in (8502,1,8600) do (
        netstat -an | findstr ":%%i" >nul 2>&1
        if !errorlevel! neq 0 (
            echo ✅ Nalezen volný port: %%i
            set WEB_PORT=%%i
            goto :found_port
        )
    )
    echo ❌ Žádný volný port v rozsahu 8502-8600
    set WEB_PORT=8501
    :found_port
) else (
    echo ✅ Port 8501 je volný
    set WEB_PORT=8501
)

echo.
echo 🚀 Spouštím Webomat na portu !WEB_PORT!...
echo.

streamlit run app.py --server.port !WEB_PORT! --server.address localhost --server.headless false

if !errorlevel! equ 0 (
    echo.
    echo ✅ Aplikace úspěšně spuštěna!
    echo 🌐 Otevírám v prohlížeči na http://localhost:!WEB_PORT!
    echo.
    timeout /t 3 >nul
    start http://localhost:!WEB_PORT!
) else (
    echo.
    echo ❌ Spouštění selhalo (kód: !errorlevel!)
    echo.
    echo 🔧 Možná řešení:
    echo    • Spusťte jako Administrator
    echo    • Zkontrolujte soubory ve streamlit_app\
    echo    • Zkontrolujte instalaci závislostí: pip install -r requirements.txt
    echo    • Zkuste jiný port: streamlit run app.py --server.port 8502
    echo.
)

echo.
echo 🎉 Děkujeme za použití Webomat!
echo.
pause