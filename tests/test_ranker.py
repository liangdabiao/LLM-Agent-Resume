"""
测试排名器模块
"""
import pytest
from app.core.ranker import Ranker


class TestRanker:
    """测试排名器"""

    def test_init(self):
        """测试初始化"""
        ranker = Ranker()
        assert ranker is not None

    def test_rank_resumes(self):
        """测试简历排序功能"""
        ranker = Ranker()
        
        # 创建模拟简历数据（包含评分）
        resumes = [
            {
                "id": "resume_001",
                "scores": {
                    "overall_score": 0.8
                }
            },
            {
                "id": "resume_002",
                "scores": {
                    "overall_score": 0.9
                }
            },
            {
                "id": "resume_003",
                "scores": {
                    "overall_score": 0.7
                }
            }
        ]
        
        # 执行排序
        ranked_resumes = ranker.rank_resumes(resumes, None)
        
        # 验证结果（按得分降序排列）
        assert len(ranked_resumes) == 3
        assert ranked_resumes[0]["id"] == "resume_002"
        assert ranked_resumes[1]["id"] == "resume_001"
        assert ranked_resumes[2]["id"] == "resume_003"
        
        # 验证排名信息
        assert ranked_resumes[0]["rank"] == 1
        assert ranked_resumes[1]["rank"] == 2
        assert ranked_resumes[2]["rank"] == 3

    def test_get_top_resumes(self):
        """测试获取前N名简历"""
        ranker = Ranker()
        
        # 创建模拟简历数据（已排序）
        ranked_resumes = [
            {"id": "resume_001", "rank": 1},
            {"id": "resume_002", "rank": 2},
            {"id": "resume_003", "rank": 3},
            {"id": "resume_004", "rank": 4},
            {"id": "resume_005", "rank": 5}
        ]
        
        # 获取前3名简历
        top_resumes = ranker.get_top_resumes(ranked_resumes, 3)
        
        # 验证结果
        assert len(top_resumes) == 3
        assert top_resumes[0]["id"] == "resume_001"
        assert top_resumes[1]["id"] == "resume_002"
        assert top_resumes[2]["id"] == "resume_003"

    def test_filter_by_threshold(self):
        """测试根据阈值过滤简历"""
        ranker = Ranker()
        
        # 创建模拟简历数据（已排序）
        ranked_resumes = [
            {"id": "resume_001", "scores": {"overall_score": 0.9}},
            {"id": "resume_002", "scores": {"overall_score": 0.7}},
            {"id": "resume_003", "scores": {"overall_score": 0.5}},
            {"id": "resume_004", "scores": {"overall_score": 0.3}}
        ]
        
        # 过滤得分至少为0.6的简历
        filtered_resumes = ranker.filter_by_threshold(ranked_resumes, 0.6)
        
        # 验证结果
        assert len(filtered_resumes) == 2
        assert filtered_resumes[0]["id"] == "resume_001"
        assert filtered_resumes[1]["id"] == "resume_002"


if __name__ == "__main__":
    pytest.main([__file__])