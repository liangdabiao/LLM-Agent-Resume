"""
测试检索器模块
"""
import pytest
from unittest.mock import patch, MagicMock

from app.core.retriever import Retriever
from app.core.vector_store import VectorStoreManager
from app.models.metadata import QueryMetadata


class TestRetriever:
    """测试检索器"""

    def test_init(self):
        """测试初始化"""
        # Mock向量存储管理器
        mock_vector_store_manager = MagicMock()
        
        # 创建检索器
        retriever = Retriever(mock_vector_store_manager)
        
        # 验证初始化
        assert retriever.vector_store_manager == mock_vector_store_manager

    def test_add_resume(self):
        """测试添加简历"""
        # Mock向量存储管理器
        mock_vector_store_manager = MagicMock()
        mock_vector_store_manager.get_collection.return_value = MagicMock()
        mock_vector_store_manager.add_documents.return_value = None
        
        # 创建检索器
        retriever = Retriever(mock_vector_store_manager)
        
        # 测试添加简历
        resume_id = "resume_001"
        resume_text = "这是一份简历文本内容"
        metadata = {"name": "张三", "skills": ["Python", "Java"]}
        
        retriever.add_resume(resume_id, resume_text, metadata)
        
        # 验证向量存储管理器的方法被调用
        mock_vector_store_manager.get_collection.assert_called_once_with("resumes")
        mock_vector_store_manager.add_documents.assert_called_once_with(
            collection_name="resumes",
            documents=[resume_text],
            metadatas=[metadata],
            ids=[resume_id]
        )

    def test_retrieve(self):
        """测试检索功能"""
        # Mock向量存储管理器
        mock_vector_store_manager = MagicMock()
        mock_vector_store_manager.query_collection.return_value = {
            "ids": [["resume_001", "resume_002"]],
            "documents": [["简历文本1", "简历文本2"]],
            "metadatas": [[{"name": "张三"}, {"name": "李四"}]],
            "distances": [[0.1, 0.2]]
        }
        
        # 创建检索器
        retriever = Retriever(mock_vector_store_manager)
        
        # 创建查询元数据
        query_metadata = QueryMetadata(
            keywords=["Python", "后端"],
            required_skills=["Python", "Django"],
            min_experience_years=3
        )
        
        # 执行检索
        results = retriever.retrieve(query_metadata, n_results=5)
        
        # 验证结果
        assert len(results) == 2
        assert results[0]["id"] == "resume_001"
        assert results[0]["text"] == "简历文本1"
        assert results[0]["metadata"]["name"] == "张三"
        assert results[0]["distance"] == 0.1
        
        # 验证向量存储管理器的方法被调用
        mock_vector_store_manager.query_collection.assert_called_once()
        args, kwargs = mock_vector_store_manager.query_collection.call_args
        assert kwargs["collection_name"] == "resumes"
        assert kwargs["n_results"] == 5
        # 检查查询文本是否包含查询条件
        assert "Python" in kwargs["query_texts"][0]
        assert "后端" in kwargs["query_texts"][0]
        assert "Django" in kwargs["query_texts"][0]
        assert "3年" in kwargs["query_texts"][0]

    def test_convert_query_to_text(self):
        """测试查询元数据转换为文本"""
        # Mock向量存储管理器
        mock_vector_store_manager = MagicMock()
        
        # 创建检索器
        retriever = Retriever(mock_vector_store_manager)
        
        # 创建查询元数据
        query_metadata = QueryMetadata(
            keywords=["Python", "后端"],
            required_skills=["Python", "Django"],
            min_experience_years=3,
            required_education="本科",
            required_industries=["互联网", "电商"],
            locations=["北京", "上海"],
            required_languages=["中文", "英语"]
        )
        
        # 转换查询元数据为文本
        query_text = retriever._convert_query_to_text(query_metadata)
        
        # 验证转换结果
        assert "Python" in query_text
        assert "后端" in query_text
        assert "Django" in query_text
        assert "3年" in query_text
        assert "本科" in query_text
        assert "互联网" in query_text
        assert "电商" in query_text
        assert "北京" in query_text
        assert "上海" in query_text
        assert "中文" in query_text
        assert "英语" in query_text

    def test_format_results(self):
        """测试格式化检索结果"""
        # Mock向量存储管理器
        mock_vector_store_manager = MagicMock()
        
        # 创建检索器
        retriever = Retriever(mock_vector_store_manager)
        
        # 创建模拟的检索结果
        mock_results = {
            "ids": [["resume_001", "resume_002"]],
            "documents": [["简历文本1", "简历文本2"]],
            "metadatas": [[{"name": "张三"}, {"name": "李四"}]],
            "distances": [[0.1, 0.2]]
        }
        
        # 格式化结果
        formatted_results = retriever._format_results(mock_results)
        
        # 验证格式化结果
        assert len(formatted_results) == 2
        assert formatted_results[0]["id"] == "resume_001"
        assert formatted_results[0]["text"] == "简历文本1"
        assert formatted_results[0]["metadata"]["name"] == "张三"
        assert formatted_results[0]["distance"] == 0.1
        
        assert formatted_results[1]["id"] == "resume_002"
        assert formatted_results[1]["text"] == "简历文本2"
        assert formatted_results[1]["metadata"]["name"] == "李四"
        assert formatted_results[1]["distance"] == 0.2

    def test_format_results_empty(self):
        """测试格式化空检索结果"""
        # Mock向量存储管理器
        mock_vector_store_manager = MagicMock()
        
        # 创建检索器
        retriever = Retriever(mock_vector_store_manager)
        
        # 创建空的检索结果
        mock_results = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }
        
        # 格式化结果
        formatted_results = retriever._format_results(mock_results)
        
        # 验证格式化结果为空列表
        assert formatted_results == []


if __name__ == "__main__":
    pytest.main([__file__])