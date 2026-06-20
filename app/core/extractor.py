from typing import Dict, Any, List, Optional
from app.core.llm_client import LLMClient
from app.core.cache_manager import CacheManager
from app.models.metadata import ResumeMetadata
from loguru import logger
import json
import hashlib


class MetadataExtractor:
    """
    元数据提取器
    """
    
    def __init__(self, llm_client: LLMClient, cache_manager: Optional[CacheManager] = None):
        """
        初始化元数据提取器
        
        Args:
            llm_client (LLMClient): LLM客户端实例
            cache_manager (CacheManager, optional): 缓存管理器实例
        """
        self.llm_client = llm_client
        self.cache_manager = cache_manager
        logger.info("Initialized MetadataExtractor")

    def extract_metadata(self, resume_text: str) -> ResumeMetadata:
        """
        从简历文本中提取元数据
        
        Args:
            resume_text (str): 简历文本内容
            
        Returns:
            ResumeMetadata: 提取的元数据对象
            
        Raises:
            ValueError: 如果解析的JSON格式无效
            Exception: 如果提取过程失败
        """
        try:
            # 生成简历文本的哈希值作为缓存键
            cache_key = f"metadata_{hashlib.md5(resume_text.encode()).hexdigest()}"
            
            # 尝试从缓存中获取结果
            if self.cache_manager:
                cached_result = self.cache_manager.get(cache_key)
                if cached_result:
                    logger.info(f"Retrieved metadata from cache for key: {cache_key}")
                    return ResumeMetadata(**cached_result)
            
            # 构造提示词
            prompt = self._create_extraction_prompt(resume_text)
            
            # 使用LLM生成提取结果
            response = self.llm_client.generate_text(prompt)
            
            # 解析响应为JSON
            metadata_dict = self._parse_response(response)
            
            # 创建ResumeMetadata对象
            metadata = ResumeMetadata(**metadata_dict)
            
            # 将结果存入缓存
            if self.cache_manager:
                self.cache_manager.set(cache_key, metadata_dict, expire=3600)  # 缓存1小时
                logger.info(f"Cached metadata for key: {cache_key}")
            
            logger.info(f"Extracted metadata for candidate: {metadata.name}")
            return metadata
            
        except ValueError as e:
            logger.error(f"Invalid JSON format in LLM response: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
            raise Exception(f"Failed to extract metadata: {e}")

    def _create_extraction_prompt(self, resume_text: str) -> str:
        """
        创建元数据提取提示词
        
        Args:
            resume_text (str): 简历文本内容
            
        Returns:
            str: 构造的提示词
        """
        prompt = f"""
请从以下简历文本中提取元数据，并以JSON格式返回结果。

简历文本:
{resume_text}

请提取以下字段：
- name: 姓名
- email: 邮箱地址
- phone: 电话号码
- address: 地址
- work_experience: 工作经历列表，每个项目包含公司名称(company)、职位(title)、开始时间(start_date)、结束时间(end_date)、工作描述(description)
- education: 教育背景列表，每个项目包含学校名称(institution)、专业(major)、学位(degree)、开始时间(start_date)、结束时间(end_date)
- skills: 技能列表
- projects: 项目经历列表，每个项目包含项目名称(name)、项目描述(description)、项目时间(period)
- languages: 语言能力列表
- certifications: 证书列表
- expected_salary: 期望薪资
- preferred_locations: 期望工作地点列表
- summary: 个人简介
- additional_info: 其他信息

请严格按照以下JSON格式返回结果，不要包含其他文本：
{{
  "name": "张三",
  "email": "zhangsan@example.com",
  "phone": "13800138000",
  "address": "北京市朝阳区",
  "work_experience": [
    {{
      "company": "ABC公司",
      "title": "软件工程师",
      "start_date": "2020-01",
      "end_date": "2023-12",
      "description": "负责..."
    }}
  ],
  "education": [
    {{
      "institution": "清华大学",
      "major": "计算机科学与技术",
      "degree": "本科",
      "start_date": "2016-09",
      "end_date": "2020-06"
    }}
  ],
  "skills": ["Python", "Java", "SQL"],
  "projects": [
    {{
      "name": "电商系统",
      "description": "开发了一个电商系统",
      "period": "2022-01 至 2022-06"
    }}
  ],
  "languages": ["中文", "英语"],
  "certifications": ["软件设计师"],
  "expected_salary": "20K-30K",
  "preferred_locations": ["北京", "上海"],
  "summary": "具有5年工作经验的软件工程师",
  "additional_info": "其他信息"
}}

只返回JSON，不要包含其他解释文本。
"""
        return prompt

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        解析LLM响应
        
        Args:
            response (str): LLM生成的响应
            
        Returns:
            Dict[str, Any]: 解析后的元数据字典
            
        Raises:
            ValueError: 如果响应不是有效的JSON格式
        """
        try:
            # 尝试直接解析JSON
            metadata_dict = json.loads(response)
            return metadata_dict
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试从响应中提取JSON部分
            # 这种情况可能发生在LLM返回了额外的解释文本时
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end != -1 and start < end:
                json_str = response[start:end]
                try:
                    metadata_dict = json.loads(json_str)
                    return metadata_dict
                except json.JSONDecodeError:
                    pass
            
            # 如果所有尝试都失败，抛出异常
            raise ValueError(f"Failed to parse response as JSON: {response}")