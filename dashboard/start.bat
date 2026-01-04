@echo off
echo Starting Real Estate Dashboard...
echo.
echo Starting backend server...
cd backend
start cmd /k "uvicorn app:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul
echo.
echo Backend started at http://localhost:8000
echo.
echo Opening frontend in browser...
cd ..\frontend
start index.html
echo.
echo Dashboard is ready!

