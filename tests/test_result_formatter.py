"""
测试结果格式化器模块
"""
import pytest
import os
import tempfile
from app.core.result_formatter import ResultFormatter
from app.models.metadata import QueryMetadata


class TestResultFormatter:
    """测试结果格式化器"""

    def test_init(self):
        """测试初始化"""
        formatter = ResultFormatter()
        assert formatter is not None

    def test_format_results(self):
        """测试格式化结果"""
        formatter = ResultFormatter()
        
        # 创建模拟候选人数据
        candidates = [
            {
                "id": "resume_001",
                "rank": 1,
                "metadata": {
                    "name": "张三",
                    "email": "zhangsan@example.com",
                    "phone": "13800138000",
                    "skills": ["Python", "Django"],
                    "expected_salary": "20K-30K",
                    "preferred_locations": ["北京"]
                },
                "scores": {
                    "overall_score": 0.95,
                    "skill_score": 0.9,
                    "experience_score": 0.8
                },
                "analysis": "这是一份详细的候选人评价报告..."
            }
        ]
        
        # 创建查询元数据
        query_metadata = QueryMetadata(
            keywords=["Python"],
            required_skills=["Python"]
        )
        
        # 格式化结果
        formatted_results = formatter.format_results(candidates, query_metadata)
        
        # 验证结果
        assert formatted_results["total_candidates"] == 1
        assert len(formatted_results["candidates"]) == 1
        assert formatted_results["candidates"][0]["id"] == "resume_001"
        assert formatted_results["candidates"][0]["rank"] == 1
        assert formatted_results["candidates"][0]["name"] == "张三"
        assert formatted_results["candidates"][0]["scores"]["overall_score"] == 0.95
        assert formatted_results["candidates"][0]["analysis"] == "这是一份详细的候选人评价报告..."
        assert formatted_results["summary"]["average_score"] == 0.95

    def test_format_query(self):
        """测试格式化查询信息"""
        formatter = ResultFormatter()
        
        # 创建查询元数据
        query_metadata = QueryMetadata(
            keywords=["Python", "后端"],
            required_skills=["Python"],
            min_experience_years=3
        )
        
        # 格式化查询信息
        formatted_query = formatter._format_query(query_metadata)
        
        # 验证结果
        assert "Python" in formatted_query["keywords"]
        assert "Python" in formatted_query["required_skills"]
        assert formatted_query["min_experience_years"] == 3

    def test_format_candidates(self):
        """测试格式化候选人列表"""
        formatter = ResultFormatter()
        
        # 创建模拟候选人数据
        candidates = [
            {
                "id": "resume_001",
                "rank": 1,
                "metadata": {
                    "name": "张三",
                    "email": "zhangsan@example.com",
                    "phone": "13800138000",
                    "skills": ["Python", "Django"],
                    "expected_salary": "20K-30K",
                    "preferred_locations": ["北京"]
                },
                "scores": {
                    "overall_score": 0.95
                },
                "analysis": "这是一份详细的候选人评价报告..."
            }
        ]
        
        # 格式化候选人列表
        formatted_candidates = formatter._format_candidates(candidates)
        
        # 验证结果
        assert len(formatted_candidates) == 1
        assert formatted_candidates[0]["id"] == "resume_001"
        assert formatted_candidates[0]["rank"] == 1
        assert formatted_candidates[0]["name"] == "张三"
        assert formatted_candidates[0]["contact_info"]["email"] == "zhangsan@example.com"
        assert formatted_candidates[0]["contact_info"]["phone"] == "13800138000"
        assert "Python" in formatted_candidates[0]["basic_info"]["skills"]
        assert formatted_candidates[0]["basic_info"]["expected_salary"] == "20K-30K"
        assert "北京" in formatted_candidates[0]["basic_info"]["preferred_locations"]
        assert formatted_candidates[0]["scores"]["overall_score"] == 0.95
        assert formatted_candidates[0]["analysis"] == "这是一份详细的候选人评价报告..."

    def test_generate_summary(self):
        """测试生成结果摘要"""
        formatter = ResultFormatter()
        
        # 创建模拟候选人数据
        candidates = [
            {
                "scores": {"overall_score": 0.9}
            },
            {
                "scores": {"overall_score": 0.8}
            },
            {
                "scores": {"overall_score": 0.7}
            }
        ]
        
        # 生成摘要
        summary = formatter._generate_summary(candidates)
        
        # 验证结果
        assert abs(summary["average_score"] - 0.8) < 0.001
        assert summary["top_score"] == 0.9
        assert summary["bottom_score"] == 0.7

    def test_export_to_json(self):
        """测试导出为JSON文件"""
        formatter = ResultFormatter()
        
        # 创建模拟结果数据
        results = {
            "total_candidates": 1,
            "candidates": [
                {
                    "id": "resume_001",
                    "name": "张三"
                }
            ]
        }
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp_file:
            tmp_file_path = tmp_file.name
        
        try:
            # 导出为JSON文件
            formatter.export_to_json(results, tmp_file_path)
            
            # 验证文件是否存在
            assert os.path.exists(tmp_file_path)
            
            # 读取文件内容并验证
            with open(tmp_file_path, 'r', encoding='utf-8') as f:
                import json
                content = json.load(f)
                assert content["total_candidates"] == 1
                assert content["candidates"][0]["name"] == "张三"
        finally:
            # 清理临时文件
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    def test_export_to_text(self):
        """测试导出为文本文件"""
        formatter = ResultFormatter()
        
        # 创建模拟结果数据
        results = {
            "query": {
                "keywords": ["Python"]
            },
            "total_candidates": 1,
            "candidates": [
                {
                    "rank": 1,
                    "name": "张三",
                    "scores": {"overall_score": 0.95},
                    "basic_info": {
                        "skills": ["Python"],
                        "expected_salary": "20K-30K",
                        "preferred_locations": ["北京"]
                    },
                    "analysis": "这是一份详细的候选人评价报告..."
                }
            ],
            "summary": {
                "average_score": 0.95
            }
        }
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as tmp_file:
            tmp_file_path = tmp_file.name
        
        try:
            # 导出为文本文件
            formatter.export_to_text(results, tmp_file_path)
            
            # 验证文件是否存在
            assert os.path.exists(tmp_file_path)
            
            # 读取文件内容并验证
            with open(tmp_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "职位筛选结果报告" in content
                assert "张三" in content
                assert "0.95" in content
        finally:
            # 清理临时文件
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)


if __name__ == "__main__":
    pytest.main([__file__])