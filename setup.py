"""
This is a setup.py script generated for the Stock Report Crawler application.
"""
from setuptools import setup

APP = ['gui.py']
DATA_FILES = [
    'stock_codes.json',
]
OPTIONS = {
    'argv_emulation': True,
    'packages': ['tkinter', 'requests', 'pandas', 'tkcalendar'],
    'plist': {
        'CFBundleName': '股票报告下载器',
        'CFBundleDisplayName': '股票报告下载器',
        'CFBundleGetInfoString': "股票财务报告下载工具",
        'CFBundleIdentifier': "com.stockcrawler.app",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
