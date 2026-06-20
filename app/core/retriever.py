from typing import List, Dict, Any, Optional
from app.core.vector_store import VectorStoreManager
from app.core.metadata_utils import deserialize_metadata
from app.models.metadata import ResumeMetadata, QueryMetadata
from loguru import logger


class Retriever:
    """
    检索器，用于实现基于查询的语义检索功能
    """
    
    def __init__(self, vector_store_manager: VectorStoreManager):
        """
        初始化检索器
        
        Args:
            vector_store_manager (VectorStoreManager): 向量存储管理器实例
        """
        self.vector_store_manager = vector_store_manager
        logger.info("Initialized Retriever")

    def add_resume(self, resume_id: str, resume_text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        将简历文本添加到向量数据库中
        
        Args:
            resume_id (str): 简历ID
            resume_text (str): 简历文本内容
            metadata (Dict[str, Any], optional): 简历元数据
        """
        try:
            # 确保集合存在
            collection_name = "resumes"
            try:
                self.vector_store_manager.get_collection(collection_name)
            except Exception:
                # 如果集合不存在，则创建它
                self.vector_store_manager.create_collection(collection_name)
            
            # 添加文档到向量数据库（序列化由 add_documents 内部统一处理）
            self.vector_store_manager.add_documents(
                collection_name=collection_name,
                documents=[resume_text],
                metadatas=[metadata] if metadata else None,
                ids=[resume_id]
            )
            
            logger.info(f"Added resume {resume_id} to vector store")
        except Exception as e:
            logger.error(f"Failed to add resume {resume_id} to vector store: {e}")
            raise

    def retrieve(self, query_metadata: QueryMetadata, n_results: int = 10) -> List[Dict[str, Any]]:
        """
        根据查询元数据检索相关简历
        
        Args:
            query_metadata (QueryMetadata): 查询元数据
            n_results (int): 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 检索到的简历列表，每个元素包含简历ID、文本内容和元数据
        """
        try:
            # 将查询元数据转换为查询文本
            query_text = self._convert_query_to_text(query_metadata)
            
            # 执行语义检索
            collection_name = "resumes"
            results = self.vector_store_manager.query_collection(
                collection_name=collection_name,
                query_texts=[query_text],
                n_results=n_results
            )
            
            # 格式化结果
            formatted_results = self._format_results(results)
            
            logger.info(f"Retrieved {len(formatted_results)} resumes")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to retrieve resumes: {e}")
            raise

    def _convert_query_to_text(self, query_metadata: QueryMetadata) -> str:
        """
        将查询元数据转换为查询文本
        
        Args:
            query_metadata (QueryMetadata): 查询元数据
            
        Returns:
            str: 查询文本
        """
        # 构造查询文本
        query_parts = []
        
        if query_metadata.keywords:
            query_parts.append(f"关键词: {', '.join(query_metadata.keywords)}")
            
        if query_metadata.required_skills:
            query_parts.append(f"所需技能: {', '.join(query_metadata.required_skills)}")
            
        if query_metadata.preferred_skills:
            query_parts.append(f"优先技能: {', '.join(query_metadata.preferred_skills)}")
            
        if query_metadata.min_experience_years:
            query_parts.append(f"最少经验年限: {query_metadata.min_experience_years}年")
            
        if query_metadata.required_education:
            query_parts.append(f"所需学历: {query_metadata.required_education}")
            
        if query_metadata.required_industries:
            query_parts.append(f"所需行业: {', '.join(query_metadata.required_industries)}")
            
        if query_metadata.preferred_industries:
            query_parts.append(f"优先行业: {', '.join(query_metadata.preferred_industries)}")
            
        if query_metadata.locations:
            query_parts.append(f"工作地点: {', '.join(query_metadata.locations)}")
            
        if query_metadata.required_languages:
            query_parts.append(f"语言要求: {', '.join(query_metadata.required_languages)}")
            
        if query_metadata.required_certifications:
            query_parts.append(f"证书要求: {', '.join(query_metadata.required_certifications)}")
            
        if query_metadata.custom_conditions:
            query_parts.append(f"其他要求: {query_metadata.custom_conditions}")
            
        # 如果没有特定的查询条件，使用关键词作为默认查询
        if not query_parts:
            return "简历"
            
        return "; ".join(query_parts)

    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        格式化检索结果
        
        Args:
            results (Dict[str, Any]): 原始检索结果
            
        Returns:
            List[Dict[str, Any]]: 格式化后的检索结果
        """
        formatted_results = []
        
        try:
            # 添加日志输出来调试问题
            logger.info(f"Format results input type: {type(results)}")
            logger.info(f"Format results keys: {results.keys() if isinstance(results, dict) else 'N/A'}")
            
            # 检查是否有检索到结果
            if not isinstance(results, dict) or not results.get("ids") or not results["ids"]:
                logger.warning("No valid results to format")
                return formatted_results
                
            # 处理结果格式，兼容一维和二维数组
            ids = results["ids"]
            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])
            distances = results.get("distances", [])
            
            # 添加日志输出来查看结果格式
            logger.info(f"Ids type: {type(ids)}")
            logger.info(f"Ids content: {ids}")
            logger.info(f"Documents type: {type(documents)}")
            logger.info(f"Documents content: {documents}")
            logger.info(f"Metadatas type: {type(metadatas)}")
            logger.info(f"Metadatas content: {metadatas}")
            
            # 确定结果是一维还是二维数组
            is_2d = isinstance(ids[0], list) if ids and len(ids) > 0 else False
            
            # 遍历所有结果
            for i in range(len(ids[0]) if is_2d else len(ids)):
                # 根据数组维度获取对应的值
                id_val = ids[0][i] if is_2d else ids[i]
                doc_val = documents[0][i] if is_2d and documents and len(documents) > 0 and documents[0] else (documents[i] if documents and len(documents) > i else "")
                meta_val = metadatas[0][i] if is_2d and metadatas and len(metadatas) > 0 and metadatas[0] else (metadatas[i] if metadatas and len(metadatas) > i else {})
                dist_val = distances[0][i] if is_2d and distances and len(distances) > 0 and distances[0] else (distances[i] if distances and len(distances) > i else None)
                
                # 确保 meta_val 是字典
                if not isinstance(meta_val, dict):
                    logger.warning(f"Metadata is not a dict, converting to dict: {meta_val}")
                    meta_val = {} if meta_val is None else {str(meta_val): meta_val}

                # 反序列化元数据，将 JSON 字符串字段还原为 list/dict，供下游使用
                meta_val = deserialize_metadata(meta_val)

                result = {
                    "id": id_val,
                    "text": doc_val,
                    "metadata": meta_val,
                    "distance": dist_val
                }
                formatted_results.append(result)
                
        except Exception as e:
            logger.error(f"Failed to format results: {e}")
            
        logger.info(f"Formatted {len(formatted_results)} results")
        return formatted_results