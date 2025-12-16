# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Deep Think Evolving

import sys
from pathlib import Path

block_cipher = None

# Get the project root
project_root = Path(SPECPATH)

a = Analysis(
    ['server.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include frontend build
        ('dist', 'dist'),
        # Include knowledge_base directory structure
        ('knowledge_base', 'knowledge_base'),
        # Include source files
        ('src', 'src'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'google.generativeai',
        'langgraph',
        'langchain_core',
        'langchain_google_genai',
        'httpx',
        'h11',
        'anyio',
        'starlette',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DeepThinkEvolving',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Show console for debugging; set to False for release
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if available
)
