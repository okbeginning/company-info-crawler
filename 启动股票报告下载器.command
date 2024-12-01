#!/bin/bash

# 切换到程序所在目录
cd /Users/junchen/CascadeProjects/stock_crawler
echo "当前工作目录: $(pwd)"

# 运行打包后的程序
./StockReportCrawler-v1.0.0-mac/StockReportCrawler/StockReportCrawler 2>&1

# 如果程序出错，等待用户确认
if [ $? -ne 0 ]; then
    echo "程序运行出错"
    read -p "按回车键退出..."
fi
