#!/usr/bin/env bash
set -e

echo "============================================================"
echo "  🚀 Starting RazorLoop: Autonomous Revenue Recovery System  "
echo "  Track 03 - Razorpay Buildathon                             "
echo "============================================================"

# Kill any existing instances on 8000 or 5173
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 5173/tcp 2>/dev/null || true

# 1. Start Backend
echo "Starting Backend API on http://localhost:8000 ..."
PYTHONPATH=. ./razorpay_env/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 2

# 2. Start Frontend
echo "Starting Frontend Terminal on http://localhost:5173 ..."
npm --prefix frontend run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

echo ""
echo "✅ RazorLoop is running!"
echo "   • Dashboard UI:  http://localhost:5173"
echo "   • Backend API:   http://localhost:8000"
echo "   • API Docs:      http://localhost:8000/docs"
echo "   • Telegram Bot:  @razor_loop_bot"
echo ""
echo "Press CTRL+C to terminate all services."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
