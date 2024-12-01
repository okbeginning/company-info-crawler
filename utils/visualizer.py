import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import os
from .config_manager import ConfigManager
from .logger import Logger

class DataVisualizer:
    def __init__(self):
        self.config = ConfigManager()
        self.logger = Logger.get_logger(__name__)
        self._setup_style()
    
    def _setup_style(self):
        """设置图表样式"""
        style = self.config.get('analysis.chart_style', 'seaborn')
        plt.style.use(style)
    
    def create_financial_charts(self, data: Dict[str, pd.DataFrame], 
                              save_dir: str) -> List[str]:
        """创建财务数据图表
        
        Args:
            data: 财务数据字典
            save_dir: 保存目录
        
        Returns:
            保存的图表文件路径列表
        """
        saved_files = []
        try:
            os.makedirs(save_dir, exist_ok=True)
            
            # 设置图表大小
            fig_size = self.config.get('analysis.default_chart_size', [10, 6])
            
            # 创建资产负债趋势图
            if '资产负债表' in data:
                balance_file = self._create_balance_sheet_chart(
                    data['资产负债表'],
                    save_dir,
                    fig_size
                )
                if balance_file:
                    saved_files.append(balance_file)
            
            # 创建利润趋势图
            if '利润表' in data:
                profit_file = self._create_profit_chart(
                    data['利润表'],
                    save_dir,
                    fig_size
                )
                if profit_file:
                    saved_files.append(profit_file)
            
            # 创建现金流量趋势图
            if '现金流量表' in data:
                cash_flow_file = self._create_cash_flow_chart(
                    data['现金流量表'],
                    save_dir,
                    fig_size
                )
                if cash_flow_file:
                    saved_files.append(cash_flow_file)
            
            return saved_files
            
        except Exception as e:
            self.logger.error(f"创建财务图表时出错: {str(e)}")
            return saved_files
    
    def _create_balance_sheet_chart(self, data: pd.DataFrame, 
                                  save_dir: str, 
                                  fig_size: Tuple[int, int]) -> Optional[str]:
        """创建资产负债趋势图"""
        try:
            plt.figure(figsize=fig_size)
            
            # 提取关键指标
            metrics = ['资产总计', '负债合计', '所有者权益合计']
            for metric in metrics:
                if metric in data.columns:
                    plt.plot(data.index, data[metric], label=metric, marker='o')
            
            plt.title('资产负债趋势分析')
            plt.xlabel('报告期')
            plt.ylabel('金额（元）')
            plt.legend()
            plt.grid(True)
            
            # 保存图表
            save_path = os.path.join(save_dir, 'balance_sheet_trend.png')
            plt.savefig(save_path)
            plt.close()
            
            return save_path
            
        except Exception as e:
            self.logger.error(f"创建资产负债趋势图时出错: {str(e)}")
            return None
    
    def _create_profit_chart(self, data: pd.DataFrame,
                           save_dir: str,
                           fig_size: Tuple[int, int]) -> Optional[str]:
        """创建利润趋势图"""
        try:
            plt.figure(figsize=fig_size)
            
            # 提取关键指标
            metrics = ['营业收入', '营业利润', '净利润']
            for metric in metrics:
                if metric in data.columns:
                    plt.plot(data.index, data[metric], label=metric, marker='o')
            
            plt.title('利润趋势分析')
            plt.xlabel('报告期')
            plt.ylabel('金额（元）')
            plt.legend()
            plt.grid(True)
            
            # 保存图表
            save_path = os.path.join(save_dir, 'profit_trend.png')
            plt.savefig(save_path)
            plt.close()
            
            return save_path
            
        except Exception as e:
            self.logger.error(f"创建利润趋势图时出错: {str(e)}")
            return None
    
    def _create_cash_flow_chart(self, data: pd.DataFrame,
                              save_dir: str,
                              fig_size: Tuple[int, int]) -> Optional[str]:
        """创建现金流量趋势图"""
        try:
            plt.figure(figsize=fig_size)
            
            # 提取关键指标
            metrics = ['经营活动产生的现金流量净额',
                      '投资活动产生的现金流量净额',
                      '筹资活动产生的现金流量净额']
            for metric in metrics:
                if metric in data.columns:
                    plt.plot(data.index, data[metric], label=metric, marker='o')
            
            plt.title('现金流量趋势分析')
            plt.xlabel('报告期')
            plt.ylabel('金额（元）')
            plt.legend()
            plt.grid(True)
            
            # 保存图表
            save_path = os.path.join(save_dir, 'cash_flow_trend.png')
            plt.savefig(save_path)
            plt.close()
            
            return save_path
            
        except Exception as e:
            self.logger.error(f"创建现金流量趋势图时出错: {str(e)}")
            return None
