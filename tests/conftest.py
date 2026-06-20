"""
pytest 公共配置

在导入应用模块之前注入测试用的环境变量，避免 `app.api.routes` 在模块加载时
实例化 LLMClient / VectorStoreManager 因缺少 OPENAI_API_KEY 而报错。
这些是占位值，构造客户端时不会发起网络请求。
"""
import os
import hashlib

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_BASE_URL", "https://test.url/v1")
# 单元测试固定使用 ChromaDB 后端，避免误连真实 Milvus
os.environ["VECTOR_DB"] = "chroma"

import pytest


class FakeEmbeddings:
    """确定性假嵌入模型，避免测试发起真实网络请求。

    根据文本内容生成稳定的 8 维向量，相同文本得到相同向量。
    """

    DIM = 8

    def __init__(self, *args, **kwargs):
        # 兼容 OpenAIEmbeddings(model=..., openai_api_key=..., openai_api_base=...)
        pass

    def _embed(self, text: str):
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # 取前 DIM 个字节归一化到 [0, 1)
        return [digest[i] / 255.0 for i in range(self.DIM)]

    def embed_documents(self, texts):
        return [self._embed(t) for t in texts]

    def embed_query(self, text):
        return self._embed(text)


@pytest.fixture(autouse=True)
def fake_embeddings(monkeypatch):
    """全局替换 VectorStoreManager 使用的 OpenAIEmbeddings，避免真实网络调用。"""
    monkeypatch.setattr(
        "app.core.vector_store.OpenAIEmbeddings",
        FakeEmbeddings,
        raising=False,
    )
    # Milvus 后端（若被导入）同样替换为假嵌入
    monkeypatch.setattr(
        "app.core.milvus_store.OpenAIEmbeddings",
        FakeEmbeddings,
        raising=False,
    )
    yield
