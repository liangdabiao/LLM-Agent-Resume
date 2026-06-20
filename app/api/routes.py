"""
API 路由
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import base64
import uuid
import json
from datetime import datetime
from loguru import logger

from app.api.models import (
    UploadResumeRequest, UploadResumeResponse, QueryRequest, QueryResponse,
    ScreeningResult
)
from app.core.document_parser import DocumentParser
from app.core.extractor import MetadataExtractor
from app.core.llm_client import LLMClient
from app.core.query_parser import QueryParser
from app.core.vector_store_factory import get_vector_store_manager
from app.core.retriever import Retriever
from app.core.filter import HardFilter
from app.core.scorer import Scorer
from app.core.ranker import Ranker
from app.core.analyzer import CandidateAnalyzer
from app.core.result_formatter import ResultFormatter
from app.models.metadata import ResumeMetadata, QueryMetadata

router = APIRouter(prefix="/api/v1")

# 初始化核心组件
llm_client = LLMClient()
document_parser = DocumentParser()
metadata_extractor = MetadataExtractor(llm_client)
query_parser = QueryParser(llm_client)
vector_store_manager = get_vector_store_manager()
retriever = Retriever(vector_store_manager)
hard_filter = HardFilter()
scorer = Scorer()
ranker = Ranker()
candidate_analyzer = CandidateAnalyzer(llm_client)
result_formatter = ResultFormatter()

# 存储简历和查询结果的内存字典（在实际应用中应使用数据库）
resume_storage = {}
query_storage = {}


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok"}


@router.get("/resumes")
async def list_resumes():
    """列出已上传的简历（摘要信息）。"""
    items = []
    for rid, data in resume_storage.items():
        meta = data.get("metadata", {}) or {}
        items.append({
            "resume_id": rid,
            "filename": data.get("filename", ""),
            "name": meta.get("name", ""),
            "created_at": data.get("created_at"),
        })
    return {"total": len(items), "resumes": items}


@router.post("/resumes", response_model=UploadResumeResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    上传简历接口
    
    Args:
        file (UploadFile): 上传的简历文件
        
    Returns:
        UploadResumeResponse: 上传结果
    """
    try:
        from loguru import logger
        logger.info(f"[upload_resume] 开始处理文件: {file.filename}")
        content = await file.read()
        resume_id = str(uuid.uuid4())
        logger.info(f"[upload_resume] 文件读取完成, 大小: {len(content)} bytes, resume_id: {resume_id}")
        if file.filename.endswith('.pdf'):
            import tempfile, os
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            logger.info(f"[upload_resume] 临时PDF文件已保存: {tmp_path}")
            try:
                resume_text = document_parser.parse_pdf(tmp_path)
                logger.info(f"[upload_resume] PDF解析完成, 文本长度: {len(resume_text)}")
            finally:
                os.remove(tmp_path)
                logger.info(f"[upload_resume] 临时PDF文件已删除: {tmp_path}")
        else:
            resume_text = content.decode('utf-8')
            logger.info(f"[upload_resume] 非PDF文件解析完成, 文本长度: {len(resume_text)}")
        logger.info(f"[upload_resume] 开始提取元数据")
        metadata = metadata_extractor.extract_metadata(resume_text)
        logger.info(f"[upload_resume] 元数据提取完成: {metadata}")
        resume_storage[resume_id] = {
            "id": resume_id,
            "filename": file.filename,
            "text": resume_text,
            "metadata": metadata.dict(),
            "created_at": datetime.now()
        }
        logger.info(f"[upload_resume] 简历已存储, resume_id: {resume_id}")
        retriever.add_resume(resume_id, resume_text, metadata.dict())
        logger.info(f"[upload_resume] 向量数据库已更新, resume_id: {resume_id}")
        return UploadResumeResponse(
            resume_id=resume_id,
            message=f"简历 '{file.filename}' 上传成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传简历失败: {str(e)}")


@router.post("/queries", response_model=QueryResponse)
async def submit_query(query_request: QueryRequest):
    """
    提交筛选查询接口
    
    Args:
        query_request (QueryRequest): 查询请求
        
    Returns:
        QueryResponse: 查询提交结果
    """
    try:
        # 解析查询
        query_metadata = query_parser.parse_query(query_request.query_text)
        
        # 生成查询ID
        query_id = str(uuid.uuid4())
        
        # 存储查询数据
        query_storage[query_id] = {
            "id": query_id,
            "text": query_request.query_text,
            "metadata": query_metadata.dict(),
            "created_at": datetime.now()
        }
        
        return QueryResponse(
            query_id=query_id,
            message="查询提交成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交查询失败: {str(e)}")


@router.get("/results/{query_id}", response_model=ScreeningResult)
async def get_screening_results(query_id: str):
    """
    获取筛选结果接口
    
    Args:
        query_id (str): 查询ID
        
    Returns:
        ScreeningResult: 筛选结果
    """
    try:
        # 检查查询是否存在
        if query_id not in query_storage:
            raise HTTPException(status_code=404, detail="查询不存在")
        
        # 获取查询数据
        query_data = query_storage[query_id]
        query_metadata = QueryMetadata(**query_data["metadata"])
        
        # 检索相关简历
        retrieved_resumes = retriever.retrieve(query_metadata)
        
        # 硬性条件过滤
        filtered_resumes = hard_filter.filter_resumes(retrieved_resumes, query_metadata)
        
        # 多维度评分
        scored_resumes = scorer.score_resumes(filtered_resumes, query_metadata)
        
        # 综合评分与排序
        ranked_resumes = ranker.rank_resumes(scored_resumes, query_metadata)
        
        # 候选人分析
        analyzed_candidates = candidate_analyzer.analyze_candidates(ranked_resumes, query_metadata)
        
        # 格式化结果
        formatted_results = result_formatter.format_results(analyzed_candidates, query_metadata)
        
        # 转换为API响应模型
        candidates = []
        for candidate_data in formatted_results["candidates"]:
            # 提取技能分数
            skill_scores = []
            for skill in candidate_data.get("basic_info", {}).get("skills", []):
                skill_scores.append({
                    "name": skill,
                    "score": candidate_data.get("scores", {}).get("skill_score", 0)
                })
            

            # 从basic_info中获取工作经历（已处理为JSON字符串）
            work_experience_str = candidate_data.get("basic_info", {}).get("work_experience", "")
            work_experience = []
            if work_experience_str:
                try:
                    work_experience = json.loads(work_experience_str)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode work_experience JSON: {work_experience_str}")

            # 从basic_info中获取教育背景（已处理为JSON字符串）
            education_str = candidate_data.get("basic_info", {}).get("education", "")
            education = []
            if education_str:
                try:
                    education = json.loads(education_str)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode education JSON: {education_str}")
            
            candidate = {
                "id": candidate_data.get("id", ""),
                "rank": candidate_data.get("rank", 0),
                "name": candidate_data.get("name", ""),
                "email": candidate_data.get("contact_info", {}).get("email"),
                "phone": candidate_data.get("contact_info", {}).get("phone"),
                "overall_score": candidate_data.get("scores", {}).get("overall_score", 0),
                "work_experience": work_experience,
                "education": education,
                "skill_scores": skill_scores,
                "skills": candidate_data.get("basic_info", {}).get("skills", []),
                "expected_salary": candidate_data.get("basic_info", {}).get("expected_salary"),
                "preferred_locations": candidate_data.get("basic_info", {}).get("preferred_locations", []),
                "analysis": candidate_data.get("analysis", "")
            }
            candidates.append(candidate)
        
        result = ScreeningResult(
            query_id=query_id,
            query_text=query_data["text"],
            total_candidates=formatted_results["total_candidates"],
            candidates=candidates,
            created_at=query_data["created_at"]
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取筛选结果失败: {str(e)}")


@router.get("/resumes/{resume_id}")
async def get_resume(resume_id: str):
    """
    获取简历详情接口
    
    Args:
        resume_id (str): 简历ID
        
    Returns:
        dict: 简历详情
    """
    try:
        # 检查简历是否存在
        if resume_id not in resume_storage:
            raise HTTPException(status_code=404, detail="简历不存在")
        
        # 返回简历数据
        return resume_storage[resume_id]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取简历详情失败: {str(e)}")