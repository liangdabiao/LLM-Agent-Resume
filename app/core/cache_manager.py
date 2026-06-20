import diskcache
from typing import Any, Optional
from loguru import logger
import os


class CacheManager:
    """
    缓存管理模块
    """
    
    def __init__(self, cache_directory: str = "./cache"):
        """
        初始化缓存管理器
        
        Args:
            cache_directory (str): 缓存目录路径
        """
        self.cache_directory = cache_directory
        # 创建缓存目录
        os.makedirs(self.cache_directory, exist_ok=True)
        
        # 初始化diskcache
        self.cache = diskcache.Cache(self.cache_directory)
        logger.info(f"Initialized cache manager with directory: {self.cache_directory}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        从缓存获取值
        
        Args:
            key (str): 缓存键
            default (Any): 默认值
            
        Returns:
            Any: 缓存值或默认值
        """
        try:
            value = self.cache.get(key, default)
            if value != default:
                logger.debug(f"Cache hit for key: {key}")
            else:
                logger.debug(f"Cache miss for key: {key}")
            return value
        except Exception as e:
            logger.error(f"Failed to get cache value for key {key}: {e}")
            return default

    def set(self, key: str, value: Any, expire: Optional[float] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key (str): 缓存键
            value (Any): 缓存值
            expire (float, optional): 过期时间(秒)
            
        Returns:
            bool: 是否设置成功
        """
        try:
            self.cache.set(key, value, expire=expire)
            logger.debug(f"Set cache value for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to set cache value for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        删除缓存值
        
        Args:
            key (str): 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        try:
            result = self.cache.delete(key)
            if result:
                logger.debug(f"Deleted cache value for key: {key}")
            else:
                logger.debug(f"No cache value to delete for key: {key}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete cache value for key {key}: {e}")
            return False

    def clear(self) -> bool:
        """
        清空所有缓存
        
        Returns:
            bool: 是否清空成功
        """
        try:
            self.cache.clear()
            logger.info("Cleared all cache")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    def close(self) -> None:
        """
        关闭缓存连接
        """
        try:
            self.cache.close()
            logger.debug("Closed cache connection")
        except Exception as e:
            logger.error(f"Failed to close cache connection: {e}")