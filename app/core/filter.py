from typing import List, Dict, Any
from app.core.metadata_utils import coerce_to_list
from app.models.metadata import ResumeMetadata, QueryMetadata
from loguru import logger


class HardFilter:
    """
    硬性条件过滤器，用于根据硬性条件过滤简历
    """
    
    def __init__(self):
        """
        初始化硬性条件过滤器
        """
        logger.info("Initialized HardFilter")

    @staticmethod
    def _fuzzy_in(target: str, candidates: List[Any]) -> bool:
        """大小写不敏感的双向子串匹配。

        用于兼容 LLM 抽取的措辞差异，例如查询 "北京" 命中简历 "北京市"，
        查询 "Django" 命中 "Django框架"。target 为空视为匹配。
        """
        t = str(target).strip().lower()
        if not t:
            return True
        for c in candidates:
            cs = str(c).strip().lower()
            if not cs:
                continue
            if t in cs or cs in t:
                return True
        return False

    @staticmethod
    def _resume_text(resume: Dict[str, Any]) -> str:
        """汇总简历正文与摘要，用于结构化字段缺失时的兜底匹配。

        LLM 抽取常会遗漏部分技能/地点（仅出现在正文里），因此硬性条件
        匹配时同时检索原始文本，避免误杀合格候选人。
        """
        metadata = resume.get("metadata", {}) if isinstance(resume, dict) else {}
        parts = [
            str(resume.get("text", "")),
            str(metadata.get("summary", "")) if isinstance(metadata, dict) else "",
            str(metadata.get("additional_info", "")) if isinstance(metadata, dict) else "",
        ]
        return " ".join(parts).lower()

    @staticmethod
    def _parse_year(date_str: Any) -> tuple:
        """健壮地解析日期字符串，返回 (年份, 是否至今)。

        支持以下形式：
        - 2020-01、2020/01、2020.01、2020年1月
        - 至今 / present / now / 当前 / 今（视为当前年份）
        - 纯数字年份 2020
        无法解析时返回 (None, False)。
        """
        from datetime import datetime

        if date_str is None:
            return None, False

        s = str(date_str).strip().lower()
        if not s:
            return None, False

        # 处理“至今”等表示当前的词
        present_markers = {"至今", "present", "now", "当前", "今", "现在", "今至今"}
        if s in present_markers:
            return datetime.now().year, True

        # 移除常见中文/英文后缀，只保留开头数字
        import re
        m = re.search(r"(\d{4})", s)
        if m:
            try:
                year = int(m.group(1))
                if 1950 <= year <= datetime.now().year + 1:
                    return year, False
            except ValueError:
                pass

        return None, False

    def _matches(self, target: str, candidates: List[Any], fulltext: str = "") -> bool:
        """结构化字段模糊匹配，命中失败时回退到全文子串匹配。"""
        if self._fuzzy_in(target, candidates):
            return True
        t = str(target).strip().lower()
        return bool(t) and bool(fulltext) and t in fulltext

    def filter_resumes(self, resumes: List[Dict[str, Any]], query_metadata: QueryMetadata) -> List[Dict[str, Any]]:
        """
        根据查询元数据过滤简历
        
        Args:
            resumes (List[Dict[str, Any]]): 简历列表
            query_metadata (QueryMetadata): 查询元数据
            
        Returns:
            List[Dict[str, Any]]: 过滤后的简历列表
        """
        try:
            # 添加日志来调试问题
            logger.info(f"Resume filter input type: {type(resumes)}")
            logger.info(f"Resume filter input length: {len(resumes) if isinstance(resumes, list) else 'N/A'}")
            if isinstance(resumes, list) and resumes:
                logger.info(f"First resume type: {type(resumes[0])}")
                logger.info(f"First resume content: {resumes[0]}")
                
                # 过滤掉非字典类型的简历
                resumes = [r for r in resumes if isinstance(r, dict)]
                logger.info(f"Filtered non-dict resumes, remaining: {len(resumes)}")
                
            filtered_resumes = resumes.copy() if isinstance(resumes, list) else []
            
            # 根据所需经验年限过滤
            if query_metadata.min_experience_years is not None and isinstance(filtered_resumes, list):
                logger.info(f"Before experience filter: {len(filtered_resumes)}")
                filtered_resumes = self._filter_by_experience(filtered_resumes, query_metadata.min_experience_years)
                logger.info(f"After experience filter: {len(filtered_resumes)}")
            
            # 根据所需学历过滤
            if query_metadata.required_education is not None and isinstance(filtered_resumes, list):
                logger.info(f"Before education filter: {len(filtered_resumes)}")
                filtered_resumes = self._filter_by_education(filtered_resumes, query_metadata.required_education)
                logger.info(f"After education filter: {len(filtered_resumes)}")
            
            # 根据所需技能过滤
            if query_metadata.required_skills and isinstance(filtered_resumes, list):
                logger.info(f"Before skills filter: {len(filtered_resumes)}")
                filtered_resumes = self._filter_by_skills(filtered_resumes, query_metadata.required_skills)
                logger.info(f"After skills filter: {len(filtered_resumes)}")
            
            # 根据工作地点过滤
            if query_metadata.locations and isinstance(filtered_resumes, list):
                logger.info(f"Before locations filter: {len(filtered_resumes)}")
                filtered_resumes = self._filter_by_locations(filtered_resumes, query_metadata.locations)
                logger.info(f"After locations filter: {len(filtered_resumes)}")
            
            # 根据语言要求过滤
            if query_metadata.required_languages and isinstance(filtered_resumes, list):
                logger.info(f"Before languages filter: {len(filtered_resumes)}")
                filtered_resumes = self._filter_by_languages(filtered_resumes, query_metadata.required_languages)
                logger.info(f"After languages filter: {len(filtered_resumes)}")
            
            # 根据证书要求过滤
            if query_metadata.required_certifications and isinstance(filtered_resumes, list):
                logger.info(f"Before certifications filter: {len(filtered_resumes)}")
                filtered_resumes = self._filter_by_certifications(filtered_resumes, query_metadata.required_certifications)
                logger.info(f"After certifications filter: {len(filtered_resumes)}")
            
            logger.info(f"Filtered resumes from {len(resumes)} to {len(filtered_resumes)}")
            return filtered_resumes
            
        except Exception as e:
            logger.error(f"Failed to filter resumes: {e}")
            raise

    def _filter_by_experience(self, resumes: List[Dict[str, Any]], min_experience_years: int) -> List[Dict[str, Any]]:
        """
        根据经验年限过滤简历
        
        Args:
            resumes (List[Dict[str, Any]]): 简历列表
            min_experience_years (int): 最少经验年限
            
        Returns:
            List[Dict[str, Any]]: 过滤后的简历列表
        """
        filtered_resumes = []
        
        for resume in resumes:
            # 检查resume是否为字典类型
            if not isinstance(resume, dict):
                logger.warning(f"Skipping non-dict resume: {type(resume)}")
                continue
            
            # 从元数据中提取工作经验
            metadata = resume.get("metadata", {})
            if not isinstance(metadata, dict):
                logger.warning(f"Skipping resume with non-dict metadata: {type(metadata)}")
                continue
                
            work_experience = metadata.get("work_experience", [])
            # 兼容 list / JSON 字符串 / 逗号分隔字符串
            work_experience = coerce_to_list(work_experience)

            # 计算总工作经验年限
            total_experience = 0
            has_experience_data = False
            for exp in work_experience:
                if not isinstance(exp, dict):
                    logger.warning(f"Skipping non-dict work experience entry: {type(exp)}")
                    continue

                start_date = exp.get("start_date")
                end_date = exp.get("end_date")
                if start_date and end_date:
                    has_experience_data = True
                    # 简单计算年份差（实际项目中可能需要更精确的计算）
                    start_year = int(start_date.split("-")[0]) if "-" in start_date else 0
                    end_year = int(end_date.split("-")[0]) if "-" in end_date else 2025
                    total_experience += end_year - start_year

            # 若简历缺少可解析的经验数据，则不在此条件上误杀（数据缺失 != 不满足）；
            # 若有数据但年限不足，则按硬性条件过滤。
            if not has_experience_data or total_experience >= min_experience_years:
                filtered_resumes.append(resume)
                
        return filtered_resumes

    def _filter_by_education(self, resumes: List[Dict[str, Any]], required_education: str) -> List[Dict[str, Any]]:
        """
        根据学历过滤简历
        
        Args:
            resumes (List[Dict[str, Any]]): 简历列表
            required_education (str): 所需学历
            
        Returns:
            List[Dict[str, Any]]: 过滤后的简历列表
        """
        # 学历等级映射
        education_levels = {
            "大专": 1,
            "本科": 2,
            "硕士": 3,
            "博士": 4
        }
        
        required_level = education_levels.get(required_education, 0)
        filtered_resumes = []
        
        for resume in resumes:
            # 检查resume是否为字典类型
            if not isinstance(resume, dict):
                logger.warning(f"Skipping non-dict resume: {type(resume)}")
                continue
            
            # 从元数据中提取教育背景
            metadata = resume.get("metadata", {})
            if not isinstance(metadata, dict):
                logger.warning(f"Skipping resume with non-dict metadata: {type(metadata)}")
                continue
                
            education_list = metadata.get("education", [])
            # 兼容 list / JSON 字符串 / 逗号分隔字符串
            education_list = coerce_to_list(education_list)

            # 检查是否有满足要求的学历
            meets_requirement = False
            has_degree_data = False
            for edu in education_list:
                if not isinstance(edu, dict):
                    logger.warning(f"Skipping non-dict education entry: {type(edu)}")
                    continue

                degree = edu.get("degree", "")
                if degree:
                    has_degree_data = True
                if education_levels.get(degree, 0) >= required_level:
                    meets_requirement = True
                    break

            # 缺少可识别的学历数据则不在此条件误杀（数据缺失 != 不满足）
            if meets_requirement or not has_degree_data:
                filtered_resumes.append(resume)
                
        return filtered_resumes

    def _filter_by_skills(self, resumes: List[Dict[str, Any]], required_skills: List[str]) -> List[Dict[str, Any]]:
        """
        根据技能过滤简历
        
        Args:
            resumes (List[Dict[str, Any]]): 简历列表
            required_skills (List[str]): 所需技能列表
            
        Returns:
            List[Dict[str, Any]]: 过滤后的简历列表
        """
        filtered_resumes = []
        
        for resume in resumes:
            # 检查resume是否为字典类型
            if not isinstance(resume, dict):
                logger.warning(f"Skipping non-dict resume: {type(resume)}")
                continue
            
            # 从元数据中提取技能
            metadata = resume.get("metadata", {})
            if not isinstance(metadata, dict):
                logger.warning(f"Skipping resume with non-dict metadata: {type(metadata)}")
                continue
                
            skills = metadata.get("skills", [])
            # 兼容 list / JSON 字符串 / 逗号分隔字符串
            skills = coerce_to_list(skills)

            # 检查是否包含所有必需技能：结构化字段优先，回退到简历全文
            # （LLM 常把技能写进正文而漏填 skills 字段）
            fulltext = self._resume_text(resume)
            meets_requirement = all(self._matches(skill, skills, fulltext) for skill in required_skills)

            if meets_requirement:
                filtered_resumes.append(resume)
                
        return filtered_resumes

    def _filter_by_locations(self, resumes: List[Dict[str, Any]], locations: List[str]) -> List[Dict[str, Any]]:
        """
        根据工作地点过滤简历
        
        Args:
            resumes (List[Dict[str, Any]]): 简历列表
            locations (List[str]): 工作地点列表
            
        Returns:
            List[Dict[str, Any]]: 过滤后的简历列表
        """
        filtered_resumes = []
        
        for resume in resumes:
            # 检查resume是否为字典类型
            if not isinstance(resume, dict):
                logger.warning(f"Skipping non-dict resume: {type(resume)}")
                continue
            
            # 从元数据中提取期望工作地点
            metadata = resume.get("metadata", {})
            if not isinstance(metadata, dict):
                logger.warning(f"Skipping resume with non-dict metadata: {type(metadata)}")
                continue
                
            preferred_locations = metadata.get("preferred_locations", [])
            # 兼容 list / JSON 字符串 / 逗号分隔字符串
            preferred_locations = coerce_to_list(preferred_locations)

            # 无地点数据则不在此条件误杀
            if not preferred_locations:
                filtered_resumes.append(resume)
                continue

            # 检查是否有匹配的地点（结构化优先，回退全文；"北京" 命中 "北京市"）
            fulltext = self._resume_text(resume)
            meets_requirement = any(self._matches(location, preferred_locations, fulltext) for location in locations)

            if meets_requirement:
                filtered_resumes.append(resume)
                
        return filtered_resumes

    def _filter_by_languages(self, resumes: List[Dict[str, Any]], required_languages: List[str]) -> List[Dict[str, Any]]:
        """
        根据语言要求过滤简历
        
        Args:
            resumes (List[Dict[str, Any]]): 简历列表
            required_languages (List[str]): 语言要求列表
            
        Returns:
            List[Dict[str, Any]]: 过滤后的简历列表
        """
        filtered_resumes = []
        
        for resume in resumes:
            # 检查resume是否为字典类型
            if not isinstance(resume, dict):
                logger.warning(f"Skipping non-dict resume: {type(resume)}")
                continue
            
            # 从元数据中提取语言能力
            metadata = resume.get("metadata", {})
            if not isinstance(metadata, dict):
                logger.warning(f"Skipping resume with non-dict metadata: {type(metadata)}")
                continue
                
            languages = metadata.get("languages", [])
            # 兼容 list / JSON 字符串 / 逗号分隔字符串
            languages = coerce_to_list(languages)

            # 无语言数据则不在此条件误杀
            if not languages:
                filtered_resumes.append(resume)
                continue

            # 检查是否满足所有语言要求（结构化优先，回退全文）
            fulltext = self._resume_text(resume)
            meets_requirement = all(self._matches(language, languages, fulltext) for language in required_languages)

            if meets_requirement:
                filtered_resumes.append(resume)
                
        return filtered_resumes

    def _filter_by_certifications(self, resumes: List[Dict[str, Any]], required_certifications: List[str]) -> List[Dict[str, Any]]:
        """
        根据证书要求过滤简历
        
        Args:
            resumes (List[Dict[str, Any]]): 简历列表
            required_certifications (List[str]): 证书要求列表
            
        Returns:
            List[Dict[str, Any]]: 过滤后的简历列表
        """
        filtered_resumes = []
        
        for resume in resumes:
            # 检查resume是否为字典类型
            if not isinstance(resume, dict):
                logger.warning(f"Skipping non-dict resume: {type(resume)}")
                continue
            
            # 从元数据中提取证书
            metadata = resume.get("metadata", {})
            if not isinstance(metadata, dict):
                logger.warning(f"Skipping resume with non-dict metadata: {type(metadata)}")
                continue
                
            certifications = metadata.get("certifications", [])
            # 兼容 list / JSON 字符串 / 逗号分隔字符串
            certifications = coerce_to_list(certifications)

            # 无证书数据则不在此条件误杀
            if not certifications:
                filtered_resumes.append(resume)
                continue

            # 检查是否满足所有证书要求（结构化优先，回退全文）
            fulltext = self._resume_text(resume)
            meets_requirement = all(self._matches(cert, certifications, fulltext) for cert in required_certifications)

            if meets_requirement:
                filtered_resumes.append(resume)
                
        return filtered_resumes