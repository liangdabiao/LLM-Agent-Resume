"""
测试候选人分析器模块
"""
import pytest
import os
from unittest.mock import patch, MagicMock

from app.core.analyzer import CandidateAnalyzer
from app.core.llm_client import LLMClient
from app.models.metadata import QueryMetadata


class TestCandidateAnalyzer:
    """测试候选人分析器"""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://test.url/v1"})
    def test_init(self):
        """测试初始化"""
        llm_client = LLMClient()
        analyzer = CandidateAnalyzer(llm_client)
        assert analyzer.llm_client == llm_client

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://test.url/v1"})
    @patch("app.core.analyzer.LLMClient")
    def test_analyze_candidate(self, mock_llm_client_class):
        """测试分析单个候选人"""
        # Mock LLM客户端
        mock_llm_client = MagicMock()
        mock_llm_client.generate_text.return_value = "这是一份详细的候选人评价报告..."
        mock_llm_client_class.return_value = mock_llm_client
        
        # 创建分析器
        analyzer = CandidateAnalyzer(mock_llm_client)
        
        # 创建模拟简历数据
        resume = {
            "id": "resume_001",
            "metadata": {
                "name": "张三",
                "skills": ["Python", "Django"],
                "work_experience": [
                    {
                        "company": "互联网公司",
                        "title": "软件工程师",
                        "start_date": "2020-01",
                        "end_date": "2023-12",
                        "description": "负责后端开发工作"
                    }
                ],
                "education": [
                    {
                        "institution": "清华大学",
                        "major": "计算机科学",
                        "degree": "本科",
                        "start_date": "2016-09",
                        "end_date": "2020-06"
                    }
                ]
            }
        }
        
        # 创建查询元数据
        query_metadata = QueryMetadata(
            required_skills=["Python"],
            min_experience_years=3
        )
        
        # 分析候选人
        analyzed_candidate = analyzer.analyze_candidate(resume, query_metadata)
        
        # 验证结果
        assert analyzed_candidate["id"] == "resume_001"
        assert "analysis" in analyzed_candidate
        assert analyzed_candidate["analysis"] == "这是一份详细的候选人评价报告..."
        
        # 验证LLM客户端被调用
        mock_llm_client.generate_text.assert_called_once()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://test.url/v1"})
    @patch("app.core.analyzer.LLMClient")
    def test_analyze_candidates(self, mock_llm_client_class):
        """测试批量分析候选人"""
        # Mock LLM客户端
        mock_llm_client = MagicMock()
        mock_llm_client.generate_text.return_value = "这是一份详细的候选人评价报告..."
        mock_llm_client_class.return_value = mock_llm_client
        
        # 创建分析器
        analyzer = CandidateAnalyzer(mock_llm_client)
        
        # 创建模拟简历数据
        resumes = [
            {
                "id": "resume_001",
                "metadata": {"name": "张三"}
            },
            {
                "id": "resume_002",
                "metadata": {"name": "李四"}
            }
        ]
        
        # 创建查询元数据
        query_metadata = QueryMetadata()
        
        # 批量分析候选人
        analyzed_candidates = analyzer.analyze_candidates(resumes, query_metadata)
        
        # 验证结果
        assert len(analyzed_candidates) == 2
        assert analyzed_candidates[0]["id"] == "resume_001"
        assert analyzed_candidates[1]["id"] == "resume_002"
        assert "analysis" in analyzed_candidates[0]
        assert "analysis" in analyzed_candidates[1]
        
        # 验证LLM客户端被调用两次
        assert mock_llm_client.generate_text.call_count == 2

    def test_format_work_experience(self):
        """测试格式化工作经历"""
        # 创建分析器实例（不依赖LLM客户端）
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://test.url/v1"}):
            llm_client = LLMClient()
            analyzer = CandidateAnalyzer(llm_client)
        
        # 创建模拟工作经历数据
        work_experience = [
            {
                "company": "互联网公司",
                "title": "软件工程师",
                "start_date": "2020-01",
                "end_date": "2023-12",
                "description": "负责后端开发工作"
            }
        ]
        
        # 格式化工作经历
        formatted = analyzer._format_work_experience(work_experience)
        
        # 验证结果
        assert "互联网公司" in formatted
        assert "软件工程师" in formatted
        assert "2020-01" in formatted
        assert "2023-12" in formatted
        assert "负责后端开发工作" in formatted

    def test_format_education(self):
        """测试格式化教育背景"""
        # 创建分析器实例（不依赖LLM客户端）
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://test.url/v1"}):
            llm_client = LLMClient()
            analyzer = CandidateAnalyzer(llm_client)
        
        # 创建模拟教育背景数据
        education = [
            {
                "institution": "清华大学",
                "major": "计算机科学",
                "degree": "本科",
                "start_date": "2016-09",
                "end_date": "2020-06"
            }
        ]
        
        # 格式化教育背景
        formatted = analyzer._format_education(education)
        
        # 验证结果
        assert "清华大学" in formatted
        assert "计算机科学" in formatted
        assert "本科" in formatted
        assert "2016-09" in formatted
        assert "2020-06" in formatted


if __name__ == "__main__":
    pytest.main([__file__])