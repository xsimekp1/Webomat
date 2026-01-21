@echo off
REM Webomat PowerShell Launcher

echo.
echo Starting Webomat with PowerShell...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0run_webomat.ps1"

echo.
echo Webomat launcher finished.
echo.
pause