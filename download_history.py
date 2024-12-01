import json
import os
from datetime import datetime

class DownloadHistory:
    def __init__(self):
        self.history_file = "download_history.json"
        self.history = self._load_history()

    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"downloads": []}
        return {"downloads": []}

    def _save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def add_record(self, stock_code, stock_name, report_type, year, file_path):
        """添加下载记录"""
        record = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "report_type": report_type,
            "year": year,
            "file_path": file_path,
            "download_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.history["downloads"].insert(0, record)  # 新记录插入到开头
        self._save_history()

    def get_recent_downloads(self, limit=10):
        """获取最近的下载记录"""
        return self.history["downloads"][:limit]

    def search_history(self, keyword):
        """搜索下载历史"""
        results = []
        for record in self.history["downloads"]:
            if (keyword in record["stock_code"] or 
                keyword in record["stock_name"] or 
                keyword in record["report_type"]):
                results.append(record)
        return results

    def get_stock_history(self, stock_code):
        """获取特定股票的下载历史"""
        return [r for r in self.history["downloads"] if r["stock_code"] == stock_code]

    def clear_history(self):
        """清空下载历史"""
        self.history = {"downloads": []}
        self._save_history()
