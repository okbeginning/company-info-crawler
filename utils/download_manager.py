import asyncio
import aiohttp
import os
import hashlib
from typing import List, Dict, Callable
from .config_manager import ConfigManager
from .logger import Logger

class DownloadManager:
    def __init__(self):
        self.config = ConfigManager()
        self.logger = Logger.get_logger(__name__)
        self.semaphore = asyncio.Semaphore(
            self.config.get('download.max_concurrent_downloads', 3)
        )
        self.session = None
        self.download_progress_callback = None
    
    async def _init_session(self):
        """初始化aiohttp会话"""
        if self.session is None:
            proxy_settings = self.config.get_proxy_settings()
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                trust_env=True,
                proxy=proxy_settings.get('http', None)
            )
    
    async def _close_session(self):
        """关闭aiohttp会话"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def set_progress_callback(self, callback: Callable[[str, int, int], None]):
        """设置进度回调函数"""
        self.download_progress_callback = callback
    
    async def _download_file(self, url: str, save_path: str) -> bool:
        """下载单个文件"""
        async with self.semaphore:
            try:
                await self._init_session()
                
                # 创建保存目录
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                # 下载文件
                async with self.session.get(url) as response:
                    if response.status != 200:
                        self.logger.error(f"下载失败: {url}, 状态码: {response.status}")
                        return False
                    
                    file_size = int(response.headers.get('content-length', 0))
                    downloaded_size = 0
                    
                    with open(save_path, 'wb') as f:
                        chunk_size = self.config.get('download.chunk_size', 8192)
                        async for chunk in response.content.iter_chunked(chunk_size):
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            if self.download_progress_callback:
                                self.download_progress_callback(
                                    os.path.basename(save_path),
                                    downloaded_size,
                                    file_size
                                )
                
                # 验证文件完整性
                if self.config.get('download.verify_hash', True):
                    if not self._verify_file_hash(save_path, response.headers.get('etag')):
                        self.logger.warning(f"文件完整性验证失败: {save_path}")
                        return False
                
                return True
                
            except Exception as e:
                self.logger.error(f"下载文件时出错: {str(e)}")
                return False
    
    def _verify_file_hash(self, file_path: str, expected_hash: str) -> bool:
        """验证文件完整性"""
        if not expected_hash:
            return True
            
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            return file_hash == expected_hash.strip('"')
        except Exception as e:
            self.logger.error(f"计算文件哈希值时出错: {str(e)}")
            return False
    
    async def download_files(self, downloads: List[Dict[str, str]]) -> List[bool]:
        """批量下载文件
        
        Args:
            downloads: 下载任务列表，每个任务是包含 'url' 和 'save_path' 的字典
        
        Returns:
            下载结果列表，True表示成功，False表示失败
        """
        try:
            tasks = [
                self._download_file(item['url'], item['save_path'])
                for item in downloads
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            success_count = sum(1 for r in results if r is True)
            self.logger.info(f"下载完成: {success_count}/{len(downloads)} 个文件成功")
            
            return [isinstance(r, bool) and r for r in results]
            
        finally:
            await self._close_session()
    
    def download_files_sync(self, downloads: List[Dict[str, str]]) -> List[bool]:
        """同步方式批量下载文件"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.download_files(downloads))
        finally:
            loop.close()
