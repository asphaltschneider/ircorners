# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['trackbuilder.py'],
             pathex=['C:\\Users\\akira\\Documents\\Repositories\\ircorners\\venv\\lib\\site-packages'],
             binaries=[],
             datas=[],
             hiddenimports=["pynput.keyboard._win32", "pynput.mouse._win32"],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='trackbuilder',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
