from typing import List, Dict, Any, Optional
from app.core.llm_client import LLMClient
from app.models.metadata import QueryMetadata
from loguru import logger
import json


class QueryParser:
    """
    查询解析器，用于解析HR的自然语言查询
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        初始化查询解析器
        
        Args:
            llm_client (LLMClient): LLM客户端实例
        """
        self.llm_client = llm_client
        logger.info("Initialized QueryParser")

    def parse_query(self, query_text: str) -> QueryMetadata:
        """
        解析自然语言查询为结构化查询元数据
        
        Args:
            query_text (str): HR的自然语言查询
            
        Returns:
            QueryMetadata: 结构化的查询元数据对象
        """
        try:
            # 构造提示词
            prompt = self._create_parsing_prompt(query_text)
            
            # 使用LLM生成解析结果
            response = self.llm_client.generate_text(prompt)
            
            # 解析响应为JSON
            query_dict = self._parse_response(response)
            
            # 创建QueryMetadata对象
            query_metadata = QueryMetadata(**query_dict)
            
            logger.info(f"Parsed query: {query_metadata}")
            return query_metadata
            
        except Exception as e:
            logger.error(f"Failed to parse query: {e}")
            raise

    def _create_parsing_prompt(self, query_text: str) -> str:
        """
        创建查询解析提示词
        
        Args:
            query_text (str): HR的自然语言查询
            
        Returns:
            str: 构造的提示词
        """
        prompt = f"""
请将以下HR的自然语言查询解析为结构化的查询元数据，并以JSON格式返回结果。

查询文本:
{query_text}

请提取以下字段：
- keywords: 关键词列表
- required_skills: 所需技能列表
- preferred_skills: 优先技能列表
- min_experience_years: 所需经验年限
- required_education: 所需学历
- required_industries: 所需行业列表
- preferred_industries: 优先行业列表
- salary_range: 薪资范围，包含min和max字段
- locations: 工作地点列表
- required_languages: 语言要求列表
- required_certifications: 证书要求列表
- custom_conditions: 其他自定义条件

请严格按照以下JSON格式返回结果，不要包含其他文本：
{{
  "keywords": ["Python", "后端"],
  "required_skills": ["Python", "Django", "SQL"],
  "preferred_skills": ["Redis", "Docker"],
  "min_experience_years": 3,
  "required_education": "本科",
  "required_industries": ["互联网", "电商"],
  "preferred_industries": ["金融科技"],
  "salary_range": {{"min": "20K", "max": "35K"}},
  "locations": ["北京", "上海"],
  "required_languages": ["中文", "英语"],
  "required_certifications": ["软件设计师"],
  "custom_conditions": "有团队管理经验者优先"
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
            Dict[str, Any]: 解析后的查询元数据字典
            
        Raises:
            ValueError: 如果响应不是有效的JSON格式
        """
        try:
            # 尝试直接解析JSON
            query_dict = json.loads(response)
            return query_dict
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试从响应中提取JSON部分
            # 这种情况可能发生在LLM返回了额外的解释文本时
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end != -1 and start < end:
                json_str = response[start:end]
                try:
                    query_dict = json.loads(json_str)
                    return query_dict
                except json.JSONDecodeError:
                    pass
            
            # 如果所有尝试都失败，抛出异常
            raise ValueError(f"Failed to parse response as JSON: {response}")