# Webomat Správný Startovací Skript

@echo off
chcp 65001 > nul

echo.
echo 🌐 Webomat Streamlit Aplikace
echo ========================================
echo.

REM Získání absolutní cesty k tomuto skriptu
set SCRIPT_DIR=%~dp0

REM Nastavení cestí
set WEBOMAT_DIR=%SCRIPT_DIR%\streamlit_app
set BATCH_FILE=%SCRIPT_DIR%\start_webomat.bat

echo 🔍 Kontroluji aktuální adresář...
if not exist "%WEBOMAT_DIR%\app.py" (
    echo ❌ CHYBA: Webomat soubory nebyly nalezeny!
    echo.
    echo Očekávaná struktura:
    echo   %WEBOMAT_DIR%\
    echo   ├── streamlit_app\
    echo   │   ├── app.py
    echo   │   └── ...
    echo.
    echo Správné umístění: %WEBOMAT_DIR%
    echo.
    echo 📍 Ujistěte se, že spouštíte tento skript z:
    echo   - %BATCH_FILE%
    echo   - Nebo z: %WEBOMAT_DIR%
    pause
    exit /b 1
)

echo ✅ Webomat soubory nalezeny!
echo 🚀 Spouštím aplikaci...
echo.

cd /d "%WEBOMAT_DIR%"

REM Spuštění s kontrolou chyb
if exist "start_webomat.bat" (
    start_webomat.bat
) else (
    echo ⚠️ start_webomat.bat nebyl nalezen, spouštím přímo...
    call start_app
)

echo.
echo ✅ Webomat aplikace spuštěna!
echo 🌐 Otevírám v prohlížeči na http://localhost:8501
echo.
echo Stiskněte libovolnou klávesu pro ukončení...
pause > nul