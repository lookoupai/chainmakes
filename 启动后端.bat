@echo off
title ChainMakes 后端服务
cd /d "%~dp0backend"
call venv\Scripts\activate.bat
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
