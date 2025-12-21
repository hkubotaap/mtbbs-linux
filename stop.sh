#!/bin/bash
# MTBBS Shutdown Script

echo "================================"
echo "MTBBS Shutting Down"
echo "================================"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

PIDDIR=".pids"

# Frontend停止
if [ -f "$PIDDIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat $PIDDIR/frontend.pid)
    echo -e "${RED}[1/4] Stopping Frontend (PID: $FRONTEND_PID)...${NC}"
    kill $FRONTEND_PID 2>/dev/null
    rm $PIDDIR/frontend.pid
    echo -e "${GREEN}✓ Frontend stopped${NC}"
else
    echo "[1/4] Frontend not running"
fi

# Telnet Monitor停止
if [ -f "$PIDDIR/monitor.pid" ]; then
    MONITOR_PID=$(cat $PIDDIR/monitor.pid)
    echo -e "${RED}[2/4] Stopping Telnet Monitor (PID: $MONITOR_PID)...${NC}"
    kill $MONITOR_PID 2>/dev/null
    rm $PIDDIR/monitor.pid
    echo -e "${GREEN}✓ Telnet Monitor stopped${NC}"
else
    echo "[2/4] Telnet Monitor not running"
fi

# Telnet BBS停止
if [ -f "$PIDDIR/telnet.pid" ]; then
    TELNET_PID=$(cat $PIDDIR/telnet.pid)
    echo -e "${RED}[3/4] Stopping Telnet BBS (PID: $TELNET_PID)...${NC}"
    kill $TELNET_PID 2>/dev/null
    rm $PIDDIR/telnet.pid
    echo -e "${GREEN}✓ Telnet BBS stopped${NC}"
else
    echo "[3/4] Telnet BBS not running"
fi

# Backend API停止
if [ -f "$PIDDIR/api.pid" ]; then
    API_PID=$(cat $PIDDIR/api.pid)
    echo -e "${RED}[4/4] Stopping Backend API (PID: $API_PID)...${NC}"
    kill $API_PID 2>/dev/null
    rm $PIDDIR/api.pid
    echo -e "${GREEN}✓ Backend API stopped${NC}"
else
    echo "[4/4] Backend API not running"
fi

echo ""
echo "================================"
echo -e "${GREEN}All services stopped${NC}"
echo "================================"
