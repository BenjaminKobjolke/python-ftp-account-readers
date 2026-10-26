@echo off
cd /d "%~dp0.."
uv run pytest tests -v
set TESTRESULT=%ERRORLEVEL%
exit /b %TESTRESULT%
