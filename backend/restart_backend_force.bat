@echo off
echo 正在停止后端服务...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo 正在启动后端服务...
cd /d "%~dp0"
start cmd /k "venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"

echo 后端服务已重启！
pause