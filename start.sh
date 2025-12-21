#!/bin/bash
# MTBBS Startup Script

echo "================================"
echo "MTBBS Starting Up"
echo "================================"

# カラーコード定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# PIDファイル保存先
PIDDIR=".pids"
mkdir -p $PIDDIR

# Backend API起動
echo -e "${BLUE}[1/3] Starting Backend API...${NC}"
cd "$(dirname "$0")"
python3 simple_api.py > logs/api.log 2>&1 &
API_PID=$!
echo $API_PID > $PIDDIR/api.pid
echo -e "${GREEN}✓ Backend API started (PID: $API_PID)${NC}"
echo "  API: http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"

# Telnet BBS Server起動
echo -e "${BLUE}[2/4] Starting Telnet BBS Server...${NC}"
python3 demo_server.py > logs/telnet.log 2>&1 &
TELNET_PID=$!
echo $TELNET_PID > $PIDDIR/telnet.pid
echo -e "${GREEN}✓ Telnet BBS started (PID: $TELNET_PID)${NC}"
echo "  Connect: telnet localhost 2323"

# Telnet Monitor API起動
echo -e "${BLUE}[3/4] Starting Telnet Monitor API...${NC}"
python3 telnet_monitor.py > logs/monitor.log 2>&1 &
MONITOR_PID=$!
echo $MONITOR_PID > $PIDDIR/monitor.pid
echo -e "${GREEN}✓ Telnet Monitor started (PID: $MONITOR_PID)${NC}"
echo "  Monitor API: http://localhost:8001"

# Frontend Dev Server起動
echo -e "${BLUE}[4/4] Starting Frontend Dev Server...${NC}"
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../$PIDDIR/frontend.pid
cd ..
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
echo "  Web UI: http://localhost:5173"

echo ""
echo "================================"
echo -e "${GREEN}All services started successfully!${NC}"
echo "================================"
echo ""
echo "Services:"
echo "  - Backend API:    http://localhost:8000"
echo "  - Monitor API:    http://localhost:8001"
echo "  - Frontend UI:    http://localhost:5173"
echo "  - Telnet BBS:     telnet localhost 2323"
echo ""
echo "To stop all services, run: ./stop.sh"
echo ""
