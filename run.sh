#!/bin/bash
# Aksara Platform - Auto Setup & Run (Linux / macOS)
# Menyiapkan instalasi dan menjalankan backend + frontend sekaligus
# Usage: ./run.sh  atau  bash run.sh  atau  ./run.sh --install

set -e

# Colors
SAFFRON='\033[38;5;208m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

echo -e "${SAFFRON}${BOLD}"
cat << "EOF"
   ___   _  __ _____   ___   ____   ___
  / _ | / |/ // ___/  / _ | / __ \ / _ \
 / __ |/    / \__ \  / __ |/ /_/ // , _/
/_/ |_/_/|_/ /____/ /_/ |_\____//_/|_|

EOF
echo -e "${RESET}${BOLD}Platform Belajar Aksara Bali - Auto Setup${RESET}"
echo -e "${DIM}ᬅᬓ᭄ᬱᬭ - Melestarikan Warisan, Menulis Masa Depan${RESET}"
echo ""

# Check if we're in correct dir
if [ ! -f "run.py" ]; then
    echo -e "${RED}❌ run.py not found! Run this script from repository root (where run.py exists)${RESET}"
    exit 1
fi

# Function to check command
check_cmd() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✅ $1 $( $1 --version 2>&1 | head -n1 )${RESET}"
        return 0
    else
        echo -e "${RED}❌ $1 not found!${RESET}"
        return 1
    fi
}

echo -e "${BOLD}🔍 Checking requirements...${RESET}"
MISSING=0

# Python
if ! check_cmd python3; then
    if command -v python &> /dev/null; then
        echo -e "${GREEN}✅ python $(python --version)${RESET}"
    else
        echo -e "${RED}Please install Python 3.9+ from https://python.org${RESET}"
        MISSING=1
    fi
fi

# Node
if ! check_cmd node; then
    echo -e "${RED}Please install Node.js 18+ from https://nodejs.org${RESET}"
    MISSING=1
fi

# npm
if ! check_cmd npm; then
    echo -e "${RED}Please install npm (comes with Node.js)${RESET}"
    MISSING=1
fi

if [ $MISSING -eq 1 ]; then
    echo -e "${RED}❌ Missing requirements. Please install them first.${RESET}"
    exit 1
fi

echo ""
echo -e "${BOLD}📦 Installing dependencies...${RESET}"

# Backend
echo -e "${BLUE}→ Backend: pip install -r backend/requirements.txt${RESET}"
if [ -f "backend/requirements.txt" ]; then
    # Try with venv if exists, else system
    if [ -d "venv" ]; then
        echo -e "${DIM}Using venv...${RESET}"
        source venv/bin/activate
        pip install -r backend/requirements.txt -q --break-system-packages 2>/dev/null || pip install -r backend/requirements.txt -q
    else
        pip3 install -r backend/requirements.txt -q --break-system-packages 2>/dev/null || pip3 install -r backend/requirements.txt -q || pip install -r backend/requirements.txt -q
    fi
    echo -e "${GREEN}✅ Backend installed${RESET}"
else
    echo -e "${RED}backend/requirements.txt not found!${RESET}"
fi

# Frontend
echo -e "${GREEN}→ Frontend: npm install${RESET}"
if [ -d "frontend" ]; then
    cd frontend
    if [ ! -d "node_modules" ] || [[ "$*" == *"--force-install"* ]]; then
        npm install --silent
        echo -e "${GREEN}✅ Frontend installed${RESET}"
    else
        echo -e "${YELLOW}⏩ node_modules exists, skipping (use --force-install to reinstall)${RESET}"
    fi
    cd ..
else
    echo -e "${RED}frontend/ not found!${RESET}"
fi

echo ""
echo -e "${BOLD}${GREEN}✅ Setup complete! Starting servers...${RESET}"
echo -e "${DIM}Backend: http://localhost:8000/docs"
echo -e "Frontend: http://localhost:3000${RESET}"
echo ""

# Run the Python unified runner
# Pass all args to run.py
if command -v python3 &> /dev/null; then
    python3 run.py --no-install "$@"
else
    python run.py --no-install "$@"
fi
