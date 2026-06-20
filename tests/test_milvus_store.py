"""
MilvusVectorStoreManager 单元测试

通过向 sys.modules 注入假的 `pymilvus` 模块来模拟客户端行为，
因此无需安装真实 pymilvus、也不会发起任何网络连接。
"""
import sys
import types

import pytest


# ---------------------------------------------------------------- #
# 构造假的 pymilvus 模块
# ---------------------------------------------------------------- #
class _FakeDataType:
    VARCHAR = "VARCHAR"
    FLOAT_VECTOR = "FLOAT_VECTOR"
    JSON = "JSON"


class _FakeSchema:
    def __init__(self):
        self.fields = []

    def add_field(self, name, dtype, **kwargs):
        self.fields.append((name, dtype, kwargs))


class _FakeIndexParams:
    def __init__(self):
        self.indexes = []

    def add_index(self, **kwargs):
        self.indexes.append(kwargs)


class _FakeMilvusClient:
    """记录写入数据，并对 search 返回确定性命中。"""

    def __init__(self, uri=None, token=None, **kwargs):
        self.uri = uri
        self.token = token
        self._collections = {}

    def has_collection(self, name):
        return name in self._collections

    def create_schema(self, **kwargs):
        return _FakeSchema()

    def prepare_index_params(self):
        return _FakeIndexParams()

    def create_collection(self, collection_name, schema=None, index_params=None, **kwargs):
        self._collections[collection_name] = []

    def drop_collection(self, name):
        self._collections.pop(name, None)

    def list_collections(self):
        return list(self._collections.keys())

    def upsert(self, collection_name, data):
        store = self._collections.setdefault(collection_name, [])
        by_id = {row["id"]: row for row in store}
        for row in data:
            by_id[row["id"]] = row
        self._collections[collection_name] = list(by_id.values())

    def search(self, collection_name, data, limit=5, output_fields=None, **kwargs):
        rows = self._collections.get(collection_name, [])
        results = []
        for _q in data:
            hits = []
            for row in rows[:limit]:
                hits.append({
                    "id": row["id"],
                    "distance": 0.9,
                    "entity": {
                        "document": row.get("document", ""),
                        "metadata": row.get("metadata", {}),
                    },
                })
            results.append(hits)
        return results


@pytest.fixture
def milvus_store_module(monkeypatch):
    """注入假 pymilvus 并返回（重新加载的）milvus_store 模块。"""
    fake_pymilvus = types.ModuleType("pymilvus")
    fake_pymilvus.MilvusClient = _FakeMilvusClient
    fake_pymilvus.DataType = _FakeDataType
    monkeypatch.setitem(sys.modules, "pymilvus", fake_pymilvus)

    import importlib
    import app.core.milvus_store as milvus_store
    importlib.reload(milvus_store)

    # 配置必要的连接信息 + 假嵌入
    from app.core import milvus_store as ms
    from config.config import settings
    monkeypatch.setattr(settings, "MILVUS_URI", "http://fake:19530", raising=False)
    monkeypatch.setattr(settings, "MILVUS_TOKEN", "", raising=False)
    monkeypatch.setattr(settings, "EMBEDDING_DIMENSIONS", 8, raising=False)

    # 用确定性假嵌入替换
    from tests.conftest import FakeEmbeddings
    monkeypatch.setattr(ms, "OpenAIEmbeddings", FakeEmbeddings, raising=False)

    yield ms

    importlib.reload(milvus_store)


def _make_manager(ms):
    return ms.MilvusVectorStoreManager()


def test_create_and_list_collection(milvus_store_module):
    mgr = _make_manager(milvus_store_module)
    mgr.create_collection("resume_screening")
    assert "resume_screening" in mgr.list_collections()


def test_add_and_query_documents(milvus_store_module):
    mgr = _make_manager(milvus_store_module)
    mgr.create_collection("resumes")
    mgr.add_documents(
        collection_name="resumes",
        documents=["张三 Python 后端工程师", "李四 前端工程师"],
        metadatas=[{"name": "张三", "skills": ["Python"]}, {"name": "李四", "skills": ["JS"]}],
        ids=["r1", "r2"],
    )
    res = mgr.query_collection("resumes", ["Python 后端"], n_results=2)

    # Chroma 风格二维结构
    assert set(res.keys()) == {"ids", "documents", "metadatas", "distances"}
    assert isinstance(res["ids"], list) and isinstance(res["ids"][0], list)
    assert "r1" in res["ids"][0]
    # 元数据应被反序列化回 list
    idx = res["ids"][0].index("r1")
    assert res["metadatas"][0][idx]["skills"] == ["Python"]
    # 距离为 1 - 相似度
    assert res["distances"][0][idx] == pytest.approx(0.1)


def test_upsert_overwrites_same_id(milvus_store_module):
    mgr = _make_manager(milvus_store_module)
    mgr.create_collection("resumes")
    mgr.add_documents("resumes", ["v1"], [{"name": "A"}], ["same"])
    mgr.add_documents("resumes", ["v2"], [{"name": "B"}], ["same"])
    res = mgr.query_collection("resumes", ["x"], n_results=5)
    assert res["ids"][0].count("same") == 1


def test_delete_collection(milvus_store_module):
    mgr = _make_manager(milvus_store_module)
    mgr.create_collection("tmp")
    assert "tmp" in mgr.list_collections()
    mgr.delete_collection("tmp")
    assert "tmp" not in mgr.list_collections()
