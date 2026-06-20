 
# 🧠 智能简历筛选系统 · Resume Screener

**基于 LLM + 向量检索的智能简历筛选系统**

上传简历 → 用一句话描述岗位需求 → 自动解析、检索、过滤、评分、排序并生成候选人分析报告

[快速开始](#-快速开始-5-分钟跑通) · [Web 界面](#-使用-web-界面) · [API 参考](#-api-参考) · [向量库切换](#-切换向量数据库) · [测试](#-测试) · [常见问题](#-常见问题-faq)
 

---

## 📋 目录

- [这是什么](#-这是什么)
- [核心特性](#-核心特性)
- [快速开始（5 分钟跑通）](#-快速开始-5-分钟跑通)
- [系统架构](#️-系统架构)
- [目录结构](#-目录结构)
- [详细安装](#-详细安装)
- [配置说明（环境变量）](#️-配置说明环境变量)
- [运行服务](#-运行服务)
- [使用 Web 界面](#-使用-web-界面)
- [API 参考](#-api-参考)
- [数据模型](#-数据模型)
- [评分与排序机制](#-评分与排序机制)
- [硬性条件过滤](#-硬性条件过滤)
- [切换向量数据库](#-切换向量数据库)
- [测试](#-测试)
- [常见问题 FAQ](#-常见问题-faq)
- [安全须知](#-安全须知)
- [技术栈](#-技术栈)

---

## 💡 这是什么

一个面向招聘场景的智能简历筛选后端 + 内置 Web 界面。HR 或开发者只需：

1. 上传一批简历（`.txt` / `.md` / `.pdf`）；
2. 用自然语言输入岗位需求，例如「招一名 3 年以上 Python 后端，熟悉 FastAPI，本科以上，工作地点北京」；
3. 系统自动完成 **解析 → 语义检索 → 硬性过滤 → 多维评分 → 排序 → LLM 分析**，返回排好序的候选人列表与逐人分析报告。

系统兼容任何 **OpenAI 接口规范** 的大模型服务（默认配置为智谱 BigModel `glm-4.7-flashx` + `embedding-3`），向量库默认本地 **ChromaDB**，可一键切换到 **Milvus / Zilliz Cloud**。

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🗣️ **自然语言需求** | 一句话岗位描述，LLM 自动解析为结构化查询条件 |
| 📄 **多格式简历解析** | 支持 `.txt` / `.md` / `.pdf`，LLM 抽取结构化元数据 |
| 🔍 **语义检索 + 硬性过滤** | 向量召回 + 技能/经验/地点/学历过滤，对 LLM 抽取不完美做模糊匹配与全文兜底 |
| 📊 **多维加权评分** | 技能、行业、薪资、学历、地点、标签 6 维度加权综合打分 |
| 📝 **候选人分析报告** | LLM 为每位候选人生成匹配度分析 |
| 🖥️ **开箱即用 Web UI** | FastAPI 自带静态前端，无需单独部署前端工程 |
| 🔌 **可插拔向量库** | 默认 ChromaDB（本地零依赖），可选 Milvus / Zilliz Cloud |
| 🧩 **接口兼容设计** | 两种向量库实现同一接口，切换后端业务代码零改动 |

---

## 🚀 快速开始（5 分钟跑通）

```bash
# 1. 进入项目目录
cd resume_screening

# 2. 安装依赖（建议先创建虚拟环境）
pip install -r requirements.txt

# 3. 配置密钥：复制模板并填入你的 API Key
cp .env.example .env
#   然后编辑 .env，至少填写 LLM_API_KEY / EMBEDDING_API_KEY

# 4. 启动服务（含内置 Web 界面）
uvicorn app.main:app --reload --port 8000
```

打开浏览器访问 **http://localhost:8000/** 即可使用界面；接口文档在 **http://localhost:8000/docs**。

> 💡 默认使用本地 ChromaDB，无需任何额外数据库服务即可运行。

---

## 🏗️ 系统架构

```
                         ┌──────────────────────────────────────────────┐
   浏览器  /ui/  ───────▶ │              FastAPI  (app/main.py)            │
   REST API /api/v1 ────▶ │   CORS 中间件 + 静态前端 + APIRouter            │
                         └──────────────────────┬───────────────────────┘
                                                │
        ┌───────────────────────────────────────┴───────────────────────────────────┐
        │                                                                             │
   📥 上传简历流程                                                              🔎 查询筛选流程
        │                                                                             │
   ┌────▼─────┐  ┌──────────┐  ┌───────────┐  ┌──────────────┐      ┌───────────┐  ┌──────────┐
   │ 解析文本  │─▶│ 抽取元数据 │─▶│ 生成向量   │─▶│  向量库入库    │      │ 解析查询   │─▶│ 语义检索  │
   │ parser   │  │ extractor│  │ embedding │  │ vector store │      │ query LLM │  │ retriever│
   └──────────┘  └────(LLM)──┘  └───────────┘  └──────────────┘      └────(LLM)──┘  └────┬─────┘
                                                                                         │
                                          ┌──────────────────────────────────────────────┘
                                          ▼
                              ┌─────────┐  ┌────────┐  ┌────────┐  ┌──────────┐  ┌──────────┐
                              │ 硬性过滤 │─▶│ 多维评分 │─▶│ 综合排序 │─▶│ 候选人分析 │─▶│ 结果格式化 │
                              │ filter  │  │ scorer │  │ ranker │  │ analyzer │  │formatter │
                              └─────────┘  └────────┘  └────────┘  └───(LLM)───┘  └──────────┘
```

**核心模块（`app/core/`）：**

| 模块 | 职责 |
|------|------|
| `document_parser.py` | 解析 txt / pdf 文本 |
| `extractor.py` | 调用 LLM 抽取简历结构化元数据 |
| `query_parser.py` | 调用 LLM 把自然语言需求解析为结构化查询 |
| `vector_store.py` | ChromaDB 向量库管理器 |
| `milvus_store.py` | Milvus / Zilliz 向量库管理器（与 Chroma 同接口） |
| `vector_store_factory.py` | 按 `VECTOR_DB` 配置选择后端 |
| `retriever.py` | 语义检索，统一格式化结果 |
| `filter.py` | 硬性条件过滤（模糊匹配 + 全文兜底） |
| `scorer.py` | 6 维度加权评分 |
| `ranker.py` | 综合排序与 Top-N |
| `analyzer.py` | LLM 生成候选人分析报告 |
| `result_formatter.py` | 整理为 API 响应结构 |
| `metadata_utils.py` | 元数据序列化/反序列化与类型兜底 |
| `llm_client.py` | LLM 调用封装 |
| `cache_manager.py` | 结果缓存 |

---

## 📁 目录结构

```
resume_screening/
├── app/
│   ├── main.py                  # 应用入口：CORS + 静态页面挂载 + 路由
│   ├── api/
│   │   ├── routes.py            # 全部 REST 接口
│   │   └── models.py            # 请求/响应 Pydantic 模型
│   ├── core/                    # 核心业务模块（见上表）
│   └── models/
│       └── metadata.py          # ResumeMetadata / QueryMetadata
├── config/
│   └── config.py                # 集中式配置（读取环境变量）
├── static/                      # 内置 Web 前端
│   ├── index.html
│   ├── app.js
│   └── style.css
├── tests/                       # 单元测试（pytest，假嵌入、不联网）
├── integration_test.py          # 全链路集成测试（真实 key）
├── milvus_live_test.py          # Milvus / Zilliz 在线连通测试
├── requirements.txt
├── .env.example                 # 配置模板（复制为 .env）
└── README.md
```

---

## 📦 详细安装

### 前置要求

- **Python 3.10+**
- 一个兼容 OpenAI 接口的 LLM 服务密钥（如智谱 BigModel、OpenAI 等）
- （可选）Milvus / Zilliz Cloud 实例，仅在使用 Milvus 后端时需要

### 安装步骤

```bash
cd resume_screening

# 建议使用虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

> `pymilvus` 已包含在依赖中，但仅在 `VECTOR_DB=milvus` 时才会被导入；默认 ChromaDB 路径不依赖它。

### 获取智谱 API Key（示例）

1. 访问 [智谱 BigModel 开放平台](https://open.bigmodel.cn/)，注册并登录；
2. 在「API Keys」中创建密钥；
3. 对话模型与向量模型可使用同一密钥，Base URL 为 `https://open.bigmodel.cn/api/paas/v4/`。

---

## ⚙️ 配置说明（环境变量）

复制模板并按需修改：

```bash
cp .env.example .env
```

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_API_KEY` | 对话模型 API Key | — |
| `LLM_BASE_URL` | 对话模型 Base URL（OpenAI 兼容） | — |
| `LLM_MODEL` | 对话模型名 | `gpt-4o` |
| `LLM_TEMPERATURE` | 采样温度 | `0.0` |
| `EMBEDDING_API_KEY` | 向量模型 Key（缺省回退 `LLM_*` / `OPENAI_*`） | — |
| `EMBEDDING_BASE_URL` | 向量模型 Base URL | — |
| `EMBEDDING_MODEL` | 向量模型名 | `text-embedding-3-small` |
| `EMBEDDING_DIMENSIONS` | 向量维度（智谱 embedding-3 支持 256~2048） | `2048` |
| `VECTOR_DB` | 向量库后端：`chroma` / `milvus` | `chroma` |
| `CHROMA_PERSIST_DIR` | ChromaDB 持久化目录 | `./chroma_db` |
| `MILVUS_URI` | Milvus/Zilliz 完整连接 URI（优先级最高） | — |
| `MILVUS_HOST` / `MILVUS_PORT` | 未提供 URI 时自动拼接 | — |
| `MILVUS_TOKEN` | Milvus/Zilliz 鉴权 Token | — |
| `MILVUS_COLLECTION` | 简历集合名 | `resume_screening` |
| `INDEX` / `MILVUS_INDEX` | 向量索引类型（`AUTOINDEX`/`IVF_FLAT`/`HNSW`…） | `AUTOINDEX` |
| `SERVER_ALLOWED_ORIGINS` | 允许的前端来源（逗号分隔，留空=允许全部） | `*` |
| `CACHE_DIR` | 缓存目录 | `./cache` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

**最小可用配置示例（`.env`）：**

```env
LLM_API_KEY=你的智谱key
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
LLM_MODEL=glm-4.7-flashx

EMBEDDING_API_KEY=你的智谱key
EMBEDDING_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
EMBEDDING_MODEL=embedding-3
EMBEDDING_DIMENSIONS=2048

VECTOR_DB=chroma
```

> **兼容性**：如果未设置 `LLM_*` / `EMBEDDING_*`，系统会回退到统一的 `OPENAI_API_KEY` / `OPENAI_BASE_URL`。

> ⚠️ **向量维度一致性**：`EMBEDDING_DIMENSIONS` 必须与向量库已存数据维度一致。**切换维度后必须重建集合**（删除 `CHROMA_PERSIST_DIR` 目录，或删除 Milvus 集合），否则检索会报维度不匹配。

---

## ▶️ 运行服务

### 开发模式（热重载）

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 生产模式（多进程）

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

启动后：

- 🖥️ Web 界面：`http://localhost:8000/`（根路径自动重定向到 `/ui/`）
- 📚 Swagger 文档：`http://localhost:8000/docs`
- 📖 ReDoc 文档：`http://localhost:8000/redoc`

---

## 🖥️ 使用 Web 界面

界面分为左右两栏，操作流程：

1. **左栏 · 上传简历**：点击选择一个或多个 `.txt` / `.pdf` 文件 → 点击「上传」。上传日志会实时显示成功/失败，并自动刷新下方「已上传简历」列表。
2. **右栏 · 输入岗位需求**：在文本框输入自然语言描述，例如：
   > 招聘一名有 3 年以上经验的 Python 后端工程师，熟悉 FastAPI 和分布式系统，本科及以上学历，工作地点北京。
3. **开始筛选**：点击「开始筛选」，系统执行完整管线（解析 → 检索 → 过滤 → 评分 → 排序 → 分析）。
4. **查看结果**：右栏渲染排好序的候选人卡片，含排名、综合评分、联系方式、期望地点/薪资、技能标签与 LLM 分析报告。

> 顶部状态徽标会每 30 秒自动检测后端健康状态。

---

## 🔌 API 参考

所有接口前缀为 `/api/v1`。

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET`  | `/health` | 健康检查 |
| `GET`  | `/resumes` | 列出已上传简历（摘要） |
| `POST` | `/resumes` | 上传简历（`multipart/form-data`，字段名 `file`） |
| `GET`  | `/resumes/{resume_id}` | 获取单份简历详情 |
| `POST` | `/queries` | 提交岗位需求查询 |
| `GET`  | `/results/{query_id}` | 执行筛选并返回排序结果 |

### 1) 上传简历

```bash
curl -F "file=@resume.txt" http://localhost:8000/api/v1/resumes
```

响应：

```json
{ "resume_id": "42834ae2-...", "message": "简历 'resume.txt' 上传成功" }
```

### 2) 列出简历

```bash
curl http://localhost:8000/api/v1/resumes
```

```json
{
  "total": 2,
  "resumes": [
    { "resume_id": "42834ae2-...", "filename": "zhangsan.txt", "name": "张三", "created_at": "2026-06-20T20:00:27" }
  ]
}
```

### 3) 提交查询

```bash
curl -X POST http://localhost:8000/api/v1/queries \
  -H "Content-Type: application/json" \
  -d '{"query_text":"3年以上Python后端、熟悉FastAPI、北京"}'
```

```json
{ "query_id": "7b602c7b-...", "message": "查询提交成功" }
```

### 4) 获取筛选结果

```bash
curl http://localhost:8000/api/v1/results/7b602c7b-...
```

```json
{
  "query_id": "7b602c7b-...",
  "query_text": "3年以上Python后端、熟悉FastAPI、北京",
  "total_candidates": 1,
  "candidates": [
    {
      "id": "42834ae2-...",
      "rank": 1,
      "name": "张三",
      "email": "zhangsan@example.com",
      "phone": "13800000000",
      "overall_score": 0.84,
      "skills": ["Python", "Django", "FastAPI", "PostgreSQL"],
      "preferred_locations": ["北京"],
      "expected_salary": null,
      "work_experience": [ { "company": "...", "title": "...", "start_date": "2019-01", "end_date": "2024-01" } ],
      "education": [ { "major": "计算机科学", "degree": "本科" } ],
      "skill_scores": [ { "name": "Python", "score": 0.8 } ],
      "analysis": "该候选人拥有 5 年 Python 后端经验……"
    }
  ],
  "created_at": "2026-06-20T20:03:11"
}
```

> 典型用法：先 `POST /queries` 拿到 `query_id`，再 `GET /results/{query_id}` 触发完整筛选流程。

---

## 🧬 数据模型

### ResumeMetadata（简历结构化元数据，由 LLM 抽取）

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | str | 姓名 |
| `email` / `phone` / `address` | str? | 联系方式 |
| `work_experience` | list[dict] | 工作经历（company / title / start_date / end_date / description） |
| `education` | list[dict] | 教育背景（institution / major / degree / start_date / end_date） |
| `skills` | list[str] | 技能 |
| `projects` | list[dict] | 项目经历 |
| `languages` | list[str] | 语言能力 |
| `certifications` | list[str] | 证书 |
| `expected_salary` | str? | 期望薪资 |
| `preferred_locations` | list[str] | 期望工作地点 |
| `summary` | str? | 个人简介 |

### QueryMetadata（查询结构化条件，由 LLM 解析）

| 字段 | 类型 | 说明 |
|------|------|------|
| `keywords` | list[str] | 关键词 |
| `required_skills` / `preferred_skills` | list[str] | 必需 / 优先技能 |
| `min_experience_years` | int? | 最少经验年限 |
| `required_education` | str? | 学历要求 |
| `required_industries` / `preferred_industries` | list[str] | 必需 / 优先行业 |
| `salary_range` | dict? | 薪资范围 |
| `locations` | list[str] | 工作地点 |
| `required_languages` | list[str] | 语言要求 |
| `required_certifications` | list[str] | 证书要求 |
| `custom_conditions` | str? | 其他自定义条件 |

---

## 📊 评分与排序机制

候选人通过硬性过滤后，`scorer.py` 计算 6 个维度得分（均归一化到 `0~1`），再加权求综合分：

| 维度 | 权重 | 计算逻辑（简述） |
|------|------|------------------|
| 技能 `skill_score` | **0.30** | 必需技能命中率 ×0.8 + 优先技能命中率 ×0.2 |
| 行业 `industry_score` | **0.20** | 工作经历与所需行业匹配度 |
| 地点 `location_score` | **0.20** | 期望地点与岗位地点匹配度 |
| 薪资 `salary_score` | **0.10** | 期望薪资与薪资范围匹配度 |
| 学历 `education_score` | **0.10** | 学历层级是否达标 |
| 标签 `tag_score` | **0.10** | 关键词/自定义条件匹配度 |

```
overall_score = skill*0.3 + industry*0.2 + location*0.2 + salary*0.1 + education*0.1 + tag*0.1
```

`ranker.py` 按 `overall_score` 降序排序并赋予 `rank`。当某维度无对应查询条件时，该维度记满分（不惩罚候选人）。

---

## 🛡️ 硬性条件过滤

`filter.py` 在评分前先按硬性条件初筛，并针对「LLM 抽取不完美」做了健壮性增强：

- **双向模糊匹配**：大小写不敏感的双向子串匹配。如查询「北京」可命中「北京市」，查询「Django」可命中「Django框架」。
- **全文兜底**：结构化字段（如 `skills`）未命中时，回退到简历正文 + 摘要做子串匹配，避免漏掉只在正文中提及技能的合格候选人。
- **缺失即宽松**：候选人该字段为空时不直接淘汰，交由后续评分区分。

过滤维度：经验年限、学历、技能、工作地点、语言、证书。

---

## 🗄️ 切换向量数据库

### 默认：ChromaDB（本地，零依赖）

```env
VECTOR_DB=chroma
CHROMA_PERSIST_DIR=./chroma_db
```

无需额外服务，数据持久化到本地目录，适合开发与中小规模使用。

### 可选：Milvus / Zilliz Cloud

```env
VECTOR_DB=milvus
MILVUS_HOST=https://your-instance.serverless.cloud.zilliz.com.cn
MILVUS_PORT=80
MILVUS_TOKEN=你的token
MILVUS_COLLECTION=resume_screening
INDEX=AUTOINDEX
```

**实现要点：**

- `MilvusVectorStoreManager`（`app/core/milvus_store.py`）实现了与 ChromaDB 版**完全一致的接口**，查询结果统一返回 Chroma 风格的二维结构，因此上层检索/过滤/评分逻辑**零改动**。
- 集合 schema：`id`(VARCHAR 主键) + `vector`(FLOAT_VECTOR) + `document`(VARCHAR) + `metadata`(JSON)。`metadata` 为原生 JSON 字段，可直接存储嵌套 list/dict，无需序列化。
- 使用**独立的简历集合**，不会污染同一实例上的其他业务集合。
- 也可直接提供完整 `MILVUS_URI` 代替 `HOST`+`PORT`。

> ⚠️ **Zilliz Serverless 免费实例通常有 5 个集合上限**。若已达上限将无法创建新集合，请在控制台释放槽位或升级实例。

---

## ✅ 测试

本项目提供三层测试，覆盖从单元到真实在线的完整链路：

```bash
cd resume_screening

# 1) 单元测试：假嵌入、固定 chroma 后端、不联网（最快，CI 友好）
python -m pytest tests/ -q
#   预期：82 passed

# 2) 全链路集成测试：使用 .env 真实 key，覆盖 上传→查询→结果 + 内置 UI
python integration_test.py
#   预期：ALL INTEGRATION CHECKS PASSED

# 3) Milvus / Zilliz 在线连通测试：临时集合，测试后自动清理
python milvus_live_test.py
#   预期：ALL MILVUS LIVE CHECKS PASSED
```

| 测试 | 是否联网 | 用途 |
|------|----------|------|
| `pytest tests/` | 否（假嵌入） | 模块逻辑回归，CI 必跑 |
| `integration_test.py` | 是（LLM+Embedding） | 真实业务流程 + UI 验证 |
| `milvus_live_test.py` | 是（Milvus） | 向量库连通与读写验证 |

**测试设计说明：**

- 单元测试通过 `tests/conftest.py` 注入确定性假嵌入并固定 `VECTOR_DB=chroma`，不发起任何真实网络请求。
- `milvus_live_test.py` 使用带时间戳的临时集合 `resume_screening_tmp_<ts>`，完成 创建→插入→检索→删除；若实例已达集合上限，会在验证连通性后安全跳过写入测试，**不删除任何已有业务集合**。

---

## ❓ 常见问题 FAQ

**Q：启动报 `EMBEDDING_API_KEY ... is not set`？**
A：`.env` 未配置或未被加载。确认在 `resume_screening/` 目录下存在 `.env` 并填写了 `EMBEDDING_API_KEY`（或 `LLM_API_KEY` / `OPENAI_API_KEY` 作为回退）。

**Q：检索报维度不匹配 / dimension mismatch？**
A：`EMBEDDING_DIMENSIONS` 与已存数据维度不一致。删除 `CHROMA_PERSIST_DIR` 目录（或删除 Milvus 集合）后重新上传简历。

**Q：筛选结果为空 / 候选人为 0？**
A：通常是没有上传相关简历，或查询条件过严。系统已对 LLM 抽取做了模糊匹配与全文兜底，但仍需简历库中存在相关数据。

**Q：上传 PDF 解析为空？**
A：扫描件/图片型 PDF 无法直接抽取文本，请使用文本型 PDF 或先 OCR。

**Q：切到 Milvus 后报 `exceeded the limit number of collections`？**
A：Zilliz Serverless 免费实例集合数已达上限（通常 5 个），请释放一个集合或升级实例。

**Q：前端跨域报错？**
A：将前端来源加入 `SERVER_ALLOWED_ORIGINS`（逗号分隔），生产环境不要使用通配 `*`。

---

## 🔐 安全须知

- `.env` 已加入 `.gitignore`，**切勿提交真实密钥**；仅提交 `.env.example` 占位模板。
- 生产环境通过 `SERVER_ALLOWED_ORIGINS` 限制跨域来源，避免通配 `*`。
- 简历/查询数据当前存储在**内存字典**中（进程重启即丢失），生产环境应替换为持久化数据库。
- 向量库与 LLM 服务的 Key/Token 请通过环境变量或密钥管理服务注入，勿硬编码。

---

## 🧰 技术栈

| 类别 | 选型 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| LLM / Embedding | OpenAI 兼容接口（默认智谱 BigModel `glm-4.7-flashx` + `embedding-3`） |
| LLM 编排 | LangChain |
| 向量数据库 | ChromaDB（默认） / Milvus · Zilliz Cloud（可选） |
| 文档解析 | pypdf |
| 数据校验 | Pydantic |
| 日志 | loguru |
| 测试 | pytest |
| 前端 | 原生 HTML + CSS + JavaScript（FastAPI StaticFiles 内置） |

---

<div align="center">

如有问题或建议，欢迎提交 Issue 🙌
特别感谢 https://linux.do 社区佬友
</div>
