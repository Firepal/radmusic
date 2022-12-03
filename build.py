import PyInstaller.__main__

PyInstaller.__main__.run([
    'run.py',
    '--onefile',
    '--console',
    '--name', 'umc'
])

input("Press Enter to continue... ")