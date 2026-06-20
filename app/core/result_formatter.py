from typing import List, Dict, Any
from app.models.metadata import QueryMetadata
from app.core.metadata_utils import coerce_to_list
from loguru import logger
import json


class ResultFormatter:
    """
    结果格式化器，用于聚合和格式化筛选结果
    """

    def __init__(self):
        """
        初始化结果格式化器
        """
        logger.info("Initialized ResultFormatter")

    def format_results(self, candidates: List[Dict[str, Any]], query_metadata: QueryMetadata) -> Dict[str, Any]:
        """
        格式化筛选结果
        """
        try:
            results = {
                "query": self._format_query(query_metadata),
                "total_candidates": len(candidates),
                "candidates": self._format_candidates(candidates),
                "summary": self._generate_summary(candidates)
            }

            logger.info(f"Formatted results for {len(candidates)} candidates")
            return results

        except Exception as e:
            logger.error(f"Failed to format results: {e}")
            raise

    def _format_query(self, query_metadata: QueryMetadata) -> Dict[str, Any]:
        """格式化查询信息"""
        return {
            "keywords": query_metadata.keywords,
            "required_skills": query_metadata.required_skills,
            "preferred_skills": query_metadata.preferred_skills,
            "min_experience_years": query_metadata.min_experience_years,
            "required_education": query_metadata.required_education,
            "required_industries": query_metadata.required_industries,
            "preferred_industries": query_metadata.preferred_industries,
            "salary_range": query_metadata.salary_range,
            "locations": query_metadata.locations,
            "required_languages": query_metadata.required_languages,
            "required_certifications": query_metadata.required_certifications,
            "custom_conditions": query_metadata.custom_conditions
        }

    def _format_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        格式化候选人列表，保持列表字段为原生列表，避免 JSON 字符串往返。
        """
        formatted_candidates = []

        for candidate in candidates:
            metadata = candidate.get("metadata", {}) or {}
            if not isinstance(metadata, dict):
                metadata = {}

            skills = coerce_to_list(metadata.get("skills", []))
            preferred_locations = coerce_to_list(metadata.get("preferred_locations", []))
            work_experience = coerce_to_list(metadata.get("work_experience", []))
            education = coerce_to_list(metadata.get("education", []))
            projects = coerce_to_list(metadata.get("projects", []))
            languages = coerce_to_list(metadata.get("languages", []))
            certifications = coerce_to_list(metadata.get("certifications", []))

            formatted_candidate = {
                "id": candidate.get("id"),
                "rank": candidate.get("rank"),
                "name": metadata.get("name"),
                "scores": candidate.get("scores", {}),
                "analysis": candidate.get("analysis"),
                "contact_info": {
                    "email": metadata.get("email"),
                    "phone": metadata.get("phone")
                },
                "basic_info": {
                    "skills": skills,
                    "expected_salary": metadata.get("expected_salary"),
                    "preferred_locations": preferred_locations,
                    "work_experience": work_experience,
                    "education": education,
                    "projects": projects,
                    "languages": languages,
                    "certifications": certifications
                }
            }
            formatted_candidates.append(formatted_candidate)

        return formatted_candidates

    def _generate_summary(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成结果摘要"""
        if not candidates:
            return {
                "average_score": 0,
                "top_score": 0,
                "bottom_score": 0
            }

        scores = [candidate.get("scores", {}).get("overall_score", 0) for candidate in candidates]

        return {
            "average_score": sum(scores) / len(scores),
            "top_score": max(scores),
            "bottom_score": min(scores)
        }

    def export_to_json(self, results: Dict[str, Any], file_path: str) -> None:
        """将结果导出为JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"Exported results to JSON file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to export results to JSON: {e}")
            raise

    def export_to_text(self, results: Dict[str, Any], file_path: str) -> None:
        """将结果导出为文本文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("职位筛选结果报告\n")
                f.write("=" * 50 + "\n\n")

                query = results.get("query", {})
                f.write("查询条件:\n")
                for key, value in query.items():
                    if value:
                        f.write(f"  {key}: {value}\n")
                f.write("\n")

                f.write(f"候选人总数: {results.get('total_candidates', 0)}\n\n")

                candidates = results.get("candidates", [])
                for candidate in candidates:
                    f.write(f"候选人 {candidate.get('rank', 0)}: {candidate.get('name', '未知')}\n")
                    f.write(f"  综合得分: {candidate.get('scores', {}).get('overall_score', 0):.2f}\n")
                    f.write(f"  技能: {', '.join(coerce_to_list(candidate.get('basic_info', {}).get('skills', [])))}\n")
                    f.write(f"  期望薪资: {candidate.get('basic_info', {}).get('expected_salary', '未知')}\n")
                    f.write(f"  期望工作地点: {', '.join(coerce_to_list(candidate.get('basic_info', {}).get('preferred_locations', [])))}\n")
                    f.write(f"  综合评价:\n{candidate.get('analysis', '无')}\n\n")

                summary = results.get("summary", {})
                f.write("结果摘要:\n")
                f.write(f"  平均得分: {summary.get('average_score', 0):.2f}\n")
                f.write(f"  最高得分: {summary.get('top_score', 0):.2f}\n")
                f.write(f"  最低得分: {summary.get('bottom_score', 0):.2f}\n")

            logger.info(f"Exported results to text file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to export results to text: {e}")
            raise
