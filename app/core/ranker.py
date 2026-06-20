from typing import List, Dict, Any
from app.models.metadata import ResumeMetadata, QueryMetadata
from loguru import logger


class Ranker:
    """
    排名器，用于对简历进行综合评分和排序
    """
    
    def __init__(self):
        """
        初始化排名器
        """
        logger.info("Initialized Ranker")

    def rank_resumes(self, resumes: List[Dict[str, Any]], query_metadata: QueryMetadata) -> List[Dict[str, Any]]:
        """
        对简历进行综合评分和排序
        
        Args:
            resumes (List[Dict[str, Any]]): 简历列表（已包含评分）
            query_metadata (QueryMetadata): 查询元数据
            
        Returns:
            List[Dict[str, Any]]: 排序后的简历列表
        """
        try:
            # 按综合得分排序（降序）
            ranked_resumes = sorted(resumes, key=lambda x: x.get("scores", {}).get("overall_score", 0), reverse=True)
            
            # 添加排名信息
            for i, resume in enumerate(ranked_resumes):
                resume_with_rank = resume.copy()
                resume_with_rank["rank"] = i + 1
                ranked_resumes[i] = resume_with_rank
            
            logger.info(f"Ranked {len(ranked_resumes)} resumes")
            return ranked_resumes
            
        except Exception as e:
            logger.error(f"Failed to rank resumes: {e}")
            raise

    def get_top_resumes(self, resumes: List[Dict[str, Any]], n: int = 10) -> List[Dict[str, Any]]:
        """
        获取排名前N的简历
        
        Args:
            resumes (List[Dict[str, Any]]): 排序后的简历列表
            n (int): 返回的简历数量
            
        Returns:
            List[Dict[str, Any]]: 前N名的简历列表
        """
        return resumes[:n]

    def filter_by_threshold(self, resumes: List[Dict[str, Any]], threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        根据阈值过滤简历
        
        Args:
            resumes (List[Dict[str, Any]]): 排序后的简历列表
            threshold (float): 最低得分阈值
            
        Returns:
            List[Dict[str, Any]]: 过滤后的简历列表
        """
        return [resume for resume in resumes if resume.get("scores", {}).get("overall_score", 0) >= threshold]