# -*- mode: python -*-

block_cipher = None
app_name = 'client'

a = Analysis(['client.py'],
             pathex=['/Users/kimjh/workspace/cn01/client'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
a.datas += [('login_dialog.ui', 'login_dialog.ui', 'login_dialog'), ('main_window.ui', 'main_window.ui', 'main_window')]

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
		  exclude_binaries=True,
          name=app_name,
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False
		)
coll = COLLECT(exe,
		a.binaries,
		a.zipfiles,
		a.datas,
		strip=False,
		upx=True,
		name=app_name)
