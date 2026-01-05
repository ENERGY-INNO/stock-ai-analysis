#!/bin/bash
# =================================================
# 🛑 Stock AI Analysis - Background Stopper
# =================================================

cd "$(dirname "$0")"

echo "🛑 Stopping Stock AI System..."

# PID 파일에서 프로세스 종료
if [ -f logs/server.pid ]; then
    kill $(cat logs/server.pid) 2>/dev/null && echo "   ✅ Flask server stopped"
    rm logs/server.pid
fi

if [ -f logs/ngrok.pid ]; then
    kill $(cat logs/ngrok.pid) 2>/dev/null && echo "   ✅ ngrok stopped"
    rm logs/ngrok.pid
fi

if [ -f logs/localtunnel.pid ]; then
    kill $(cat logs/localtunnel.pid) 2>/dev/null && echo "   ✅ localtunnel stopped"
    rm logs/localtunnel.pid
fi

# 혹시 남아있는 프로세스 정리
pkill -f "python3 run_all.py" 2>/dev/null
pkill -f "ngrok http 5001" 2>/dev/null
pkill -f "lt --port 5001" 2>/dev/null

echo ""
echo "✅ All services stopped."
