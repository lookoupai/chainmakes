@echo off
echo 正在清理旧的后端进程...

REM 查找并终止所有uvicorn进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /F /PID %%a 2>nul
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
    taskkill /F /PID %%a 2>nul
)

echo 等待进程完全终止...
timeout /t 2 /nobreak >nul

echo 启动新的后端服务器...
cd /d "%~dp0"
call venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause