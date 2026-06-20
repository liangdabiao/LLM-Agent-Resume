"""
Milvus / Zilliz Cloud 向量数据库管理模块

实现与 `VectorStoreManager` (ChromaDB) 完全一致的接口，使其可以作为可选的
后端被 `vector_store_factory` 无缝切换。查询结果统一返回 Chroma 风格的二维
字典结构，因此上层的 `Retriever._format_results` 无需任何改动。

集合 schema:
    - id:       VARCHAR  主键
    - vector:   FLOAT_VECTOR  (维度取 settings.EMBEDDING_DIMENSIONS)
    - document: VARCHAR  原始文档文本
    - metadata: JSON     业务元数据（已序列化为标量的字典）

依赖 pymilvus 的 MilvusClient（轻量客户端，兼容本地 Milvus 与 Zilliz Cloud）。
"""
import os
from typing import List, Dict, Any, Optional

from loguru import logger
from langchain_openai import OpenAIEmbeddings

from config.config import settings


# 单条 VARCHAR 字段的最大长度（document 文本可能较长）
_DOCUMENT_MAX_LENGTH = 65535
_ID_MAX_LENGTH = 512


class MilvusVectorStoreManager:
    """
    基于 Milvus / Zilliz Cloud 的向量数据库管理器。

    对外暴露与 ChromaDB 版 `VectorStoreManager` 相同的方法签名：
    create_collection / get_collection / delete_collection / list_collections /
    add_documents / query_collection。
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        token: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ):
        """
        初始化 Milvus 管理器。

        Args:
            uri (str): Milvus / Zilliz 连接 URI，默认取配置 MILVUS_URI
            token (str): 鉴权 token，默认取配置 MILVUS_TOKEN
            embedding_model (str): 嵌入模型名称，默认取配置
        """
        # 延迟导入，避免未安装 pymilvus 时影响默认 Chroma 路径
        try:
            from pymilvus import MilvusClient
        except ImportError as e:  # pragma: no cover - 缺少依赖时给出清晰提示
            raise ImportError(
                "使用 Milvus 向量库需要安装 pymilvus：pip install pymilvus"
            ) from e

        self.uri = uri or settings.MILVUS_URI
        self.token = token or settings.MILVUS_TOKEN
        if not self.uri:
            raise ValueError("MILVUS_URI 未配置，无法连接 Milvus / Zilliz")

        embedding_model = embedding_model or settings.EMBEDDING_MODEL

        # 初始化嵌入模型（与 Chroma 版保持一致的 key/base_url 回退逻辑）
        api_key = os.getenv("EMBEDDING_API_KEY") or os.getenv("OPENAI_API_KEY") or settings.EMBEDDING_API_KEY
        base_url = os.getenv("EMBEDDING_BASE_URL") or os.getenv("OPENAI_BASE_URL") or settings.EMBEDDING_BASE_URL
        if not api_key:
            raise ValueError("EMBEDDING_API_KEY (or OPENAI_API_KEY) environment variable is not set")

        embedding_kwargs = {
            "model": embedding_model,
            "openai_api_key": api_key,
            "openai_api_base": base_url,
        }
        self.dimensions = getattr(settings, "EMBEDDING_DIMENSIONS", None) or 1536
        if getattr(settings, "EMBEDDING_DIMENSIONS", None):
            embedding_kwargs["dimensions"] = settings.EMBEDDING_DIMENSIONS

        self.embeddings = OpenAIEmbeddings(**embedding_kwargs)
        self.index_type = getattr(settings, "MILVUS_INDEX", "AUTOINDEX") or "AUTOINDEX"

        # 建立客户端连接
        self.client = MilvusClient(uri=self.uri, token=self.token or None)
        logger.info(
            f"Initialized Milvus client uri={self.uri}, dim={self.dimensions}, index={self.index_type}"
        )

    # ------------------------------------------------------------------ #
    # 集合管理
    # ------------------------------------------------------------------ #
    def create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        创建集合（若已存在则直接返回）。

        Args:
            name (str): 集合名称
            metadata (Dict[str, Any], optional): 兼容 Chroma 接口，Milvus 不使用

        Returns:
            str: 集合名称
        """
        if self.client.has_collection(name):
            logger.debug(f"Milvus collection already exists: {name}")
            return name

        from pymilvus import DataType

        schema = self.client.create_schema(auto_id=False, enable_dynamic_field=True)
        schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=_ID_MAX_LENGTH)
        schema.add_field("vector", DataType.FLOAT_VECTOR, dim=self.dimensions)
        schema.add_field("document", DataType.VARCHAR, max_length=_DOCUMENT_MAX_LENGTH)
        schema.add_field("metadata", DataType.JSON)

        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type=self.index_type,
            metric_type="COSINE",
        )

        self.client.create_collection(
            collection_name=name,
            schema=schema,
            index_params=index_params,
        )
        logger.info(f"Created Milvus collection: {name}")
        return name

    def get_collection(self, name: str) -> str:
        """
        获取集合（不存在则自动创建）。返回集合名称以保持轻量。
        """
        if not self.client.has_collection(name):
            logger.warning(f"Milvus collection {name} does not exist, creating...")
            return self.create_collection(name)
        return name

    def delete_collection(self, name: str) -> None:
        """删除集合。"""
        try:
            if self.client.has_collection(name):
                self.client.drop_collection(name)
            logger.info(f"Dropped Milvus collection: {name}")
        except Exception as e:
            logger.error(f"Failed to drop Milvus collection {name}: {e}")
            raise

    def list_collections(self) -> List[str]:
        """列出所有集合名称。"""
        names = self.client.list_collections()
        logger.debug(f"Listed Milvus collections: {names}")
        return names

    # ------------------------------------------------------------------ #
    # 文档读写
    # ------------------------------------------------------------------ #
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        """
        向集合插入/更新文档（upsert 语义：同 id 覆盖）。

        Args:
            collection_name (str): 集合名称
            documents (List[str]): 文档文本列表
            metadatas (List[Dict[str, Any]], optional): 元数据列表
            ids (List[str], optional): 文档 ID 列表
        """
        self.get_collection(collection_name)

        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]

        if metadatas is None:
            metadatas = [{} for _ in documents]
        # Milvus 的 metadata 为原生 JSON 字段，支持嵌套 list/dict，故原样存储，
        # 无需像 ChromaDB 那样把列表序列化为标量字符串。
        normalized = [m or {} for m in metadatas]

        try:
            logger.info(f"Generating embeddings for {len(documents)} documents (Milvus)")
            embeddings = self.embeddings.embed_documents(documents)

            rows = []
            for doc_id, doc, vec, meta in zip(ids, documents, embeddings, normalized):
                rows.append({
                    "id": str(doc_id),
                    "vector": vec,
                    "document": doc,
                    "metadata": meta,
                })

            self.client.upsert(collection_name=collection_name, data=rows)
            logger.info(f"Upserted {len(rows)} documents to Milvus collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to add documents to Milvus collection {collection_name}: {e}")
            raise

    def query_collection(
        self,
        collection_name: str,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        语义检索，返回 Chroma 风格的二维结果字典。

        Returns:
            Dict[str, Any]: {ids, documents, metadatas, distances}，每个值均为二维列表
        """
        self.get_collection(collection_name)

        ids_2d: List[List[str]] = []
        docs_2d: List[List[str]] = []
        metas_2d: List[List[Dict[str, Any]]] = []
        dists_2d: List[List[float]] = []

        try:
            logger.info(f"Generating embeddings for {len(query_texts)} query texts (Milvus)")
            query_embeddings = [self.embeddings.embed_query(text) for text in query_texts]

            search_res = self.client.search(
                collection_name=collection_name,
                data=query_embeddings,
                limit=n_results,
                output_fields=["document", "metadata"],
            )

            for hits in search_res:
                row_ids, row_docs, row_metas, row_dists = [], [], [], []
                for hit in hits:
                    entity = hit.get("entity", {}) if isinstance(hit, dict) else {}
                    row_ids.append(hit.get("id"))
                    row_docs.append(entity.get("document", ""))
                    row_metas.append(entity.get("metadata", {}) or {})
                    # COSINE: 距离 = 1 - 相似度，越小越相近
                    row_dists.append(1.0 - float(hit.get("distance", 0.0)))
                ids_2d.append(row_ids)
                docs_2d.append(row_docs)
                metas_2d.append(row_metas)
                dists_2d.append(row_dists)

            logger.info(f"Queried Milvus collection {collection_name} with {len(query_texts)} texts")
        except Exception as e:
            logger.error(f"Failed to query Milvus collection {collection_name}: {e}")
            raise

        return {
            "ids": ids_2d,
            "documents": docs_2d,
            "metadatas": metas_2d,
            "distances": dists_2d,
        }
