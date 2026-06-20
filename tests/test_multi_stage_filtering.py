import pytest
from unittest.mock import patch, MagicMock

from app.core.filter import HardFilter
from app.core.scorer import Scorer
from app.core.ranker import Ranker
from app.models.metadata import QueryMetadata


def test_multi_stage_filtering_integration():
    """测试多阶段筛选逻辑的集成流程"""
    # 创建模拟简历数据
    sample_resumes = [
        {
            "id": "resume_001",
            "text": "张三的简历，拥有5年Python开发经验，熟悉Django框架，曾在互联网公司工作",
            "metadata": {
                "name": "张三",
                "skills": ["Python", "Django", "MySQL"],
                "work_experience": [
                    {"company": "互联网公司", "start_date": "2019-01", "end_date": "2023-12"}
                ],
                "education": [{"degree": "本科"}],
                "preferred_locations": ["北京"],
                "expected_salary": "20K-30K",
                "languages": ["中文", "英语"],
                "certifications": ["软件设计师"],
                "summary": "Python开发工程师，有丰富的Web开发经验"
            }
        },
        {
            "id": "resume_002",
            "text": "李四的简历，拥有3年Java开发经验，熟悉Spring框架，曾在金融公司工作",
            "metadata": {
                "name": "李四",
                "skills": ["Java", "Spring", "Oracle"],
                "work_experience": [
                    {"company": "金融公司", "start_date": "2021-01", "end_date": "2023-12"}
                ],
                "education": [{"degree": "硕士"}],
                "preferred_locations": ["上海"],
                "expected_salary": "15K-25K",
                "languages": ["中文"],
                "certifications": [],
                "summary": "Java开发工程师，专注于后端服务开发"
            }
        },
        {
            "id": "resume_003",
            "text": "王五的简历，拥有4年Python开发经验，熟悉Flask框架，曾在电商公司工作",
            "metadata": {
                "name": "王五",
                "skills": ["Python", "Flask", "PostgreSQL"],
                "work_experience": [
                    {"company": "电商公司", "start_date": "2020-01", "end_date": "2023-12"}
                ],
                "education": [{"degree": "本科"}],
                "preferred_locations": ["北京", "深圳"],
                "expected_salary": "18K-28K",
                "languages": ["中文", "英语"],
                "certifications": ["PMP"],
                "summary": "Python全栈工程师，熟悉电商平台开发"
            }
        }
    ]
    
    # 创建查询元数据
    query_metadata = QueryMetadata(
        keywords=["Python", "后端"],
        required_skills=["Python"],
        min_experience_years=3,
        required_education="本科",
        required_industries=["互联网", "电商"],
        locations=["北京"],
        required_languages=["英语"],
        salary_range={"min": "15K", "max": "35K"}
    )
    
    # 创建筛选器、评分器和排名器
    hard_filter = HardFilter()
    scorer = Scorer()
    ranker = Ranker()
    
    # 执行多阶段筛选
    # 第一阶段：硬性条件过滤
    filtered_resumes = hard_filter.filter_resumes(sample_resumes, query_metadata)
    
    # 第二阶段：多维度评分
    scored_resumes = scorer.score_resumes(filtered_resumes, query_metadata)
    
    # 第三阶段：综合评分与排序
    ranked_resumes = ranker.rank_resumes(scored_resumes, query_metadata)
    
    # 验证结果
    # 应该只有张三和王五的简历通过硬性条件过滤（李四不满足行业要求）
    assert len(ranked_resumes) == 2
    
    # 验证排序结果（张三的综合得分应该高于王五）
    assert ranked_resumes[0]["id"] == "resume_001"  # 张三
    assert ranked_resumes[1]["id"] == "resume_003"  # 王五
    
    # 验证排名信息
    assert ranked_resumes[0]["rank"] == 1
    assert ranked_resumes[1]["rank"] == 2
    
    # 验证得分信息
    assert "scores" in ranked_resumes[0]
    assert "overall_score" in ranked_resumes[0]["scores"]
    assert ranked_resumes[0]["scores"]["overall_score"] > 0


if __name__ == "__main__":
    test_multi_stage_filtering_integration()
    print("Multi-stage filtering integration test passed!")