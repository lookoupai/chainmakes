@echo off
title Diagnose Spread Issue
cd /d "%~dp0backend"

echo ========================================
echo Spread Calculation Diagnosis
echo ========================================
echo.

call venv\Scripts\activate.bat
python diagnose_spread.py

echo.
pause