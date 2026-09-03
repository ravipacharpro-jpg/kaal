@echo off
REM Kaal installer — Windows (cmd). Python 3.11+ chahiye (python.org se).
cd /d "%~dp0.."
python --version || (echo [31mPython nahi mila — python.org se install karo[0m & exit /b 1)
pip install -r requirements.txt -q
echo Kaal ready — chalao: python -m kaal
echo Wrapper ke liye: install\kaal.bat ko PATH me dalo ya seedha python -m kaal
