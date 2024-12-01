#!/bin/bash

# 确保脚本在错误时退出
set -e

echo "开始构建 Stock Report Crawler..."

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 创建虚拟环境
echo "创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 升级 pip
echo "升级 pip..."
python3 -m pip install --upgrade pip

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 运行测试（如果有的话）
# echo "运行测试..."
# python3 -m pytest tests/

# 使用 PyInstaller 打包
echo "打包应用程序..."
pyinstaller package.spec

# 创建分发包
echo "创建分发包..."
VERSION=$(python3 -c "import json; print(json.load(open('version.json'))['version'])")
DIST_NAME="StockReportCrawler-v${VERSION}-mac"

# 创建分发目录
mkdir -p "dist/${DIST_NAME}"

# 复制必要文件
cp -r "dist/StockReportCrawler" "dist/${DIST_NAME}/"
cp README.md "dist/${DIST_NAME}/"
cp requirements.txt "dist/${DIST_NAME}/"
cp config.yaml "dist/${DIST_NAME}/"
cp stock_codes.json "dist/${DIST_NAME}/"

# 创建启动脚本
cat > "dist/${DIST_NAME}/启动股票报告下载器.command" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
./StockReportCrawler/StockReportCrawler
EOF

# 设置权限
chmod +x "dist/${DIST_NAME}/启动股票报告下载器.command"

# 创建压缩包
cd dist
zip -r "${DIST_NAME}.zip" "${DIST_NAME}"
cd ..

echo "构建完成！"
echo "分发包位置: dist/${DIST_NAME}.zip"

# 清理虚拟环境
deactivate
