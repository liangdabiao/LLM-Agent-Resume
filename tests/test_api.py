"""
测试API模块
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

from app.main import app

client = TestClient(app)


class TestAPI:
    """测试API接口"""

    def test_health_check(self):
        """测试健康检查接口"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @patch('app.api.routes.document_parser')
    @patch('app.api.routes.metadata_extractor')
    @patch('app.api.routes.retriever')
    def test_upload_resume(self, mock_retriever, mock_metadata_extractor, mock_document_parser):
        """测试上传简历接口"""
        # Mock各个组件
        mock_document_parser.parse_pdf.return_value = "这是一份简历文本"
        mock_metadata_extractor.extract_metadata.return_value = MagicMock(
            dict=MagicMock(return_value={
                "name": "张三",
                "email": "zhangsan@example.com"
            })
        )
        mock_retriever.add_resume.return_value = None

        # 创建测试文件
        test_content = b"This is a test resume file"
        
        # 发送上传请求
        response = client.post(
            "/api/v1/resumes",
            files={"file": ("test_resume.pdf", test_content, "application/pdf")}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "resume_id" in data
        assert "message" in data

    @patch('app.api.routes.query_parser')
    def test_submit_query(self, mock_query_parser):
        """测试提交筛选查询接口"""
        # Mock查询解析器
        mock_query_parser.parse_query.return_value = MagicMock(
            dict=MagicMock(return_value={
                "keywords": ["Python"],
                "required_skills": ["Python"]
            })
        )

        # 发送查询请求
        query_data = {"query_text": "寻找Python开发者"}
        response = client.post("/api/v1/queries", json=query_data)
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "query_id" in data
        assert "message" in data

    @patch('app.api.routes.query_storage')
    @patch('app.api.routes.retriever')
    @patch('app.api.routes.hard_filter')
    @patch('app.api.routes.scorer')
    @patch('app.api.routes.ranker')
    @patch('app.api.routes.candidate_analyzer')
    @patch('app.api.routes.result_formatter')
    def test_get_screening_results(self, mock_result_formatter, mock_candidate_analyzer, 
                                   mock_ranker, mock_scorer, mock_hard_filter, 
                                   mock_retriever, mock_query_storage):
        """测试获取筛选结果接口"""
        # Mock各个组件
        mock_query_storage.__contains__.return_value = True
        mock_query_storage.__getitem__.return_value = {
            "id": "test_query_id",
            "text": "寻找Python开发者",
            "metadata": {
                "keywords": ["Python"],
                "required_skills": ["Python"]
            },
            "created_at": "2025-01-01T00:00:00"
        }
        
        mock_retriever.retrieve.return_value = [
            {
                "id": "candidate_001",
                "text": "这是一份简历文本",
                "metadata": {
                    "name": "张三",
                    "email": "zhangsan@example.com",
                    "skills": ["Python", "Django"],
                    "work_experience": [],
                    "education": []
                }
            }
        ]
        
        mock_hard_filter.filter_resumes.return_value = [
            {
                "id": "candidate_001",
                "text": "这是一份简历文本",
                "metadata": {
                    "name": "张三",
                    "email": "zhangsan@example.com",
                    "skills": ["Python", "Django"],
                    "work_experience": [],
                    "education": []
                }
            }
        ]
        
        mock_scorer.score_resumes.return_value = [
            {
                "id": "candidate_001",
                "text": "这是一份简历文本",
                "metadata": {
                    "name": "张三",
                    "email": "zhangsan@example.com",
                    "skills": ["Python", "Django"],
                    "work_experience": [],
                    "education": []
                },
                "scores": {
                    "overall_score": 0.95,
                    "skill_score": 0.9
                }
            }
        ]
        
        mock_ranker.rank_resumes.return_value = [
            {
                "id": "candidate_001",
                "rank": 1,
                "text": "这是一份简历文本",
                "metadata": {
                    "name": "张三",
                    "email": "zhangsan@example.com",
                    "skills": ["Python", "Django"],
                    "work_experience": [],
                    "education": []
                },
                "scores": {
                    "overall_score": 0.95,
                    "skill_score": 0.9
                }
            }
        ]
        
        mock_candidate_analyzer.analyze_candidates.return_value = [
            {
                "id": "candidate_001",
                "rank": 1,
                "text": "这是一份简历文本",
                "metadata": {
                    "name": "张三",
                    "email": "zhangsan@example.com",
                    "skills": ["Python", "Django"],
                    "work_experience": [],
                    "education": []
                },
                "scores": {
                    "overall_score": 0.95,
                    "skill_score": 0.9
                },
                "analysis": "这是一份详细的候选人评价报告..."
            }
        ]
        
        mock_result_formatter.format_results.return_value = {
            "total_candidates": 1,
            "candidates": [
                {
                    "id": "candidate_001",
                    "rank": 1,
                    "name": "张三",
                    "contact_info": {
                        "email": "zhangsan@example.com",
                        "phone": "13800138000"
                    },
                    "scores": {
                        "overall_score": 0.95,
                        "skill_score": 0.9
                    },
                    "basic_info": {
                        "skills": ["Python", "Django"],
                        "expected_salary": "20K-30K",
                        "preferred_locations": ["北京"]
                    },
                    "analysis": "这是一份详细的候选人评价报告...",
                    "metadata": {
                        "work_experience": [],
                        "education": []
                    }
                }
            ],
            "summary": {
                "average_score": 0.95
            }
        }

        # 发送获取结果请求
        response = client.get("/api/v1/results/test_query_id")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["query_id"] == "test_query_id"
        assert data["total_candidates"] == 1
        assert len(data["candidates"]) == 1
        assert data["candidates"][0]["name"] == "张三"

    def test_get_resume_not_found(self):
        """测试获取不存在的简历"""
        response = client.get("/api/v1/resumes/nonexistent_id")
        assert response.status_code == 404

    def test_get_screening_results_not_found(self):
        """测试获取不存在的筛选结果"""
        with patch('app.api.routes.query_storage') as mock_query_storage:
            mock_query_storage.__contains__.return_value = False
            
            response = client.get("/api/v1/results/nonexistent_id")
            assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__])