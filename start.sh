#!/bin/bash
echo "=========================================="
echo "  🎯 Internship Hunter - Starting..."
echo "=========================================="
echo ""

# Start backend
echo "Starting backend server on port 8000..."
python -m backend.run &
BACKEND_PID=$!

sleep 3

# Start frontend
echo "Starting frontend dev server..."
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "=========================================="
echo "  ✅ Both servers starting!"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "=========================================="
echo ""
echo "First time? Open http://localhost:5173/setup"

wait
