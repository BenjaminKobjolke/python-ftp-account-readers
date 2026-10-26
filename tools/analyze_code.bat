@echo off
cd /d "%~dp0.."
uv run ruff check . || exit /b 1
uv run ruff format --check . || exit /b 1
uv run mypy || exit /b 1
exit /b 0
