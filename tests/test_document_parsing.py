"""
测试文档解析与元数据提取模块
"""
import pytest
import os
from unittest.mock import patch, MagicMock

from app.core.document_parser import DocumentParser
from app.core.extractor import MetadataExtractor
from app.core.llm_client import LLMClient
from app.models.metadata import ResumeMetadata


class TestDocumentParser:
    """测试文档解析器"""

    def test_init(self):
        """测试初始化"""
        parser = DocumentParser()
        assert parser is not None

    # Note: PDF解析测试需要实际的PDF文件，这里省略


class TestMetadataExtractor:
    """测试元数据提取器"""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://test.url/v1"})
    def test_init(self):
        """测试初始化"""
        llm_client = LLMClient()
        extractor = MetadataExtractor(llm_client)
        assert extractor.llm_client == llm_client

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://test.url/v1"})
    @patch("app.core.extractor.LLMClient")
    def test_extract_metadata(self, mock_llm_client_class):
        """测试元数据提取"""
        # Mock LLM客户端实例
        mock_llm_client = MagicMock()
        mock_llm_client.generate_text.return_value = '{"name": "张三", "email": "zhangsan@example.com", "phone": "13800138000"}'
        mock_llm_client_class.return_value = mock_llm_client
        
        # 创建提取器
        extractor = MetadataExtractor(mock_llm_client)
        
        # 测试提取元数据
        resume_text = "张三的简历内容..."
        metadata = extractor.extract_metadata(resume_text)
        
        # 验证结果
        assert isinstance(metadata, ResumeMetadata)
        assert metadata.name == "张三"
        assert metadata.email == "zhangsan@example.com"
        assert metadata.phone == "13800138000"

    def test_parse_response(self):
        """测试解析响应"""
        # 创建真实的提取器实例（不依赖LLM客户端）
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://test.url/v1"}):
            llm_client = LLMClient()
            extractor = MetadataExtractor(llm_client)
            
            # 测试直接JSON响应
            response = '{"name": "李四", "email": "lisi@example.com"}'
            result = extractor._parse_response(response)
            assert result["name"] == "李四"
            assert result["email"] == "lisi@example.com"
            
            # 测试带额外文本的JSON响应
            response = '这是解释文本\n{"name": "王五", "email": "wangwu@example.com"}\n这是更多解释文本'
            result = extractor._parse_response(response)
            assert result["name"] == "王五"
            assert result["email"] == "wangwu@example.com"

    def test_parse_response_invalid_json(self):
        """测试解析无效JSON响应"""
        # 创建真实的提取器实例（不依赖LLM客户端）
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://test.url/v1"}):
            llm_client = LLMClient()
            extractor = MetadataExtractor(llm_client)
            
            # 测试无效JSON响应
            response = "这不是有效的JSON"
            with pytest.raises(ValueError):
                extractor._parse_response(response)


if __name__ == "__main__":
    pytest.main([__file__])