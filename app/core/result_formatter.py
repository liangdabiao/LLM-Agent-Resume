from typing import List, Dict, Any
from app.models.metadata import QueryMetadata
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
        
        Args:
            candidates (List[Dict[str, Any]]): 候选人列表
            query_metadata (QueryMetadata): 查询元数据
            
        Returns:
            Dict[str, Any]: 格式化后的筛选结果
        """
        try:
            # 创建结果结构
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
        """
        格式化查询信息
        
        Args:
            query_metadata (QueryMetadata): 查询元数据
            
        Returns:
            Dict[str, Any]: 格式化后的查询信息
        """
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
        格式化候选人列表
        
        Args:
            candidates (List[Dict[str, Any]]): 候选人列表
            
        Returns:
            List[Dict[str, Any]]: 格式化后的候选人列表
        """
        formatted_candidates = []
        
        for candidate in candidates:
            # 处理skills字段，确保是列表类型
            skills = candidate.get("metadata", {}).get("skills", [])
            if isinstance(skills, str):
                logger.info(f"Converting string skills to list in result formatter: {skills}")
                # 尝试将JSON字符串转换回列表
                try:
                    skills = json.loads(skills)
                    if not isinstance(skills, list):
                        skills = [s.strip() for s in skills.split(',')] if ',' in skills else [skills]
                except json.JSONDecodeError:
                    skills = [s.strip() for s in skills.split(',')] if ',' in skills else [skills]
            elif not isinstance(skills, list):
                skills = []
                logger.warning(f"Invalid skills type in result formatter: {type(skills)}")

            # 处理preferred_locations字段，确保是列表类型
            preferred_locations = candidate.get("metadata", {}).get("preferred_locations", [])
            if isinstance(preferred_locations, str):
                logger.info(f"Converting string preferred_locations to list in result formatter: {preferred_locations}")
                preferred_locations = [loc.strip() for loc in preferred_locations.split(',')] if ',' in preferred_locations else [preferred_locations]
            elif not isinstance(preferred_locations, list):
                preferred_locations = []
                logger.warning(f"Invalid preferred_locations type in result formatter: {type(preferred_locations)}")

            # 处理work_experience字段，将列表转换为JSON字符串
            work_experience = candidate.get("metadata", {}).get("work_experience", [])
            if isinstance(work_experience, list):
                logger.info(f"Converting work_experience list to JSON string in result formatter")
                work_experience = json.dumps(work_experience)
            elif not isinstance(work_experience, str):
                work_experience = ""
                logger.warning(f"Invalid work_experience type in result formatter: {type(work_experience)}")

            # 处理education字段，将列表转换为JSON字符串
            education = candidate.get("metadata", {}).get("education", [])
            if isinstance(education, list):
                logger.info(f"Converting education list to JSON string in result formatter")
                education = json.dumps(education)
            elif not isinstance(education, str):
                education = ""
                logger.warning(f"Invalid education type in result formatter: {type(education)}")

            # 处理projects字段，将列表转换为JSON字符串
            projects = candidate.get("metadata", {}).get("projects", [])
            if isinstance(projects, list):
                logger.info(f"Converting projects list to JSON string in result formatter")
                projects = json.dumps(projects)
            elif not isinstance(projects, str):
                projects = ""
                logger.warning(f"Invalid projects type in result formatter: {type(projects)}")

            # 处理languages字段，将列表转换为JSON字符串
            languages = candidate.get("metadata", {}).get("languages", [])
            if isinstance(languages, list):
                logger.info(f"Converting languages list to JSON string in result formatter")
                languages = json.dumps(languages)
            elif not isinstance(languages, str):
                languages = ""
                logger.warning(f"Invalid languages type in result formatter: {type(languages)}")

            # 处理certifications字段，将列表转换为JSON字符串
            certifications = candidate.get("metadata", {}).get("certifications", [])
            if isinstance(certifications, list):
                logger.info(f"Converting certifications list to JSON string in result formatter")
                certifications = json.dumps(certifications)
            elif not isinstance(certifications, str):
                certifications = ""
                logger.warning(f"Invalid certifications type in result formatter: {type(certifications)}")

            formatted_candidate = {
                "id": candidate.get("id"),
                "rank": candidate.get("rank"),
                "name": candidate.get("metadata", {}).get("name"),
                "scores": candidate.get("scores", {}),
                "analysis": candidate.get("analysis"),
                "contact_info": {
                    "email": candidate.get("metadata", {}).get("email"),
                    "phone": candidate.get("metadata", {}).get("phone")
                },
                "basic_info": {
                    "skills": skills,
                    "expected_salary": candidate.get("metadata", {}).get("expected_salary"),
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
        """
        生成结果摘要
        
        Args:
            candidates (List[Dict[str, Any]]): 候选人列表
            
        Returns:
            Dict[str, Any]: 结果摘要
        """
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
        """
        将结果导出为JSON文件
        
        Args:
            results (Dict[str, Any]): 筛选结果
            file_path (str): 导出文件路径
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"Exported results to JSON file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to export results to JSON: {e}")
            raise

    def export_to_text(self, results: Dict[str, Any], file_path: str) -> None:
        """
        将结果导出为文本文件
        
        Args:
            results (Dict[str, Any]): 筛选结果
            file_path (str): 导出文件路径
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 写入查询信息
                f.write("职位筛选结果报告\n")
                f.write("=" * 50 + "\n\n")
                
                query = results.get("query", {})
                f.write("查询条件:\n")
                for key, value in query.items():
                    if value:
                        f.write(f"  {key}: {value}\n")
                f.write("\n")
                
                # 写入候选人信息
                f.write(f"候选人总数: {results.get('total_candidates', 0)}\n\n")
                
                candidates = results.get("candidates", [])
                for candidate in candidates:
                    f.write(f"候选人 {candidate.get('rank', 0)}: {candidate.get('name', '未知')}\n")
                    f.write(f"  综合得分: {candidate.get('scores', {}).get('overall_score', 0):.2f}\n")
                    f.write(f"  技能: {', '.join(candidate.get('basic_info', {}).get('skills', []))}\n")
                    f.write(f"  期望薪资: {candidate.get('basic_info', {}).get('expected_salary', '未知')}\n")
                    f.write(f"  期望工作地点: {', '.join(candidate.get('basic_info', {}).get('preferred_locations', []))}\n")
                    f.write(f"  综合评价:\n{candidate.get('analysis', '无')}\n\n")
                
                # 写入摘要
                summary = results.get("summary", {})
                f.write("结果摘要:\n")
                f.write(f"  平均得分: {summary.get('average_score', 0):.2f}\n")
                f.write(f"  最高得分: {summary.get('top_score', 0):.2f}\n")
                f.write(f"  最低得分: {summary.get('bottom_score', 0):.2f}\n")
            
            logger.info(f"Exported results to text file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to export results to text: {e}")
            raise