#!/usr/bin/env python3
"""
智能简历筛选系统演示脚本
"""
import os
import tempfile
from app.core.document_parser import DocumentParser
from app.core.extractor import MetadataExtractor
from app.core.llm_client import LLMClient
from app.core.query_parser import QueryParser
from app.core.vector_store import VectorStoreManager
from app.core.retriever import Retriever
from app.core.filter import HardFilter
from app.core.scorer import Scorer
from app.core.ranker import Ranker
from app.core.analyzer import CandidateAnalyzer
from app.core.result_formatter import ResultFormatter
from app.core.cache_manager import CacheManager
from app.models.metadata import ResumeMetadata, QueryMetadata


def main():
    """主演示函数"""
    print("=== 智能简历筛选系统演示 ===\n")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    cache_dir = tempfile.mkdtemp()
    
    try:
        # 初始化所有核心组件
        llm_client = LLMClient()
        cache_manager = CacheManager(cache_directory=cache_dir)
        document_parser = DocumentParser(cache_manager=cache_manager)
        metadata_extractor = MetadataExtractor(llm_client, cache_manager=cache_manager)
        query_parser = QueryParser(llm_client)
        vector_store_manager = VectorStoreManager(persist_directory=temp_dir)
        retriever = Retriever(vector_store_manager)
        hard_filter = HardFilter()
        scorer = Scorer()
        ranker = Ranker()
        candidate_analyzer = CandidateAnalyzer(llm_client)
        result_formatter = ResultFormatter()
        
        # 创建示例简历数据
        sample_resumes = [
            {
                "id": "resume_001",
                "text": "张三的简历，拥有5年Python开发经验，熟悉Django框架，曾在互联网公司工作，有丰富的后端开发经验。",
                "metadata": {
                    "name": "张三",
                    "email": "zhangsan@example.com",
                    "phone": "13800138000",
                    "skills": ["Python", "Django", "MySQL", "Redis"],
                    "work_experience": [
                        {
                            "company": "互联网公司",
                            "title": "高级软件工程师",
                            "start_date": "2019-01",
                            "end_date": "2023-12",
                            "description": "负责后端服务开发和架构设计"
                        }
                    ],
                    "education": [
                        {
                            "institution": "清华大学",
                            "major": "计算机科学与技术",
                            "degree": "本科",
                            "start_date": "2015-09",
                            "end_date": "2019-06"
                        }
                    ],
                    "expected_salary": "25K-35K",
                    "preferred_locations": ["北京", "上海"]
                }
            },
            {
                "id": "resume_002",
                "text": "李四的简历，拥有3年Java开发经验，熟悉Spring框架，曾在金融公司工作，专注于企业级应用开发。",
                "metadata": {
                    "name": "李四",
                    "email": "lisi@example.com",
                    "phone": "13900139000",
                    "skills": ["Java", "Spring", "Oracle", "MQ"],
                    "work_experience": [
                        {
                            "company": "金融公司",
                            "title": "软件工程师",
                            "start_date": "2021-01",
                            "end_date": "2023-12",
                            "description": "负责金融系统开发和维护"
                        }
                    ],
                    "education": [
                        {
                            "institution": "北京大学",
                            "major": "软件工程",
                            "degree": "硕士",
                            "start_date": "2018-09",
                            "end_date": "2021-06"
                        }
                    ],
                    "expected_salary": "20K-30K",
                    "preferred_locations": ["上海", "深圳"]
                }
            }
        ]
        
        # 将简历添加到向量数据库
        print("1. 添加简历到向量数据库...")
        for resume in sample_resumes:
            retriever.add_resume(
                resume["id"], 
                resume["text"], 
                resume["metadata"]
            )
        print("   完成!\n")
        
        # 创建示例查询
        query_text = "寻找3年以上经验的Python后端工程师，熟悉Django框架，有互联网公司工作经验，期望薪资20K以上"
        print(f"2. 解析查询: {query_text}")
        query_metadata = query_parser.parse_query(query_text)
        print("   完成!\n")
        
        # 检索相关简历
        print("3. 检索相关简历...")
        retrieved_resumes = retriever.retrieve(query_metadata)
        print(f"   检索到 {len(retrieved_resumes)} 份简历\n")
        
        # 硬性条件过滤
        print("4. 硬性条件过滤...")
        filtered_resumes = hard_filter.filter_resumes(retrieved_resumes, query_metadata)
        print(f"   过滤后剩余 {len(filtered_resumes)} 份简历\n")
        
        # 多维度评分
        print("5. 多维度评分...")
        scored_resumes = scorer.score_resumes(filtered_resumes, query_metadata)
        print("   评分完成!\n")
        
        # 综合评分与排序
        print("6. 综合评分与排序...")
        ranked_resumes = ranker.rank_resumes(scored_resumes, query_metadata)
        print("   排序完成!\n")
        
        # 候选人分析
        print("7. 候选人分析...")
        analyzed_candidates = candidate_analyzer.analyze_candidates(ranked_resumes, query_metadata)
        print("   分析完成!\n")
        
        # 结果格式化
        print("8. 格式化结果...")
        formatted_results = result_formatter.format_results(analyzed_candidates, query_metadata)
        print("   格式化完成!\n")
        
        # 输出结果
        print("=== 筛选结果 ===")
        print(f"查询: {query_text}")
        print(f"总候选人数量: {formatted_results['total_candidates']}")
        print("\n候选人列表:")
        for candidate in formatted_results['candidates']:
            print(f"  排名: {candidate['rank']}")
            print(f"  姓名: {candidate['name']}")
            print(f"  综合得分: {candidate['scores']['overall_score']:.2f}")
            print(f"  技能: {', '.join(candidate['basic_info']['skills'])}")
            print(f"  期望薪资: {candidate['basic_info']['expected_salary']}")
            print(f"  期望工作地点: {', '.join(candidate['basic_info']['preferred_locations'])}")
            print(f"  综合评价: {candidate['analysis'][:100]}...")
            print()
        
        print("=== 演示完成 ===")
        
    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        shutil.rmtree(cache_dir, ignore_errors=True)


if __name__ == "__main__":
    main()