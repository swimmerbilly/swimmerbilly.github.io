@echo off
setlocal
cd /d "%~dp0"

echo Starting Personal Assistant backend...
cd backend
if not exist .venv (
  python -m venv .venv
  call .venv\Scripts\activate.bat
  pip install -r requirements.txt -q
) else (
  call .venv\Scripts\activate.bat
)
start "PA Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"

echo Starting Personal Assistant frontend...
cd ..\frontend
if not exist node_modules (
  call npm install
)
start "PA Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Personal Assistant is starting in two windows:
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo.
echo Close those windows to stop the app.
pause
