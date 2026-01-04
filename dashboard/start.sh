#!/bin/bash

echo "Starting Real Estate Dashboard..."
echo ""
echo "Starting backend server..."
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 3
echo ""
echo "Backend started at http://localhost:8000"
echo ""
echo "Starting frontend server..."
cd ../frontend
python3 -m http.server 8080 &
FRONTEND_PID=$!
echo ""
echo "Frontend started at http://localhost:8080"
echo ""
echo "Dashboard is ready!"
echo "Press Ctrl+C to stop servers"
wait

