#!/bin/bash
# =================================================
# 📊 Stock AI Analysis - Status Checker
# =================================================

cd "$(dirname "$0")"

echo "📊 Stock AI System Status"
echo "=========================="
echo ""

# Flask 서버 (포트 5001)
if lsof -ti:5001 > /dev/null 2>&1; then
    echo "✅ Flask Server:   RUNNING (http://localhost:5001)"
else
    echo "❌ Flask Server:   STOPPED"
fi

# ngrok
if pgrep -f "ngrok http 5001" > /dev/null; then
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else 'N/A')" 2>/dev/null || echo "Fetching...")
    echo "✅ ngrok:          RUNNING ($NGROK_URL)"
else
    echo "❌ ngrok:          STOPPED"
fi

# localtunnel
if pgrep -f "lt --port 5001" > /dev/null; then
    echo "✅ localtunnel:    RUNNING (https://stock-ai-jsj.loca.lt)"
else
    echo "❌ localtunnel:    STOPPED"
fi

echo ""
echo "📁 Log files in: $(pwd)/logs/"
