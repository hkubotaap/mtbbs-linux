#!/bin/bash
# MTBBS Installation and Update Script

echo "================================"
echo "MTBBS Setup & Update"
echo "================================"

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ログディレクトリ作成
echo -e "${BLUE}Creating log directories...${NC}"
mkdir -p logs
mkdir -p .pids
echo -e "${GREEN}✓ Directories created${NC}"

# Python依存関係のインストール/更新
echo ""
echo -e "${BLUE}[1/2] Installing/Updating Python dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip3 install --upgrade -r requirements.txt
    echo -e "${GREEN}✓ Python packages installed${NC}"
else
    echo -e "${YELLOW}⚠ requirements.txt not found, installing common packages...${NC}"
    pip3 install --upgrade fastapi uvicorn python-multipart
    echo -e "${GREEN}✓ Core packages installed${NC}"
fi

# Node.js依存関係のインストール/更新
echo ""
echo -e "${BLUE}[2/2] Installing/Updating Node.js dependencies...${NC}"
if [ -d "frontend" ]; then
    cd frontend
    if [ -f "package.json" ]; then
        npm install
        echo -e "${GREEN}✓ Node.js packages installed${NC}"
    else
        echo -e "${YELLOW}⚠ package.json not found${NC}"
    fi
    cd ..
else
    echo -e "${YELLOW}⚠ frontend directory not found${NC}"
fi

echo ""
echo "================================"
echo -e "${GREEN}Setup complete!${NC}"
echo "================================"
echo ""
echo "Next steps:"
echo "  1. Run './start.sh' to start all services"
echo "  2. Access web UI at http://localhost:5173"
echo "  3. Connect to BBS: telnet localhost 2323"
echo ""
