# 智能简历筛选系统开发规划 (To-Do List)

## 阶段一：项目初始化与核心框架搭建 (Week 1-2)

### 1. 项目环境与依赖
- [x] 初始化Python项目环境 (Python 3.10+)
- [x] 创建 `requirements.txt` 或 `pyproject.toml` 文件
- [x] 安装核心依赖项:
  - LLM框架 (例如: Langchain, LlamaIndex)
  - 向量数据库客户端 (例如: chromadb)
  - PDF解析库 (例如: PyPDF2, pdfplumber, 或集成LlamaParse API)
  - Web框架 (例如: FastAPI, Flask)
  - 异步支持库 (例如: asyncio, aiohttp)
  - 配置管理 (例如: pydantic for settings)
  - 缓存库 (例如: diskcache, redis-py)
  - 日志库 (例如: loguru, structlog)

### 2. 项目结构设计
- [x] 设计并创建基础项目目录结构:
  ```
  resume_screening/
  ├── app/                  # 主应用代码
  │   ├── api/              # API路由
  │   ├── core/             # 核心业务逻辑
  │   ├── models/           # 数据模型 (Pydantic/SQL)
  │   ├── utils/            # 工具函数
  │   └── main.py           # 应用入口
  ├── data/                 # 数据文件 (简历样本, 缓存)
  ├── tests/                # 测试代码
  ├── config/               # 配置文件
  ├── notebooks/            # 探索性分析/原型 notebook
  └── README.md
  ```
- [x] 编写 `README.md` 草稿，包含项目简介、安装步骤、快速开始指南。

### 3. 核心模块框架代码
- [x] 定义核心数据模型 (`models/metadata.py` for Resume Metadata, Query Metadata)
- [x] 搭建向量数据库连接与基本索引管理模块 (`core/vector_store.py`)
- [x] 搭建LLM客户端连接模块 (`core/llm_client.py`)
- [x] 搭建文档解析器接口 (`core/document_parser.py`) (先用占位符或基础PDF转文本)
- [x] 搭建缓存管理模块 (`core/cache_manager.py`)

## 阶段二：核心能力开发与集成 (Week 3-6)

### 4. 文档解析与元数据提取
- [x] 实现PDF简历的基础解析功能 (PDF -> Text/Markdown)
- [ ] 集成多模态LLM或LlamaParse API进行高级解析 (可选，视效果而定)
- [x] 开发元数据提取功能:
  - [x] 设计/完善 `Metadata` Pydantic模型
  - [x] 编写Prompt，利用LLM从简历文本中提取元数据
  - [x] 实现元数据提取函数 (`core/extractor.py`)
  - [x] 集成缓存机制到解析和提取流程

### 5. 查询理解模块
- [x] 开发自然语言查询解析功能:
  - [x] 设计查询条件的结构化模型
  - [x] 编写Prompt，利用LLM从HR输入中提取查询条件
  - [x] 实现查询解析函数 (`core/query_parser.py`)

### 6. 向量索引与语义检索
- [x] 实现简历文本的向量化处理 (使用选定的Embedding模型)
- [x] 完善向量数据库的索引创建、更新、删除功能
- [x] 实现基于查询向量的语义检索功能 (`core/retriever.py`)

### 7. 多阶段筛选逻辑
- [x] 实现硬性条件过滤器 (`core/filter.py`)
- [x] 设计并实现多维度评分算法 (`core/scorer.py`)
  - [x] 行业领域匹配
  - [x] 技能匹配
  - [x] 薪资匹配
  - [x] 学历匹配
  - [x] 地理位置匹配
  - [x] 个性标签匹配
- [x] 实现综合评分与排序逻辑 (`core/ranker.py`)

### 8. 候选人分析与结果生成
- [x] 利用LLM生成候选人综合评价 (`core/analyzer.py`)
- [x] 设计候选人匹配结果的数据结构
- [x] 开发结果聚合与格式化输出功能 (`core/result_formatter.py`)

## 阶段三：API开发与系统整合 (Week 7-8)

### 9. Web API开发
- [x] 使用FastAPI/Flask开发RESTful API接口:
  - [x] 上传简历接口
  - [x] 提交筛选查询接口
  - [x] 获取筛选结果接口
- [x] 实现API请求/响应的数据模型
- [x] 将核心模块逻辑整合到API路由中

### 10. 系统集成与测试
- [x] 进行端到端集成测试
- [x] 修复集成过程中发现的问题
- [x] 编写核心模块的单元测试

## 阶段四：优化、部署与文档 (Week 9-10)

### 11. 性能优化与错误处理
- [x] 优化关键路径性能 (如缓存策略、批量处理)
- [x] 添加全面的错误处理和日志记录
- [x] 进行压力测试和性能调优

### 12. 部署准备
- [x] 编写Dockerfile
- [x] 配置环境变量管理
- [x] 准备部署脚本或CI/CD流程

### 13. 文档完善
- [x] 完善 `README.md`，包括详细的安装、配置、运行说明
- [x] 编写API文档
- [x] 编写开发者指南和贡献指南

### 14. 最终测试与验收
- [x] 进行完整的系统测试
- [x] 准备演示材料
- [x] 项目总结与回顾