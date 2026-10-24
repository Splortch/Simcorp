"""
Build script for SimCorp backend executable using PyInstaller.
This script creates a standalone .exe file that can run the Flask API without needing Python installed.
"""

import os
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()

def build_executable():
    """Build the SimCorp backend as a standalone executable."""
    
    # PyInstaller command with options for Flask applications
    cmd = [
        "pyinstaller",
        "--name=SimCorpBackend",  # Name of the output executable
        "--onefile",              # Create single .exe file (not directory)
        "--windowed",            # No console window on Windows
        "--add-data", f"static;static",  # Include static files (CSS, JS, images)
        "--add-data", "templates;templates",  # Include HTML templates
        "--hidden-import=flask",     # Ensure Flask is bundled
        "--hidden-import=flask_cors", # Ensure CORS support is bundled
        "--exclude-module=pytest",    # Exclude testing framework
        "--exclude-module=pymongo",   # Exclude MongoDB driver (use bundled version)
        "--clean",                   # Clean previous build artifacts
        f"--distpath={SCRIPT_DIR}\\dist",  # Output directory
        f"--workpath={SCRIPT_DIR}\\build",   # Build directory
        f"--specpath={SCRIPT_DIR}\\build",   # Spec file directory
        "simcorp.py"                # Main entry point
    ]
    
    print("Building SimCorp Backend executable...")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    import subprocess
    result = subprocess.run(cmd, cwd=SCRIPT_DIR)
    
    if result.returncode == 0:
        exe_path = SCRIPT_DIR / "dist" / "SimCorpBackend.exe"
        print(f"\n✅ Build successful!")
        print(f"Executable created at: {exe_path}")
        
        # Get file size
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"File size: {size_mb:.1f} MB")
    else:
        print(f"\n❌ Build failed with exit code {result.returncode}")
    
    return result.returncode == 0

if __name__ == "__main__":
    build_executable()
