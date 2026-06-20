import pytest
from unittest.mock import patch, MagicMock
import os

from app.core.query_parser import QueryParser
from app.core.llm_client import LLMClient
from app.models.metadata import QueryMetadata


def test_query_parsing_integration():
    """测试查询解析的集成流程"""
    # 创建一个模拟的查询文本
    sample_query_text = "寻找3年以上经验的Python后端工程师，熟悉Django和Flask框架，有电商平台经验者优先，薪资范围20K-35K，工作地点在北京或上海"

    # 测试查询解析器
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://test.url/v1"}):
        llm_client = LLMClient()
        
        # Mock LLM客户端的响应
        mock_response = '{"keywords": ["Python", "后端"], "required_skills": ["Python", "Django", "Flask"], "min_experience_years": 3, "preferred_industries": ["电商"], "salary_range": {"min": "20K", "max": "35K"}, "locations": ["北京", "上海"]}'
        
        with patch.object(llm_client, 'generate_text', return_value=mock_response) as mock_generate:
            parser = QueryParser(llm_client)
            
            # 解析查询
            query_metadata = parser.parse_query(sample_query_text)
            
            # 验证结果
            assert isinstance(query_metadata, QueryMetadata)
            assert "Python" in query_metadata.keywords
            assert "Python" in query_metadata.required_skills
            assert "Django" in query_metadata.required_skills
            assert "Flask" in query_metadata.required_skills
            assert query_metadata.min_experience_years == 3
            assert "电商" in query_metadata.preferred_industries
            assert query_metadata.salary_range["min"] == "20K"
            assert query_metadata.salary_range["max"] == "35K"
            assert "北京" in query_metadata.locations
            assert "上海" in query_metadata.locations
            
            # 验证LLM客户端被调用
            mock_generate.assert_called_once()


if __name__ == "__main__":
    test_query_parsing_integration()
    print("Query parsing integration test passed!")