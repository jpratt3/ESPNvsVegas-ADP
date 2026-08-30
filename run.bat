@echo off
cd /d "%~dp0"
start "" http://localhost:8642
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8642
