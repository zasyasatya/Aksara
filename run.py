#!/usr/bin/env python3
"""
Aksara launcher - menjalankan seluruh platform tanpa Docker.

    python run.py                 siapkan semuanya, lalu layani aplikasi
    python run.py --build         paksa build ulang UI statis, lalu layani aplikasi
    python run.py --backend-only  API saja (tanpa build UI)
    python run.py --dev           FastAPI + Next.js dev server (hot reload)
    python run.py --port 9000     layani aplikasi pada port lain
    python run.py --check         diagnosis lingkungan, lalu keluar

Python 3.10+ adalah satu-satunya syarat wajib. Node.js bersifat opsional:
tanpanya, Aksara tetap menjalankan API dan dapat melayani UI yang telah dibuild
sebelumnya. Skrip ini hanya memakai standard library agar dapat dijalankan
sebelum dependensi proyek dipasang.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import venv
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
STATIC = BACKEND / "app" / "static"
VENV = ROOT / ".venv"
REQUIREMENTS = BACKEND / "requirements.txt"
DEPS_STAMP = VENV / ".aksara-requirements.sha256"
NPM_STAMP = FRONTEND / "node_modules" / ".aksara-lock.sha256"

MIN_PY: Tuple[int, int] = (3, 10)
MIN_NODE_MAJOR = 18
DEFAULT_API_PORT = 8000
DEFAULT_FRONTEND_PORT = 3000

IS_WIN = os.name == "nt"
G, Y, R, B, DIM, RESET = (
    "\033[32m",
    "\033[33m",
    "\033[31m",
    "\033[34m",
    "\033[2m",
    "\033[0m",
)
# Older Windows consoles print ANSI escape codes literally. Windows Terminal,
# modern cmd.exe, and PowerShell support them, so keep colours there.
if IS_WIN and not (
    os.environ.get("WT_SESSION")
    or os.environ.get("ANSICON")
    or os.environ.get("TERM")
):
    G = Y = R = B = DIM = RESET = ""


# ---------------------------------------------------------------------------
# Console and process helpers
# ---------------------------------------------------------------------------
def say(message: str, colour: str = "") -> None:
    print("{}{}{}".format(colour, message, RESET), flush=True)


def step(number: int, total: int, message: str) -> None:
    say("\n[{}/{}] {}".format(number, total, message), B)


def command_text(command: Sequence[Union[str, Path]]) -> str:
    return " ".join(str(part) for part in command)


def run(
    command: Sequence[Union[str, Path]],
    cwd: Optional[Path] = None,
    check: bool = True,
    quiet: bool = False,
    env: Optional[Dict[str, str]] = None,
) -> int:
    """Run a command and stream its output unless ``quiet`` is requested."""
    cmd = [str(part) for part in command]
    printable = command_text(cmd)
    say("  $ {}".format(printable), DIM)

    kwargs: Dict[str, object] = {
        "cwd": str(cwd) if cwd else None,
        "env": env,
    }
    if quiet:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.STDOUT

    try:
        completed = subprocess.run(cmd, **kwargs)
    except FileNotFoundError:
        if check:
            raise SystemExit("{}Command not found: {}{}".format(R, cmd[0], RESET))
        return 127

    if check and completed.returncode != 0:
        raise SystemExit(
            "{}Command failed ({}): {}{}".format(
                R, completed.returncode, printable, RESET
            )
        )
    return completed.returncode


def have(binary: str) -> Optional[str]:
    """Find a command, including Windows' ``.cmd`` shims for npm."""
    candidates = (binary, "{}.cmd".format(binary)) if IS_WIN else (binary,)
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
    return None


def command_output(command: Sequence[Union[str, Path]]) -> str:
    """Return a command's stdout, or an empty string when it cannot run."""
    try:
        completed = subprocess.run(
            [str(part) for part in command],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
    except OSError:
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""


def valid_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("port must be a number")
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


# ---------------------------------------------------------------------------
# Environment and Python dependencies
# ---------------------------------------------------------------------------
def check_project_layout() -> None:
    required = (
        (BACKEND / "app" / "main.py", "backend/app/main.py"),
        (REQUIREMENTS, "backend/requirements.txt"),
        (FRONTEND / "package.json", "frontend/package.json"),
    )
    missing = [label for path, label in required if not path.is_file()]
    if missing:
        raise SystemExit(
            "{}Project files missing: {}. Run this command from the Aksara "
            "repository root.{}".format(R, ", ".join(missing), RESET)
        )


def check_python() -> None:
    """Validate the interpreter that is *already running this file*.

    We intentionally do not use ``which python`` here. If this script has
    started, Python is installed and usable; checking a separate PATH alias is
    what produced false "Python not found" errors on Windows machines that use
    the ``py`` launcher.
    """
    version = sys.version_info
    if version[:2] < MIN_PY:
        raise SystemExit(
            "{}Python {}.{}+ is required; this launcher is running on {}.{}.{}\n"
            "Install a newer Python from https://python.org/downloads and run "
            "the command again.{}".format(
                R,
                MIN_PY[0],
                MIN_PY[1],
                version.major,
                version.minor,
                version.micro,
                RESET,
            )
        )


def venv_bin(name: str) -> Path:
    """Return an executable path inside the project virtual environment."""
    if IS_WIN:
        return VENV / "Scripts" / "{}.exe".format(name)
    return VENV / "bin" / name


def ensure_venv() -> Path:
    """Create a local virtual environment when needed and return its Python."""
    python = venv_bin("python")
    if python.is_file():
        say("  virtual environment ready  {}{}{}".format(DIM, VENV, RESET), G)
        return python

    # A venv copied from another operating system or interrupted during setup
    # has the directory but not the correct interpreter. Repair it instead of
    # later reporting an unrelated pip/Python error.
    if VENV.exists():
        say("  repairing incomplete virtual environment ...", Y)
        if VENV.is_dir():
            shutil.rmtree(VENV)
        else:
            VENV.unlink()

    say("  creating virtual environment (.venv) ...")
    try:
        venv.EnvBuilder(with_pip=True, clear=False).create(str(VENV))
    except Exception as exc:
        raise SystemExit(
            "{}Could not create .venv: {}\n"
            "On Debian/Ubuntu install the venv package first: "
            "sudo apt install python3-venv{}".format(R, exc, RESET)
        )

    if not python.is_file():
        raise SystemExit(
            "{}Virtual environment was created but its Python interpreter is missing.{}".format(
                R, RESET
            )
        )
    say("  virtual environment created", G)
    return python


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def stamp_matches(path: Path, expected: str) -> bool:
    try:
        return path.read_text(encoding="utf-8").strip() == expected
    except OSError:
        return False


def runtime_dependencies_available(python: Path) -> bool:
    """Check imports required by the FastAPI application without importing it."""
    if not python.is_file():
        return False
    probe = "import fastapi, uvicorn, pydantic, pydantic_settings, multipart"
    try:
        completed = subprocess.run(
            [str(python), "-c", probe],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False
    return completed.returncode == 0


def dependencies_installed(python: Path) -> bool:
    """True when imports work and requirements have not changed since install."""
    try:
        requirements_digest = file_hash(REQUIREMENTS)
    except OSError:
        return False
    return runtime_dependencies_available(python) and stamp_matches(
        DEPS_STAMP, requirements_digest
    )


def install_dependencies(python: Path, force: bool = False) -> None:
    if not force and dependencies_installed(python):
        say("  Python dependencies are up to date", G)
        return

    say("  installing Python dependencies (first run may take a minute) ...")
    # This runs inside .venv, so no --break-system-packages workaround or
    # global Python installation is needed.
    run(
        [
            python,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
            "--disable-pip-version-check",
            "--quiet",
        ],
        check=False,
    )
    run(
        [
            python,
            "-m",
            "pip",
            "install",
            "-r",
            REQUIREMENTS,
            "--disable-pip-version-check",
        ]
    )

    if not runtime_dependencies_available(python):
        raise SystemExit(
            "{}Dependencies were installed but required imports still fail. "
            "Try: python run.py --reinstall{}".format(R, RESET)
        )
    DEPS_STAMP.write_text(file_hash(REQUIREMENTS), encoding="utf-8")
    say("  Python dependencies installed", G)


# ---------------------------------------------------------------------------
# Frontend build
# ---------------------------------------------------------------------------
def ui_present() -> bool:
    return (STATIC / "index.html").is_file()


BUILD_STAMP = STATIC / ".build-stamp"

# Sources whose contents affect the static export. Build products and
# node_modules are intentionally excluded.
SOURCE_DIRECTORIES = ("app", "components", "lib", "public")
SOURCE_FILES = (
    "package.json",
    "package-lock.json",
    "next.config.js",
    "tailwind.config.ts",
    "tsconfig.json",
    "postcss.config.js",
)
LESSON_CATALOG = BACKEND / "app" / "data" / "lessons.json"


def source_fingerprint() -> str:
    """Create a content hash of all frontend source and generated route input."""
    digest = hashlib.sha256()
    paths: List[Path] = [FRONTEND / filename for filename in SOURCE_FILES]

    for directory in SOURCE_DIRECTORIES:
        source_root = FRONTEND / directory
        if source_root.is_dir():
            paths.extend(path for path in source_root.rglob("*") if path.is_file())

    # The lesson catalogue determines static pages for /learn/[id].
    if LESSON_CATALOG.is_file():
        paths.append(LESSON_CATALOG)

    for path in sorted(paths, key=lambda item: str(item)):
        if not path.is_file():
            continue
        try:
            digest.update(str(path.relative_to(ROOT)).encode("utf-8"))
            digest.update(path.read_bytes())
        except OSError:
            # A file changing while a build starts should make the next start
            # rebuild rather than crash the launcher.
            continue
    return digest.hexdigest()


def ui_stale() -> bool:
    """Return True when the static UI does not match its source files."""
    if not ui_present():
        return True
    try:
        return BUILD_STAMP.read_text(encoding="utf-8").strip() != source_fingerprint()
    except OSError:
        return True


def node_version() -> Tuple[Optional[str], Optional[int]]:
    node = have("node")
    if not node:
        return None, None
    version = command_output([node, "--version"])
    try:
        major = int(version.lstrip("vV").split(".", 1)[0])
    except (ValueError, IndexError):
        major = None
    return version or None, major


def frontend_tools_available(show_error: bool = True) -> bool:
    node, major = node_version()
    npm = have("npm")
    if not node or not npm:
        if show_error:
            say("  Node.js/npm not found - skipping the web UI build.", Y)
            say(
                "    The API will still run. Install Node {}+ from https://nodejs.org "
                "to build the interface.".format(MIN_NODE_MAJOR),
                Y,
            )
        return False
    if major is None or major < MIN_NODE_MAJOR:
        if show_error:
            say(
                "  Node {} is too old; Node {}+ is required to build the UI.".format(
                    node, MIN_NODE_MAJOR
                ),
                R,
            )
        return False
    return True


def frontend_dependency_hash() -> str:
    lockfile = FRONTEND / "package-lock.json"
    return file_hash(lockfile if lockfile.is_file() else FRONTEND / "package.json")


def frontend_dependencies_installed() -> bool:
    node_modules = FRONTEND / "node_modules"
    if not node_modules.is_dir():
        return False
    try:
        return stamp_matches(NPM_STAMP, frontend_dependency_hash())
    except OSError:
        return False


def ensure_frontend_dependencies(force: bool = False) -> bool:
    """Install npm dependencies when absent or when the lockfile changed."""
    if not frontend_tools_available():
        return False

    npm = have("npm")
    assert npm is not None  # guarded by frontend_tools_available

    if not force and frontend_dependencies_installed():
        say("  npm packages are up to date", G)
        return True

    lockfile = FRONTEND / "package-lock.json"
    if force and (FRONTEND / "node_modules").is_dir():
        say("  reinstalling npm packages ...", Y)
    elif (FRONTEND / "node_modules").is_dir():
        say("  package lock changed - synchronising npm packages ...", Y)
    else:
        say("  installing npm packages (first run may take a few minutes) ...")

    # npm ci is reproducible. A stale hand-edited lockfile should not block a
    # local launch forever, so fall back to npm install with a visible message.
    if lockfile.is_file():
        status = run([npm, "ci"], cwd=FRONTEND, check=False)
        if status != 0:
            say("  npm ci failed; falling back to npm install", Y)
            run([npm, "install"], cwd=FRONTEND)
    else:
        run([npm, "install"], cwd=FRONTEND)

    if not (FRONTEND / "node_modules").is_dir():
        say("  npm finished but node_modules is missing", R)
        return False
    NPM_STAMP.write_text(frontend_dependency_hash(), encoding="utf-8")
    say("  npm packages installed", G)
    return True


def build_frontend(force: bool = False, force_packages: bool = False) -> bool:
    """Export Next.js to ``backend/app/static``. Return whether a UI is usable."""
    if ui_present() and not force and not force_packages:
        if not ui_stale():
            say("  UI bundle is up to date", G)
            return True
        if not frontend_tools_available(show_error=False):
            say("  UI bundle is OUT OF DATE and Node.js is not installed.", Y)
            say("    Serving the previous build; new UI pages may be unavailable.", Y)
            say("    Install Node.js, then run: python run.py --build", Y)
            return True
        say("  source changed since the last build - recompiling", Y)

    if not frontend_tools_available():
        return False
    if not ensure_frontend_dependencies(force=force_packages):
        return False

    node, _ = node_version()
    npm = have("npm")
    assert npm is not None
    npm_version = command_output([npm, "--version"])
    say("  node {}, npm {}".format(node or "unknown", npm_version or "unknown"))
    say("  building the Next.js static export ...")

    build_env = dict(os.environ)
    build_env.update(
        {
            "BUILD_EXPORT": "1",
            "NEXT_TELEMETRY_DISABLED": "1",
            # Keep browser API calls same-origin. FastAPI serves /api when the
            # exported files are copied into backend/app/static.
            "NEXT_PUBLIC_API_URL": "/api",
        }
    )
    if run([npm, "run", "build"], cwd=FRONTEND, check=False, env=build_env) != 0:
        say("  frontend build failed - continuing with the API only.", R)
        return False

    output = FRONTEND / "out"
    if not (output / "index.html").is_file():
        say("  build produced no static export at {}".format(output), R)
        return False

    if STATIC.exists():
        if STATIC.is_dir():
            shutil.rmtree(STATIC)
        else:
            STATIC.unlink()
    shutil.copytree(output, STATIC)
    try:
        BUILD_STAMP.write_text(source_fingerprint(), encoding="utf-8")
    except OSError:
        # The exported UI is still valid; it will simply be rebuilt next time.
        pass
    say("  UI compiled into {}".format(STATIC.relative_to(ROOT)), G)
    return True


# ---------------------------------------------------------------------------
# Serving
# ---------------------------------------------------------------------------
def display_host(host: str) -> str:
    return "localhost" if host in ("0.0.0.0", "127.0.0.1", "::") else host


def server_environment(has_ui: bool) -> Dict[str, str]:
    environment = dict(os.environ)
    environment["PYTHONUNBUFFERED"] = "1"
    # app.main reads this before mounting static files. It keeps --backend-only
    # truly API-only even if an older static bundle is present on disk.
    environment["AKSARA_SERVE_UI"] = "1" if has_ui else "0"
    return environment


def serve(
    python: Path,
    host: str,
    port: int,
    reload: bool,
    has_ui: bool,
) -> None:
    shown = display_host(host)
    say("\n" + "=" * 62, G)
    say("  Aksara is starting", G)
    say("=" * 62, G)
    if has_ui:
        say("  Web app   http://{}:{}".format(shown, port))
        say("  Translate http://{}:{}/translate".format(shown, port))
    else:
        say("  API only  http://{}:{}   (no UI bundle)".format(shown, port), Y)
    say("  API docs  http://{}:{}/docs".format(shown, port))
    say("  Health    http://{}:{}/api/health".format(shown, port))
    say("\n  Stop with Ctrl+C", DIM)
    say("=" * 62 + "\n", G)

    command: List[Union[str, Path]] = [
        python,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        command.append("--reload")

    try:
        status = run(
            command,
            cwd=BACKEND,
            check=False,
            env=server_environment(has_ui),
        )
    except KeyboardInterrupt:
        say("\nAksara stopped.", Y)
        return
    if status:
        raise SystemExit("{}Server stopped with exit code {}.{}".format(R, status, RESET))


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def next_environment(api_port: int) -> Dict[str, str]:
    environment = dict(os.environ)
    environment.update(
        {
            "NEXT_TELEMETRY_DISABLED": "1",
            # The browser always requests /api from the Next.js origin. The
            # rewrite target remains inside this machine, never the visitor's
            # localhost address.
            "NEXT_PUBLIC_API_URL": "/api",
            "AKSARA_BACKEND_URL": "http://127.0.0.1:{}".format(api_port),
        }
    )
    return environment


def serve_dev(python: Path, host: str, api_port: int, frontend_port: int) -> None:
    """Run FastAPI and the Next.js development server with hot reload."""
    if not ensure_frontend_dependencies():
        raise SystemExit(
            "{}--dev needs Node.js {}+ and npm.{}".format(R, MIN_NODE_MAJOR, RESET)
        )
    npm = have("npm")
    assert npm is not None

    shown = display_host(host)
    say("\n" + "=" * 62, G)
    say("  Aksara development mode", G)
    say("=" * 62, G)
    say("  UI (hot reload)  http://{}:{}  <- use this URL".format(shown, frontend_port))
    say("  API              http://{}:{}".format(shown, api_port))
    say("  API docs         http://{}:{}/docs".format(shown, api_port))
    say("\n  Stop with Ctrl+C", DIM)
    say("=" * 62 + "\n", G)

    api = subprocess.Popen(
        [
            str(python),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            host,
            "--port",
            str(api_port),
            "--reload",
        ],
        cwd=str(BACKEND),
        env=server_environment(False),
    )
    try:
        status = run(
            [npm, "run", "dev", "--", "--hostname", host, "--port", str(frontend_port)],
            cwd=FRONTEND,
            check=False,
            env=next_environment(api_port),
        )
        if status:
            raise SystemExit(
                "{}Next.js dev server stopped with exit code {}.{}".format(
                    R, status, RESET
                )
            )
    except KeyboardInterrupt:
        pass
    finally:
        stop_process(api)
        say("\nAksara stopped.", Y)


def serve_frontend_only(host: str, api_port: int, frontend_port: int) -> None:
    """Keep the legacy --frontend-only mode for a separately running API."""
    if not ensure_frontend_dependencies():
        raise SystemExit(
            "{}--frontend-only needs Node.js {}+ and npm.{}".format(
                R, MIN_NODE_MAJOR, RESET
            )
        )
    npm = have("npm")
    assert npm is not None
    shown = display_host(host)
    say("\nFrontend-only mode: http://{}:{}".format(shown, frontend_port), G)
    say(
        "The API proxy expects an API already running at http://127.0.0.1:{}".format(
            api_port
        ),
        Y,
    )
    try:
        status = run(
            [npm, "run", "dev", "--", "--hostname", host, "--port", str(frontend_port)],
            cwd=FRONTEND,
            check=False,
            env=next_environment(api_port),
        )
    except KeyboardInterrupt:
        say("\nAksara stopped.", Y)
        return
    if status:
        raise SystemExit(
            "{}Next.js dev server stopped with exit code {}.{}".format(R, status, RESET)
        )


# ---------------------------------------------------------------------------
# Diagnosis and command-line interface
# ---------------------------------------------------------------------------
def diagnose() -> None:
    say("Aksara environment check\n", B)
    ok = True

    version = sys.version_info
    good_python = version[:2] >= MIN_PY
    ok = ok and good_python
    say(
        "  {}  Python {}.{}.{}{}".format(
            "PASS" if good_python else "FAIL",
            version.major,
            version.minor,
            version.micro,
            "" if good_python else "  (need {}.{})".format(*MIN_PY),
        ),
        G if good_python else R,
    )
    say("  ....  Interpreter {}".format(sys.executable), DIM)
    say("  ....  Platform {} {}".format(platform.system(), platform.machine()), DIM)

    node, major = node_version()
    if node:
        node_status = major is not None and major >= MIN_NODE_MAJOR
        say(
            "  {}  Node {}{}".format(
                "PASS" if node_status else "WARN",
                node,
                "" if node_status else "  (need {}+ to build UI)".format(MIN_NODE_MAJOR),
            ),
            G if node_status else Y,
        )
    else:
        say("  WARN  Node.js not found - API still works; UI cannot be rebuilt", Y)

    npm = have("npm")
    if npm:
        say("  PASS  npm {}".format(command_output([npm, "--version"]) or "available"), G)
    else:
        say("  WARN  npm not found - UI cannot be rebuilt", Y)

    venv_python = venv_bin("python")
    if venv_python.is_file():
        if dependencies_installed(venv_python):
            say("  PASS  virtualenv and Python dependencies are ready", G)
        elif runtime_dependencies_available(venv_python):
            say("  WARN  dependencies import correctly but need synchronising", Y)
        else:
            say("  WARN  virtualenv exists but Python dependencies are missing", Y)
    elif VENV.exists():
        say("  WARN  virtualenv is incomplete and will be repaired on launch", Y)
    else:
        say("  ....  virtualenv will be created on first run", DIM)

    if not ui_present():
        say("  WARN  UI bundle not built", Y)
    elif ui_stale():
        say("  WARN  UI bundle is stale - run: python run.py --build", Y)
    else:
        say("  PASS  UI bundle is up to date", G)

    layout = (
        (BACKEND / "app" / "main.py", "backend/app/main.py"),
        (REQUIREMENTS, "backend/requirements.txt"),
        (FRONTEND / "package.json", "frontend/package.json"),
    )
    missing = [label for path, label in layout if not path.is_file()]
    if missing:
        ok = False
        say("  FAIL  Missing project files: {}".format(", ".join(missing)), R)

    if IS_WIN:
        say("\n  Tip: run.bat automatically tries py -3, python, and python3.", DIM)
    say(
        "\n  {}".format(
            "Ready. Run: python run.py" if ok else "Fix the FAIL items above."
        ),
        G if ok else R,
    )


def banner() -> None:
    say("=" * 62, B)
    say("  Aksara - Platform Belajar Aksara Bali", B)
    say("  ᬅᬓ᭄ᬱᬭ  •  Melestarikan Warisan, Menulis Masa Depan", B)
    say("=" * 62, B)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Aksara without Docker.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--backend-only", action="store_true", help="run only the FastAPI API")
    modes.add_argument(
        "--frontend-only",
        action="store_true",
        help="run only Next.js dev server (expects a separate API)",
    )
    parser.add_argument("--build", action="store_true", help="force a static UI rebuild")
    parser.add_argument("--dev", action="store_true", help="run FastAPI + Next.js with hot reload")
    parser.add_argument("--check", action="store_true", help="diagnose the environment and exit")
    parser.add_argument("--reinstall", action="store_true", help="reinstall Python dependencies")
    parser.add_argument(
        "--install-only",
        action="store_true",
        help="install dependencies/build UI, then exit without serving",
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="do not install missing dependencies (legacy compatibility)",
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="bind address (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        "--port-backend",
        dest="port",
        type=valid_port,
        default=DEFAULT_API_PORT,
        help="API / production web port (default: {})".format(DEFAULT_API_PORT),
    )
    parser.add_argument(
        "--frontend-port",
        "--port-frontend",
        dest="frontend_port",
        type=valid_port,
        default=DEFAULT_FRONTEND_PORT,
        help="Next.js dev port (default: {})".format(DEFAULT_FRONTEND_PORT),
    )

    # Existing shortcuts from the first launcher remain accepted. Normal
    # launches already install what is missing; --install explicitly refreshes
    # Python requirements and --force-install also refreshes npm packages.
    parser.add_argument("--install", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--force-install", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--skip-check", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args()
    if args.build and args.backend_only:
        parser.error("--build cannot be used with --backend-only")
    if args.build and (args.dev or args.frontend_only):
        parser.error("--build creates the production static UI; omit --dev/--frontend-only")
    return args


def main() -> None:
    args = parse_arguments()
    check_python()
    check_project_layout()

    if args.check:
        diagnose()
        return

    banner()
    force_packages = bool(args.force_install)
    reinstall = bool(args.install or args.reinstall or args.force_install)

    # --frontend-only only needs the Python interpreter that already launched
    # this file; it deliberately avoids creating an unused backend venv.
    if args.frontend_only:
        total = 3
        step(1, total, "Checking Python")
        say(
            "  Python {}.{}.{} on {}".format(
                sys.version_info.major,
                sys.version_info.minor,
                sys.version_info.micro,
                platform.system(),
            ),
            G,
        )
        step(2, total, "Preparing the web interface")
        if args.no_install:
            if not (FRONTEND / "node_modules").is_dir():
                raise SystemExit(
                    "{}npm packages are missing; remove --no-install to install them.{}".format(
                        R, RESET
                    )
                )
        elif not ensure_frontend_dependencies(force=force_packages):
            raise SystemExit(
                "{}Could not prepare the frontend. Install Node.js {}+ and npm.{}".format(
                    R, MIN_NODE_MAJOR, RESET
                )
            )
        if args.install_only:
            say("\nAksara frontend dependencies are ready.", G)
            return
        step(3, total, "Starting Next.js")
        serve_frontend_only(args.host, args.port, args.frontend_port)
        return

    total = 3 if args.backend_only else 4
    step(1, total, "Checking Python")
    say(
        "  Python {}.{}.{} on {}".format(
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
            platform.system(),
        ),
        G,
    )

    step(2, total, "Preparing the virtual environment")
    python = ensure_venv()
    if args.no_install:
        if not runtime_dependencies_available(python):
            raise SystemExit(
                "{}Python dependencies are missing; remove --no-install to install them.{}".format(
                    R, RESET
                )
            )
        say("  using existing Python dependencies", G)
    else:
        install_dependencies(python, force=reinstall)

    has_ui = False
    if not args.backend_only:
        step(3, total, "Preparing the web interface")
        if args.dev:
            if args.no_install:
                if not (FRONTEND / "node_modules").is_dir():
                    raise SystemExit(
                        "{}npm packages are missing; remove --no-install to install them.{}".format(
                            R, RESET
                        )
                    )
            elif not ensure_frontend_dependencies(force=force_packages):
                raise SystemExit(
                    "{}--dev needs Node.js {}+ and npm.{}".format(
                        R, MIN_NODE_MAJOR, RESET
                    )
                )
        else:
            has_ui = build_frontend(force=args.build, force_packages=force_packages)

    if args.install_only:
        if args.backend_only:
            say("\nAksara API dependencies are ready.", G)
        elif has_ui:
            say("\nAksara is installed and the UI bundle is ready.", G)
        else:
            say("\nAksara API dependencies are ready (UI was not built).", Y)
        return

    step(total, total, "Starting Aksara")
    if args.dev:
        if args.backend_only:
            serve(python, args.host, args.port, reload=True, has_ui=False)
        else:
            serve_dev(python, args.host, args.port, args.frontend_port)
    else:
        # An existing bundle remains useful when Node is unavailable. The
        # backend receives the final decision through AKSARA_SERVE_UI.
        serve(
            python,
            args.host,
            args.port,
            reload=False,
            has_ui=(not args.backend_only) and (has_ui or ui_present()),
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        say("\nInterrupted.", Y)
        sys.exit(130)
