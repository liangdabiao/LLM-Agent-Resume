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
        计算技能匹配得分。支持模糊子串匹配，例如 "Django" 命中 "Django框架"。
        """
        skills_raw = resume.get("metadata", {}).get("skills", [])
        resume_skills = [str(s).lower() for s in coerce_to_list(skills_raw)]
        required_skills = [s.lower() for s in query_metadata.required_skills]
        preferred_skills = [s.lower() for s in query_metadata.preferred_skills]

        if not required_skills and not preferred_skills:
            return 1.0

        fulltext = self._resume_text(resume)

        def match_rate(skills: List[str]) -> float:
            if not skills:
                return 0.0
            matched = 0
            for skill in skills:
                if any(skill in rs or rs in skill for rs in resume_skills):
                    matched += 1
                elif skill in fulltext:
                    matched += 1
            return matched / len(skills)

        required_match = match_rate(required_skills)
        preferred_match = match_rate(preferred_skills)

        if required_skills and preferred_skills:
            return min(required_match * 0.8 + preferred_match * 0.2, 1.0)
        if required_skills:
            return min(required_match, 1.0)
        return min(preferred_match, 1.0)

    def _calculate_industry_score(self, resume: Dict[str, Any], query_metadata: QueryMetadata) -> float:
        """
        计算行业领域匹配得分。将行业关键词与工作经历文本做子串匹配，
        而不是直接比较公司名称。
        """
        work_experience = coerce_to_list(resume.get("metadata", {}).get("work_experience", []))
        required_industries = [i.lower() for i in query_metadata.required_industries]
        preferred_industries = [i.lower() for i in query_metadata.preferred_industries]

        if not required_industries and not preferred_industries:
            return 1.0

        exp_texts = []
        for exp in work_experience:
            if not isinstance(exp, dict):
                continue
            parts = [
                str(exp.get("company", "")),
                str(exp.get("title", "")),
                str(exp.get("description", "")),
            ]
            exp_texts.append(" ".join(parts).lower())
        exp_text = " ".join(exp_texts)

        def match_rate(industries: List[str]) -> float:
            if not industries:
                return 0.0
            matched = sum(1 for ind in industries if ind in exp_text)
            return matched / len(industries)

        required_match = match_rate(required_industries)
        preferred_match = match_rate(preferred_industries)

        if required_industries and preferred_industries:
            return min(required_match * 0.8 + preferred_match * 0.2, 1.0)
        if required_industries:
            return min(required_match, 1.0)
        return min(preferred_match, 1.0)

    def _calculate_salary_score(self, resume: Dict[str, Any], query_metadata: QueryMetadata) -> float:
        """
        计算薪资匹配得分
        """
        expected_salary = resume.get("metadata", {}).get("expected_salary", "")
        salary_range = query_metadata.salary_range

        if not salary_range or not expected_salary:
            return 1.0

        try:
            expected_min, expected_max = self._parse_salary(expected_salary)

            range_min = salary_range.get("min", "0")
            range_max = salary_range.get("max", "1000000")
            range_min_val, range_max_val = self._parse_salary(f"{range_min}-{range_max}")

            if expected_min >= range_min_val and expected_max <= range_max_val:
                return 1.0

            overlap_min = max(expected_min, range_min_val)
            overlap_max = min(expected_max, range_max_val)

            if overlap_min < overlap_max:
                overlap_range = overlap_max - overlap_min
                expected_range = expected_max - expected_min
                if expected_range > 0:
                    return min(overlap_range / expected_range, 1.0)

            return 0.0

        except Exception as e:
            logger.warning(f"Failed to calculate salary score: {e}")
            return 0.5

    def _parse_salary(self, salary_str: str) -> Tuple[float, float]:
        """
        解析薪资字符串，支持 K、万、元、面议 等常见表达。

        Returns:
            Tuple[float, float]: (最小薪资, 最大薪资)，单位：元
        """
        import re

        if salary_str is None:
            return 0.0, 1000000.0

        s = str(salary_str).replace(" ", "").lower().strip()
        if not s or "面议" in s or "negotiable" in s:
            return 0.0, 1000000.0

        numbers = [float(n) for n in re.findall(r"\d+\.?\d*", s)]
        if not numbers:
            return 0.0, 1000000.0

        unit = 1.0
        if "万" in s:
            unit = 10000.0
        elif "k" in s:
            unit = 1000.0

        if "-" in s and len(numbers) >= 2:
            min_val = numbers[0] * unit
            max_val = numbers[1] * unit
        elif "~" in s and len(numbers) >= 2:
            min_val = numbers[0] * unit
            max_val = numbers[1] * unit
        else:
            val = numbers[0] * unit
            min_val = val
            max_val = val

        return min_val, max_val

    def _calculate_education_score(self, resume: Dict[str, Any], query_metadata: QueryMetadata) -> float:
        """
        计算学历匹配得分
        """
        education_levels = {
            "大专": 1,
            "本科": 2,
            "硕士": 3,
            "博士": 4
        }

        education_list = coerce_to_list(resume.get("metadata", {}).get("education", []))
        required_education = query_metadata.required_education

        if not required_education:
            return 1.0

        max_education_level = 0
        for edu in education_list:
            if not isinstance(edu, dict):
                continue
            degree = edu.get("degree", "")
            level = education_levels.get(degree, 0)
            if level > max_education_level:
                max_education_level = level

        required_level = education_levels.get(required_education, 0)

        if required_level == 0:
            return 1.0

        if max_education_level >= required_level:
            return 1.0

        return max_education_level / required_level

    def _calculate_location_score(self, resume: Dict[str, Any], query_metadata: QueryMetadata) -> float:
        """
        计算地理位置匹配得分，使用模糊匹配（如“北京”命中“北京市”）。
        """
        preferred_locations = [str(loc).lower() for loc in coerce_to_list(resume.get("metadata", {}).get("preferred_locations", []))]
        query_locations = [str(loc).lower() for loc in query_metadata.locations]

        if not query_locations:
            return 1.0

        if not preferred_locations:
            return 0.0

        matched = 0
        for qloc in query_locations:
            for ploc in preferred_locations:
                if qloc in ploc or ploc in qloc:
                    matched += 1
                    break

        return min(matched / len(query_locations), 1.0)

    def _calculate_tag_score(self, resume: Dict[str, Any], query_metadata: QueryMetadata) -> float:
        """
        计算个性标签/关键词匹配得分，支持中文子串匹配。
        """
        metadata = resume.get("metadata", {}) if isinstance(resume, dict) else {}
        if not isinstance(metadata, dict):
            metadata = {}

        parts = [
            str(metadata.get("summary", "")),
            str(metadata.get("additional_info", "")),
            str(resume.get("text", "")),
        ]
        resume_text = " ".join(parts).lower()

        query_keywords = [k.lower() for k in query_metadata.keywords if k]

        if not query_keywords:
            return 1.0

        if not resume_text.strip():
            return 0.0

        matched = sum(1 for kw in query_keywords if kw in resume_text)
        return min(matched / len(query_keywords), 1.0)

    @staticmethod
    def _resume_text(resume: Dict[str, Any]) -> str:
        """汇总简历正文与摘要，用于技能等字段缺失时的兜底匹配。"""
        metadata = resume.get("metadata", {}) if isinstance(resume, dict) else {}
        if not isinstance(metadata, dict):
            metadata = {}
        parts = [
            str(resume.get("text", "")),
            str(metadata.get("summary", "")),
            str(metadata.get("additional_info", "")),
        ]
        return " ".join(parts).lower()
