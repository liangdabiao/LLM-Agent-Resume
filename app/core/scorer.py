from typing import List, Dict, Any, Tuple
from app.core.metadata_utils import coerce_to_list
from app.models.metadata import ResumeMetadata, QueryMetadata
from loguru import logger


class Scorer:
    """
    多维度评分器，用于对简历进行多维度评分
    """
    
    def __init__(self):
        """
        初始化评分器
        """
        logger.info("Initialized Scorer")

    def score_resumes(self, resumes: List[Dict[str, Any]], query_metadata: QueryMetadata) -> List[Dict[str, Any]]:
        """
        对简历进行多维度评分
        
        Args:
            resumes (List[Dict[str, Any]]): 简历列表
            query_metadata (QueryMetadata): 查询元数据
            
        Returns:
            List[Dict[str, Any]]: 包含评分的简历列表
        """
        try:
            scored_resumes = []
            
            for resume in resumes:
                # 计算各项得分
                skill_score = self._calculate_skill_score(resume, query_metadata)
                industry_score = self._calculate_industry_score(resume, query_metadata)
                salary_score = self._calculate_salary_score(resume, query_metadata)
                education_score = self._calculate_education_score(resume, query_metadata)
                location_score = self._calculate_location_score(resume, query_metadata)
                tag_score = self._calculate_tag_score(resume, query_metadata)
                
                # 计算综合得分（加权平均）
                overall_score = (
                    skill_score * 0.3 +
                    industry_score * 0.2 +
                    salary_score * 0.1 +
                    education_score * 0.1 +
                    location_score * 0.2 +
                    tag_score * 0.1
                )
                
                # 添加得分到简历数据中
                scored_resume = resume.copy()
                scored_resume["scores"] = {
                    "skill_score": skill_score,
                    "industry_score": industry_score,
                    "salary_score": salary_score,
                    "education_score": education_score,
                    "location_score": location_score,
                    "tag_score": tag_score,
                    "overall_score": overall_score
                }
                
                scored_resumes.append(scored_resume)
            
            logger.info(f"Scored {len(scored_resumes)} resumes")
            return scored_resumes
            
        except Exception as e:
            logger.error(f"Failed to score resumes: {e}")
            raise

    def _calculate_skill_score(self, resume: Dict[str, Any], query_metadata: QueryMetadata) -> float:
        """
        计算技能匹配得分
        
        Args:
            resume (Dict[str, Any]): 简历数据
            query_metadata (QueryMetadata): 查询元数据
            
        Returns:
            float: 技能匹配得分 (0-1)
        """
        # 获取简历技能和查询所需技能（兼容 list / JSON 字符串）
        skills_raw = resume.get("metadata", {}).get("skills", [])
        resume_skills = set([str(s).lower() for s in coerce_to_list(skills_raw)])
        required_skills = set([s.lower() for s in query_metadata.required_skills])
        preferred_skills = set([s.lower() for s in query_metadata.preferred_skills])
        
        # 如果没有技能要求，得分为1
        if not required_skills and not preferred_skills:
            return 1.0
        
        # 计算必需技能匹配度
        required_match = 0.0
        if required_skills:
            required_match = len(resume_skills.intersection(required_skills)) / len(required_skills)
        
        # 计算优先技能匹配度
        preferred_match = 0.0
        if preferred_skills:
            preferred_match = len(resume_skills.intersection(preferred_skills)) / len(preferred_skills)
        
        # 综合得分（必需技能权重0.8，优先技能权重0.2）
        skill_score = required_match * 0.8 + preferred_match * 0.2
        
        return min(skill_score, 1.0)

    def _calculate_industry_score(self, resume: Dict[str, Any], query_metadata: QueryMetadata) -> float:
        """
        计算行业领域匹配得分
        
        Args:
            resume (Dict[str, Any]): 简历数据
            query_metadata (QueryMetadata): 查询元数据
            
        Returns:
            float: 行业领域匹配得分 (0-1)
        """
        # 获取简历中的工作经历和查询所需行业（兼容 list / JSON 字符串）
        work_experience = coerce_to_list(resume.get("metadata", {}).get("work_experience", []))
        required_industries = set([i.lower() for i in query_metadata.required_industries])
        preferred_industries = set([i.lower() for i in query_metadata.preferred_industries])
        
        # 如果没有行业要求，得分为1
        if not required_industries and not preferred_industries:
            return 1.0
        
        # 提取工作经历中的公司行业
        resume_industries = set()
        for exp in work_experience:
            if not isinstance(exp, dict):
                continue
            company = exp.get("company", "")
            # 这里简化处理，实际项目中可能需要通过公司名称查询行业信息
            # 或者从简历的其他字段获取行业信息
            resume_industries.add(str(company).lower())
        
        # 计算必需行业匹配度
        required_match = 0.0
        if required_industries:
            required_match = len(resume_industries.intersection(required_industries)) / len(required_industries)
        
        # 计算优先行业匹配度
        preferred_match = 0.0
        if preferred_industries:
            preferred_match = len(resume_industries.intersection(preferred_industries)) / len(preferred_industries)
        
        # 综合得分（必需行业权重0.8，优先行业权重0.2）
        industry_score = required_match * 0.8 + preferred_match * 0.2
        
        return min(industry_score, 1.0)

    def _calculate_salary_score(self, resume: Dict[str, Any], query_metadata: QueryMetadata) -> float:
        """
        计算薪资匹配得分
        
        Args:
            resume (Dict[str, Any]): 简历数据
            query_metadata (QueryMetadata): 查询元数据
            
        Returns:
            float: 薪资匹配得分 (0-1)
        """
        # 获取简历期望薪资和查询薪资范围
        expected_salary = resume.get("metadata", {}).get("expected_salary", "")
        salary_range = query_metadata.salary_range
        
        # 如果没有薪资要求或期望薪资信息，得分为1
        if not salary_range or not expected_salary:
            return 1.0
        
        # 简化处理，实际项目中可能需要更复杂的薪资解析和比较逻辑
        # 这里假设薪资格式为 "数字K" 或 "数字K-数字K"
        try:
            # 解析期望薪资
            expected_min, expected_max = self._parse_salary(expected_salary)
            
            # 解析查询薪资范围
            range_min = salary_range.get("min", "0K")
            range_max = salary_range.get("max", "1000K")
            range_min_val, range_max_val = self._parse_salary(f"{range_min}-{range_max}")
            
            # 计算薪资匹配度
            # 如果期望薪资完全在范围内，得分为1
            if expected_min >= range_min_val and expected_max <= range_max_val:
                return 1.0
            
            # 如果部分重叠，计算重叠比例
            overlap_min = max(expected_min, range_min_val)
            overlap_max = min(expected_max, range_max_val)
            
            if overlap_min < overlap_max:
                overlap_range = overlap_max - overlap_min
                expected_range = expected_max - expected_min
                if expected_range > 0:
                    return min(overlap_range / expected_range, 1.0)
            
            # 如果没有重叠，得分为0
            return 0.0
            
        except Exception as e:
            logger.warning(f"Failed to calculate salary score: {e}")
            return 0.5  # 返回中等得分作为默认值

    def _parse_salary(self, salary_str: str) -> Tuple[float, float]:
        """
        解析薪资字符串
        
        Args:
            salary_str (str): 薪资字符串
            
        Returns:
            Tuple[float, float]: (最小薪资, 最大薪资)
        """
        # 移除空格并转换为小写
        salary_str = salary_str.replace(" ", "").lower()
        
        # 处理范围格式 "数字K-数字K"
        if "-" in salary_str:
            parts = salary_str.split("-")
            min_val = float(parts[0].replace("k", "")) * 1000
            max_val = float(parts[1].replace("k", "")) * 1000
            return min_val, max_val
        
        # 处理单个值格式 "数字K"
        if "k" in salary_str:
            val = float(salary_str.replace("k", "")) * 1000
            return val, val
            
        # 默认返回
        return 0.0, 1000000.0

    def _calculate_education_score(self, resume: Dict[str, Any], query_metadata: QueryMetadata) -> float:
        """
        计算学历匹配得分
        
        Args:
            resume (Dict[str, Any]): 简历数据
            query_metadata (QueryMetadata): 查询元数据
            
        Returns:
            float: 学历匹配得分 (0-1)
        """
        # 学历等级映射
        education_levels = {
            "大专": 1,
            "本科": 2,
            "硕士": 3,
            "博士": 4
        }
        
        # 获取简历学历和查询所需学历（兼容 list / JSON 字符串）
        education_list = coerce_to_list(resume.get("metadata", {}).get("education", []))
        required_education = query_metadata.required_education
        
        # 如果没有学历要求，得分为1
        if not required_education:
            return 1.0
        
        # 获取最高学历
        max_education_level = 0
        for edu in education_list:
            if not isinstance(edu, dict):
                continue
            degree = edu.get("degree", "")
            level = education_levels.get(degree, 0)
            if level > max_education_level:
                max_education_level = level
        
        # 获取所需学历等级
        required_level = education_levels.get(required_education, 0)
        
        # 计算得分
        if required_level == 0:
            return 1.0
            
        if max_education_level >= required_level:
            return 1.0
            
        return max_education_level / required_level

    def _calculate_location_score(self, resume: Dict[str, Any], query_metadata: QueryMetadata) -> float:
        """
        计算地理位置匹配得分
        
        Args:
            resume (Dict[str, Any]): 简历数据
            query_metadata (QueryMetadata): 查询元数据
            
        Returns:
            float: 地理位置匹配得分 (0-1)
        """
        # 获取简历期望工作地点和查询工作地点（兼容 list / JSON 字符串）
        preferred_locations = set(coerce_to_list(resume.get("metadata", {}).get("preferred_locations", [])))
        query_locations = set(query_metadata.locations)
        
        # 如果没有地点要求，得分为1
        if not query_locations:
            return 1.0
        
        # 计算匹配度
        intersection = len(preferred_locations.intersection(query_locations))
        union = len(preferred_locations.union(query_locations))
        
        if union == 0:
            return 1.0
            
        return intersection / union

    def _calculate_tag_score(self, resume: Dict[str, Any], query_metadata: QueryMetadata) -> float:
        """
        计算个性标签匹配得分
        
        Args:
            resume (Dict[str, Any]): 简历数据
            query_metadata (QueryMetadata): 查询元数据
            
        Returns:
            float: 个性标签匹配得分 (0-1)
        """
        # 这里简化处理，实际项目中可能需要从简历中提取个性标签
        # 并与查询中的个性标签要求进行匹配
        
        # 获取简历中的关键词和查询关键词
        resume_keywords = set()
        summary = resume.get("metadata", {}).get("summary", "")
        if summary:
            # 简化处理，实际项目中可能需要使用NLP技术提取关键词
            resume_keywords = set(summary.lower().split())
        
        query_keywords = set([k.lower() for k in query_metadata.keywords])
        
        # 如果没有关键词要求，得分为1
        if not query_keywords:
            return 1.0
        
        # 计算匹配度
        intersection = len(resume_keywords.intersection(query_keywords))
        union = len(resume_keywords.union(query_keywords))
        
        if union == 0:
            return 1.0
            
        return intersection / union