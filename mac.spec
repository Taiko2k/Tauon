# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

import subprocess
prefix = subprocess.run(['brew', '--prefix'], capture_output=True, text=True).stdout.strip()

a = Analysis(['tauon.py'],
             pathex=['/Users/kai/TauonMusicBox'],
             binaries=[('lib/libphazor.so', 'lib/'),
              #(prefix + '/bin/ffmpeg', '.'),
              (prefix + '/lib/libao*.dylib', '.'),
              (prefix + '/lib/libsamplerate*.dylib', '.'),
              (prefix + '/lib/libvorbis*.dylib', '.'),
              (prefix + '/lib/libmpg123*.dylib', '.'),
              (prefix + '/lib/libopus*.dylib', '.'),
              (prefix + '/lib/libopenmpt*.dylib', '.')],
             datas=[('assets', 'assets'), ('theme', 'theme'), ('input.txt', '.')],
             hiddenimports=[],
             hookspath=['extra/pyinstaller-hooks'],
             hooksconfig={},
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
          [],
          exclude_binaries=True,
          name='Tauon Music Box',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon='assets/tau-mac.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='TauonMusicBox')
app = BUNDLE(coll,
             name='TauonMusicBox.app',
             icon='assets/tau-mac.icns',
             bundle_identifier=None,
             info_plist={
                'LSEnvironment': {
                    'LANG': 'en_US.UTF-8',
                    'LC_CTYPE': 'en_US.UTF-8'
                }
             }
             )
