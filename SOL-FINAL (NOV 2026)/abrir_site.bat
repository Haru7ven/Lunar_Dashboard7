@echo off
echo ===================================================
echo   SOL - A iniciar servidor local para o dashboard
echo ===================================================
cd /d "%~dp0web"
start "" http://localhost:8080
python -m http.server 8080
