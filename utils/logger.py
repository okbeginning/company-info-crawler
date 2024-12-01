import logging
import logging.handlers
import os
from .config_manager import ConfigManager

class Logger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.config = ConfigManager()
        self._setup_logger()
        self._initialized = True
    
    def _setup_logger(self):
        """配置日志系统"""
        log_file = self.config.get('logging.file', 'stock_crawler.log')
        log_level = self.config.get('logging.level', 'INFO')
        log_format = self.config.get('logging.format',
                                   '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        max_size = self.config.get('logging.max_size', 10 * 1024 * 1024)  # 10MB
        backup_count = self.config.get('logging.backup_count', 5)
        
        # 创建日志目录
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 配置根日志记录器
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, log_level))
        
        # 创建格式化器
        formatter = logging.Formatter(log_format)
        
        # 添加文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    @staticmethod
    def get_logger(name: str = None) -> logging.Logger:
        """获取日志记录器"""
        return logging.getLogger(name)
