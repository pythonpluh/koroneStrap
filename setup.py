from setuptools import setup

APP = ['koroneStrap.py']
OPTIONS = {
    'argv_emulation': True,
    'packages': ['colorama'],
    'plist': {
        'LSBackgroundOnly': False, 
        'CFBundleName': 'koroneStrap',
        'CFBundleIdentifier': 'dev.korone.strap',
        'CFBundleShortVersionString': '1.0',
        'CFBundleVersion': '1.0',
    },
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)