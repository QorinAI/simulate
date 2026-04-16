const form = document.querySelector("#life-form");
const fileInput = document.querySelector("#profile-file");
const fileName = document.querySelector("#file-name");
const loadSample = document.querySelector("#load-sample");
const backendStatus = document.querySelector("#backend-status");
const engineStatus = document.querySelector("#engine-status");
const resultPanel = document.querySelector("#result-panel");
const reviewPanel = document.querySelector("#review-panel");
const generateButton = document.querySelector("#generate-button");
const loadingPanel = document.querySelector("#loading-panel");
const loadingStage = document.querySelector("#loading-stage");
const branchGrid = document.querySelector("#branch-grid");
const compareGrid = document.querySelector("#compare-grid");
const timeline = document.querySelector("#timeline");
const evidenceList = document.querySelector("#evidence-list");
const missingList = document.querySelector("#missing-list");
const rerunList = document.querySelector("#rerun-list");
const resultTitle = document.querySelector("#result-title");
const resultSummary = document.querySelector("#result-summary");
const confidenceValue = document.querySelector("#confidence-value");
const resultEngine = document.querySelector("#result-engine");
const qualityWarning = document.querySelector("#quality-warning");
const qualityWarningText = document.querySelector("#quality-warning-text");
const profileSummary = document.querySelector("#profile-summary");
const profileQuestion = document.querySelector("#profile-question");
const profileMissing = document.querySelector("#profile-missing");

const sample = {
  name: "Alex",
  age: "29",
  location: "上海",
  career: "AI 产品经理",
  background:
    "过去几年主要在互联网和 AI 应用方向工作，做过增长、产品策略和模型体验评估。现在想判断未来 3 到 10 年应该继续走大厂产品路线、去海外读研，还是加入早期 AI 创业团队。比较在意长期成长、收入上限、生活稳定性和亲密关系。",
  interests:
    "喜欢 AI 产品、写作、心理学、城市生活、长期主义。希望未来不是只有工作，也要有关系、健康、创作和自由度。",
  question: "如果我未来两年在国内 AI 创业和出国读研之间选择，十年后会怎样？",
  constraints: "预算有限；不想长期 80 小时工作；希望 3 年内关系和城市生活更稳定。",
  risk: "6",
  balance: "8",
  mobility: "7",
  focus: "career",
  whatif: ["overseas", "startup"],
  engine: "deterministic",
};

let backendAvailable = false;
let currentProfile = null;
let currentPreview = null;

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function words(value) {
  return String(value || "")
    .split(/[\s,，;；、\n]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function labelForWhatIf(value) {
  return {
    overseas: "出国读研",
    startup: "加入创业团队",
    stable: "稳定现金流",
    family: "优先亲密关系",
  }[value] || value;
}

function formData() {
  const data = new FormData(form);
  return {
    name: String(data.get("name") || "你").trim() || "你",
    age: Number(data.get("age") || 29),
    location: String(data.get("location") || "未填写").trim(),
    career: String(data.get("career") || "未填写").trim(),
    background: String(data.get("background") || "").trim(),
    interests: String(data.get("interests") || "").trim(),
    question: String(data.get("question") || "").trim(),
    constraints: String(data.get("constraints") || "").trim(),
    focus: String(data.get("focus") || "whole"),
    risk: Number(data.get("risk") || 5),
    balance: Number(data.get("balance") || 5),
    mobility: Number(data.get("mobility") || 5),
    whatif: data.getAll("whatif"),
    engine: String(data.get("engine") || "deterministic"),
    includeSensitive: Boolean(data.get("includeSensitive")),
    localOnly: Boolean(data.get("localOnly")),
  };
}

function setForm(values) {
  Object.entries(values).forEach(([key, value]) => {
    if (key === "whatif") {
      form.querySelectorAll('input[name="whatif"]').forEach((input) => {
        input.checked = value.includes(input.value);
      });
      return;
    }
    const field = form.elements[key];
    if (!field) return;
    if (field instanceof RadioNodeList) {
      Array.from(field).forEach((input) => {
        input.checked = input.value === value;
      });
      return;
    }
    field.value = value;
  });
  updateSliderOutputs();
}

function updateSliderOutputs() {
  document.querySelector("#risk-value").textContent = form.elements.risk.value;
  document.querySelector("#balance-value").textContent = form.elements.balance.value;
  document.querySelector("#mobility-value").textContent = form.elements.mobility.value;
}

function renderList(target, items) {
  target.innerHTML = items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function setStep(activeStep) {
  document.querySelectorAll(".stepper li").forEach((item) => {
    item.classList.toggle("active", item.dataset.step === activeStep);
  });
}

function profileRichness(profile) {
  const fields = [
    profile.background.length > 120,
    profile.interests.length > 40,
    profile.question.length > 20,
    profile.constraints.length > 20,
    profile.location !== "未填写",
    profile.career !== "未填写",
    profile.whatif.length > 0,
  ];
  return fields.filter(Boolean).length / fields.length;
}

function missingSignals(profile) {
  const missing = [];
  if (profile.background.length < 120) missing.push("缺少连续经历和关键转折");
  if (!profile.interests || profile.interests.length < 30) missing.push("兴趣与价值观还太薄");
  if (!profile.constraints || profile.constraints.length < 20) missing.push("现实约束没有说清");
  if (!profile.question || profile.question.length < 20) missing.push("本次推演问题不够具体");
  if (!profile.includeSensitive) missing.push("关系、家庭、健康等高敏信息未纳入");
  return missing.slice(0, 5);
}

function normalizeProbabilities(items) {
  const total = items.reduce((sum, item) => sum + item.raw, 0);
  let assigned = 0;
  return items.map((item, index) => {
    const probability =
      index === items.length - 1
        ? Math.max(1, 100 - assigned)
        : Math.max(1, Math.round((item.raw / total) * 100));
    assigned += probability;
    return { ...item, probability };
  });
}

function localReading(profile) {
  const risk = profile.risk / 10;
  const balance = profile.balance / 10;
  const mobility = profile.mobility / 10;
  const has = (name) => profile.whatif.includes(name);
  const text = `${profile.background} ${profile.interests} ${profile.constraints}`.toLowerCase();
  const relationshipSignal = /(关系|家庭|伴侣|结婚|孩子|亲密)/.test(text) ? 0.08 : 0;
  const creatorSignal = /(写作|创作|内容|产品|创业|独立)/.test(text) ? 0.06 : 0;
  const missing = missingSignals(profile);
  const confidence = clamp(0.54 + profileRichness(profile) * 0.24 - missing.length * 0.025, 0.46, 0.86);
  const branches = normalizeProbabilities([
    {
      id: "steady",
      raw: 0.34 + balance * 0.11 - risk * 0.04 + (has("stable") ? 0.08 : 0),
      title: "稳步复利路径",
      tone: "green",
      landing: "在熟悉行业继续积累可信度，把职业上升、现金流和生活节奏放在同一张表里。",
      upside: ["稳定现金流让选择权变多", "人际和城市生活更容易沉淀"],
      watch: ["避免舒适区吞掉增长速度", "每 6 个月检查一次技能杠杆"],
    },
    {
      id: "bet",
      raw: 0.31 + risk * 0.14 + mobility * 0.07 + creatorSignal + (has("startup") ? 0.1 : 0),
      title: "高上限下注路径",
      tone: "red",
      landing: "把未来两年压到高密度 AI 机会里，换取更快的能力复利和更大的波动。",
      upside: ["可能更早进入核心决策层", "作品、网络和商业判断会快速压缩成长周期"],
      watch: ["工作强度会挤压关系和健康", "需要预设退出窗口而不是无限硬扛"],
    },
    {
      id: "reset",
      raw: 0.28 + mobility * 0.11 + balance * 0.03 + relationshipSignal + (has("overseas") ? 0.1 : 0),
      title: "迁移重塑路径",
      tone: "gold",
      landing: "用城市、学校或跨国环境重组身份和网络，但短期要承受现金流与归属感波动。",
      upside: ["新网络会改变中长期机会密度", "有机会重新定义生活方式"],
      watch: ["前 18 个月最容易怀疑选择", "关系和预算需要更早做压力测试"],
    },
  ])
    .sort((a, b) => b.probability - a.probability)
    .map((branch, index) => ({
      ...branch,
      confidence: Math.round((confidence - index * 0.03) * 100),
    }));

  const avgConfidence = Math.round(branches.reduce((sum, branch) => sum + branch.confidence, 0) / branches.length);
  const lead = branches[0];
  return {
    run_id: `local-${Date.now()}`,
    source: "browser-local-fallback",
    engine: {
      mode: "deterministic",
      provider: "browser",
      model: "deterministic-web-mvp",
    },
    profile,
    profile_review: {
      summary: `${profile.name}，${profile.age} 岁，当前在 ${profile.location}，身份是 ${profile.career}。`,
      decision_frame: profile.question || "本次还没有写清最想推演的问题。",
      missing,
    },
    one_screen: {
      title: `${profile.name} 的三条可能人生`,
      summary: `当前更像是“${lead.title}”领先，但不是命运预测。真正的分歧在于 ${profile.risk >= 6 ? "你愿意承受多大波动" : "你愿意牺牲多少上限"}，以及 ${profile.balance >= 7 ? "生活稳定能否成为主约束" : "生活稳定是否会被延后处理"}。`,
      confidence: avgConfidence,
    },
    branches,
    timeline: [
      {
        year: "现在",
        title: "确认问题边界",
        body: `${profile.name} 当前最重要的不是马上选“最佳人生”，而是把 ${profile.question || "核心选择"} 拆成可验证的 2 到 3 个假设。`,
      },
      {
        year: "1 年",
        title: "第一次硬分叉",
        body: `${lead.title} 会先考验节奏管理。若投入方向没有带来可见作品、收入信号或关系稳定感，需要降低承诺成本。`,
      },
      {
        year: "3 年",
        title: "路径开始显形",
        body: "职业、城市和关系会开始互相牵制。这个阶段最该看的是精力是否还能支持长期复利，而不是只看头衔变化。",
      },
      {
        year: "10 年",
        title: "生活形状落地",
        body: "最好的结果不是单点成功，而是职业杠杆、现金流、亲密关系和身体节奏之间形成可持续组合。",
      },
    ],
    trust: {
      evidence: [
        `当前身份：${profile.career}`,
        `城市与迁移：${profile.location}，迁移意愿 ${profile.mobility}/10`,
        `兴趣价值观：${words(profile.interests).slice(0, 6).join("、") || "未充分填写"}`,
        `约束：${profile.constraints || "未充分填写"}`,
        profile.whatif.length ? `What-if：${profile.whatif.map(labelForWhatIf).join("、")}` : "",
      ].filter(Boolean),
      missing: missing.length ? missing : ["关键输入足够生成第一版推演"],
      rerun: [
        !profile.includeSensitive ? "如果愿意，单独补充关系、家庭或健康约束，但保留删除权。" : "",
        "补一段最近两年真实选择经历，而不是只写目标。",
        "给每个 what-if 加一个可接受代价，例如预算、时间、关系压力。",
        "下一次重跑时只改一个关键变量，方便看出分支变化。",
      ].filter(Boolean),
    },
  };
}

async function apiJson(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`API ${path} failed: ${response.status}`);
  return response.json();
}

async function checkBackend() {
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    backendAvailable = response.ok;
  } catch {
    backendAvailable = false;
  }
  backendStatus.textContent = backendAvailable ? "本地 API 已连接" : "浏览器本地模式";
  updateEngineStatus(formData().engine);
}

async function getPreview(profile) {
  if (!backendAvailable) return localReading(profile);
  try {
    return await apiJson("/api/profile", profile);
  } catch {
    backendAvailable = false;
    backendStatus.textContent = "浏览器本地模式";
    return localReading(profile);
  }
}

async function getReading(profile) {
  if (!backendAvailable) return localReading(profile);
  try {
    return await apiJson(`/api/simulate?engine=${encodeURIComponent(profile.engine)}`, profile);
  } catch {
    backendAvailable = false;
    backendStatus.textContent = "浏览器本地模式";
    return localReading(profile);
  }
}

function renderReview(preview) {
  const review = preview.profile_review || {};
  profileSummary.textContent = review.summary || "画像摘要生成失败。";
  profileQuestion.textContent = review.decision_frame || currentProfile.question || "未填写问题。";
  renderList(profileMissing, review.missing || preview.trust?.missing || []);
  reviewPanel.hidden = false;
  setStep("review");
}

function renderReading(reading) {
  const oneScreen = reading.one_screen || {};
  const branches = reading.branches || [];
  const trust = reading.trust || {};
  const quality = reading.quality || {};
  const chineseQuality = quality.chinese_artifacts || quality.chinese_report || {};
  const betaBlockers = quality.beta_blockers || [];
  resultTitle.textContent = oneScreen.title || `${currentProfile.name} 的三条可能人生`;
  resultSummary.textContent = oneScreen.summary || "路径会基于你提供的背景、兴趣、约束和 what-if 权重重新生成。";
  confidenceValue.textContent = `${oneScreen.confidence || 0}%`;
  const engine = reading.engine || {};
  const engineLabel =
    engine.mode === "simulate_life"
      ? `Kimi 2.5 (${engine.provider || "moonshot"})`
      : "deterministic";
  resultEngine.textContent = `本次使用：${engineLabel}`;
  updateEngineStatus(engine.mode || currentProfile.engine);

  branchGrid.innerHTML = branches
    .map(
      (branch, index) => `
        <article class="branch-card" data-tone="${branch.tone}">
          <div class="branch-top">
            <span class="branch-index">Path ${index + 1}</span>
            <span class="tag">${branch.confidence}% 置信</span>
          </div>
          <h3 class="branch-title">${escapeHtml(branch.title)}</h3>
          <div class="branch-meta">
            <span class="probability">${branch.probability}%</span>
            <span class="confidence">情景权重</span>
          </div>
          <div class="bar" style="color: var(--${branch.tone})">
            <span style="width:${branch.probability}%"></span>
          </div>
          <p>${escapeHtml(branch.landing)}</p>
          <div class="branch-columns">
            <div>
              <h4>获得什么</h4>
              <ul>${(branch.upside || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
            </div>
            <div>
              <h4>失去什么</h4>
              <ul>${(branch.watch || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
            </div>
          </div>
        </article>
      `,
    )
    .join("");

  compareGrid.innerHTML = branches
    .map(
      (branch) => `
        <div class="compare-card">
          <h4>${escapeHtml(branch.title)}</h4>
          <dl>
            <div><dt>机会</dt><dd>${escapeHtml((branch.upside || [])[0] || "待补充")}</dd></div>
            <div><dt>代价</dt><dd>${escapeHtml((branch.watch || [])[0] || "待补充")}</dd></div>
            <div><dt>生活节奏</dt><dd>${branch.id === "bet" ? "高密度" : branch.id === "reset" ? "重适应" : "可持续"}</dd></div>
            <div><dt>现金流</dt><dd>${branch.id === "reset" ? "短期承压" : branch.id === "bet" ? "波动更大" : "更稳定"}</dd></div>
          </dl>
        </div>
      `,
    )
    .join("");

  timeline.innerHTML = (reading.timeline || [])
    .map(
      (row) => `
        <div class="timeline-row">
          <div class="timeline-year">${escapeHtml(row.year)}</div>
          <div class="timeline-body">
            <h4>${escapeHtml(row.title)}</h4>
            <p>${escapeHtml(row.body)}</p>
          </div>
        </div>
      `,
    )
    .join("");

  renderList(evidenceList, trust.evidence || []);
  renderList(missingList, trust.missing || []);
  const rerunItems = [...(trust.rerun || [])];
  if (betaBlockers.includes("chinese_report_fluency_not_beta_ready")) {
    rerunItems.unshift(chineseQuality.summary || "中文报告还不够通顺，不能进入 beta。");
    qualityWarning.hidden = false;
    qualityWarningText.textContent =
      chineseQuality.summary || "中文报告还不够通顺，不能进入 beta。";
  } else {
    qualityWarning.hidden = true;
    qualityWarningText.textContent = "";
  }
  renderList(rerunList, rerunItems);
}

async function showLoading() {
  const stages = ["解析画像", "构建分支", "检查可信度", "组装结果"];
  const isKimi = (currentProfile?.engine || "") === "simulate_life";
  resultPanel.setAttribute("aria-busy", "true");
  loadingPanel.hidden = false;
  generateButton.disabled = true;
  generateButton.dataset.originalLabel = generateButton.textContent;
  generateButton.textContent = isKimi ? "正在调用 Kimi 2.5..." : "正在生成...";
  for (const stage of stages) {
    loadingStage.textContent = stage;
    await new Promise((resolve) => setTimeout(resolve, isKimi ? 750 : 180));
  }
}

function hideLoading() {
  loadingPanel.hidden = true;
  generateButton.disabled = false;
  generateButton.textContent = generateButton.dataset.originalLabel || "生成路径";
  resultPanel.setAttribute("aria-busy", "false");
}

function updateEngineStatus(engine) {
  engineStatus.textContent = engine === "simulate_life" ? "Kimi 2.5" : "deterministic";
}

fileInput.addEventListener("change", () => {
  const [file] = fileInput.files;
  if (!file) return;
  fileName.textContent = file.name;
  const reader = new FileReader();
  reader.onload = () => {
    const existing = form.elements.background.value.trim();
    form.elements.background.value = [existing, String(reader.result || "").trim()]
      .filter(Boolean)
      .join("\n\n");
  };
  reader.readAsText(file);
});

form.addEventListener("input", (event) => {
  if (event.target.matches('input[type="range"]')) updateSliderOutputs();
  if (event.target.matches('input[name="engine"]')) updateEngineStatus(event.target.value);
  setStep("intake");
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  currentProfile = formData();
  currentPreview = await getPreview(currentProfile);
  renderReview(currentPreview);
  reviewPanel.scrollIntoView({ behavior: "smooth", block: "start" });
});

generateButton.addEventListener("click", async () => {
  currentProfile = currentProfile || formData();
  setStep("result");
  await showLoading();
  const reading = await getReading(currentProfile);
  hideLoading();
  renderReading(reading);
});

loadSample.addEventListener("click", () => {
  setForm(sample);
  fileInput.value = "";
  fileName.textContent = "可上传简历、自述、兴趣清单或人生困惑";
  setStep("intake");
});

setForm(sample);
updateSliderOutputs();
checkBackend();
const initialReading = localReading(formData());
currentProfile = formData();
currentPreview = initialReading;
renderReview(initialReading);
renderReading(initialReading);
