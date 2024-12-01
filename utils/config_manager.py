import os
import yaml
from cryptography.fernet import Fernet
import logging
from typing import Any, Dict

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.config_file = "config.yaml"
        self.key_file = ".config.key"
        self._config = None
        self._cipher_suite = None
        self._load_or_create_key()
        self._load_config()
        self._initialized = True
    
    def _load_or_create_key(self):
        """加载或创建加密密钥"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        self._cipher_suite = Fernet(key)
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
            else:
                logging.warning(f"配置文件 {self.config_file} 不存在")
                self._config = {}
        except Exception as e:
            logging.error(f"加载配置文件失败: {str(e)}")
            self._config = {}
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, allow_unicode=True)
        except Exception as e:
            logging.error(f"保存配置文件失败: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        try:
            keys = key.split('.')
            value = self._config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value
        self.save_config()
    
    def encrypt_value(self, value: str) -> str:
        """加密敏感信息"""
        return self._cipher_suite.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """解密敏感信息"""
        try:
            return self._cipher_suite.decrypt(encrypted_value.encode()).decode()
        except Exception:
            return ""
    
    def get_proxy_settings(self) -> Dict[str, str]:
        """获取代理设置"""
        if not self.get('proxy.enabled', False):
            return {}
            
        proxy_settings = {
            'http': self.get('proxy.http', ''),
            'https': self.get('proxy.https', '')
        }
        
        # 如果设置了认证信息，添加到代理URL中
        username = self.get('proxy.auth.username', '')
        password = self.get('proxy.auth.password', '')
        if username and password:
            decrypted_password = self.decrypt_value(password)
            for protocol in ['http', 'https']:
                if proxy_settings[protocol]:
                    proxy_settings[protocol] = proxy_settings[protocol].replace(
                        '://', f'://{username}:{decrypted_password}@'
                    )
        
        return proxy_settings
    
    def set_proxy_settings(self, settings: Dict[str, str]):
        """设置代理配置"""
        self.set('proxy.enabled', bool(settings))
        if settings:
            self.set('proxy.http', settings.get('http', ''))
            self.set('proxy.https', settings.get('https', ''))
            if 'username' in settings:
                self.set('proxy.auth.username', settings['username'])
            if 'password' in settings:
                encrypted_password = self.encrypt_value(settings['password'])
                self.set('proxy.auth.password', encrypted_password)
