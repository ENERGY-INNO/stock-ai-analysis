#!/bin/bash
# =================================================
# 🚀 Stock AI Analysis - Background Runner
# =================================================
# 터미널을 닫아도 서버가 계속 실행됩니다.
#
# 사용법:
#   시작: ./background_start.sh
#   중지: ./background_stop.sh
#   상태: ./background_status.sh
# =================================================

cd "$(dirname "$0")"

# 로그 디렉토리 생성
mkdir -p logs

echo "🚀 Starting Stock AI System in background..."

# 기존 프로세스 종료
pkill -f "python3 run_all.py" 2>/dev/null
pkill -f "ngrok http 5001" 2>/dev/null
pkill -f "lt --port 5001" 2>/dev/null
sleep 2

# Flask 서버 시작
echo "📊 Starting Flask server..."
nohup python3 run_all.py --server-only > logs/server.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > logs/server.pid
echo "   Server PID: $SERVER_PID"

# 서버 시작 대기
sleep 3

# ngrok 터널 시작
echo "🌐 Starting ngrok tunnel..."
nohup /opt/homebrew/bin/ngrok http 5001 > logs/ngrok.log 2>&1 &
NGROK_PID=$!
echo $NGROK_PID > logs/ngrok.pid
echo "   ngrok PID: $NGROK_PID"

# localtunnel 시작 (옵션)
echo "🔗 Starting localtunnel..."
nohup lt --port 5001 --subdomain stock-ai-jsj > logs/localtunnel.log 2>&1 &
LT_PID=$!
echo $LT_PID > logs/localtunnel.pid
echo "   localtunnel PID: $LT_PID"

sleep 3

# ngrok URL 가져오기
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else 'N/A')" 2>/dev/null || echo "N/A")

echo ""
echo "=============================================="
echo "✅ Stock AI System is now running in background!"
echo "=============================================="
echo ""
echo "📌 Local:       http://localhost:5001"
echo "🌐 ngrok:       $NGROK_URL"
echo "🔗 localtunnel: https://stock-ai-jsj.loca.lt"
echo ""
echo "📁 Logs:        $(pwd)/logs/"
echo "💡 Stop:        ./background_stop.sh"
echo "=============================================="
