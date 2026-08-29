#!/usr/bin/env python3
"""
Aksara Platform - Unified Runner
Menjalankan Backend FastAPI + Frontend Next.js sekaligus dalam satu file Python

Usage:
  python run.py              # Run both backend & frontend
  python run.py --install    # Install dependencies + run
  python run.py --backend-only
  python run.py --frontend-only
  python run.py --no-install --port-backend 8000 --port-frontend 3000

Fitur:
  - Auto-check Python & Node version
  - Auto-install backend (pip) & frontend (npm)
  - Concurrent run dengan process management
  - Graceful shutdown (Ctrl+C)
  - Colored logs dengan prefix [BACKEND] & [FRONTEND]
  - Health check & auto-open browser info

Branding: Aksara - Melestarikan Warisan, Menulis Masa Depan
"""

import os
import sys
import time
import signal
import argparse
import subprocess
import threading
import shutil
from pathlib import Path
from datetime import datetime

# === CONFIG ===
ROOT_DIR = Path(__file__).parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
BACKEND_PORT = 8000
FRONTEND_PORT = 3000

# Colors for terminal
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    SAFFRON = "\033[38;5;208m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    DIM = "\033[2m"

def log(prefix, message, color=Colors.RESET):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{Colors.DIM}[{timestamp}]{Colors.RESET} {color}[{prefix}]{Colors.RESET} {message}")

def banner():
    print(f"""
{Colors.SAFFRON}{Colors.BOLD}
   ___   _  __ _____   ___   ____   ___ 
  / _ | / |/ // ___/  / _ | / __ \\ / _ \\
 / __ |/    / \\__ \\  / __ |/ /_/ // , _/
/_/ |_/_/|_/ /____/ /_/ |_\\____//_/|_|

{Colors.RESET}{Colors.BOLD}Platform Belajar Aksara Bali{Colors.RESET}
{Colors.DIM}Melestarikan Warisan, Menulis Masa Depan
Ngajegang Warisan, Nyurat Masa Depan
ᬅᬓ᭄ᬱᬭ - ᬧ᭄ᬮᬢ᭄ᬨᭀᬃᬫ᭄ ᬩᭂᬮᬚᬃ ᬅᬓ᭄ᬱᬭ ᬩᬮᬶ{Colors.RESET}

{Colors.CYAN}Backend:{Colors.RESET}  FastAPI  → http://localhost:{BACKEND_PORT}  (docs: /docs)
{Colors.GREEN}Frontend:{Colors.RESET} Next.js  → http://localhost:{FRONTEND_PORT}
{Colors.YELLOW}Translate:{Colors.RESET} Latin ↔ Aksara Bali (95% akurasi, gantungan cerdas)

{Colors.DIM}Press Ctrl+C to stop both servers{Colors.RESET}
""")

def check_requirements():
    """Check Python & Node versions"""
    print(f"{Colors.BOLD}🔍 Checking requirements...{Colors.RESET}")
    
    # Python
    py_version = sys.version_info
    if py_version < (3, 9):
        log("CHECK", f"Python {py_version.major}.{py_version.minor} too old, need >=3.9", Colors.RED)
        return False
    log("CHECK", f"Python {py_version.major}.{py_version.minor}.{py_version.micro} ✅", Colors.GREEN)
    
    # Node
    if not shutil.which("node"):
        log("CHECK", "Node.js not found! Install from https://nodejs.org", Colors.RED)
        return False
    try:
        node_ver = subprocess.check_output(["node", "--version"], text=True).strip()
        log("CHECK", f"Node {node_ver} ✅", Colors.GREEN)
    except:
        log("CHECK", "Node check failed", Colors.YELLOW)
    
    # npm
    if not shutil.which("npm"):
        log("CHECK", "npm not found!", Colors.RED)
        return False
    try:
        npm_ver = subprocess.check_output(["npm", "--version"], text=True).strip()
        log("CHECK", f"npm {npm_ver} ✅", Colors.GREEN)
    except:
        pass
    
    # Check directories
    if not BACKEND_DIR.exists():
        log("CHECK", f"Backend dir not found: {BACKEND_DIR}", Colors.RED)
        return False
    if not FRONTEND_DIR.exists():
        log("CHECK", f"Frontend dir not found: {FRONTEND_DIR}", Colors.RED)
        return False
    
    log("CHECK", "All requirements OK ✅", Colors.GREEN)
    return True

def install_backend():
    """Install backend dependencies"""
    log("BACKEND", "Installing Python dependencies...", Colors.BLUE)
    req_file = BACKEND_DIR / "requirements.txt"
    if not req_file.exists():
        log("BACKEND", "requirements.txt not found!", Colors.RED)
        return False
    
    try:
        # Try with --break-system-packages for PEP 668 systems
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file), "--break-system-packages", "-q"]
        result = subprocess.run(cmd, cwd=ROOT_DIR)
        if result.returncode != 0:
            # Fallback without break-system-packages
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file), "-q"]
            result = subprocess.run(cmd, cwd=ROOT_DIR)
        
        if result.returncode == 0:
            log("BACKEND", "Dependencies installed ✅", Colors.GREEN)
            return True
        else:
            log("BACKEND", "Failed to install backend deps", Colors.RED)
            return False
    except Exception as e:
        log("BACKEND", f"Install error: {e}", Colors.RED)
        return False

def install_frontend():
    """Install frontend dependencies"""
    log("FRONTEND", "Installing Node dependencies (npm install)...", Colors.BLUE)
    try:
        # Check if node_modules exists
        if (FRONTEND_DIR / "node_modules").exists():
            log("FRONTEND", "node_modules exists, skipping npm install (use --force-install to reinstall)", Colors.YELLOW)
            return True
        
        cmd = ["npm", "install", "--silent"]
        result = subprocess.run(cmd, cwd=FRONTEND_DIR, shell=os.name == 'nt')
        if result.returncode == 0:
            log("FRONTEND", "Dependencies installed ✅", Colors.GREEN)
            return True
        else:
            log("FRONTEND", "npm install failed", Colors.RED)
            return False
    except Exception as e:
        log("FRONTEND", f"Install error: {e}", Colors.RED)
        return False

class ProcessLogger(threading.Thread):
    """Thread to log process output with prefix"""
    def __init__(self, process, prefix, color):
        super().__init__(daemon=True)
        self.process = process
        self.prefix = prefix
        self.color = color
    
    def run(self):
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    # Clean and print
                    clean = line.rstrip()
                    if clean:
                        print(f"{self.color}[{self.prefix}]{Colors.RESET} {clean}")
        except:
            pass

def run_backend(port):
    """Start FastAPI backend"""
    log("BACKEND", f"Starting FastAPI on port {port}...", Colors.BLUE)
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--reload",
        "--reload-dir", str(BACKEND_DIR / "app")
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            cwd=BACKEND_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        logger = ProcessLogger(process, "BACKEND", Colors.BLUE)
        logger.start()
        return process
    except Exception as e:
        log("BACKEND", f"Failed to start: {e}", Colors.RED)
        return None

def run_frontend(port, backend_port):
    """Start Next.js frontend"""
    log("FRONTEND", f"Starting Next.js on port {port}...", Colors.GREEN)
    
    env = os.environ.copy()
    env["PORT"] = str(port)
    env["NEXT_PUBLIC_API_URL"] = f"http://localhost:{backend_port}/api"
    env["BROWSER"] = "none"  # Don't auto-open browser from Next
    
    cmd = ["npm", "run", "dev", "--", "-p", str(port)]
    
    try:
        process = subprocess.Popen(
            cmd,
            cwd=FRONTEND_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=os.name == 'nt'
        )
        logger = ProcessLogger(process, "FRONTEND", Colors.GREEN)
        logger.start()
        return process
    except Exception as e:
        log("FRONTEND", f"Failed to start: {e}", Colors.RED)
        return None

def main():
    parser = argparse.ArgumentParser(description="Aksara Platform Unified Runner")
    parser.add_argument("--install", action="store_true", help="Install dependencies before running")
    parser.add_argument("--force-install", action="store_true", help="Force reinstall dependencies")
    parser.add_argument("--backend-only", action="store_true", help="Run backend only")
    parser.add_argument("--frontend-only", action="store_true", help="Run frontend only")
    parser.add_argument("--port-backend", type=int, default=BACKEND_PORT, help="Backend port")
    parser.add_argument("--port-frontend", type=int, default=FRONTEND_PORT, help="Frontend port")
    parser.add_argument("--no-install", action="store_true", help="Skip installation check")
    parser.add_argument("--skip-check", action="store_true", help="Skip requirements check")
    
    args = parser.parse_args()
    
    banner()
    
    if not args.skip_check:
        if not check_requirements():
            log("MAIN", "Requirements check failed. Install Node.js & Python 3.9+", Colors.RED)
            sys.exit(1)
    
    # Install if requested
    if args.install or args.force_install:
        if args.force_install:
            # Remove node_modules for fresh install
            nm = FRONTEND_DIR / "node_modules"
            if nm.exists():
                log("MAIN", "Removing old node_modules for fresh install...", Colors.YELLOW)
                shutil.rmtree(nm, ignore_errors=True)
        
        print(f"\n{Colors.BOLD}📦 Installing dependencies...{Colors.RESET}")
        if not args.frontend_only:
            if not install_backend():
                sys.exit(1)
        if not args.backend_only:
            if not install_frontend():
                sys.exit(1)
        print()
    elif not args.no_install:
        # Auto-check if node_modules exists
        if not args.backend_only and not (FRONTEND_DIR / "node_modules").exists():
            log("MAIN", "Frontend dependencies not found, installing...", Colors.YELLOW)
            install_frontend()
    
    # Setup signal handling
    processes = []
    
    def signal_handler(sig, frame):
        log("MAIN", "\n🛑 Shutting down servers...", Colors.YELLOW)
        for p in processes:
            try:
                if p.poll() is None:
                    # Try graceful first
                    if os.name == 'nt':
                        p.terminate()
                    else:
                        p.send_signal(signal.SIGTERM)
                    # Wait a bit, then kill
                    try:
                        p.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        p.kill()
            except:
                pass
        log("MAIN", "All servers stopped. Matur suksma! 🙏", Colors.GREEN)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start servers
    backend_process = None
    frontend_process = None
    
    if not args.frontend_only:
        backend_process = run_backend(args.port_backend)
        if backend_process:
            processes.append(backend_process)
            log("MAIN", f"Backend PID {backend_process.pid} → http://localhost:{args.port_backend}/docs", Colors.BLUE)
        else:
            log("MAIN", "Backend failed to start!", Colors.RED)
            sys.exit(1)
    
    # Wait a bit for backend to start
    if not args.frontend_only and not args.backend_only:
        log("MAIN", "Waiting 3s for backend to warm up...", Colors.DIM)
        time.sleep(3)
    
    if not args.backend_only:
        frontend_process = run_frontend(args.port_frontend, args.port_backend)
        if frontend_process:
            processes.append(frontend_process)
            log("MAIN", f"Frontend PID {frontend_process.pid} → http://localhost:{args.port_frontend}", Colors.GREEN)
        else:
            log("MAIN", "Frontend failed to start!", Colors.RED)
            # Kill backend if frontend fails
            for p in processes:
                try:
                    p.terminate()
                except:
                    pass
            sys.exit(1)
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}✅ Aksara Platform is running!{Colors.RESET}")
    print(f"{Colors.CYAN}   Backend:{Colors.RESET}  http://localhost:{args.port_backend}  (API docs: http://localhost:{args.port_backend}/docs)")
    print(f"{Colors.GREEN}   Frontend:{Colors.RESET} http://localhost:{args.port_frontend}")
    print(f"{Colors.YELLOW}   Translate:{Colors.RESET} http://localhost:{args.port_frontend}/translate")
    print(f"{Colors.SAFFRON}   Learn:{Colors.RESET}     http://localhost:{args.port_frontend}/learn")
    print(f"{Colors.DIM}\n   Logs: [BACKEND] = FastAPI, [FRONTEND] = Next.js")
    print(f"   Press Ctrl+C to stop both servers{Colors.RESET}\n")
    
    # Monitor processes
    try:
        while True:
            # Check if any process died
            for p in processes:
                if p.poll() is not None:
                    # Process died
                    if p == backend_process:
                        log("MAIN", f"Backend process died with code {p.returncode}! Restarting? (Ctrl+C to stop)", Colors.RED)
                    else:
                        log("MAIN", f"Frontend process died with code {p.returncode}!", Colors.RED)
                    # For MVP, just exit and let user restart
                    # Could add auto-restart logic here
                    signal_handler(None, None)
            
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
