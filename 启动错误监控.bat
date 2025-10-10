@echo off
title ChainMakes Error Monitor
cd /d "%~dp0backend"

echo ========================================
echo ChainMakes Error Monitor Tool
echo ========================================
echo.
echo This tool will monitor trading bot errors in real-time
echo Error logs: backend/logs/trading_errors.log
echo Error summary: backend/logs/error_summary.txt
echo.
echo Press Ctrl+C to stop monitoring
echo.
echo ========================================
echo.

call venv\Scripts\activate.bat
python scripts/monitor_trading_errors.py

pause