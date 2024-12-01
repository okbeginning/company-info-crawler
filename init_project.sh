#!/bin/bash

# 确保脚本在错误时退出
set -e

echo "初始化 Stock Report Crawler 项目环境..."

# 创建必要的目录
mkdir -p downloads
mkdir -p logs
mkdir -p utils

# 创建 __init__.py 文件
touch utils/__init__.py

# 设置 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate

# 升级 pip
python3 -m pip install --upgrade pip

# 安装基本依赖
pip install requests pandas tkcalendar openpyxl

# 安装高级功能依赖
pip install PyPDF2 matplotlib pdfplumber cryptography aiohttp PyYAML schedule

# 安装开发工具
pip install pyinstaller

echo "项目环境初始化完成！"
