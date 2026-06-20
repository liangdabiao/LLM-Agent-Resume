"""
全链路真实集成测试（使用 .env 中的真实智谱 key）。
不经过 pytest，因此不会触发 conftest 的假嵌入，真正打通 LLM + Embedding + API。
"""
import io
import sys
import time

from fastapi.testclient import TestClient

# 导入应用（routes 在导入时会用真实 key 实例化各组件）
from app.main import app  # noqa


def main():
    client = TestClient(app)
    failures = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print(f"[{status}] {name} {detail}")
        if not cond:
            failures.append(name)

    # 1) 健康检查
    r = client.get("/api/v1/health")
    check("health", r.status_code == 200 and r.json().get("status") == "ok", f"-> {r.status_code}")

    # 1b) 内置前端页面可访问 + 根路径重定向
    r = client.get("/ui/")
    check("ui page served", r.status_code == 200 and "简历筛选" in r.text, f"-> {r.status_code}")
    r = client.get("/", follow_redirects=False)
    check("root redirects to /ui", r.status_code in (307, 308) and "/ui" in r.headers.get("location", ""),
          f"-> {r.status_code} {r.headers.get('location')}")

    # 1c) 简历列表（初始为空或含历史数据）
    r = client.get("/api/v1/resumes")
    check("list resumes", r.status_code == 200 and "resumes" in r.json(), f"-> {r.status_code}")

    # 2) 上传两份简历（txt）
    resume_a = (
        "张三\n邮箱: zhangsan@example.com\n电话: 13800000000\n"
        "拥有5年Python后端开发经验(2019-01 至 2024-01)，精通 Django、FastAPI、PostgreSQL。\n"
        "本科毕业于计算机科学专业。期望工作地点：北京。"
    )
    resume_b = (
        "李四\n邮箱: lisi@example.com\n"
        "应届毕业生，熟悉 Java 与 Spring，1年实习经验。硕士学历。期望工作地点：上海。"
    )

    ids = []
    for fname, text in [("zhangsan.txt", resume_a), ("lisi.txt", resume_b)]:
        files = {"file": (fname, io.BytesIO(text.encode("utf-8")), "text/plain")}
        r = client.post("/api/v1/resumes", files=files)
        check(f"upload {fname}", r.status_code == 200, f"-> {r.status_code} {r.text[:200]}")
        if r.status_code == 200:
            ids.append(r.json()["resume_id"])

    # 3) 获取简历详情
    if ids:
        r = client.get(f"/api/v1/resumes/{ids[0]}")
        meta = r.json().get("metadata", {}) if r.status_code == 200 else {}
        check("get_resume detail", r.status_code == 200, f"-> name={meta.get('name')}")

    # 4) 提交查询
    query_text = "寻找3年以上Python开发经验、会Django、工作地点北京的工程师"
    r = client.post("/api/v1/queries", json={"query_text": query_text})
    check("submit_query", r.status_code == 200, f"-> {r.status_code} {r.text[:200]}")
    query_id = r.json()["query_id"] if r.status_code == 200 else None

    # 5) 获取筛选结果（全流程：检索→过滤→评分→排序→分析→格式化）
    if query_id:
        r = client.get(f"/api/v1/results/{query_id}")
        ok = r.status_code == 200
        check("get_results", ok, f"-> {r.status_code} {r.text[:300]}")
        if ok:
            data = r.json()
            cands = data.get("candidates", [])
            check("results has candidates", len(cands) >= 1, f"-> total={data.get('total_candidates')}")
            if cands:
                top = cands[0]
                print(f"    Top candidate: name={top.get('name')} score={top.get('overall_score')} "
                      f"skills={top.get('skills')}")
                check("top candidate has analysis", bool(top.get("analysis")),
                      f"-> analysis_len={len(top.get('analysis') or '')}")
                check("top candidate is 张三 (北京/Python)",
                      top.get("name") == "张三" or any("Python" in str(s) for s in top.get("skills", [])))

    # 6) 错误路径：不存在的查询/简历
    r = client.get("/api/v1/results/not-exist-id")
    check("missing query -> 404", r.status_code == 404, f"-> {r.status_code}")
    r = client.get("/api/v1/resumes/not-exist-id")
    check("missing resume -> 404", r.status_code == 404, f"-> {r.status_code}")

    print("\n==== SUMMARY ====")
    if failures:
        print(f"FAILED: {len(failures)} -> {failures}")
        sys.exit(1)
    print("ALL INTEGRATION CHECKS PASSED")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"Elapsed: {time.time() - t0:.1f}s")
