from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class UploadResumeRequest(BaseModel):
    """上传简历请求模型"""
    filename: str
    content: str  # Base64编码的文件内容


class UploadResumeResponse(BaseModel):
    """上传简历响应模型"""
    resume_id: str
    message: str


class QueryRequest(BaseModel):
    """筛选查询请求模型"""
    query_text: str


class QueryResponse(BaseModel):
    """筛选查询响应模型"""
    query_id: str
    message: str


class Skill(BaseModel):
    """技能模型"""
    name: str
    score: float


class WorkExperience(BaseModel):
    """工作经历模型"""
    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class Education(BaseModel):
    """教育背景模型"""
    institution: Optional[str] = None
    major: Optional[str] = None
    degree: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class Candidate(BaseModel):
    """候选人模型"""
    id: str
    rank: int
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    overall_score: float = 0.0
    skill_scores: List[Skill] = []
    work_experience: List[WorkExperience] = []
    education: List[Education] = []
    skills: List[str] = []
    expected_salary: Optional[str] = None
    preferred_locations: List[str] = []
    analysis: str = ""


class ScreeningResult(BaseModel):
    """筛选结果模型"""
    query_id: str
    query_text: str
    total_candidates: int
    candidates: List[Candidate]
    created_at: datetime


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str
    message: str