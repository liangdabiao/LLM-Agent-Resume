"""
测试多维度评分器模块
"""
import pytest
from app.core.scorer import Scorer
from app.models.metadata import QueryMetadata


class TestScorer:
    """测试多维度评分器"""

    def test_init(self):
        """测试初始化"""
        scorer = Scorer()
        assert scorer is not None

    def test_calculate_skill_score(self):
        """测试技能匹配得分计算"""
        scorer = Scorer()

        resume = {
            "metadata": {
                "skills": ["Python", "Java", "SQL"]
            }
        }

        query_metadata = QueryMetadata(
            required_skills=["Python", "SQL"],
            preferred_skills=["Redis"]
        )

        skill_score = scorer._calculate_skill_score(resume, query_metadata)

        # 必需技能完全匹配，优先技能不匹配
        assert skill_score == 0.8  # 0.8 * 1.0 + 0.2 * 0.0

    def test_calculate_skill_score_fuzzy(self):
        """测试技能模糊匹配"""
        scorer = Scorer()

        resume = {
            "metadata": {
                "skills": ["Django框架"]
            }
        }

        query_metadata = QueryMetadata(
            required_skills=["Django"]
        )

        skill_score = scorer._calculate_skill_score(resume, query_metadata)
        assert skill_score == 1.0

    def test_calculate_industry_score(self):
        """测试行业领域匹配得分计算（基于工作经历文本子串匹配）"""
        scorer = Scorer()

        resume = {
            "metadata": {
                "work_experience": [
                    {
                        "company": "ABC科技有限公司",
                        "title": "互联网产品经理",
                        "description": "负责互联网金融产品设计"
                    }
                ]
            }
        }

        query_metadata = QueryMetadata(
            required_industries=["互联网"],
            preferred_industries=["医疗"]
        )

        industry_score = scorer._calculate_industry_score(resume, query_metadata)

        # 必需行业匹配，优先行业不匹配
        assert industry_score == 0.8  # 0.8 * 1.0 + 0.2 * 0.0

    def test_calculate_salary_score(self):
        """测试薪资匹配得分计算"""
        scorer = Scorer()

        resume = {
            "metadata": {
                "expected_salary": "20K-30K"
            }
        }

        query_metadata = QueryMetadata(
            salary_range={"min": "15K", "max": "35K"}
        )

        salary_score = scorer._calculate_salary_score(resume, query_metadata)
        assert salary_score == 1.0

    def test_parse_salary(self):
        """测试薪资解析"""
        scorer = Scorer()

        # 范围格式
        min_val, max_val = scorer._parse_salary("20K-30K")
        assert min_val == 20000
        assert max_val == 30000

        # 单个值格式
        min_val, max_val = scorer._parse_salary("25K")
        assert min_val == 25000
        assert max_val == 25000

        # 中文“万”
        min_val, max_val = scorer._parse_salary("20万-30万")
        assert min_val == 200000
        assert max_val == 300000

        min_val, max_val = scorer._parse_salary("25万")
        assert min_val == 250000
        assert max_val == 250000

        # 面议
        min_val, max_val = scorer._parse_salary("面议")
        assert min_val == 0.0
        assert max_val == 1000000.0

    def test_calculate_education_score(self):
        """测试学历匹配得分计算"""
        scorer = Scorer()

        resume = {
            "metadata": {
                "education": [
                    {"degree": "硕士"}
                ]
            }
        }

        education_score = scorer._calculate_education_score(resume, QueryMetadata(required_education="本科"))
        assert education_score == 1.0  # 硕士高于本科要求

        education_score = scorer._calculate_education_score(resume, QueryMetadata(required_education="博士"))
        assert education_score == 0.75  # 硕士是博士要求的3/4

    def test_calculate_location_score(self):
        """测试地理位置模糊匹配得分"""
        scorer = Scorer()

        resume = {
            "metadata": {
                "preferred_locations": ["北京", "上海", "广州"]
            }
        }

        query_metadata = QueryMetadata(
            locations=["北京", "深圳"]
        )

        location_score = scorer._calculate_location_score(resume, query_metadata)

        # “北京”匹配，“深圳”不匹配，得分为 1/2
        assert location_score == 0.5

    def test_calculate_location_score_fuzzy(self):
        """测试地点模糊匹配（如“北京”命中“北京市”）"""
        scorer = Scorer()

        resume = {
            "metadata": {
                "preferred_locations": ["北京市"]
            }
        }

        query_metadata = QueryMetadata(
            locations=["北京"]
        )

        location_score = scorer._calculate_location_score(resume, query_metadata)
        assert location_score == 1.0

    def test_calculate_tag_score(self):
        """测试个性标签/关键词匹配得分（中文子串匹配）"""
        scorer = Scorer()

        resume = {
            "metadata": {
                "summary": "具有丰富的大数据处理经验，熟悉Python生态"
            }
        }

        query_metadata = QueryMetadata(
            keywords=["大数据", "Python"]
        )

        tag_score = scorer._calculate_tag_score(resume, query_metadata)
        assert tag_score == 1.0

    def test_calculate_tag_score_partial(self):
        """测试关键词部分匹配"""
        scorer = Scorer()

        resume = {
            "metadata": {
                "summary": "Python开发工程师"
            }
        }

        query_metadata = QueryMetadata(
            keywords=["Python", "大数据"]
        )

        tag_score = scorer._calculate_tag_score(resume, query_metadata)
        assert tag_score == 0.5

    def test_score_resumes(self):
        """测试简历评分功能"""
        scorer = Scorer()

        resumes = [
            {
                "id": "resume_001",
                "metadata": {
                    "skills": ["Python", "Java", "SQL"],
                    "work_experience": [
                        {"company": "互联网公司", "title": "后端开发"}
                    ],
                    "education": [
                        {"degree": "本科"}
                    ],
                    "preferred_locations": ["北京"],
                    "expected_salary": "20K-30K",
                    "summary": "Python开发工程师"
                }
            }
        ]

        query_metadata = QueryMetadata(
            required_skills=["Python"],
            required_industries=["互联网"],
            required_education="本科",
            locations=["北京"],
            salary_range={"min": "15K", "max": "35K"},
            keywords=["Python"]
        )

        scored_resumes = scorer.score_resumes(resumes, query_metadata)

        assert len(scored_resumes) == 1
        assert "scores" in scored_resumes[0]
        assert "overall_score" in scored_resumes[0]["scores"]
        assert scored_resumes[0]["scores"]["overall_score"] > 0


if __name__ == "__main__":
    pytest.main([__file__])
