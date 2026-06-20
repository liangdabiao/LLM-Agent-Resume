"""
测试硬性条件过滤器模块
"""
import pytest
from app.core.filter import HardFilter
from app.models.metadata import QueryMetadata


class TestHardFilter:
    """测试硬性条件过滤器"""

    def test_init(self):
        """测试初始化"""
        filter_obj = HardFilter()
        assert filter_obj is not None

    def test_filter_by_experience(self):
        """测试根据经验年限过滤"""
        filter_obj = HardFilter()
        
        # 创建模拟简历数据
        resumes = [
            {
                "id": "resume_001",
                "metadata": {
                    "work_experience": [
                        {"start_date": "2020-01", "end_date": "2023-12"},
                        {"start_date": "2018-01", "end_date": "2019-12"}
                    ]
                }
            },
            {
                "id": "resume_002",
                "metadata": {
                    "work_experience": [
                        {"start_date": "2022-01", "end_date": "2023-12"}
                    ]
                }
            }
        ]
        
        # 过滤经验年限至少为3年的简历
        filtered_resumes = filter_obj._filter_by_experience(resumes, 3)
        
        # 验证结果
        assert len(filtered_resumes) == 1
        assert filtered_resumes[0]["id"] == "resume_001"

    def test_filter_by_education(self):
        """测试根据学历过滤"""
        filter_obj = HardFilter()
        
        # 创建模拟简历数据
        resumes = [
            {
                "id": "resume_001",
                "metadata": {
                    "education": [
                        {"degree": "本科"}
                    ]
                }
            },
            {
                "id": "resume_002",
                "metadata": {
                    "education": [
                        {"degree": "硕士"}
                    ]
                }
            },
            {
                "id": "resume_003",
                "metadata": {
                    "education": [
                        {"degree": "大专"}
                    ]
                }
            }
        ]
        
        # 过滤学历至少为本科的简历
        filtered_resumes = filter_obj._filter_by_education(resumes, "本科")
        
        # 验证结果
        assert len(filtered_resumes) == 2
        assert filtered_resumes[0]["id"] == "resume_001"
        assert filtered_resumes[1]["id"] == "resume_002"

    def test_filter_by_skills(self):
        """测试根据技能过滤"""
        filter_obj = HardFilter()
        
        # 创建模拟简历数据
        resumes = [
            {
                "id": "resume_001",
                "metadata": {
                    "skills": ["Python", "Java", "SQL"]
                }
            },
            {
                "id": "resume_002",
                "metadata": {
                    "skills": ["Java", "Spring"]
                }
            }
        ]
        
        # 过滤需要Python和SQL技能的简历
        required_skills = ["Python", "SQL"]
        filtered_resumes = filter_obj._filter_by_skills(resumes, required_skills)
        
        # 验证结果
        assert len(filtered_resumes) == 1
        assert filtered_resumes[0]["id"] == "resume_001"

    def test_filter_by_locations(self):
        """测试根据工作地点过滤"""
        filter_obj = HardFilter()
        
        # 创建模拟简历数据
        resumes = [
            {
                "id": "resume_001",
                "metadata": {
                    "preferred_locations": ["北京", "上海"]
                }
            },
            {
                "id": "resume_002",
                "metadata": {
                    "preferred_locations": ["广州", "深圳"]
                }
            }
        ]
        
        # 过滤期望工作地点包括北京的简历
        locations = ["北京"]
        filtered_resumes = filter_obj._filter_by_locations(resumes, locations)
        
        # 验证结果
        assert len(filtered_resumes) == 1
        assert filtered_resumes[0]["id"] == "resume_001"

    def test_filter_by_languages(self):
        """测试根据语言要求过滤"""
        filter_obj = HardFilter()
        
        # 创建模拟简历数据
        resumes = [
            {
                "id": "resume_001",
                "metadata": {
                    "languages": ["中文", "英语"]
                }
            },
            {
                "id": "resume_002",
                "metadata": {
                    "languages": ["中文"]
                }
            }
        ]
        
        # 过滤需要英语的简历
        required_languages = ["英语"]
        filtered_resumes = filter_obj._filter_by_languages(resumes, required_languages)
        
        # 验证结果
        assert len(filtered_resumes) == 1
        assert filtered_resumes[0]["id"] == "resume_001"

    def test_filter_by_certifications(self):
        """测试根据证书要求过滤"""
        filter_obj = HardFilter()
        
        # 创建模拟简历数据
        resumes = [
            {
                "id": "resume_001",
                "metadata": {
                    "certifications": ["软件设计师", "PMP"]
                }
            },
            {
                "id": "resume_002",
                "metadata": {
                    "certifications": ["软件设计师"]
                }
            }
        ]
        
        # 过滤需要PMP证书的简历
        required_certifications = ["PMP"]
        filtered_resumes = filter_obj._filter_by_certifications(resumes, required_certifications)
        
        # 验证结果
        assert len(filtered_resumes) == 1
        assert filtered_resumes[0]["id"] == "resume_001"

    def test_filter_resumes(self):
        """测试综合过滤功能"""
        filter_obj = HardFilter()
        
        # 创建模拟简历数据
        resumes = [
            {
                "id": "resume_001",
                "metadata": {
                    "work_experience": [
                        {"start_date": "2020-01", "end_date": "2023-12"}
                    ],
                    "education": [
                        {"degree": "本科"}
                    ],
                    "skills": ["Python", "Java"],
                    "preferred_locations": ["北京"],
                    "languages": ["中文", "英语"],
                    "certifications": ["软件设计师"]
                }
            },
            {
                "id": "resume_002",
                "metadata": {
                    "work_experience": [
                        {"start_date": "2022-01", "end_date": "2023-12"}
                    ],
                    "education": [
                        {"degree": "大专"}
                    ],
                    "skills": ["Java"],
                    "preferred_locations": ["上海"],
                    "languages": ["中文"],
                    "certifications": []
                }
            }
        ]
        
        # 创建查询元数据
        query_metadata = QueryMetadata(
            min_experience_years=2,
            required_education="本科",
            required_skills=["Python"],
            locations=["北京"],
            required_languages=["英语"],
            required_certifications=["软件设计师"]
        )
        
        # 执行过滤
        filtered_resumes = filter_obj.filter_resumes(resumes, query_metadata)
        
        # 验证结果
        assert len(filtered_resumes) == 1
        assert filtered_resumes[0]["id"] == "resume_001"


if __name__ == "__main__":
    pytest.main([__file__])