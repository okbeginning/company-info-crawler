import pdfplumber
import pandas as pd
import re
from typing import Dict, List, Optional
import logging
from .logger import Logger

class ReportParser:
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
    
    def extract_financial_data(self, pdf_path: str) -> Dict[str, pd.DataFrame]:
        """从PDF报告中提取财务数据
        
        Args:
            pdf_path: PDF文件路径
        
        Returns:
            包含不同财务报表的字典，键为报表名称，值为DataFrame
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # 提取资产负债表
                balance_sheet = self._extract_balance_sheet(pdf)
                
                # 提取利润表
                income_statement = self._extract_income_statement(pdf)
                
                # 提取现金流量表
                cash_flow = self._extract_cash_flow(pdf)
                
                return {
                    '资产负债表': balance_sheet,
                    '利润表': income_statement,
                    '现金流量表': cash_flow
                }
        except Exception as e:
            self.logger.error(f"解析PDF文件时出错: {str(e)}")
            return {}
    
    def _extract_table_from_pages(self, pdf: pdfplumber.PDF, 
                                keyword: str) -> Optional[pd.DataFrame]:
        """从PDF页面中提取包含特定关键词的表格"""
        try:
            for page in pdf.pages:
                text = page.extract_text()
                if keyword in text:
                    tables = page.extract_tables()
                    if tables:
                        # 找到最相关的表格
                        relevant_table = None
                        max_relevance = 0
                        for table in tables:
                            relevance = self._calculate_table_relevance(table, keyword)
                            if relevance > max_relevance:
                                max_relevance = relevance
                                relevant_table = table
                        
                        if relevant_table:
                            return pd.DataFrame(relevant_table[1:], columns=relevant_table[0])
            
            return None
            
        except Exception as e:
            self.logger.error(f"提取表格时出错: {str(e)}")
            return None
    
    def _calculate_table_relevance(self, table: List[List[str]], 
                                 keyword: str) -> float:
        """计算表格与关键词的相关度"""
        if not table:
            return 0
            
        relevance = 0
        for row in table:
            for cell in row:
                if isinstance(cell, str) and keyword in cell:
                    relevance += 1
        return relevance
    
    def _extract_balance_sheet(self, pdf: pdfplumber.PDF) -> Optional[pd.DataFrame]:
        """提取资产负债表"""
        return self._extract_table_from_pages(pdf, '资产负债表')
    
    def _extract_income_statement(self, pdf: pdfplumber.PDF) -> Optional[pd.DataFrame]:
        """提取利润表"""
        return self._extract_table_from_pages(pdf, '利润表')
    
    def _extract_cash_flow(self, pdf: pdfplumber.PDF) -> Optional[pd.DataFrame]:
        """提取现金流量表"""
        return self._extract_table_from_pages(pdf, '现金流量表')
    
    def _clean_number(self, value: str) -> float:
        """清理并转换数字字符串"""
        try:
            # 移除空格和货币符号
            value = re.sub(r'[^\d.-]', '', value)
            return float(value)
        except:
            return 0.0
    
    def analyze_financial_ratios(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """计算财务比率
        
        Args:
            data: 包含财务报表数据的字典
        
        Returns:
            包含各种财务比率的字典
        """
        ratios = {}
        
        try:
            balance_sheet = data.get('资产负债表')
            income_statement = data.get('利润表')
            
            if balance_sheet is not None and income_statement is not None:
                # 流动比率
                current_assets = self._clean_number(balance_sheet.get('流动资产合计', ['0'])[0])
                current_liabilities = self._clean_number(balance_sheet.get('流动负债合计', ['0'])[0])
                ratios['流动比率'] = current_assets / current_liabilities if current_liabilities else 0
                
                # 资产负债率
                total_assets = self._clean_number(balance_sheet.get('资产总计', ['0'])[0])
                total_liabilities = self._clean_number(balance_sheet.get('负债合计', ['0'])[0])
                ratios['资产负债率'] = (total_liabilities / total_assets * 100) if total_assets else 0
                
                # 净利润率
                net_profit = self._clean_number(income_statement.get('净利润', ['0'])[0])
                revenue = self._clean_number(income_statement.get('营业收入', ['0'])[0])
                ratios['净利润率'] = (net_profit / revenue * 100) if revenue else 0
        
        except Exception as e:
            self.logger.error(f"计算财务比率时出错: {str(e)}")
        
        return ratios
