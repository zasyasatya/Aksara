#!/bin/bash
# Aksara Platform - Full Auto Installer
# One command to install everything from scratch
# Usage: chmod +x install.sh && ./install.sh

set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
SAFFRON='\033[38;5;208m'
RESET='\033[0m'

echo -e "${SAFFRON}${BOLD}"
echo "   ___   _  __ _____   ___   ____   ___   INSTALLER"
echo "  / _ | / |/ // ___/  / _ | / __ \ / _ \\"
echo " / __ |/    / \\__ \\  / __ |/ /_/ // , _/"
echo "/_/ |_/_/|_/ /____/ /_/ |_\\____//_/|_|"
echo -e "${RESET}"
echo -e "${BOLD}Aksara Bali - Full Auto Installer${RESET}"
echo ""

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi
echo -e "OS: ${BOLD}$OS${RESET}"

# Check Python
echo -e "\n${BOLD}1. Python${RESET}"
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✅ $(python3 --version)${RESET}"
    PYTHON=python3
elif command -v python &> /dev/null; then
    echo -e "${GREEN}✅ $(python --version)${RESET}"
    PYTHON=python
else
    echo -e "${RED}❌ Python not found. Install Python 3.9+${RESET}"
    echo "   Linux: sudo apt install python3 python3-pip python3-venv"
    echo "   macOS: brew install python@3.11"
    echo "   Windows: https://python.org/downloads"
    exit 1
fi

# Check Node
echo -e "\n${BOLD}2. Node.js${RESET}"
if command -v node &> /dev/null; then
    echo -e "${GREEN}✅ $(node --version)${RESET}"
else
    echo -e "${YELLOW}⚠️ Node.js not found, attempting auto-install...${RESET}"
    if [[ "$OS" == "linux" ]]; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs
    elif [[ "$OS" == "macos" ]]; then
        if command -v brew &> /dev/null; then
            brew install node@20
        else
            echo -e "${RED}Install Node.js from https://nodejs.org${RESET}"
            exit 1
        fi
    else
        echo -e "${RED}Install Node.js from https://nodejs.org${RESET}"
        exit 1
    fi
fi

# Check npm
echo -e "\n${BOLD}3. npm${RESET}"
if command -v npm &> /dev/null; then
    echo -e "${GREEN}✅ npm $(npm --version)${RESET}"
else
    echo -e "${RED}❌ npm not found${RESET}"
    exit 1
fi

# Backend setup
echo -e "\n${BOLD}4. Backend Setup (FastAPI)${RESET}"
if [ -f "backend/requirements.txt" ]; then
    echo "Installing Python deps..."
    $PYTHON -m pip install -r backend/requirements.txt --break-system-packages -q 2>/dev/null || $PYTHON -m pip install -r backend/requirements.txt -q
    echo -e "${GREEN}✅ Backend ready${RESET}"
    
    # Test backend
    echo "Testing backend..."
    cd backend
    $PYTHON -m pytest app/tests/test_transliterator.py -q 2>&1 | tail -5
    cd ..
else
    echo -e "${RED}backend/requirements.txt missing${RESET}"
fi

# Frontend setup
echo -e "\n${BOLD}5. Frontend Setup (Next.js)${RESET}"
if [ -d "frontend" ]; then
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "Installing Node deps (this may take 1-2 minutes)..."
        npm install --silent
    else
        echo "node_modules exists, updating..."
        npm install --silent 2>&1 | tail -3
    fi
    
    echo "Testing frontend build..."
    npm run build 2>&1 | tail -10
    echo -e "${GREEN}✅ Frontend ready${RESET}"
    cd ..
else
    echo -e "${RED}frontend/ missing${RESET}"
fi

# Make run files executable
echo -e "\n${BOLD}6. Making runners executable${RESET}"
chmod +x run.py run.sh 2>/dev/null || true
chmod +x install.sh 2>/dev/null || true

echo -e "\n${GREEN}${BOLD}✅ Installation Complete!${RESET}"
echo ""
echo -e "${BOLD}To run:${RESET}"
echo -e "  ${SAFFRON}python3 run.py${RESET}          # Run both backend & frontend"
echo -e "  ${SAFFRON}./run.sh${RESET}               # Auto setup + run (Linux/macOS)"
echo -e "  ${SAFFRON}run.bat${RESET}               # Auto setup + run (Windows)"
echo ""
echo -e "${BOLD}URLs:${RESET}"
echo -e "  Backend:  http://localhost:8000/docs"
echo -e "  Frontend: http://localhost:3000"
echo -e "  Translate: http://localhost:3000/translate"
echo ""
echo -e "${BOLD}Matur suksma! 🙏${RESET}"
