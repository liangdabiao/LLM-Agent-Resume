import pytest
import os
from unittest.mock import patch, MagicMock

from app.core.analyzer import CandidateAnalyzer
from app.core.result_formatter import ResultFormatter
from app.core.llm_client import LLMClient
from app.models.metadata import QueryMetadata


def test_candidate_analysis_and_result_formatting_integration():
    """测试候选人分析与结果格式化流程的集成"""
    # 创建模拟候选人数据
    sample_candidates = [
        {
            "id": "candidate_001",
            "rank": 1,
            "metadata": {
                "name": "张三",
                "email": "zhangsan@example.com",
                "phone": "13800138000",
                "skills": ["Python", "Django", "MySQL"],
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
                ],
                "expected_salary": "20K-30K",
                "preferred_locations": ["北京"]
            },
            "scores": {
                "overall_score": 0.95,
                "skill_score": 0.9,
                "experience_score": 0.8
            }
        },
        {
            "id": "candidate_002",
            "rank": 2,
            "metadata": {
                "name": "李四",
                "email": "lisi@example.com",
                "phone": "13800138001",
                "skills": ["Java", "Spring", "Oracle"],
                "work_experience": [
                    {
                        "company": "金融公司",
                        "title": "后端工程师",
                        "start_date": "2021-01",
                        "end_date": "2023-12",
                        "description": "负责金融系统开发"
                    }
                ],
                "education": [
                    {
                        "institution": "北京大学",
                        "major": "软件工程",
                        "degree": "硕士",
                        "start_date": "2019-09",
                        "end_date": "2021-06"
                    }
                ],
                "expected_salary": "15K-25K",
                "preferred_locations": ["上海"]
            },
            "scores": {
                "overall_score": 0.85,
                "skill_score": 0.8,
                "experience_score": 0.7
            }
        }
    ]
    
    # 创建查询元数据
    query_metadata = QueryMetadata(
        keywords=["Python", "后端"],
        required_skills=["Python"],
        min_experience_years=3,
        required_education="本科",
        locations=["北京"]
    )
    
    # Mock LLM客户端
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://test.url/v1"}):
        llm_client = LLMClient()
        
        # Mock LLM客户端的响应
        with patch.object(llm_client, 'generate_text', return_value="这是一份详细的候选人评价报告...") as mock_generate:
            # 创建分析器和格式化器
            analyzer = CandidateAnalyzer(llm_client)
            formatter = ResultFormatter()
            
            # 执行候选人分析
            analyzed_candidates = analyzer.analyze_candidates(sample_candidates, query_metadata)
            
            # 格式化结果
            formatted_results = formatter.format_results(analyzed_candidates, query_metadata)
            
            # 验证结果
            assert formatted_results["total_candidates"] == 2
            assert len(formatted_results["candidates"]) == 2
            
            # 验证第一个候选人
            candidate_1 = formatted_results["candidates"][0]
            assert candidate_1["id"] == "candidate_001"
            assert candidate_1["rank"] == 1
            assert candidate_1["name"] == "张三"
            assert candidate_1["scores"]["overall_score"] == 0.95
            assert candidate_1["analysis"] == "这是一份详细的候选人评价报告..."
            assert candidate_1["contact_info"]["email"] == "zhangsan@example.com"
            assert "Python" in candidate_1["basic_info"]["skills"]
            
            # 验证第二个候选人
            candidate_2 = formatted_results["candidates"][1]
            assert candidate_2["id"] == "candidate_002"
            assert candidate_2["rank"] == 2
            assert candidate_2["name"] == "李四"
            assert candidate_2["scores"]["overall_score"] == 0.85
            assert candidate_2["analysis"] == "这是一份详细的候选人评价报告..."
            assert candidate_2["contact_info"]["email"] == "lisi@example.com"
            assert "Java" in candidate_2["basic_info"]["skills"]
            
            # 验证查询信息
            assert "Python" in formatted_results["query"]["keywords"]
            assert "Python" in formatted_results["query"]["required_skills"]
            
            # 验证摘要信息
            assert abs(formatted_results["summary"]["average_score"] - 0.9) < 0.001
            assert formatted_results["summary"]["top_score"] == 0.95
            assert formatted_results["summary"]["bottom_score"] == 0.85
            
            # 验证LLM客户端被调用
            assert mock_generate.call_count == 2


if __name__ == "__main__":
    test_candidate_analysis_and_result_formatting_integration()
    print("Candidate analysis and result formatting integration test passed!")