from typing import List, Dict, Any
from app.core.llm_client import LLMClient
from app.models.metadata import ResumeMetadata, QueryMetadata
from loguru import logger


class CandidateAnalyzer:
    """
    候选人分析器，用于生成候选人综合评价
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        初始化候选人分析器
        
        Args:
            llm_client (LLMClient): LLM客户端实例
        """
        self.llm_client = llm_client
        logger.info("Initialized CandidateAnalyzer")

    def analyze_candidate(self, resume: Dict[str, Any], query_metadata: QueryMetadata) -> Dict[str, Any]:
        """
        生成候选人的综合评价
        
        Args:
            resume (Dict[str, Any]): 简历数据
            query_metadata (QueryMetadata): 查询元数据
            
        Returns:
            Dict[str, Any]: 包含综合评价的候选人数据
        """
        try:
            # 检查resume是否为字典类型
            if not isinstance(resume, dict):
                logger.warning(f"Skipping non-dict resume in analysis: {type(resume)}")
                # 创建一个包含错误信息的候选人数据
                candidate = {}
                candidate["id"] = "unknown"
                candidate["analysis"] = "分析失败：简历格式无效"
                return candidate


            # 构造分析提示词
            prompt = self._create_analysis_prompt(resume, query_metadata)
            
            # 使用LLM生成分析结果
            analysis = self.llm_client.generate_text(prompt)
            
            # 创建包含分析结果的候选人数据
            candidate = resume.copy()
            candidate["analysis"] = analysis
            
            logger.info(f"Analyzed candidate: {resume.get('id', 'unknown')}")
            return candidate
            
        except Exception as e:
            logger.error(f"Failed to analyze candidate: {e}")
            raise

    def analyze_candidates(self, resumes: List[Dict[str, Any]], query_metadata: QueryMetadata) -> List[Dict[str, Any]]:
        """
        批量生成候选人的综合评价
        
        Args:
            resumes (List[Dict[str, Any]]): 简历列表
            query_metadata (QueryMetadata): 查询元数据
            
        Returns:
            List[Dict[str, Any]]: 包含综合评价的候选人列表
        """
        analyzed_candidates = []
        
        for resume in resumes:
            try:
                analyzed_candidate = self.analyze_candidate(resume, query_metadata)
                analyzed_candidates.append(analyzed_candidate)
            except Exception as e:
                logger.error(f"Failed to analyze candidate {resume.get('id', 'unknown')}: {e}")
                # 即使某个候选人分析失败，也继续处理其他候选人
                analyzed_candidate = resume.copy()
                analyzed_candidate["analysis"] = "分析失败"
                analyzed_candidates.append(analyzed_candidate)
        
        return analyzed_candidates

    def _create_analysis_prompt(self, resume: Dict[str, Any], query_metadata: QueryMetadata) -> str:
        """
        创建候选人分析提示词
        
        Args:
            resume (Dict[str, Any]): 简历数据
            query_metadata (QueryMetadata): 查询元数据
            
        Returns:
            str: 构造的提示词
        """
        # 提取简历关键信息
        metadata = resume.get("metadata", {})
        # 检查metadata是否为字典类型
        if not isinstance(metadata, dict):
            logger.warning(f"Invalid metadata type in resume: {type(metadata)}")
            metadata = {}

        name = metadata.get("name", "未知")
        skills = metadata.get("skills", [])
        work_experience = metadata.get("work_experience", [])
        education = metadata.get("education", [])
        
        # 提取查询关键信息
        required_skills = query_metadata.required_skills
        preferred_skills = query_metadata.preferred_skills
        min_experience_years = query_metadata.min_experience_years
        required_education = query_metadata.required_education
        
        prompt = f"""
你是一个专业的HR顾问，请根据以下简历信息和职位要求，对候选人进行综合评价。

候选人姓名: {name}

简历信息:
1. 技能: {', '.join(skills)}
2. 工作经历: 
   {self._format_work_experience(work_experience)}
3. 教育背景: 
   {self._format_education(education)}

职位要求:
1. 必需技能: {', '.join(required_skills) if required_skills else "无"}
2. 优先技能: {', '.join(preferred_skills) if preferred_skills else "无"}
3. 最少经验年限: {min_experience_years if min_experience_years else "无要求"}
4. 学历要求: {required_education if required_education else "无要求"}

请从以下几个维度对候选人进行评价:
1. 技能匹配度: 候选人的技能与职位要求的匹配程度
2. 经验匹配度: 候选人的工作经验与职位要求的匹配程度
3. 教育背景匹配度: 候选人的教育背景与职位要求的匹配程度
4. 综合优势: 候选人的突出优势
5. 潜在风险: 候选人可能存在的不足或风险
6. 推荐建议: 是否推荐该候选人进入下一轮面试，以及相关建议

请用中文输出一份结构清晰、内容详实的候选人评价报告。
"""
        return prompt

    def _format_work_experience(self, work_experience: List[Dict[str, Any]]) -> str:
        """
        格式化工作经历
        
        Args:
            work_experience (List[Dict[str, Any]]): 工作经历列表
            
        Returns:
            str: 格式化后的工作经历
        """
        # 检查work_experience是否为列表类型
        if not isinstance(work_experience, list):
            logger.warning(f"Invalid work_experience type: {type(work_experience)}")
            return "工作经历格式无效"

        if not work_experience:
            return "无工作经历"
        
        formatted = []
        for exp in work_experience:
            # 检查每个经历是否为字典类型
            if not isinstance(exp, dict):
                logger.warning(f"Invalid work experience entry type: {type(exp)}")
                formatted.append("   - 无效的工作经历条目")
                continue

            company = exp.get("company", "未知公司")
            title = exp.get("title", "未知职位")
            start_date = exp.get("start_date", "未知开始时间")
            end_date = exp.get("end_date", "未知结束时间")
            description = exp.get("description", "")
            
            exp_str = f"   - {company} ({title}) {start_date} - {end_date}"
            if description:
                exp_str += f"\n     工作描述: {description}"
            formatted.append(exp_str)
        
        return "\n".join(formatted)

    def _format_education(self, education: List[Dict[str, Any]]) -> str:
        """
        格式化教育背景
        
        Args:
            education (List[Dict[str, Any]]): 教育背景列表
            
        Returns:
            str: 格式化后的教育背景
        """
        # 检查education是否为列表类型
        if not isinstance(education, list):
            logger.warning(f"Invalid education type: {type(education)}")
            return "教育背景格式无效"

        if not education:
            return "无教育背景"
        
        formatted = []
        for edu in education:
            # 检查每个教育背景是否为字典类型
            if not isinstance(edu, dict):
                logger.warning(f"Invalid education entry type: {type(edu)}")
                formatted.append("   - 无效的教育背景条目")
                continue

            institution = edu.get("institution", "未知院校")
            major = edu.get("major", "未知专业")
            degree = edu.get("degree", "未知学位")
            start_date = edu.get("start_date", "未知开始时间")
            end_date = edu.get("end_date", "未知结束时间")
            
            edu_str = f"   - {institution} ({major}) {degree} {start_date} - {end_date}"
            formatted.append(edu_str)
        
        return "\n".join(formatted)