from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date


class ResumeMetadata(BaseModel):
    """
    简历元数据模型
    """
    # 基本信息
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    
    # 工作经历
    work_experience: List[Dict[str, Any]] = []
    
    # 教育背景
    education: List[Dict[str, Any]] = []
    
    # 技能
    skills: List[str] = []
    
    # 项目经历
    projects: List[Dict[str, Any]] = []
    
    # 语言能力
    languages: List[str] = []
    
    # 证书
    certifications: List[str] = []
    
    # 期望薪资
    expected_salary: Optional[str] = None
    
    # 期望工作地点
    preferred_locations: List[str] = []
    
    # 个人简介
    summary: Optional[str] = None
    
    # 其他信息
    additional_info: Optional[str] = None


class QueryMetadata(BaseModel):
    """
    查询元数据模型
    """
    # 关键词
    keywords: List[str] = []
    
    # 所需技能
    required_skills: List[str] = []
    
    # 优先技能
    preferred_skills: List[str] = []
    
    # 所需经验年限
    min_experience_years: Optional[int] = None
    
    # 所需学历
    required_education: Optional[str] = None
    
    # 所需行业
    required_industries: List[str] = []
    
    # 优先行业
    preferred_industries: List[str] = []
    
    # 薪资范围
    salary_range: Optional[Dict[str, Any]] = None
    
    # 工作地点
    locations: List[str] = []
    
    # 语言要求
    required_languages: List[str] = []
    
    # 证书要求
    required_certifications: List[str] = []
    
    # 其他自定义条件
    custom_conditions: Optional[str] = None