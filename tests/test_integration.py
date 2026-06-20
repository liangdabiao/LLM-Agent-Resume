import pytest
from unittest.mock import patch, MagicMock
import os

from app.core.document_parser import DocumentParser
from app.core.extractor import MetadataExtractor
from app.core.llm_client import LLMClient
from app.models.metadata import ResumeMetadata


def test_document_parsing_and_metadata_extraction():
    """测试文档解析和元数据提取的集成流程"""
    # 创建一个模拟的简历文本
    sample_resume_text = """
    张三
    邮箱: zhangsan@example.com
    电话: 13800138000
    地址: 北京市朝阳区

    工作经历:
    2020.01 - 2023.12  ABC公司 软件工程师
    - 负责软件开发和维护
    - 参与项目需求分析和设计

    教育背景:
    2016.09 - 2020.06 清华大学 计算机科学与技术 本科

    技能:
    Python, Java, SQL

    项目经历:
    2022.01 - 2022.06 电商系统
    - 开发了一个电商系统

    语言能力:
    中文(母语), 英语(熟练)

    证书:
    软件设计师

    期望薪资: 20K-30K
    期望工作地点: 北京, 上海

    个人简介:
    具有5年工作经验的软件工程师
    """

    # 测试文档解析器
    parser = DocumentParser()
    assert parser is not None

    # 测试元数据提取器
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://test.url/v1"}):
        llm_client = LLMClient()
        
        # Mock LLM客户端的响应
        with patch.object(llm_client, 'generate_text', return_value='{"name": "张三", "email": "zhangsan@example.com", "phone": "13800138000", "skills": ["Python", "Java", "SQL"]}') as mock_generate:
            extractor = MetadataExtractor(llm_client)
            
            # 提取元数据
            metadata = extractor.extract_metadata(sample_resume_text)
            
            # 验证结果
            assert isinstance(metadata, ResumeMetadata)
            assert metadata.name == "张三"
            assert metadata.email == "zhangsan@example.com"
            assert metadata.phone == "13800138000"
            assert "Python" in metadata.skills
            assert "Java" in metadata.skills
            assert "SQL" in metadata.skills
            
            # 验证LLM客户端被调用
            mock_generate.assert_called_once()


if __name__ == "__main__":
    test_document_parsing_and_metadata_extraction()
    print("Document parsing and metadata extraction integration test passed!")