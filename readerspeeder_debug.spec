# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['readerspeeder.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pyttsx3', 'simpleaudio'],
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
    [],
    exclude_binaries=True,
    name='ReaderSpeeder',
    debug=True,  # Enable debug mode
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set console to True to keep the console window
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ReaderSpeeder',
)
