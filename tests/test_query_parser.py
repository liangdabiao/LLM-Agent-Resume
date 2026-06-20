"""
测试查询理解模块
"""
import pytest
import os
from unittest.mock import patch, MagicMock

from app.core.query_parser import QueryParser
from app.core.llm_client import LLMClient
from app.models.metadata import QueryMetadata


class TestQueryParser:
    """测试查询解析器"""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://test.url/v1"})
    def test_init(self):
        """测试初始化"""
        llm_client = LLMClient()
        parser = QueryParser(llm_client)
        assert parser.llm_client == llm_client

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://test.url/v1"})
    @patch("app.core.query_parser.LLMClient")
    def test_parse_query(self, mock_llm_client_class):
        """测试查询解析"""
        # Mock LLM客户端实例
        mock_llm_client = MagicMock()
        mock_response = '{"keywords": ["Python", "后端"], "required_skills": ["Python", "Django"], "min_experience_years": 3}'
        mock_llm_client.generate_text.return_value = mock_response
        mock_llm_client_class.return_value = mock_llm_client
        
        # 创建查询解析器
        parser = QueryParser(mock_llm_client)
        
        # 测试解析查询
        query_text = "寻找3年以上经验的Python后端工程师，熟悉Django框架"
        query_metadata = parser.parse_query(query_text)
        
        # 验证结果
        assert isinstance(query_metadata, QueryMetadata)
        assert "Python" in query_metadata.keywords
        assert "Python" in query_metadata.required_skills
        assert "Django" in query_metadata.required_skills
        assert query_metadata.min_experience_years == 3

    def test_parse_response(self):
        """测试解析响应"""
        # 创建真实的查询解析器实例（不依赖LLM客户端）
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://test.url/v1"}):
            llm_client = LLMClient()
            parser = QueryParser(llm_client)
            
            # 测试直接JSON响应
            response = '{"keywords": ["Java", "后端"], "min_experience_years": 5}'
            result = parser._parse_response(response)
            assert "Java" in result["keywords"]
            assert result["min_experience_years"] == 5
            
            # 测试带额外文本的JSON响应
            response = '这是解释文本\\n{"keywords": ["Python", "前端"], "min_experience_years": 2}\\n这是更多解释文本'
            result = parser._parse_response(response)
            assert "Python" in result["keywords"]
            assert result["min_experience_years"] == 2

    def test_parse_response_invalid_json(self):
        """测试解析无效JSON响应"""
        # 创建真实的查询解析器实例（不依赖LLM客户端）
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://test.url/v1"}):
            llm_client = LLMClient()
            parser = QueryParser(llm_client)
            
            # 测试无效JSON响应
            response = "这不是有效的JSON"
            with pytest.raises(ValueError):
                parser._parse_response(response)


if __name__ == "__main__":
    pytest.main([__file__])