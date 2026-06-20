"""
向量库工厂 (vector_store_factory) 单元测试
"""
import importlib

import pytest

from app.core import vector_store_factory
from app.core.vector_store import VectorStoreManager


def test_factory_default_returns_chroma():
    """默认（VECTOR_DB=chroma）应返回 ChromaDB 管理器。"""
    mgr = vector_store_factory.get_vector_store_manager("chroma")
    assert isinstance(mgr, VectorStoreManager)


def test_factory_unknown_falls_back_to_chroma():
    """未知后端名应回退到 ChromaDB。"""
    mgr = vector_store_factory.get_vector_store_manager("not-a-real-db")
    assert isinstance(mgr, VectorStoreManager)


def test_factory_milvus_dispatches(monkeypatch):
    """指定 milvus 时应实例化 MilvusVectorStoreManager（此处用桩替换）。"""
    created = {}

    class FakeMilvus:
        def __init__(self, *args, **kwargs):
            created["ok"] = True

    import app.core.milvus_store as milvus_store
    monkeypatch.setattr(milvus_store, "MilvusVectorStoreManager", FakeMilvus, raising=True)

    mgr = vector_store_factory.get_vector_store_manager("milvus")
    assert isinstance(mgr, FakeMilvus)
    assert created.get("ok") is True


def test_factory_reads_settings_default(monkeypatch):
    """未显式传参时读取 settings.VECTOR_DB。"""
    monkeypatch.setattr(vector_store_factory.settings, "VECTOR_DB", "chroma", raising=False)
    mgr = vector_store_factory.get_vector_store_manager()
    assert isinstance(mgr, VectorStoreManager)
