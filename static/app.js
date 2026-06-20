// 智能简历筛选系统 - 前端逻辑
const API = "/api/v1";

const $ = (id) => document.getElementById(id);

// 转义 HTML，防止 XSS
function escapeHtml(text) {
  if (text == null) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// 简单 Markdown 渲染：标题、加粗、斜体、列表、代码块
function markdownToHtml(md) {
  if (!md) return "";
  const lines = md.split("\n");
  let html = "";
  let inList = false;
  let listType = null;

  const closeList = () => {
    if (inList) {
      html += listType === "ol" ? "</ol>" : "</ul>";
      inList = false;
      listType = null;
    }
  };

  const inline = (text) => {
    return escapeHtml(text)
      .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, "<em>$1</em>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) { closeList(); continue; }
    const headerMatch = trimmed.match(/^(#{1,6})\s+(.*)$/);
    if (headerMatch) {
      closeList();
      const level = Math.min(headerMatch[1].length + 2, 6);
      html += `<h${level}>${inline(headerMatch[2])}</h${level}>`;
      continue;
    }
    const ulMatch = trimmed.match(/^[-*]\s+(.*)$/);
    if (ulMatch) {
      if (!inList || listType !== "ul") { closeList(); html += "<ul>"; inList = true; listType = "ul"; }
      html += `<li>${inline(ulMatch[1])}</li>`;
      continue;
    }
    const olMatch = trimmed.match(/^\d+\.\s+(.*)$/);
    if (olMatch) {
      if (!inList || listType !== "ol") { closeList(); html += "<ol>"; inList = true; listType = "ol"; }
      html += `<li>${inline(olMatch[1])}</li>`;
      continue;
    }
    closeList();
    html += `<p>${inline(line)}</p>`;
  }

  closeList();
  return html;
}

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
        log.innerHTML += `\n<span class="ok">✓ ${escapeHtml(file.name)} 上传成功</span>`;
      } else {
        fail++;
        log.innerHTML += `\n<span class="err">✗ ${escapeHtml(file.name)}: ${escapeHtml(data.detail || "失败")}</span>`;
      }
    } catch (e) {
      fail++;
      log.innerHTML += `\n<span class="err">✗ ${escapeHtml(file.name)}: ${escapeHtml(e.message)}</span>`;
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
        <div class="fn">${escapeHtml(r.name || r.filename || "(未命名)")}</div>
        <div class="rid">${escapeHtml(r.filename || "")} · ${escapeHtml(r.resume_id)}</div>
      </li>`).join("");
  } catch (e) {
    list.innerHTML = `<li class="empty">加载失败：${escapeHtml(e.message)}</li>`;
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
    const qres = await fetch(`${API}/queries`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query_text: text }),
    });
    const qdata = await qres.json();
    if (!qres.ok) throw new Error(qdata.detail || "提交查询失败");
    const queryId = qdata.query_id;
    log.innerHTML = `<span class="ok">查询已提交 (${escapeHtml(queryId)})，正在评估候选人…</span>`;

    const rres = await fetch(`${API}/results/${queryId}`);
    const rdata = await rres.json();
    if (!rres.ok) throw new Error(rdata.detail || "获取结果失败");
    renderResults(rdata);
  } catch (e) {
    results.innerHTML = `<div class="empty">出错：${escapeHtml(e.message)}</div>`;
    log.innerHTML = `<span class="err">${escapeHtml(e.message)}</span>`;
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
    const skills = (c.skills || []).map((s) => `<span class="tag">${escapeHtml(s)}</span>`).join("");
    const locations = escapeHtml((c.preferred_locations || []).join("、"));
    const scorePercent = (c.overall_score != null) ? Math.round(c.overall_score * 100) : "-";
    const email = c.email ? "📧 " + escapeHtml(c.email) + "　" : "";
    const phone = c.phone ? "📱 " + escapeHtml(c.phone) : "";
    const salary = c.expected_salary ? "<br>💰 期望薪资：" + escapeHtml(c.expected_salary) : "";
    const analysis = c.analysis ? `<div class="analysis">${markdownToHtml(c.analysis)}</div>` : "";
    return `
      <div class="candidate">
        <div class="candidate-head">
          <div><span class="rank">${escapeHtml(c.rank)}</span><span class="name">${escapeHtml(c.name || "(未命名)")}</span></div>
          <div class="score">${escapeHtml(scorePercent)}%</div>
        </div>
        <div class="meta">
          ${email}${phone}
          ${locations ? "<br>📍 期望地点：" + locations : ""}
          ${salary}
        </div>
        ${skills ? `<div class="skills">${skills}</div>` : ""}
        ${analysis}
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
