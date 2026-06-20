"""
测试核心模块
"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from app.core.vector_store import VectorStoreManager
from app.core.llm_client import LLMClient
from app.core.document_parser import DocumentParser
from app.core.cache_manager import CacheManager
from app.models.metadata import ResumeMetadata, QueryMetadata


class TestVectorStoreManager:
    """测试向量数据库管理器"""

    def test_init(self):
        """测试初始化"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            vsm = VectorStoreManager(persist_directory=temp_dir)
            assert vsm.persist_directory == temp_dir
            assert vsm.client is not None

    def test_create_and_get_collection(self):
        """测试创建和获取集合"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            vsm = VectorStoreManager(persist_directory=temp_dir)
            
            # 创建集合
            collection = vsm.create_collection("test_collection", {"test": "metadata"})
            assert collection.name == "test_collection"
            
            # 获取集合
            retrieved_collection = vsm.get_collection("test_collection")
            assert retrieved_collection.name == "test_collection"

    def test_list_collections(self):
        """测试列出集合"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            vsm = VectorStoreManager(persist_directory=temp_dir)
            
            # 创建几个集合
            vsm.create_collection("collection1", {"test": "metadata1"})
            vsm.create_collection("collection2", {"test": "metadata2"})
            
            # 列出集合
            collections = vsm.list_collections()
            assert "collection1" in collections
            assert "collection2" in collections

    def test_add_and_query_documents(self):
        """测试添加和查询文档"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            vsm = VectorStoreManager(persist_directory=temp_dir)
            
            # 创建集合
            collection_name = "test_collection"
            vsm.create_collection(collection_name, {"test": "metadata"})
            
            # 添加文档
            documents = ["This is document 1", "This is document 2"]
            metadatas = [{"source": "test1"}, {"source": "test2"}]
            ids = ["doc1", "doc2"]
            
            vsm.add_documents(collection_name, documents, metadatas, ids)
            
            # 查询文档
            results = vsm.query_collection(
                collection_name, 
                query_texts=["document 1"], 
                n_results=1
            )
            
            assert len(results["ids"][0]) == 1
            # 由于ChromaDB的查询结果可能不完全匹配，我们只验证查询成功执行


class TestLLMClient:
    """测试LLM客户端"""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_init(self):
        """测试初始化"""
        # 这里我们只测试初始化不抛出异常
        llm = LLMClient(model_name="gpt-3.5-turbo", temperature=0.0)
        assert llm.model_name == "gpt-3.5-turbo"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.core.llm_client.ChatOpenAI")
    def test_generate_text(self, mock_chat_openai):
        """测试生成文本"""
        # Mock模型响应
        mock_response = MagicMock()
        mock_response.content = "Generated text"
        mock_chat_openai.return_value.invoke.return_value = mock_response
        
        llm = LLMClient()
        result = llm.generate_text("Test prompt")
        
        assert result == "Generated text"


class TestDocumentParser:
    """测试文档解析器"""

    def test_init(self):
        """测试初始化"""
        parser = DocumentParser()
        assert parser is not None

    # Note: PDF解析测试需要实际的PDF文件，这里省略


class TestCacheManager:
    """测试缓存管理器"""

    def test_init(self):
        """测试初始化"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            cache = CacheManager(cache_directory=temp_dir)
            assert cache.cache_directory == temp_dir
            assert cache.cache is not None

    def test_set_and_get(self):
        """测试设置和获取缓存值"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            cache = CacheManager(cache_directory=temp_dir)
            
            # 设置值
            cache.set("key1", "value1")
            
            # 获取值
            result = cache.get("key1")
            assert result == "value1"

    def test_delete(self):
        """测试删除缓存值"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            cache = CacheManager(cache_directory=temp_dir)
            
            # 设置值
            cache.set("key1", "value1")
            
            # 删除值
            result = cache.delete("key1")
            assert result is True
            
            # 再次获取应该返回默认值
            result = cache.get("key1")
            assert result is None


class TestMetadataModels:
    """测试元数据模型"""

    def test_resume_metadata(self):
        """测试简历元数据模型"""
        metadata = ResumeMetadata(
            name="John Doe",
            email="john@example.com",
            phone="123-456-7890",
            skills=["Python", "Java"],
            expected_salary="100k-120k"
        )
        
        assert metadata.name == "John Doe"
        assert metadata.email == "john@example.com"
        assert "Python" in metadata.skills
        assert metadata.expected_salary == "100k-120k"

    def test_query_metadata(self):
        """测试查询元数据模型"""
        metadata = QueryMetadata(
            keywords=["developer", "engineer"],
            required_skills=["Python", "SQL"],
            min_experience_years=5,
            locations=["Beijing", "Shanghai"]
        )
        
        assert "developer" in metadata.keywords
        assert "Python" in metadata.required_skills
        assert metadata.min_experience_years == 5
        assert "Beijing" in metadata.locations


if __name__ == "__main__":
    pytest.main([__file__])