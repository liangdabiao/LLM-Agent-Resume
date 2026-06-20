"""
API 路由
"""
import asyncio
import uuid
import json
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.concurrency import run_in_threadpool

from app.api.models import (
    UploadResumeResponse, QueryRequest, QueryResponse, ScreeningResult
)
from app.core.cache_manager import CacheManager
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

# 常量
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# 初始化核心组件
llm_client = LLMClient()
cache_manager = CacheManager()
document_parser = DocumentParser(cache_manager=cache_manager)
metadata_extractor = MetadataExtractor(llm_client, cache_manager=cache_manager)
query_parser = QueryParser(llm_client)
vector_store_manager = get_vector_store_manager()
retriever = Retriever(vector_store_manager)
hard_filter = HardFilter()
scorer = Scorer()
ranker = Ranker()
candidate_analyzer = CandidateAnalyzer(llm_client)
result_formatter = ResultFormatter()

# 存储简历和查询结果的内存字典（在实际应用中应使用数据库）
resume_storage: Dict[str, Any] = {}
query_storage: Dict[str, Any] = {}


def _safe_json_loads(value: Any, default: Any = None) -> Any:
    """安全解析 JSON 字符串；若已是目标类型则直接返回。"""
    if default is None:
        default = []
    if isinstance(value, (list, dict)):
        return value
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"JSON parse failed for: {value}")
        return default


def _calc_skill_scores(resume_skills: list, query_metadata: QueryMetadata, overall_skill_score: float) -> list:
    """根据查询要求计算每个技能的单项得分。"""
    if not resume_skills:
        return []

    required = [s.lower() for s in query_metadata.required_skills]
    preferred = [s.lower() for s in query_metadata.preferred_skills]

    scores = []
    for skill in resume_skills:
        sl = str(skill).lower()
        matched = False
        for q in required + preferred:
            if q in sl or sl in q:
                matched = True
                break
        scores.append({
            "name": skill,
            "score": 1.0 if matched else max(overall_skill_score - 0.3, 0.0)
        })
    return scores


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
    """
    logger.info(f"[upload_resume] 开始处理文件: {file.filename}")

    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"文件大小超过限制 {MAX_FILE_SIZE / 1024 / 1024:.0f}MB")

    resume_id = str(uuid.uuid4())
    logger.info(f"[upload_resume] 文件读取完成, 大小: {len(content)} bytes, resume_id: {resume_id}")

    try:
        if file.filename.lower().endswith('.pdf'):
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            logger.info(f"[upload_resume] 临时PDF文件已保存: {tmp_path}")
            try:
                resume_text = await run_in_threadpool(document_parser.parse_pdf, tmp_path)
                logger.info(f"[upload_resume] PDF解析完成, 文本长度: {len(resume_text)}")
            finally:
                os.remove(tmp_path)
                logger.info(f"[upload_resume] 临时PDF文件已删除: {tmp_path}")
        else:
            try:
                resume_text = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="非PDF文件必须是UTF-8编码的文本")
            logger.info(f"[upload_resume] 非PDF文件解析完成, 文本长度: {len(resume_text)}")

        metadata = await run_in_threadpool(metadata_extractor.extract_metadata, resume_text)
        logger.info(f"[upload_resume] 元数据提取完成: {metadata}")

        resume_storage[resume_id] = {
            "id": resume_id,
            "filename": file.filename,
            "text": resume_text,
            "metadata": metadata.dict(),
            "created_at": datetime.now()
        }
        logger.info(f"[upload_resume] 简历已存储, resume_id: {resume_id}")

        await run_in_threadpool(retriever.add_resume, resume_id, resume_text, metadata.dict())
        logger.info(f"[upload_resume] 向量数据库已更新, resume_id: {resume_id}")

        return UploadResumeResponse(
            resume_id=resume_id,
            message=f"简历 '{file.filename}' 上传成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("上传简历失败")
        raise HTTPException(status_code=500, detail="上传简历失败，请稍后重试")


@router.post("/queries", response_model=QueryResponse)
async def submit_query(query_request: QueryRequest):
    """
    提交筛选查询接口
    """
    try:
        query_metadata = await run_in_threadpool(query_parser.parse_query, query_request.query_text)
        query_id = str(uuid.uuid4())

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
        logger.exception("提交查询失败")
        raise HTTPException(status_code=500, detail="提交查询失败，请稍后重试")


@router.get("/results/{query_id}", response_model=ScreeningResult)
async def get_screening_results(query_id: str):
    """
    获取筛选结果接口
    """
    if query_id not in query_storage:
        raise HTTPException(status_code=404, detail="查询不存在")

    try:
        query_data = query_storage[query_id]
        query_metadata = QueryMetadata(**query_data["metadata"])

        retrieved_resumes = await run_in_threadpool(retriever.retrieve, query_metadata)
        filtered_resumes = await run_in_threadpool(hard_filter.filter_resumes, retrieved_resumes, query_metadata)
        scored_resumes = await run_in_threadpool(scorer.score_resumes, filtered_resumes, query_metadata)
        ranked_resumes = await run_in_threadpool(ranker.rank_resumes, scored_resumes, query_metadata)
        analyzed_candidates = await run_in_threadpool(candidate_analyzer.analyze_candidates, ranked_resumes, query_metadata)
        formatted_results = await run_in_threadpool(result_formatter.format_results, analyzed_candidates, query_metadata)

        candidates = []
        for candidate_data in formatted_results["candidates"]:
            basic_info = candidate_data.get("basic_info", {}) or {}
            scores = candidate_data.get("scores", {}) or {}
            overall_skill_score = scores.get("skill_score", 0)

            resume_skills = _safe_json_loads(basic_info.get("skills", []), [])
            skill_scores = _calc_skill_scores(resume_skills, query_metadata, overall_skill_score)

            work_experience = _safe_json_loads(basic_info.get("work_experience", []), [])
            education = _safe_json_loads(basic_info.get("education", []), [])

            candidate = {
                "id": candidate_data.get("id", ""),
                "rank": candidate_data.get("rank", 0),
                "name": candidate_data.get("name", ""),
                "email": candidate_data.get("contact_info", {}).get("email"),
                "phone": candidate_data.get("contact_info", {}).get("phone"),
                "overall_score": scores.get("overall_score", 0),
                "work_experience": work_experience,
                "education": education,
                "skill_scores": skill_scores,
                "skills": resume_skills,
                "expected_salary": basic_info.get("expected_salary"),
                "preferred_locations": basic_info.get("preferred_locations", []),
                "analysis": candidate_data.get("analysis", "")
            }
            candidates.append(candidate)

        return ScreeningResult(
            query_id=query_id,
            query_text=query_data["text"],
            total_candidates=formatted_results["total_candidates"],
            candidates=candidates,
            created_at=query_data["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("获取筛选结果失败")
        raise HTTPException(status_code=500, detail="获取筛选结果失败，请稍后重试")


@router.get("/resumes/{resume_id}")
async def get_resume(resume_id: str):
    """
    获取简历详情接口
    """
    if resume_id not in resume_storage:
        raise HTTPException(status_code=404, detail="简历不存在")

    try:
        return resume_storage[resume_id]
    except Exception:
        logger.exception("获取简历详情失败")
        raise HTTPException(status_code=500, detail="获取简历详情失败，请稍后重试")
