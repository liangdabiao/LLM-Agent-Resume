import pypdf
from typing import List, Dict, Any
from app.core.cache_manager import CacheManager
from loguru import logger
import os
import hashlib


class DocumentParser:
    """
    文档解析器接口 (基础PDF转文本)
    """
    
    def __init__(self, cache_manager: CacheManager = None):
        """
        初始化文档解析器
        
        Args:
            cache_manager (CacheManager, optional): 缓存管理器实例
        """
        self.cache_manager = cache_manager
        logger.info("Initialized DocumentParser")
    
    def parse_pdf(self, file_path: str) -> str:
        """
        解析PDF文件为文本
        
        Args:
            file_path (str): PDF文件路径
            
        Returns:
            str: 提取的文本内容
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件不是PDF格式
            Exception: 解析失败
        """
        try:
            # 生成文件路径的哈希值作为缓存键
            cache_key = f"pdf_text_{hashlib.md5(file_path.encode()).hexdigest()}"
            
            # 尝试从缓存中获取结果
            if self.cache_manager:
                cached_result = self.cache_manager.get(cache_key)
                if cached_result:
                    logger.info(f"Retrieved PDF text from cache for file: {file_path}")
                    return cached_result
            
            # 棋查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # 检查文件扩展名
            if not file_path.lower().endswith('.pdf'):
                logger.error(f"File is not a PDF: {file_path}")
                raise ValueError(f"File is not a PDF: {file_path}")
            
            # 解析PDF
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        text += page_text
                        logger.debug(f"Extracted text from page {page_num + 1}")
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                        continue
            
            # 将结果存入缓存
            if self.cache_manager:
                self.cache_manager.set(cache_key, text, expire=3600)  # 缓存1小时
                logger.info(f"Cached PDF text for file: {file_path}")
            
            logger.info(f"Parsed PDF file: {file_path}, extracted {len(text)} characters")
            return text
            
        except FileNotFoundError:
            # 重新抛出文件未找到异常
            raise
        except ValueError:
            # 重新抛出值错误异常
            raise
        except Exception as e:
            logger.error(f"Failed to parse PDF file {file_path}: {e}")
            raise Exception(f"Failed to parse PDF file {file_path}: {e}")

    def parse_multiple_pdfs(self, file_paths: List[str]) -> Dict[str, str]:
        """
        解析多个PDF文件
        
        Args:
            file_paths (List[str]): PDF文件路径列表
            
        Returns:
            Dict[str, str]: 文件路径到提取文本的映射
        """
        results = {}
        for file_path in file_paths:
            try:
                text = self.parse_pdf(file_path)
                results[file_path] = text
            except Exception as e:
                logger.error(f"Failed to parse PDF file {file_path}: {e}")
                results[file_path] = f"ERROR: {str(e)}"
        return results