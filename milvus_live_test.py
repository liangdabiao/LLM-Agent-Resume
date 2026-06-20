"""
Milvus / Zilliz Cloud 在线连通性测试（使用 .env 中的真实连接信息）。

为避免污染业务集合，本脚本使用带时间戳的临时集合
`resume_screening_tmp_<ts>`，完成 插入 -> 检索 -> 校验 后立即删除。

运行：
    python milvus_live_test.py
依赖：
    - 已安装 pymilvus
    - .env 中配置 MILVUS_HOST/PORT(或 MILVUS_URI)、MILVUS_TOKEN
    - 有效的 Embedding key（用于生成查询向量）
"""
import sys
import time

from config.config import settings


def main():
    ts = int(time.time())
    tmp_collection = f"resume_screening_tmp_{ts}"
    failures = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print(f"[{status}] {name} {detail}")
        if not cond:
            failures.append(name)

    print(f"MILVUS_URI = {settings.MILVUS_URI}")
    print(f"INDEX      = {settings.MILVUS_INDEX}")
    print(f"DIMENSIONS = {settings.EMBEDDING_DIMENSIONS}")
    print(f"临时集合   = {tmp_collection}\n")

    if not settings.MILVUS_URI:
        print("[FAIL] 未配置 MILVUS_URI / MILVUS_HOST，无法测试")
        sys.exit(1)

    from app.core.milvus_store import MilvusVectorStoreManager

    mgr = MilvusVectorStoreManager()

    # 0) 连通性 + 鉴权：list_collections 成功即说明连接/Token 有效
    try:
        existing = mgr.list_collections()
        check("connect & list collections", isinstance(existing, list),
              f"-> existing={existing}")
    except Exception as e:
        check("connect & list collections", False, f"-> {e}")
        print("\n==== SUMMARY ====")
        print(f"FAILED: {failures}")
        sys.exit(1)

    # Zilliz Serverless 免费实例有集合数量上限（通常 5 个）。
    # 若已达上限则无法创建临时集合 —— 此时不删除任何业务集合，仅跳过写入测试。
    COLLECTION_LIMIT = 5
    if len(existing) >= COLLECTION_LIMIT:
        print(
            f"\n[SKIP] 实例已有 {len(existing)} 个集合，达到上限（{COLLECTION_LIMIT}）。"
            f"\n       连接与鉴权已验证通过，但无法创建临时集合进行写入/检索测试。"
            f"\n       如需完整在线测试，请在 Zilliz 控制台释放一个集合槽位或升级实例，"
            f"\n       然后重新运行本脚本。"
        )
        print("\n==== SUMMARY ====")
        print("CONNECTIVITY VERIFIED (write/query test skipped due to collection limit)")
        return

    try:
        # 1) 创建临时集合
        mgr.create_collection(tmp_collection)
        check("create temp collection", tmp_collection in mgr.list_collections())

        # 2) 插入文档
        mgr.add_documents(
            collection_name=tmp_collection,
            documents=[
                "张三，5年Python后端开发经验，精通FastAPI与分布式系统，本科学历，北京。",
                "李四，前端工程师，熟悉React与TypeScript，硕士学历，上海。",
            ],
            metadatas=[
                {"name": "张三", "skills": ["Python", "FastAPI"], "location": "北京"},
                {"name": "李四", "skills": ["React", "TypeScript"], "location": "上海"},
            ],
            ids=["live_r1", "live_r2"],
        )
        check("add documents", True)

        # Milvus 写入到可检索有秒级延迟，稍作等待
        time.sleep(2)

        # 3) 语义检索
        res = mgr.query_collection(
            collection_name=tmp_collection,
            query_texts=["寻找有Python和FastAPI经验的后端工程师"],
            n_results=2,
        )
        ids = res.get("ids", [[]])
        check("query returns 2d structure", isinstance(ids, list) and isinstance(ids[0], list),
              f"-> {ids}")
        hit_ids = ids[0] if ids else []
        check("query hits inserted docs", "live_r1" in hit_ids, f"-> {hit_ids}")

        if "live_r1" in hit_ids:
            idx = hit_ids.index("live_r1")
            meta = res["metadatas"][0][idx]
            check("metadata deserialized to list", isinstance(meta.get("skills"), list),
                  f"-> skills={meta.get('skills')}")
            doc = res["documents"][0][idx]
            check("document text returned", bool(doc), f"-> len={len(doc or '')}")

    finally:
        # 4) 清理临时集合
        try:
            mgr.delete_collection(tmp_collection)
            cleaned = tmp_collection not in mgr.list_collections()
            check("cleanup temp collection", cleaned)
        except Exception as e:
            check("cleanup temp collection", False, f"-> {e}")

    print("\n==== SUMMARY ====")
    if failures:
        print(f"FAILED: {len(failures)} -> {failures}")
        sys.exit(1)
    print("ALL MILVUS LIVE CHECKS PASSED")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"Elapsed: {time.time() - t0:.1f}s")
