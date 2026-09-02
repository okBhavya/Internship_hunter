@echo off
echo ==========================================
echo   🎯 Internship Hunter - Starting...
echo ==========================================
echo.

echo Starting backend server on port 8000...
start "Internship Hunter Backend" python -m backend.run

timeout /t 3 /nobreak >nul

echo Starting frontend dev server...
cd frontend
start "Internship Hunter Frontend" npm run dev
cd ..

echo.
echo ==========================================
echo   ✅ Both servers starting!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo ==========================================
echo.
echo First time? Open http://localhost:5173/setup
pause
