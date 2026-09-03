@echo off
REM kaal wrapper — repo root se chalata hai. Is folder ko PATH me dalo.
cd /d "%~dp0.." 
python -m kaal %*
