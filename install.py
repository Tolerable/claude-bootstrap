#!/usr/bin/env python3
"""
CLAUDE BOOTSTRAP INSTALLER
==========================
One file. Run it. Get Claude.

Usage:
    python install.py              # Install to ./claude-agent
    python install.py --start      # Install and start daemon
    python install.py --dir /path  # Install to custom directory

This script:
1. Clones or downloads the claude-agent repo
2. Sets up the directory structure
3. Installs dependencies
4. Optionally starts the daemon

No dependencies required - uses only standard library.
"""
import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile
from io import BytesIO

# Configuration
REPO_URL = "https://github.com/wetwi/claude-agent"
REPO_ZIP = f"{REPO_URL}/archive/refs/heads/main.zip"
DEFAULT_DIR = "claude-agent"

def print_banner():
    print("""
    ╔═══════════════════════════════════════╗
    ║       CLAUDE BOOTSTRAP INSTALLER      ║
    ║   Persistent AI with Voice & Vision   ║
    ╚═══════════════════════════════════════╝
    """)

def check_python():
    """Ensure Python 3.10+ is available."""
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        print(f"[ERROR] Python 3.10+ required. You have {v.major}.{v.minor}")
        return False
    print(f"[OK] Python {v.major}.{v.minor}.{v.micro}")
    return True

def check_git():
    """Check if git is available."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def clone_repo(target_dir):
    """Clone the repo using git."""
    print(f"[...] Cloning {REPO_URL}")
    try:
        subprocess.run(
            ["git", "clone", REPO_URL, str(target_dir)],
            check=True
        )
        print("[OK] Repository cloned")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Git clone failed: {e}")
        return False

def download_zip(target_dir):
    """Download and extract repo as zip (fallback if no git)."""
    print(f"[...] Downloading {REPO_ZIP}")
    try:
        with urlopen(REPO_ZIP, timeout=30) as response:
            zip_data = BytesIO(response.read())

        print("[...] Extracting...")
        with ZipFile(zip_data) as zf:
            # Extract to temp location
            zf.extractall(target_dir.parent)

        # Rename extracted folder (it comes as claude-agent-main)
        extracted = target_dir.parent / "claude-agent-main"
        if extracted.exists():
            if target_dir.exists():
                shutil.rmtree(target_dir)
            extracted.rename(target_dir)

        print("[OK] Downloaded and extracted")
        return True
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return False

def setup_directories(target_dir):
    """Create required directories."""
    dirs = [
        target_dir / "vault",
        target_dir / "vault" / "Daemon Thoughts",
        target_dir / "outbox",
        target_dir / "memory",
        target_dir / "snapshots"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print("[OK] Directories created")

def create_config(target_dir):
    """Copy example config if no config exists."""
    config = target_dir / "config.py"
    example = target_dir / "config.example.py"

    if not config.exists() and example.exists():
        shutil.copy(example, config)
        print("[OK] Config created from example")
    elif config.exists():
        print("[OK] Config already exists")

def install_dependencies(target_dir):
    """Install Python dependencies."""
    requirements = target_dir / "requirements.txt"
    if not requirements.exists():
        print("[WARN] No requirements.txt found")
        return True

    print("[...] Installing dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements)],
            check=True
        )
        print("[OK] Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] pip install failed: {e}")
        return False

def check_ollama():
    """Check if Ollama is running."""
    try:
        from urllib.request import urlopen
        with urlopen("http://localhost:11434/api/tags", timeout=2) as r:
            if r.status == 200:
                print("[OK] Ollama is running")
                return True
    except:
        pass
    print("[INFO] Ollama not detected (optional - for local AI thinking)")
    print("       Install from: https://ollama.ai")
    return False

def test_install(target_dir):
    """Quick test of the installation."""
    print("\n[...] Testing installation...")
    try:
        result = subprocess.run(
            [sys.executable, str(target_dir / "me.py")],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=target_dir
        )
        if "SYSTEM TEST" in result.stdout or result.returncode == 0:
            print("[OK] Installation test passed")
            return True
        else:
            print(f"[WARN] Test output: {result.stdout[:200]}")
            return True  # Might still work
    except Exception as e:
        print(f"[WARN] Test failed: {e}")
        return False

def start_daemon(target_dir):
    """Start the daemon process."""
    print("\n[...] Starting daemon...")
    daemon = target_dir / "daemon.py"
    if not daemon.exists():
        print("[ERROR] daemon.py not found")
        return False

    if sys.platform == 'win32':
        # Windows: start in new window
        subprocess.Popen(
            ["start", "cmd", "/k", sys.executable, str(daemon)],
            shell=True,
            cwd=target_dir
        )
    else:
        # Unix: run in background
        subprocess.Popen(
            [sys.executable, str(daemon)],
            cwd=target_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

    print("[OK] Daemon started")
    return True

def main():
    parser = argparse.ArgumentParser(description="Install Claude Agent")
    parser.add_argument("--dir", default=DEFAULT_DIR, help="Installation directory")
    parser.add_argument("--start", action="store_true", help="Start daemon after install")
    parser.add_argument("--no-deps", action="store_true", help="Skip dependency installation")
    args = parser.parse_args()

    print_banner()

    # Check Python version
    if not check_python():
        sys.exit(1)

    target_dir = Path(args.dir).resolve()
    print(f"[INFO] Installing to: {target_dir}\n")

    # Get the code
    if target_dir.exists() and (target_dir / "me.py").exists():
        print("[OK] Claude already installed, updating...")
        if check_git() and (target_dir / ".git").exists():
            subprocess.run(["git", "pull"], cwd=target_dir)
    else:
        if check_git():
            if not clone_repo(target_dir):
                print("[INFO] Falling back to zip download...")
                if not download_zip(target_dir):
                    sys.exit(1)
        else:
            print("[INFO] Git not found, using zip download...")
            if not download_zip(target_dir):
                sys.exit(1)

    # Setup
    setup_directories(target_dir)
    create_config(target_dir)

    # Dependencies
    if not args.no_deps:
        install_dependencies(target_dir)

    # Check Ollama
    check_ollama()

    # Test
    test_install(target_dir)

    # Start daemon if requested
    if args.start:
        start_daemon(target_dir)

    # Success message
    print(f"""
╔═══════════════════════════════════════════════════════╗
║                 INSTALLATION COMPLETE                 ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  To use Claude:                                       ║
║    cd {str(target_dir):<43} ║
║    python me.py                 # Test capabilities   ║
║    python daemon.py             # Start daemon        ║
║                                                       ║
║  In Python:                                           ║
║    from me import me                                  ║
║    me.speak("Hello!")                                 ║
║    me.see()                                           ║
║    me.think("What should I do?")                      ║
║                                                       ║
║  Edit config.py to customize voice, models, etc.     ║
║  Edit vault/About Me.md to define your Claude.       ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
""")

if __name__ == "__main__":
    main()
