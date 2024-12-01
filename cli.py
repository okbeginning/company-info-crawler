import argparse
from datetime import datetime
from crawler import StockCrawler
import json

def load_stock_codes(file_path='stock_codes.json'):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description='股票财报爬虫工具')
    parser.add_argument('--stock', '-s', help='股票名称或代码')
    parser.add_argument('--year', '-y', type=int, nargs='+', help='年份，可以指定多个，例如: 2022 2023')
    parser.add_argument('--type', '-t', nargs='+', choices=['年度报告', '半年度报告', '第一季度报告', '第三季度报告'],
                      help='报告类型，可以指定多个')
    parser.add_argument('--output', '-o', default='downloaded_reports', help='下载文件保存目录')
    
    args = parser.parse_args()
    
    # 如果没有指定股票，显示用法说明
    if not args.stock:
        parser.print_help()
        return
        
    # 加载股票代码
    stock_codes = load_stock_codes()
    stock_code = None
    
    # 查找股票代码
    if args.stock in stock_codes:
        stock_code = stock_codes[args.stock]
    else:
        # 尝试通过代码反查股票名称
        for name, code in stock_codes.items():
            if code == args.stock:
                stock_code = code
                break
                
    if not stock_code:
        print(f"未找到股票: {args.stock}")
        return
        
    # 创建爬虫实例
    crawler = StockCrawler(stock_code)
    
    # 设置下载目录
    task_dir = args.output
    
    # 获取可下载的文件列表
    files = crawler.get_available_files(
        years=args.year,
        selected_types=args.type
    )
    
    if not files:
        print("未找到符合条件的报告")
        return
        
    print(f"\n找到 {len(files)} 个文件:")
    for i, file in enumerate(files):
        print(f"{i+1}. {file['标题']} ({file['发布日期']})")
        
    # 下载所有文件
    print("\n开始下载...")
    crawler.download_selected_files(list(range(len(files))), task_dir)
    print("下载完成!")

if __name__ == '__main__':
    main()
