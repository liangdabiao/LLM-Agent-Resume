import pytest
from unittest.mock import patch, MagicMock

from app.core.retriever import Retriever
from app.core.vector_store import VectorStoreManager
from app.models.metadata import QueryMetadata


def test_retrieval_integration():
    """测试检索功能的集成流程"""
    # 创建模拟的简历数据
    sample_resumes = [
        {
            "id": "resume_001",
            "text": "张三的简历，拥有5年Python开发经验，熟悉Django框架，曾在互联网公司工作",
            "metadata": {"name": "张三", "skills": ["Python", "Django", "MySQL"]}
        },
        {
            "id": "resume_002",
            "text": "李四的简历，拥有3年Java开发经验，熟悉Spring框架，曾在金融公司工作",
            "metadata": {"name": "李四", "skills": ["Java", "Spring", "Oracle"]}
        },
        {
            "id": "resume_003",
            "text": "王五的简历，拥有4年Python开发经验，熟悉Flask框架，曾在电商公司工作",
            "metadata": {"name": "王五", "skills": ["Python", "Flask", "PostgreSQL"]}
        }
    ]
    
    # 创建模拟的查询元数据
    query_metadata = QueryMetadata(
        keywords=["Python", "后端"],
        required_skills=["Python"],
        min_experience_years=3,
        required_industries=["互联网", "电商"]
    )
    
    # Mock向量存储管理器
    mock_vector_store_manager = MagicMock()
    mock_vector_store_manager.query_collection.return_value = {
        "ids": [["resume_001", "resume_003"]],
        "documents": [[sample_resumes[0]["text"], sample_resumes[2]["text"]]],
        "metadatas": [[sample_resumes[0]["metadata"], sample_resumes[2]["metadata"]]],
        "distances": [[0.1, 0.3]]
    }
    
    # 创建检索器
    retriever = Retriever(mock_vector_store_manager)
    
    # 添加简历到向量存储（模拟）
    for resume in sample_resumes:
        retriever.add_resume(resume["id"], resume["text"], resume["metadata"])
    
    # 执行检索
    results = retriever.retrieve(query_metadata, n_results=5)
    
    # 验证结果
    assert len(results) == 2
    assert results[0]["id"] == "resume_001"
    assert "张三" in results[0]["text"]
    assert "Python" in results[0]["metadata"]["skills"]
    
    assert results[1]["id"] == "resume_003"
    assert "王五" in results[1]["text"]
    assert "Python" in results[1]["metadata"]["skills"]
    
    # 验证向量存储管理器的方法被调用
    assert mock_vector_store_manager.get_collection.call_count >= 1
    assert mock_vector_store_manager.add_documents.call_count == 3
    mock_vector_store_manager.query_collection.assert_called_once()


if __name__ == "__main__":
    test_retrieval_integration()
    print("Retrieval integration test passed!")