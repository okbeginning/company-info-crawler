import requests
import json
import time
import random

def get_stock_list():
    """获取沪深两市所有上市公司信息"""
    
    # 东方财富网的API
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "*/*",
        "Referer": "http://quote.eastmoney.com/"
    }
    
    # 沪市
    params_sh = {
        "pn": 1,  # 页码
        "pz": 5000,  # 每页数量
        "po": 1,  # 排序方向
        "np": 1,
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": 2,
        "invt": 2,
        "fid": "f3",
        "fs": "m:1",  # 沪市
        "fields": "f12,f14"  # f12是代码，f14是名称
    }
    
    # 深市
    params_sz = {
        "pn": 1,
        "pz": 5000,
        "po": 1,
        "np": 1,
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": 2,
        "invt": 2,
        "fid": "f3",
        "fs": "m:0",  # 深市
        "fields": "f12,f14"
    }
    
    stock_dict = {}
    
    try:
        # 获取沪市数据
        response_sh = requests.get(url, headers=headers, params=params_sh)
        data_sh = response_sh.json()
        
        if data_sh.get('data', {}).get('diff'):
            for item in data_sh['data']['diff']:
                stock_dict[item['f14']] = item['f12']
        
        time.sleep(random.uniform(1, 2))
        
        # 获取深市数据
        response_sz = requests.get(url, headers=headers, params=params_sz)
        data_sz = response_sz.json()
        
        if data_sz.get('data', {}).get('diff'):
            for item in data_sz['data']['diff']:
                stock_dict[item['f14']] = item['f12']
        
        # 保存到文件
        with open('stock_codes.json', 'w', encoding='utf-8') as f:
            json.dump(stock_dict, f, ensure_ascii=False, indent=2)
            
        print(f"成功获取 {len(stock_dict)} 家上市公司信息")
        
    except Exception as e:
        print(f"获取股票列表时出错: {str(e)}")
        
if __name__ == "__main__":
    get_stock_list()
