import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os
from loguru import logger
from langchain_openai import OpenAIEmbeddings
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from config.config import settings
from app.core.metadata_utils import serialize_metadata


class VectorStoreManager:
    """
    向量数据库连接与基本索引管理模块
    """

    def __init__(self, persist_directory: Optional[str] = None, embedding_model: Optional[str] = None):
        """
        初始化向量数据库管理器

        Args:
            persist_directory (str): 向量数据库持久化目录，默认取配置
            embedding_model (str): 嵌入模型名称，默认取配置
        """
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIR
        embedding_model = embedding_model or settings.EMBEDDING_MODEL
        # 创建持久化目录
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # 初始化嵌入模型（Embedding 专用 key/base_url，回退到 LLM/OPENAI）
        api_key = os.getenv("EMBEDDING_API_KEY") or os.getenv("OPENAI_API_KEY") or settings.EMBEDDING_API_KEY
        base_url = os.getenv("EMBEDDING_BASE_URL") or os.getenv("OPENAI_BASE_URL") or settings.EMBEDDING_BASE_URL

        if not api_key:
            raise ValueError("EMBEDDING_API_KEY (or OPENAI_API_KEY) environment variable is not set")
        
        # 组装嵌入模型参数；如配置了维度则透传（智谱 embedding-3 支持自定义维度）
        embedding_kwargs = {
            "model": embedding_model,
            "openai_api_key": api_key,
            "openai_api_base": base_url,
        }
        dimensions = getattr(settings, "EMBEDDING_DIMENSIONS", None)
        if dimensions:
            embedding_kwargs["dimensions"] = dimensions

        self.embeddings = OpenAIEmbeddings(**embedding_kwargs)
        logger.info(
            f"Initialized OpenAIEmbeddings with model: {embedding_model}"
            + (f", dimensions: {dimensions}" if dimensions else "")
        )
        
        # 初始化客户端
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        logger.info(f"Initialized ChromaDB client with persist directory: {self.persist_directory}")

    def create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> chromadb.Collection:
        """
        创建一个新的集合

        Args:
            name (str): 集合名称
            metadata (Dict[str, Any], optional): 集合元数据

        Returns:
            chromadb.Collection: 创建的集合对象
        """
        # 确保metadata不是空字典
        if not metadata:
            metadata = {"created_at": "2025-08-11"}
            
        # 创建集合 (不传递embedding_function参数)
        collection = self.client.create_collection(
            name=name,
            metadata=metadata
        )
        logger.info(f"Created collection: {name}")
        
        return collection

    def get_collection(self, name: str) -> chromadb.Collection:
        """
        获取一个已存在的集合，如果不存在则自动创建

        Args:
            name (str): 集合名称

        Returns:
            chromadb.Collection: 集合对象
        """
        try:
            collection = self.client.get_collection(name=name)
            logger.debug(f"Retrieved collection: {name}")
            return collection
        except Exception as e:
            logger.warning(f"Collection {name} does not exist, creating...")
            # 自动创建 collection，始终使用 embedding_function
            return self.create_collection(name)

    def delete_collection(self, name: str) -> None:
        """
        删除一个集合

        Args:
            name (str): 要删除的集合名称
        """
        try:
            self.client.delete_collection(name=name)
            logger.info(f"Deleted collection: {name}")
        except Exception as e:
            logger.error(f"Failed to delete collection {name}: {e}")
            raise

    def list_collections(self) -> List[str]:
        """
        列出所有集合名称

        Returns:
            List[str]: 集合名称列表
        """
        collections = self.client.list_collections()
        names = [collection.name for collection in collections]
        logger.debug(f"Listed collections: {names}")
        return names

    def add_documents(
        self, 
        collection_name: str, 
        documents: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """
        向指定集合添加文档（使用 upsert，不会清空集合中已有的文档）

        Args:
            collection_name (str): 集合名称
            documents (List[str]): 文档内容列表
            metadatas (List[Dict[str, Any]], optional): 文档元数据列表
            ids (List[str], optional): 文档ID列表
        """
        # 获取（或自动创建）集合，保留已有文档
        collection = self.get_collection(collection_name)

        # ChromaDB 仅支持标量元数据，列表/字典需序列化为 JSON 字符串
        serialized_metadatas = None
        if metadatas is not None:
            serialized_metadatas = [serialize_metadata(m) for m in metadatas]

        try:
            # 手动生成嵌入向量
            logger.info(f"Generating embeddings for {len(documents)} documents")
            embeddings = self.embeddings.embed_documents(documents)
            logger.info(f"Generated {len(embeddings)} embeddings")

            # 使用 upsert 添加/更新文档：同 id 覆盖，新 id 追加，已有文档保留
            collection.upsert(
                documents=documents,
                metadatas=serialized_metadatas or None,
                ids=ids or None,
                embeddings=embeddings
            )
            logger.info(f"Upserted {len(documents)} documents to collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to add documents to collection {collection_name}: {e}")
            raise

    def query_collection(
        self,
        collection_name: str,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        在指定集合中查询相似文档

        Args:
            collection_name (str): 集合名称
            query_texts (List[str]): 查询文本列表
            n_results (int): 返回结果数量
            where (Dict[str, Any], optional): 元数据过滤条件
            where_document (Dict[str, Any], optional): 文档内容过滤条件

        Returns:
            Dict[str, Any]: 查询结果
        """
        collection = self.get_collection(collection_name)
        
        try:
            # 手动生成查询文本的嵌入向量（查询使用 embed_query 语义）
            logger.info(f"Generating embeddings for {len(query_texts)} query texts")
            query_embeddings = [self.embeddings.embed_query(text) for text in query_texts]
            logger.info(f"Generated {len(query_embeddings)} query embeddings")
            
            # 使用生成的嵌入向量进行查询
            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where or None,
                where_document=where_document or None
            )
            logger.info(f"Queried collection {collection_name} with {len(query_texts)} texts")
            return results
        except Exception as e:
            logger.error(f"Failed to query collection {collection_name}: {e}")
            raise