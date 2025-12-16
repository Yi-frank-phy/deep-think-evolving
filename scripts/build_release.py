#!/usr/bin/env python3
"""
Build script for Deep Think Evolving release package.

Usage:
    python scripts/build_release.py

This script:
1. Builds the frontend (npm run build)
2. Runs PyInstaller to create the EXE
3. Creates a release zip package
"""

import subprocess
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
RELEASE_DIR = PROJECT_ROOT / "release"


def run_command(cmd: list, cwd: Path = PROJECT_ROOT):
    """Run a command and print output."""
    print(f"\n>>> Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=False)
    if result.returncode != 0:
        print(f"Error: Command failed with code {result.returncode}")
        sys.exit(1)


def main():
    print("=" * 60)
    print("Deep Think Evolving - Release Build")
    print("=" * 60)

    # Step 1: Build frontend
    print("\n[1/4] Building frontend...")
    run_command(["npm", "run", "build"])

    if not DIST_DIR.exists():
        print("Error: Frontend build failed - dist/ not found")
        sys.exit(1)
    print("✓ Frontend built successfully")

    # Step 2: Install PyInstaller if needed
    print("\n[2/4] Checking PyInstaller...")
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("Installing PyInstaller...")
        run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Step 3: Run PyInstaller
    print("\n[3/4] Building EXE with PyInstaller...")
    run_command(["pyinstaller", "--clean", "deep_think.spec"])

    exe_path = BUILD_DIR.parent / "dist" / "DeepThinkEvolving.exe"
    if not exe_path.exists():
        # PyInstaller might put it elsewhere
        exe_path = PROJECT_ROOT / "dist" / "DeepThinkEvolving.exe"
    
    if not exe_path.exists():
        print("Warning: EXE not found at expected location. Check PyInstaller output.")
    else:
        print(f"✓ EXE built: {exe_path}")

    # Step 4: Create release package
    print("\n[4/4] Creating release package...")
    RELEASE_DIR.mkdir(exist_ok=True)
    
    release_name = "DeepThinkEvolving-v2.1.0-win64"
    release_package = RELEASE_DIR / f"{release_name}.zip"
    
    # Copy EXE and create .env.example
    if exe_path.exists():
        shutil.make_archive(
            str(RELEASE_DIR / release_name),
            'zip',
            root_dir=exe_path.parent,
            base_dir="."
        )
        print(f"✓ Release package: {release_package}")

    print("\n" + "=" * 60)
    print("Build complete!")
    print("=" * 60)
    print(f"\nEXE: {exe_path}")
    print(f"Release: {release_package}")
    print("\nTo run: double-click DeepThinkEvolving.exe")
    print("Browser will auto-open to http://localhost:8000")


if __name__ == "__main__":
    main()
