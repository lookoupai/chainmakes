@echo off
chcp 65001
cd /d "%~dp0"
venv\Scripts\python.exe test_binance.py
pause
