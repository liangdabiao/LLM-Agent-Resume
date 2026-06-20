"""
向量数据库工厂

根据配置 `settings.VECTOR_DB` 选择并实例化对应的向量库管理器：
    - "chroma" (默认): ChromaDB 本地持久化
    - "milvus" / "zilliz": Milvus / Zilliz Cloud

两种实现暴露相同的接口，因此上层 Retriever 无需关心具体后端。
"""
from typing import Optional, Union
from loguru import logger

from config.config import settings
from app.core.vector_store import VectorStoreManager


def get_vector_store_manager(vector_db: Optional[str] = None):
    """
    返回向量库管理器实例。

    Args:
        vector_db (str, optional): 强制指定后端（chroma / milvus）。
            默认读取 settings.VECTOR_DB。

    Returns:
        VectorStoreManager | MilvusVectorStoreManager
    """
    backend = (vector_db or getattr(settings, "VECTOR_DB", "chroma") or "chroma").lower()

    if backend in ("milvus", "zilliz"):
        # 延迟导入，避免未安装 pymilvus 时影响默认路径
        from app.core.milvus_store import MilvusVectorStoreManager
        logger.info("Using Milvus / Zilliz vector store backend")
        return MilvusVectorStoreManager()

    if backend not in ("chroma", ""):
        logger.warning(f"Unknown VECTOR_DB='{backend}', falling back to ChromaDB")

    logger.info("Using ChromaDB vector store backend")
    return VectorStoreManager()
