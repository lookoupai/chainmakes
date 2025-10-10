@echo off
title Fix Start Price
cd /d "%~dp0backend"

echo ========================================
echo Fix Bot Start Price
echo ========================================
echo.

call venv\Scripts\activate.bat
python fix_start_price.py

echo.
pause