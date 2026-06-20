// 智能简历筛选系统 - 前端逻辑
const API = "/api/v1";

const $ = (id) => document.getElementById(id);

// ---------------- 健康检查 ----------------
async function checkHealth() {
  const badge = $("health-badge");
  try {
    const res = await fetch(`${API}/health`);
    const data = await res.json();
    if (res.ok && data.status === "ok") {
      badge.textContent = "正常";
      badge.className = "badge badge-ok";
    } else {
      throw new Error("异常");
    }
  } catch (e) {
    badge.textContent = "无法连接";
    badge.className = "badge badge-err";
  }
}

// ---------------- 上传简历 ----------------
async function uploadResumes() {
  const input = $("resume-files");
  const log = $("upload-log");
  const btn = $("upload-btn");
  const files = Array.from(input.files || []);
  if (files.length === 0) {
    log.innerHTML = '<span class="err">请先选择文件</span>';
    return;
  }
  btn.disabled = true;
  let ok = 0, fail = 0;
  log.textContent = `开始上传 ${files.length} 个文件…`;
  for (const file of files) {
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await fetch(`${API}/resumes`, { method: "POST", body: fd });
      const data = await res.json();
      if (res.ok) {
        ok++;
        log.innerHTML += `\n<span class="ok">✓ ${file.name} 上传成功</span>`;
      } else {
        fail++;
        log.innerHTML += `\n<span class="err">✗ ${file.name}: ${data.detail || "失败"}</span>`;
      }
    } catch (e) {
      fail++;
      log.innerHTML += `\n<span class="err">✗ ${file.name}: ${e.message}</span>`;
    }
  }
  log.innerHTML += `\n完成：成功 ${ok}，失败 ${fail}`;
  btn.disabled = false;
  input.value = "";
  loadResumeList();
}

// ---------------- 简历列表 ----------------
async function loadResumeList() {
  const list = $("resume-list");
  const count = $("resume-count");
  try {
    const res = await fetch(`${API}/resumes`);
    const data = await res.json();
    count.textContent = `(${data.total})`;
    if (!data.resumes || data.resumes.length === 0) {
      list.innerHTML = '<li class="empty">暂无简历</li>';
      return;
    }
    list.innerHTML = data.resumes.map((r) => `
      <li>
        <div class="fn">${r.name || r.filename || "(未命名)"}</div>
        <div class="rid">${r.filename || ""} · ${r.resume_id}</div>
      </li>`).join("");
  } catch (e) {
    list.innerHTML = `<li class="empty">加载失败：${e.message}</li>`;
  }
}

// ---------------- 提交查询 + 获取结果 ----------------
async function runQuery() {
  const text = $("query-text").value.trim();
  const log = $("query-log");
  const btn = $("query-btn");
  const results = $("results");
  const meta = $("result-meta");
  if (!text) {
    log.innerHTML = '<span class="err">请输入岗位需求</span>';
    return;
  }
  btn.disabled = true;
  meta.textContent = "";
  results.innerHTML = '<div class="spinner">正在解析查询并筛选候选人，请稍候…</div>';
  log.textContent = "提交查询中…";
  try {
    // 1. 提交查询
    const qres = await fetch(`${API}/queries`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query_text: text }),
    });
    const qdata = await qres.json();
    if (!qres.ok) throw new Error(qdata.detail || "提交查询失败");
    const queryId = qdata.query_id;
    log.innerHTML = `<span class="ok">查询已提交 (${queryId})，正在评估候选人…</span>`;

    // 2. 拉取结果
    const rres = await fetch(`${API}/results/${queryId}`);
    const rdata = await rres.json();
    if (!rres.ok) throw new Error(rdata.detail || "获取结果失败");
    renderResults(rdata);
  } catch (e) {
    results.innerHTML = `<div class="empty">出错：${e.message}</div>`;
    log.innerHTML = `<span class="err">${e.message}</span>`;
  } finally {
    btn.disabled = false;
  }
}

function renderResults(data) {
  const results = $("results");
  const meta = $("result-meta");
  meta.textContent = `(共 ${data.total_candidates} 位候选人)`;
  $("query-log").innerHTML = '<span class="ok">筛选完成</span>';

  if (!data.candidates || data.candidates.length === 0) {
    results.innerHTML = '<div class="empty">没有符合条件的候选人。</div>';
    return;
  }
  results.innerHTML = data.candidates.map((c) => {
    const skills = (c.skills || []).map((s) => `<span class="tag">${s}</span>`).join("");
    const locations = (c.preferred_locations || []).join("、");
    const score = (c.overall_score != null) ? Number(c.overall_score).toFixed(1) : "-";
    return `
      <div class="candidate">
        <div class="candidate-head">
          <div><span class="rank">${c.rank}</span><span class="name">${c.name || "(未命名)"}</span></div>
          <div class="score">${score} 分</div>
        </div>
        <div class="meta">
          ${c.email ? "📧 " + c.email + "　" : ""}${c.phone ? "📱 " + c.phone : ""}
          ${locations ? "<br>📍 期望地点：" + locations : ""}
          ${c.expected_salary ? "<br>💰 期望薪资：" + c.expected_salary : ""}
        </div>
        ${skills ? `<div class="skills">${skills}</div>` : ""}
        ${c.analysis ? `<div class="analysis">${c.analysis}</div>` : ""}
      </div>`;
  }).join("");
}

// ---------------- 事件绑定 ----------------
$("upload-btn").addEventListener("click", uploadResumes);
$("refresh-btn").addEventListener("click", loadResumeList);
$("query-btn").addEventListener("click", runQuery);

checkHealth();
loadResumeList();
setInterval(checkHealth, 30000);
